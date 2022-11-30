from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.product"

    def name_get(self):
        result = []
        for rec in self:
            if rec.product_tmpl_id.code or rec.code:
                result.append((rec.id, '[%s] - %s' % (rec.product_tmpl_id.code or rec.code, rec.name)))
            else:
                result.append((rec.id, '%s' % (rec.name)))
        return result