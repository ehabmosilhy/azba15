# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class PosOrder(models.Model):
    _inherit = "pos.order"

    class PosOrder(models.Model):
        _inherit = "pos.order"

        def get_config_params(self):
            p = self.env['ir.config_parameter'].sudo()
            return {
                'coupon_product_id': int(p.get_param('az_coupons.coupon_product_id')),
                'coupon_book_ids': [int(_) for _ in p.get_param('az_coupons.coupon_book_ids').split(',')],
                'bottle_product_id': int(p.get_param('az_coupons.bottle_product_id')),

            }
        def create_exchange_picking(self, order):
            coupon_product_id = self.get_config_params()['coupon_product_id']
            coupon_count = sum(line.qty for line in order.lines if line.product_id.id == coupon_product_id)

            if coupon_count:
                bottle_product_id = self.get_config_params()['bottle_product_id']

                session = order.session_id
                # Get the number of coupons in the current order

                # Create the internal picking for a bottle product with quantity equal to the number of coupons


                # warehouse ID
                warehouse_id = order.picking_type_id.warehouse_id.id
                internal_picking_id = self.env['stock.picking.type'].search([('warehouse_id', '=', warehouse_id), ('code', '=', 'internal')]).id
                # Create the internal picking

                internal_picking = self.env['stock.picking'].create({
                    'location_id': session.config_id.picking_type_id.default_location_src_id.id,
                    'location_dest_id': 5,  # Customer Location TODO: Get the destination location
                    'picking_type_id': internal_picking_id,
                    'origin':order.name,
                    'partner_id': order.partner_id.id

                })
                self.env['stock.move'].create({
                    'name': 'test_put_in_pack_from_different_location',
                    'location_id': session.config_id.picking_type_id.default_location_src_id.id,
                    'location_dest_id': 5,  # Customer Location TODO: Get the destination location,
                    'product_id': bottle_product_id,
                    'product_uom': self.env['product.product'].search([('id', '=', coupon_product_id)]).uom_id.id,
                    'product_uom_qty': coupon_count,
                    'picking_id': internal_picking.id,
                })



    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        order= super(PosOrder, self).create(values)

        internal_picking = self.create_exchange_picking(order)


        return order