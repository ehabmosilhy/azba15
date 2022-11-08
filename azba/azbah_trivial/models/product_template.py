from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for product in self:
            product.display_name = f'[{product.code}] {product.name}' if product.code else product.name or ''

    english_name = fields.Char(string="English Name")
    code = fields.Char(string="الكود Code")
    display_name = fields.Char(compute='_compute_display_name', store=True, readonly=False)

    _sql_constraints = [('code_uniq', 'unique (code)', """Code must be unique هذا الكود موجود من قبل!""")]


class ResPartner(models.Model):
    _inherit = "res.partner"
    arabic_name = fields.Char(string="Arabic Name")
