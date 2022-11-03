

from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"
    english_name = fields.Char(string="English Name")
    code = fields.Char(string="الكود Code")

