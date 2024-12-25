from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def check_device_status(self, mac_id):
        """
        Check the device configuration by MAC ID and return partner subscription details.

        :param mac_id: MAC ID of the device
        :return: JSON with partner subscription details
        """
        try:
            # Search for the device by its name field
            device = self.env['res.device.configuration'].search([('mac_id', '=', mac_id)], limit=1)
            if not device:
                return {"status": "error", "message": "Device not found"}

            # Get the partner associated with the device
            partner = device.partner_id
            if not partner:
                return {"status": "error", "message": "Device is not linked to any partner"}

            # Collect partner subscription details
            data = {
                "status": "success",
                "server_link": partner.server_link,
                "database_name": partner.database_name,
                "username": partner.username,
                "password": partner.password,
                "subscription_type": partner.subscription_type,
                "no_of_days": partner.no_of_days,
                "api_key": partner.api_key,
                "token": partner.token,
            }
            return data
        except Exception as e:
            return {"status": "error", "message": str(e)}
