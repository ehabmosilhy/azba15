# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CouponPurchase(models.Model):
    _name = "coupon.purchase"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the coupon purchase with prefix DPO_")

    date = fields.Date(required=True, default=fields.Date.context_today)
    product_id=fields.Many2one('product.product', string="Product", required=True)
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
    line_ids = fields.One2many('coupon.purchase.line', 'coupon_id')
    line_count = fields.Integer(compute='_compute_line_count', string='Line count')
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

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    # Update the Total
    @api.onchange('line_ids')
    def onchange_price_or_qty(self):
        total = 0
        for line in self.line_ids:
            if not line.display_type:
                total += line.price_subtotal_with_tax

        self.total = total

        # Calculate sub_total
        if self.line_count > 1:
            for indi, line in enumerate(self.line_ids):
                if line.vendor_id:
                    sub_total = 0
                    for child_id in range(indi + 1, len(self.line_ids)):
                        if not self.line_ids[child_id].display_type:
                            sub_total += self.line_ids[child_id].price_subtotal_with_tax
                        else:
                            break
                    line.price_subtotal_with_tax = sub_total

    def check_data(self, vals_list):
        if not vals_list.get('total') > 0:
            warning = {
                'message': "Please, check the data"
            }
            raise Exception(f'warning  {warning}')

    @api.model
    def create(self, vals_list):
        # self.check_data(vals_list)
        _line = vals_list['line_ids'][0][2]
        purchase_orders = {}
        coupon_lines = vals_list.get('line_ids')
        coupon = super(CouponPurchase, self).create(vals_list)
        coupon_book_serial = _line['serial']
        coupon_serial_start = (int(coupon_book_serial) * 50) - 49

        if coupon_lines:

            vendor_id = 3  # TODO Change this

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
                         , 'product_id': 39
                         , "date_planned": vals_list['date']
                         , 'price_unit': coupon_lines[0][2]['price']
                         , 'product_qty': coupon_lines[0][2]['quantity']
                     }),
                    (0, 0,
                     {
                         "sequence": 10
                         , 'product_id': 3562
                         , "date_planned": vals_list['date']
                         , 'price_unit': 0
                         , 'product_qty': 100
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
                    if not i:
                        lines[0].lot_name = str(coupon_book_serial)
                        lines[0].qty_done = 1
                    else:
                        for s in range (100):
                            lines[s].lot_name = str(coupon_serial_start) + str(s)
                            lines[s].qty_done= 1
                picking.move_line_ids = picking.move_line_ids[:-2]
                picking.button_validate()

        return coupon


class couponVendorBillLine(models.Model):
    _name = "coupon.purchase.line"
    coupon_id = fields.Many2one('coupon.purchase')
    line_count = fields.Integer(related='coupon_id.line_count')

    vendor_id = fields.Many2one('res.partner',
                                string='Vendor', domain=[('code', 'ilike', 'v%')]
                                , context={'source': 'vendor'}
                                )
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    serial = fields.Integer(string="Serial مسلسل")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    quantity = fields.Float()
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

    @api.onchange('price', 'quantity', 'tax_ids')
    def onchange_price_or_qty(self):
        self.price_subtotal = float(self.price) * float(self.quantity)
        if self.tax_ids:
            total_tax = 0
            for tax in self.tax_ids:
                total_tax += self.price_subtotal * tax.amount / 100
            self.price_subtotal_with_tax = float(self.price_subtotal) + total_tax
        else:
            self.price_subtotal_with_tax = float(self.price_subtotal)

    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        # Don't repeat vendors
        vendor_ids = self.coupon_id.line_ids.mapped('vendor_id')
        domain = [('code', 'ilike', 'v%'), ('id', 'not in', vendor_ids.ids)]
        return {'domain': {'vendor_id': domain}}
