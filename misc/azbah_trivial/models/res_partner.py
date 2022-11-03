

from odoo import fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"
    english_name = fields.Char()
    code = fields.Char(string="الكود Code")
    district = fields.Many2one("geography.district", string="الحي District")

