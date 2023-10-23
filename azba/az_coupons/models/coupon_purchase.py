# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CouponPurchase(models.Model):
    _name = "coupon.purchase"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the coupon purchase with prefix DPO_")

    date = fields.Date(required=True, default=fields.Date.context_today)
    # product_id = fields.Many2one('product.product', string="Product", required=True)
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
    # TODO: [Tech Debt] Fix this, remove hardcoding
    paper_count= fields.Selection([('20', 'دفتر 20'), ('50', 'دفتر 50'), ('100', 'دفتر 100')], string='Coupon Book')

    @api.model
    def create(self, vals_list):
        # Get configuration parameters
        config_params = self.get_config_params()
        coupon_product_id = config_params['coupon_product_id']
        coupon_book_ids = config_params['coupon_book_ids']
        paper_count = int(vals_list['paper_count'])

        # Get coupon book product id
        coupon_book_product_id = self.get_coupon_book_product_id(coupon_book_ids, paper_count)

        # Get product packaging id
        product_packaging_id = self.get_product_packaging_id(coupon_product_id, paper_count)

        # Create coupon purchase
        coupon = self.create_coupon_purchase(vals_list)

        # Create purchase order
        _new_purchase_order = self.create_purchase_order(vals_list, coupon, coupon_product_id, coupon_book_product_id,
                                                         product_packaging_id)

        # Confirm the purchase order
        _new_purchase_order.button_confirm()

        # Validate the picking
        self.validate_picking(_new_purchase_order, coupon, vals_list)

        return coupon

    def get_config_params(self):
        p = self.env['ir.config_parameter'].sudo()
        return {
            'coupon_product_id': int(p.get_param('az_coupons.coupon_product_id')),
            'coupon_book_ids': [int(_) for _ in p.get_param('az_coupons.coupon_book_ids').split(',')]
        }

    def get_coupon_book_product_id(self, coupon_book_ids, paper_count):
        coupon_book_product = self.env['coupon.book'].search(
            [('id', 'in', coupon_book_ids), ('paper_count', '=', paper_count)])
        return coupon_book_product.product_id.id if coupon_book_product else False

    def create_coupon_purchase(self, vals_list):
        vals_list['name'] = self.env['ir.sequence'].next_by_code('coupon.purchase')
        return super(CouponPurchase, self).create(vals_list)

    def create_purchase_order(self, vals_list, coupon, coupon_product_id, coupon_book_product_id, product_packaging_id):
        vendor_id = 5  # TODO: Change this
        new_purchase_order = self.get_purchase_order_dict(vals_list, coupon, vendor_id, coupon_product_id,
                                                          coupon_book_product_id, product_packaging_id)
        return self.env['purchase.order'].create(new_purchase_order)

    def get_purchase_order_dict(self, vals_list, coupon, vendor_id, coupon_product_id, coupon_book_product_id,
                                product_packaging_id):
        book_count = vals_list['quantity']
        paper_count = int(vals_list['paper_count'])
        return {
            "priority": "0",
            "coupon_purchase_id": coupon.id,
            'partner_id': vendor_id,
            "currency_id": 148,
            "picking_type_id": 551,
            'date_order': vals_list['date'],
            'date_planned': vals_list['date'],
            'order_line': [
                (0, 0, self.get_coupon_paper_line_dict(vals_list, coupon_product_id, book_count, paper_count,
                                                       product_packaging_id)),
                (0, 0, self.get_coupon_book_line_dict(vals_list, coupon_book_product_id)),
            ]
        }

    def get_coupon_paper_line_dict(self, vals_list, coupon_product_id, book_count, paper_count, product_packaging_id):
        return {
            "sequence": 10,
            'name': 'Coupon Paper',
            'product_id': coupon_product_id,
            "date_planned": vals_list['date'],
            'price_unit': 0,
            'product_qty': book_count * paper_count,
            'product_packaging_id': product_packaging_id
        }

    def get_coupon_book_line_dict(self, vals_list, coupon_book_product_id):
        return {
            "sequence": 10,
            'product_id': coupon_book_product_id,
            'product_uom': 1,
            'name': 'Coupon Book',
            "date_planned": vals_list['date'],
            'price_unit': vals_list['price'],
            'product_qty': vals_list['quantity']
        }

    def validate_picking(self, _new_purchase_order, coupon, vals_list):
        for picking in _new_purchase_order.picking_ids:
            picking.coupon_purchase_id = coupon.id
            lines = picking.move_line_ids
            book_count = vals_list['quantity']
            coupon_book_serials = [s for s in range(vals_list['first_serial'], vals_list['last_serial'] + 1)]
            self.update_lines(lines, book_count, coupon_book_serials, vals_list)
            picking.action_put_in_pack()
            picking.button_validate()
            packs = picking.move_line_ids.mapped('result_package_id')
            self._rename_packs(packs, coupon_book_serials)

    def update_lines(self, lines, book_count, coupon_book_serials, vals_list):
        paper_count = int(vals_list['paper_count'])
        book_index = 0
        for s, line in enumerate(lines):
            if s >= len(lines) - book_count:
                _serial = coupon_book_serials[book_index]
                book_index += 1
            else:
                _serial = str(int(vals_list['first_serial']) * paper_count - paper_count + s + 1)
            lines[s].lot_name = _serial
            lines[s].qty_done = 1

    def get_product_packaging_id(self, product_id, paper_count):
        p = self.env['product.product'].browse(product_id)
        packaging_id = p.packaging_ids.search([('qty', '=', paper_count)])
        if packaging_id:
            return packaging_id.id
        else:
            p = self.env['product.product'].search([('qty', '=', paper_count)])
            if p:
                return p.id

    def _rename_packs(self, packs, coupon_book_serials):
        for i in range(len(packs)):
            packs[i].name = str(coupon_book_serials[i])


    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)
    def launch_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': self.purchase_order_ids[0].id,
            'domain': [('coupon_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }
    def launch_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Inventory',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.purchase_order_ids.picking_ids[0].id,
            'context': "{'create': False}"
        }
    def launch_packages(self):
        self.ensure_one()
        packs=self.purchase_order_ids.picking_ids.move_line_ids.mapped('result_package_id').ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Packs',
            'view_mode': 'kanban,form,tree',
            'res_model': 'stock.quant.package',
            'domain': [('id', 'in', packs)],
            'context': "{'create': False}"
        }
    @api.onchange('first_serial', 'last_serial')
    def onchange_serials(self):
        if self.last_serial >= self.first_serial:
            qty = self.last_serial - self.first_serial + 1
            self.quantity = qty
