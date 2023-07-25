# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BatchPurchase(models.Model):
    _name = "batch.purchase"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the batch purchase with prefix DPO_")

    delegate_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    total = fields.Float()
    line_ids = fields.One2many('batch.purchase.line', 'batch_id')
    line_count = fields.Integer(compute='_compute_line_count', string='Line count')
    purchase_order_ids = fields.One2many('purchase.order', 'batch_purchase_id', string="Purchase Orders")
    vendor_bill_ids = fields.One2many('account.move', 'batch_purchase_id', string="Vendor Bill Ids")
    purchase_order_count = fields.Integer(string='Purchase Order Count', compute='_compute_purchase_order_count')
    vendor_bill_count = fields.Integer(string='Vendor Bill Count', compute='_compute_vendor_bill_count')

    # The type will distinguish between purchase and sarf
    type = fields.Selection([('purchase', 'Purchase'), ('sarf', 'Sarf')], default='purchase')

    # 🧮🧮🧮 Some Computing
    def _compute_purchase_order_count(self):
        for record in self:
            record.purchase_order_count = len(record.purchase_order_ids)

    def _compute_vendor_bill_count(self):
        for record in self:
            if record.type == 'purchase':
                record.vendor_bill_count = len(record.purchase_order_ids.invoice_ids)
            elif record.type == 'sarf':
                record.vendor_bill_count = len(record.vendor_bill_ids)
            else:
                record.vendor_bill_count = 0

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    # 🧮🧮🧮 ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ End of Computing 🧮

    # 🚀🚀🚀 Launch Buttons
    def _get_action_window(self, name, res_model, domain):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': 'tree,kanban,form,pivot',
            'res_model': res_model,
            'domain': domain,
            'context': "{'create': False}"
        }

    def launch_purchase_orders(self):
        return self._get_action_window('Purchase Orders', 'purchase.order', [('batch_purchase_id', '=', self.id)])

    def launch_vendor_bills(self):
        return self._get_action_window('Vendor Bills', 'account.move', [('batch_purchase_id', '=', self.id)])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ End of Launch Buttons 🚀

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

    def get_name(self, _type):
        prefix = ''
        if _type == 'purchase':
            prefix = 'DPO_'
        elif _type == 'sarf':
            prefix = 'IPO_'

        last_dpo = self.env['batch.purchase'].search([('type', '=', _type)], order='id desc', limit=1)
        new_number = str(int(last_dpo.name[4:]) + 1).zfill(5) if last_dpo else '00001'
        new_name = prefix + new_number

        return new_name

    def group_lines_by_vendor(self, line_ids):
        purchase_orders = {}

        for i, line in enumerate(line_ids):
            line_data = line[2]

            if line_data.get('display_type'):
                continue

            vendor_id = line_data.get('vendor_id')

            if not vendor_id:
                vendor_id = line_ids[i - 1][2].get('vendor_id')
                line_data['vendor_id'] = vendor_id

            if vendor_id in purchase_orders:
                purchase_orders[vendor_id].append(line_data)
            else:
                purchase_orders[vendor_id] = [line_data]

        return purchase_orders

    def compose_purchase_order(self, vals_list, vendor_id, bill_lines, _type, batch):
        purchase_order_lines = []
        for _line in bill_lines:
            purchase_order_line = (0, 0, {
                "sequence": 10,
                'product_id': _line['product_id'],
                'note': _line['note'],
                "date_planned": vals_list['date'],
                "product_uom": _line['product_uom'],
                'price_unit': _line['price'],
                'product_qty': _line['quantity'],
                'taxes_id': _line['tax_ids']
            })
            purchase_order_lines.append(purchase_order_line)

        new_purchase_order = {
            "priority": "0",
            "batch_purchase_id": batch.id,
            'partner_id': vendor_id,
            "delegate_id": vals_list['delegate_id'],
            "currency_id": 148,
            "picking_type_id": 551,
            'date_order': vals_list['date'],
            'date_planned': vals_list['date'],
            'order_line': purchase_order_lines
        }
        return new_purchase_order

    def po_to_invoice(self, bill, batch):
        # Add properties
        bill['move_type'] = 'in_invoice'
        bill['invoice_user_id'] = self.env.uid
        bill['batch_purchase_id'] = batch.id

        # Remove properties
        properties_to_remove = [
            'picking_type_id',
            'date_order',
            'date_planned',
            'priority'
        ]
        for prop in properties_to_remove:
            bill.pop(prop, None)

        # Modify order line properties
        for order_line in bill['order_line']:
            order_line[2]['quantity'] = order_line[2]['product_qty']
            order_line[2]['product_uom_id'] = order_line[2]['product_uom']
            order_line[2]['tax_ids'] = order_line[2]['taxes_id']

            properties_to_remove = [
                'product_qty',
                'product_uom',
                'date_planned',
                'taxes_id'
            ]
            for prop in properties_to_remove:
                order_line[2].pop(prop, None)

        # Rename order line
        bill['invoice_line_ids'] = bill.pop('order_line')

        return bill

    # Create Method 🏭
    @api.model
    def create(self, vals_list):
        self.check_data(vals_list)

        purchase_orders = self.group_lines_by_vendor(vals_list.get('line_ids'))
        _type = self.env.context.get('type')
        vals_list['type'] = _type

        if vals_list.get('name', "New") == 'New':
            vals_list['name'] = self.get_name(_type)

        batch = super(BatchPurchase, self).create(vals_list)

        for vendor_id, bill_lines in purchase_orders.items():
            new_purchase_order = self.compose_purchase_order(vals_list, vendor_id, bill_lines, _type, batch)

            if _type == 'purchase':
                self.create_purchase_order(vals_list, new_purchase_order, batch)
            else:
                bill = self.create_vendor_bill(vals_list, new_purchase_order, batch)
                bill.action_post()
                self.pay_bill(bill)

        return batch



    def pay_bill(self, bill):
        _register = self.env['account.payment.register'].with_context(active_ids=[bill.id], active_model='account.move')
        payment_register = _register.create({
            'journal_id': 9,
            'partner_bank_id': bill.partner_bank_id.id,
            'amount': bill.amount_residual,
            'payment_date': bill.invoice_date,
            'communication': bill.name
        })
        payment_register.action_create_payments()

    def create_purchase_order(self, vals_list, new_purchase_order, batch):
        purchase_order = self.env['purchase.order'].create(new_purchase_order)
        purchase_order.button_confirm()

        for picking in purchase_order.picking_ids:
            picking.batch_purchase_id = batch.id
            for line in picking.move_ids_without_package:
                line.quantity_done = line.product_uom_qty
                line.batch_purchase_id = batch.id
            picking.button_validate()

        purchase_order.action_create_invoice()

        for bill in purchase_order.invoice_ids:
            bill.purchase_order_id = purchase_order.id
            bill.purchase_delegate_id = purchase_order.delegate_id.id
            bill.invoice_date = vals_list['date']

            for i, line in enumerate(bill.invoice_line_ids):
                if purchase_order.order_line[i].note:
                    line.note = purchase_order.order_line[i].note

            bill.action_post()

    def create_vendor_bill(self, vals_list, new_purchase_order, batch):
        new_bill = self.po_to_invoice(new_purchase_order, batch)
        bill = self.env['account.move'].with_context(default_move_type='in_invoice')
        bill = bill.with_company(self.env.user.company_id).create(new_bill)
        bill.invoice_date = vals_list['date']
        # for some reason, the bill forgets the 'batch_purchase_id'
        bill.batch_purchase_id = new_bill['batch_purchase_id']
        bill.purchase_delegate_id = bill['delegate_id']

        return bill


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
    note = fields.Text()
    display_type = fields.Char()
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Taxes",
        help="Taxes that apply on the base amount"
        , default=[5]  # Purchase Tax 15%
    )

    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

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
        vendor_ids = self.batch_id.line_ids.mapped('vendor_id')
        domain = [('code', 'ilike', 'v%'), ('id', 'not in', vendor_ids.ids)]
        return {'domain': {'vendor_id': domain}}
