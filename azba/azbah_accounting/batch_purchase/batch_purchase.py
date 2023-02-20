# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BatchPurchase(models.Model):
    _name = "batch.purchase"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the batch purchase with prefix DPO_")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Batch purchase name must be unique!")
    ]

    delegate_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    total = fields.Float()
    line_ids = fields.One2many('batch.purchase.line', 'batch_id')
    line_count = fields.Integer(compute='_compute_line_count', string='Line count')
    purchase_order_ids = fields.One2many('purchase.order', 'batch_purchase_id', string="Purchase Orders")
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_order_count')
    vendor_bill_count = fields.Integer(string='Purchase Order Count', compute='_compute_vendor_bill_count')

    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def _compute_vendor_bill_count(self):
        for record in self:
            record.vendor_bill_count = len([invoice.id for invoice in record.purchase_order_ids])

    def launch_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Orders',
            'view_mode': 'tree,kanban,form,pivot,graph,calendar,activity',
            'res_model': 'purchase.order',
            'domain': [('batch_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }
    def launch_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'view_mode': 'tree,kanban,form,pivot,graph,activity',
            'res_model': 'account.move',
            'domain': [('batch_purchase_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    # Update the Total
    @api.onchange('line_ids')
    def onchange_price_or_qty(self):
        if self.line_count < 2 and self.line_ids and self.line_ids[-1].product_id and not self.line_ids[-1].vendor_id:
            self.line_ids[-1].unlink()
            warning = {
                'message': "You must select vendor first"
            }
            return {'warning': warning}

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
        self.check_data(vals_list)

        purchase_orders = {}
        batch_lines = vals_list.get('line_ids')

        # We need to group the lines by vendor to make all the lines of one vendor together in
        # one purchase purchase_order
        if batch_lines:
            for i in range(len(batch_lines)):
                line = batch_lines[i][2]
                if not line.get('display_type'):
                    # if the user doesn't enter a note, make it empty without the HTML characters
                    if '<br' in line['note']:
                        line['note'] = ""
                    vendor_id = line.get('vendor_id')
                    if not vendor_id:
                        vendor_id = batch_lines[i - 1][2].get('vendor_id')
                        batch_lines[i][2]['vendor_id'] = vendor_id
                    if vendor_id in purchase_orders.keys():
                        purchase_orders[vendor_id].append(line)
                    else:
                        purchase_orders[vendor_id] = [line]

        if vals_list.get('name', "New") == 'New':
            vals_list['name'] = self.env['ir.sequence'].next_by_code(
                'batch.purchase') or 'New'
        batch = super(BatchPurchase, self).create(vals_list)

        for purchase_order in purchase_orders.items():

            vendor_id = purchase_order[0]
            bill_lines = purchase_order[1]

            new_purchase_order = {
                "priority": "0",
                "batch_purchase_id": batch.id,
                'partner_id': vendor_id,
                "delegate_id": vals_list['delegate_id'],
                "currency_id": 148,
                "picking_type_id": 551
                , 'date_order': vals_list['date']
                , 'date_planned': vals_list['date']
                , 'order_line': [
                    (0, 0,
                     {
                         "sequence": 10
                         , 'product_id': _line['product_id']
                         , 'name': _line['note']
                         , "date_planned": vals_list['date']
                         , "product_uom": _line['product_uom']
                         , 'price_unit': _line['price']
                         , 'product_qty': _line['quantity']
                     }) for _line in bill_lines]
            }
            # Create the purchase purchase_order
            _new_purchase_order = self.env['purchase.order'].create(new_purchase_order)

            # Confirm the purchase_order
            _new_purchase_order.button_confirm()

            # Validate the picking
            for picking in _new_purchase_order.picking_ids:
                picking.batch_purchase_id = batch.id
                for line in picking.move_ids_without_package:
                    # receive all the quantity
                    line.quantity_done = line.product_uom_qty
                    line.batch_purchase_id = batch.id
                picking.button_validate()

            # Create the Vendor Bill
            _new_purchase_order.action_create_invoice()

            # Confirm the Vendor Bill
            for bill in _new_purchase_order.invoice_ids:
                bill.purchase_order_id = _new_purchase_order.id
                bill.purchase_delegate_id = _new_purchase_order.delegate_id.id
                # The invoice date is mandatory
                bill.invoice_date = vals_list['date']
                bill.action_post()

        return batch



class BatchVendorBillLine(models.Model):
    _name = "batch.purchase.line"
    batch_id = fields.Many2one('batch.purchase')
    line_count = fields.Integer(related='batch_id.line_count')

    vendor_id = fields.Many2one('res.partner',
                                string='Vendor', domain=[('code', 'ilike', 'v%')]
                                , context={'source': 'vendor'}
                                )
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]")
    quantity = fields.Float()
    price = fields.Float()
    price_subtotal = fields.Float(string="Sub Total")
    price_subtotal_with_tax = fields.Float(string="With Tax")
    note = fields.Html()
    display_type = fields.Char()
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        help="Taxes that apply on the base amount"
        , default=[5]  # Purchase Tax 15%
    )

    @api.onchange('price', 'quantity')
    def onchange_price_or_qty(self):
        self.price_subtotal = float(self.price) * float(self.quantity)
        self.price_subtotal_with_tax = float(self.price_subtotal) * 1.15

    @api.onchange('vendor_id')
    def onchange_vendor_id(self):
        # Don't repeat vendors
        vendor_ids = self.batch_id.line_ids.mapped('vendor_id')
        domain = [('code', 'ilike', 'v%'), ('id', 'not in', vendor_ids.ids)]
        return {'domain': {'vendor_id': domain}}
