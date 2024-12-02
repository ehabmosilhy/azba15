from odoo import api, fields, models

class ProductHistoryWizard(models.TransientModel):
    _name = 'product.history.wizard'
    _description = 'Product History Wizard'

    product_id = fields.Many2one('product.product', string='Product', default=lambda self: self.env['product.product'].browse(4))
    start_date = fields.Date(string='Start Date', required=True, default='2024-01-01')
    end_date = fields.Date(string='End Date', required=True, default='2025-01-01')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, default=lambda self: self.env['stock.warehouse'].browse(107))

    def action_view_report(self):
        self.ensure_one()
        data = {
            'ids': self.ids,
            'model': 'product.history.wizard',
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'warehouse_id': self.warehouse_id.id,
                'product_id': self.product_id.id if self.product_id else False,
            }
        }
        return self.env.ref('az_inventory.action_report_product_history').report_action(self, data=data)
