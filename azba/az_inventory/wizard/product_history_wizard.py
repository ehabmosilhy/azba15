from odoo import api, fields, models

class ProductHistoryWizard(models.TransientModel):
    _name = 'product.history.wizard'
    _description = 'Product History Wizard'

    product_id = fields.Many2one('product.product', string='Product', default=lambda self: self.env['product.product'].browse(4))
    start_date = fields.Date(string='Start Date', required=True, default='2024-01-01')
    end_date = fields.Date(string='End Date', required=True, default='2025-01-01')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, default=lambda self: self.env['stock.warehouse'].browse(107))
    location_id = fields.Many2one('stock.location', string='Location', domain="[('usage', '=', 'internal')]")

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.location_id = False

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id:
            self.warehouse_id = False

    def action_view_report(self):
        self.ensure_one()
        data = {
            'ids': self.ids,
            'model': 'product.history.wizard',
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'warehouse_id': self.warehouse_id.id if self.warehouse_id else False,
                'location_id': self.location_id.id if self.location_id else False,
                'product_id': self.product_id.id if self.product_id else False,
            }
        }
        return self.env.ref('az_inventory.action_report_product_history').report_action(self, data=data)
