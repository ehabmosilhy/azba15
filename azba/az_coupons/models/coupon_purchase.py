# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CouponPurchase(models.Model):
    _name = "coupon.purchase"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the coupon purchase with prefix DPO_")

    date = fields.Date(required=True, default=fields.Date.context_today)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    total = fields.Float()
    first_serial = fields.Integer()
    last_serial = fields.Integer()
    quantity = fields.Integer()
    price = fields.Float()
    price_subtotal = fields.Float(string="Sub Total")
    price_subtotal_with_tax = fields.Float(string="With Tax")
    note = fields.Text()
    display_type = fields.Char()
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        help="Taxes that apply on the base amount"
        , default=[5]  # Purchase Tax 15%
    )
    purchase_order_ids = fields.One2many('purchase.order', 'coupon_purchase_id', string="Purchase Orders")
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_order_count')

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def launch_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'view_mode': 'tree,kanban,form,pivot,graph,calendar,activity',
            'res_model': 'purchase.order',
            'domain': [('coupon_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def launch_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'view_mode': 'tree,kanban,form,pivot,graph,activity',
            'res_model': 'account.move',
            'domain': [('coupon_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.onchange('first_serial', 'last_serial')
    def onchange_serials(self):
        if self.last_serial >= self.first_serial:
            qty = self.last_serial - self.first_serial + 1
            self.quantity = qty

    @api.model
    def create(self, vals_list):
        # self.check_data(vals_list)
        # _line = vals_list['line_ids'][0][2]
        paper_count = 20
        purchase_orders = {}
        coupon = super(CouponPurchase, self).create(vals_list)
        coupon_book_serials = [s for s in range(vals_list['first_serial'], vals_list['last_serial'] + 1)]

        vendor_id = 5  # TODO Change this
        new_purchase_order = {
            "priority": "0",
            "coupon_purchase_id": coupon.id,
            'partner_id': vendor_id,
            "currency_id": 148,
            "picking_type_id": 551
            , 'date_order': vals_list['date']
            , 'date_planned': vals_list['date']
            , 'order_line': [
                (0, 0,
                 {
                     "sequence": 10
                     , 'product_id': vals_list['product_id']
                     , 'product_uom': 1
                     , 'name': 'Coupon Book'
                     , "date_planned": vals_list['date']
                     , 'price_unit': vals_list['price']
                     , 'product_qty': vals_list['quantity']
                 }),
                (0, 0,
                 {
                     "sequence": 10
                     , 'name': 'Coupon Paper'
                     , 'product_id': 3564
                     , "date_planned": vals_list['date']
                     , 'price_unit': 0
                     , 'product_qty': paper_count * vals_list['quantity']
                 })
            ]
        }
        _new_purchase_order = self.env['purchase.order'].create(new_purchase_order)

        # Confirm the purchase_order
        _new_purchase_order.button_confirm()

        # Validate the picking
        for picking in _new_purchase_order.picking_ids:
            picking.coupon_purchase_id = coupon.id
            for i, move in enumerate(picking.move_ids_without_package):
                move.coupon_purchase_id = coupon.id
                lines = move.move_line_ids
                if i==0:
                    for line_index, s in enumerate(coupon_book_serials):
                        lines[line_index].lot_name = str(s)
                        lines[line_index].qty_done = 1
                else:
                    for s in range(vals_list['quantity'] * paper_count):
                        lines[s].lot_name = str(int(vals_list['first_serial'])* paper_count -paper_count+ s)
                        lines[s].qty_done = 1
            # picking.move_line_ids = picking.move_line_ids[:-2]
            picking.button_validate()

        return coupon
