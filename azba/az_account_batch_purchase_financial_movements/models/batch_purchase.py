# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BatchPurchaseFinancial(models.Model):
    _name = "batch.purchase.financial"
    name = fields.Char(string="Name", copy=False, readonly=True,
                       default="New",
                       index=True, help="Unique name for the batch purchase with prefix DPO_")

    delegate_id = fields.Many2one('hr.employee', required=True)
    date = fields.Date(required=True, default=fields.Date.context_today)
    total = fields.Float()
    line_ids = fields.One2many('batch.purchase.financial.line', 'batch_id')
    line_count = fields.Integer(compute='_compute_line_count', string='Line count')
    vendor_bill_count = fields.Integer(string='Purchase Order Count', compute='_compute_vendor_bill_count')

    def _compute_vendor_bill_count(self):
        for record in self:
            record.vendor_bill_count = len(record.evn['account.move'].sudo().search(
                [('move_type', '=', 'in_invoice'), ('batch_purchase_financial_id', '=', record.id)]))

    def launch_vendor_bills(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bills',
            'view_mode': 'tree,kanban,form,pivot,graph,activity',
            'res_model': 'account.move',
            'domain': [('batch_purchase_financial_id', '=', self.id)],
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
                    vendor_id = line.get('vendor_id')
                    if not vendor_id:
                        vendor_id = batch_lines[i - 1][2].get('vendor_id')
                        batch_lines[i][2]['vendor_id'] = vendor_id
                    if vendor_id in purchase_orders.keys():
                        purchase_orders[vendor_id].append(line)
                    else:
                        purchase_orders[vendor_id] = [line]

        if vals_list.get('name', "New") == 'New':
            last_dpo = self.env['batch.purchase'].search([], order='id desc', limit=1)
            if last_dpo:
                new_name = 'DPO_' + str(int(last_dpo.name[4:]) + 1).zfill(5)
            else:
                new_name = "DPO_00001"
            vals_list['name'] = new_name
        batch = super(BatchPurchaseFinancial, self).create(vals_list)

        for bill_line_order in purchase_orders.items():
            vendor_id = bill_line_order[0]
            bill_lines = bill_line_order[1]

            new_bill = {
                'move_type': 'in_invoice',
                "batch_purchase_financial_id": batch.id,
                'partner_id': vendor_id,
                "purchase_delegate_financial_id": vals_list['delegate_id'],
                "currency_id": 148
                , 'invoice_date': vals_list['date']
                , 'invoice_line_ids': [
                    (0, 0,
                     {
                         "sequence": 10
                         , 'product_id': _line['product_id']
                         , 'note': _line['note']
                         , "product_uom_id": _line['product_uom']
                         , 'price_unit': _line['price']
                         , 'quantity': _line['quantity']
                     }) for _line in bill_lines]
            }
            # Create the purchase purchase_order
            _new_bill_order = self.env['account.move'].create(new_bill)

            # Confirm the purchase_order
            _new_bill_order.action_post()

        return batch


class BatchPurchaseFinancialLine(models.Model):
    _name = "batch.purchase.financial.line"
    batch_id = fields.Many2one('batch.purchase.financial')
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
