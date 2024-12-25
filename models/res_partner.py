from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
import xmlrpc

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_type = fields.Selection([('owner', 'Owner'), ('user', 'User')], default='user',tracking=True)
    server_link = fields.Char()
    database_name = fields.Char()
    username = fields.Char()
    password = fields.Char()
    subscription_type = fields.Selection([('online', 'Online'), ('offline', 'Offline'), ('hybrid', 'Hybrid')],
                                         default='online',tracking=True)
    customer_code = fields.Char(string="Customer Code", readonly=True)
    no_of_days = fields.Integer(tracking=True)
    api_key = fields.Char()
    token = fields.Char()
    device_line_ids = fields.Many2many('res.device.configuration')

    def sync_with_client_server(self):
        """
        Synchronize with the client server using XML-RPC.
        """
        for record in self:
            if not record.server_link or not record.database_name or not record.username or not record.password:
                raise UserError(_("Please provide server details, database name, username, and password."))

            try:
                # Connect to Client Server
                common = xmlrpc.client.ServerProxy(f"{record.server_link}/xmlrpc/2/common")
                uid = common.authenticate(record.database_name, record.username, record.password, {})
                if not uid:
                    raise UserError(_("Invalid credentials for the Client Server."))

                models = xmlrpc.client.ServerProxy(f"{record.server_link}/xmlrpc/2/object")

                # Update token_validity_hours and subscription_type on Client Server
                token_validity_hours = record.no_of_days * 24
                subscription_type = record.subscription_type
                models.execute_kw(record.database_name, uid, record.password, 'res.users', 'write', [[uid], {
                    'token_validity_hours': token_validity_hours,
                    'subscription_type': subscription_type,
                }])

                # Call generate_auth_details function on Client Server
                auth_details = models.execute_kw(
                    record.database_name, uid, record.password,
                    'res.users', 'generate_auth_details',
                    [record.username, record.password]
                )

                if auth_details.get('status') == 'success':
                    record.api_key = auth_details.get('api_key')
                    record.token = auth_details.get('token')

                    # Check and create cameras on Client Server
                    for device in record.device_line_ids:
                        camera_exist = models.execute_kw(
                            record.database_name, uid, record.password,
                            'res.camera', 'search',
                            [[('name', '=', device.name)]]
                        )
                        if not camera_exist:
                            models.execute_kw(
                                record.database_name, uid, record.password,
                                'res.camera', 'create',
                                [{'name': device.name,'mac_id': device.mac_id}]
                            )
                else:
                    raise UserError(_("Error during authentication: %s") % auth_details.get('message'))

            except Exception as e:
                raise UserError(_("An error occurred: %s") % str(e))

    @api.constrains('device_line_ids')
    def _check_device_uniqueness(self):
        """
        Ensure no device is assigned to multiple partners and update device states.
        """
        for partner in self:
            assigned_devices = partner.device_line_ids
            for device in assigned_devices:
                # Check if the device is assigned to another partner
                other_partners = self.env['res.partner'].search([
                    ('id', '!=', partner.id),
                    ('device_line_ids', 'in', device.id)
                ])
                if other_partners:
                    raise ValidationError(
                        _('The device "%s" is already assigned to another partner: %s') % (
                            device.name,
                            ', '.join(other_partners.mapped('name'))
                        )
                    )
                # Update the device state to 'assigned'
                device.state = 'assigned'
                device.partner_id = partner.id

            # Update the state of devices that are no longer assigned to this partner
            all_devices = self.env['res.device.configuration'].search([('partner_id', '=', partner.id)])
            unlinked_devices = all_devices - assigned_devices
            for device in unlinked_devices:
                device.state = 'draft'

    def action_generate_customer_code(self):
        """Generate customer_code as a sequence."""
        for partner in self:
            if not partner.customer_code:
                partner.customer_code = self.env['ir.sequence'].next_by_code('res.partner.customer.code')
            else:
                raise ValueError("Customer Code already exists for this partner.")

    @api.model
    def action_generate_customer_code_xmlrpc(self, contact):
        """Generate customer_code as a sequence."""
        partner = self.env['res.partner'].sudo().search([('id', '=', contact)], limit=1)
        if not partner:
            raise ValueError("Partner not found.")

        if not partner.customer_code:
            partner.customer_code = self.env['ir.sequence'].next_by_code('res.partner.customer.code')
        else:
            raise ValueError("Customer Code already exists for this partner.")

        return partner.customer_code  # Explicitly return the generated customer code

    @api.model
    def get_auth_details_from_server(self, customer_code):
        """
        Retrieve server details for the customer based on the given customer code.
        :param customer_code: The unique code identifying the customer.
        :return: Server details or an error message if the customer is not found.
        """
        # Search for the customer using customer_code
        customer = self.search([('customer_code', '=', customer_code)], limit=1)

        if not customer:
            return {'status': 'error', 'message': f'No customer found with code {customer_code}'}

        # Extract and return the customer's server details
        return {
            'status': 'success',
            'server_url': customer.server_link,
            'db_name': customer.database_name,
            'username': customer.username,
            'password': customer.password,
        }
