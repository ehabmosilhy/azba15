from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_qty_in_location(self, pos_config_id):
        picking_type_id = self.env['pos.config'].search([('id', '=', pos_config_id)]).picking_type_id
        location_id = picking_type_id.default_location_src_id
        return self.env['stock.quant']._get_available_quantity(self, location_id)
