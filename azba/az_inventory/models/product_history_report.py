from odoo import api, fields, models, tools

class ProductHistoryReport(models.Model):
    _name = 'product.history.report'
    _description = 'Product History with Initial Balance'
    _auto = False

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    initial_qty = fields.Float('Initial Quantity', readonly=True)
    in_qty = fields.Float('Incoming Quantity', readonly=True)
    out_qty = fields.Float('Outgoing Quantity', readonly=True)
    final_qty = fields.Float('Final Quantity', readonly=True)
    date = fields.Date('Date', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    def init(self):
        return
