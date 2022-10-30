from odoo import api, fields, models, _


class HRPermission(models.Model):
    _name = 'hr.permissions'
    _description = 'Hr Permissions'

    name = fields.Char(string="النوع", required=True)
    code = fields.Char(string="الكود")
