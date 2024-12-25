from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ResDeviceConfiguration(models.Model):
    _name = 'res.device.configuration'
    _description = 'Res Device Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('res.device.configuration.code') or _('New')

        result = super(ResDeviceConfiguration, self).create(vals)
        return result

    @api.constrains('mac_id')
    def _check_mac_id_unique(self):
        for record in self:
            if record.mac_id and self.search_count([('mac_id', '=', record.mac_id), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_('The MAC ID must be unique. The MAC ID "%s" is already in use.') % record.mac_id)

    name = fields.Char(
        string="Sequence",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    mac_id = fields.Char(string="MAC ID",tracking=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one('res.partner',string="Customer",tracking=True)
    state = fields.Selection([('draft','Draft'),('assigned','Assigned')],default='draft',tracking=True)

    def reset_draft(self):
        """
        Reset the device state to 'draft', remove the partner association,
        and delete the record from device_line_ids in res.partner.
        """
        for device in self:
            if device.partner_id:
                # Remove the device from the partner's device_line_ids
                device.partner_id.device_line_ids = [(3, device.id)]

            # Reset the state and clear the partner_id
            device.state = 'draft'
            device.partner_id = None

