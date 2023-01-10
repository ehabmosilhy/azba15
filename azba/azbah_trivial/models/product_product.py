from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.product"

    def name_get(self):
        result = []
        for rec in self:
            if rec.product_tmpl_id.code or rec.code:
                result.append((rec.id, '[%s] - %s' % (rec.product_tmpl_id.code.strip() or rec.code.strip(), rec.name)))
            else:
                result.append((rec.id, '%s' % (rec.name)))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        ids = self.env['product.template'].search(domain + args, limit=limit).ids
        records = self.search([('product_tmpl_id', 'in', ids)])
        return records.name_get()

