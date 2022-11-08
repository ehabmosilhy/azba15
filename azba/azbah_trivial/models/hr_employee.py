from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning


class HREmployee(models.Model):
    _inherit = "hr.employee"
    _order = "display_name"

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for emp in self:
            emp.display_name = f'[{emp.code}] {emp.name}' if emp.code else emp.name or ''

    code = fields.Char()

    _sql_constraints = [
        ('code_uniq', 'unique (code)', """Code must be unique هذا الكود موجود من قبل!"""),
    ]
    english_name = fields.Char("English Name")
    partner_id = fields.Many2one('res.partner', string="Contact")

    display_name = fields.Char(compute='_compute_display_name', store=True, readonly=False)

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

class HREmployeePublic(models.Model):
    _inherit = "hr.employee.public"
    code = fields.Char()
