
from odoo import api, models, modules, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    
    amount_tax = fields.Monetary(string='Tax Amount', compute='compute_amount_taxed_per_line',currency_field='company_currency_id',store=True)
    
    
    @api.depends('product_id','tax_ids','quantity','price_subtotal')
    def compute_amount_taxed_per_line(self):
        for rec in self:
            total_tax = 0
            if rec.tax_ids:
                for tax_line in rec.tax_ids:
                    total_tax += tax_line.amount
            rec.amount_tax = ( rec.price_subtotal * total_tax) / 100