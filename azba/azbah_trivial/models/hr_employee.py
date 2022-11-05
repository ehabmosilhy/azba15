from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class HREmployee(models.Model):
    _inherit = "hr.employee"

    code = fields.Char()
    english_name = fields.Char("English Name")
    partner_id = fields.Many2one('res.partner', string="Contact")

    @api.model
    def create(self, vals):
        _partner_record = {"name": vals['name']
            , "code": vals.get('code') if vals.get('code') else None
                           }
        partner_id = self.env['res.partner'].sudo().create(_partner_record).id

        vals['partner_id'] = partner_id
        vals['address_home_id'] = partner_id

        res = super(HREmployee, self).create(vals)
        return res
