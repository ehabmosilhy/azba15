# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo.tools import float_is_zero, float_round
from odoo import api, fields, models, tools, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    used_coupon_ids = fields.One2many("az.coupon.page", "order_id")

    def remove_paper(self, values):
        if 'lines' in values and values['lines']:
            for line in values['lines']:
                if line[2]['product_id'] == 3562:
                    values['lines'].remove(line)
        return values

    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        # remove the coupon product line if exists  # TODO: should remove from javascript
        values = self.remove_paper(values)
        # add bottles product if  coupon book
        # values = self.add_bottles(values)
        order = super(PosOrder, self).create(values)
        self.update_coupon(order)
        # self.create_account_moves_coupon_page(order)
        try:
            whats = self.env['whatsapp.integration']
            whats.send_whatsapp_message(order)
        except Exception:
            pass
        return order

    @api.model
    def create_coupon(self, receipt_number, partner, product_id, qty):
        created_coupons = []
        product = self.env['product.product'].browse(product_id)
        coupon_page_product = self.env['coupon.book.product'].search([('product_id', '=', product_id)],
                                                                     limit=1)

        coupon_page_count = coupon_page_product.page_count

        if coupon_page_count > 0:
            for i in range(qty):
                id = self.env['az.coupon'].create({
                    'name': product.name,
                    'page_count': coupon_page_count,
                    'product_id': product_id,
                    'receipt_number': receipt_number,
                    'partner_id': partner
                })
                created_coupons.append(id.code)

        return created_coupons

    @api.model
    def handle_pages(self, values):
        # Get the coupon_page_product from settings
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        coupon_page_product_id = IrConfigParam.get_param('az_coupons.coupon_page_product')

        if not coupon_page_product_id:
            raise UserError(_("Coupon Page Product is not set in the settings. Please configure it first."))

        product_id = self.env['product.product'].browse(int(coupon_page_product_id))

        if not product_id.exists():
            raise UserError(_("The configured Coupon Page Product does not exist."))

        partner_id = values['partner_id']
        used_coupons = []  # List to store the codes of used coupons

        for line in values['lines']:
            if line[2]['product_id'] == product_id.id:
                qty = line[2]['qty']  # Get the quantity of the product

                while qty > 0:
                    # Get the oldest valid or partial coupon book for this partner
                    coupon_book = self.env['az.coupon'].search(
                        [('partner_id', '=', partner_id),
                         ('active', '=', True),
                         ('state', '!=', 'used'),
                         ('active', '=', True)],
                        order='id asc', limit=1)

                    if not coupon_book:
                        break  # Exit loop if no valid or partial coupon book is found

                    # Get the required number of coupon pages from the coupon book
                    coupon_pages = self.env['az.coupon.page'].search(
                        [('coupon_book_id', '=', coupon_book.id),
                         ('active', '=', True),
                         ('state', '!=', 'used')],
                        order='id asc', limit=qty
                    )

                    if not coupon_pages:
                        break  # Exit loop if no valid coupon pages are found

                    # Update the state of each page to 'used'
                    for page in coupon_pages:

                        # move these lines to another place
                        page.state = 'used'
                        page.date_used = fields.Datetime.now()
                        page.pos_session_id = values['pos_session_id']
                        #####


                        qty -= 1  # Decrease the remaining quantity
                        used_coupons.append(page.code)  # Add code to the list

                        self.used_coupon_ids = [(4, page.id)]

                    # Check the state of the coupon book after updating the pages
                    valid_pages_left = self.env['az.coupon.page'].search_count(
                        [('coupon_book_id', '=', coupon_book.id),
                         ('active', '=', True),
                         ('state', '!=', 'used')]
                    )

                    if valid_pages_left == 0:
                        coupon_book.state = 'used'
                    else:
                        coupon_book.state = 'partial'

        return sorted(used_coupons)  # Return the list of used coupon codes

    def add_bottles(self, move_vals):
        lines = move_vals['invoice_line_ids']
        # Check if there is exactly one line and the product_id is 37 or 3: COUPON BOOK 20 or 50 PCS
        if len(lines) == 1 and lines[0][2]['product_id'] in (37, 38):
            # move_vals['no_picking'] = True
            line = lines[0]

            # Retrieve the page_count for the product in the line
            coupon_book_product = self.env['coupon.book.product'].search([('product_id', '=', line[2]['product_id'])],
                                                                         limit=1)
            page_count = coupon_book_product.page_count if coupon_book_product else 1

            # Duplicate the line and change the product_id to 4
            new_product = self.env['product.product'].browse(4)
            import copy
            new_line = copy.deepcopy(line)

            # Calculate the new price based on the original price divided by page_count
            new_line[2]['product_id'] = new_product.id
            new_line[2]['price_unit'] = line[2]['price_unit'] / page_count if page_count else 0
            new_line[2]['price_subtotal'] = new_line[2]['price_unit'] * new_line[2]['quantity'] * page_count
            new_line[2]['quantity'] = line[2]['quantity'] * page_count

            # Add the duplicated line to the move_vals['lines']
            lines.append(new_line)

            # Modify the existing line: set all prices to zero
            line[2]['price_unit'] = 0
            line[2]['price_subtotal'] = 0
            # line[2]['price_subtotal_incl'] = 0

        return move_vals

    def coupon_page_move(self, move_vals):
        order = self
        lines = order.lines

        product_id = order.lines[0].product_id
        line = lines[0]

        qty = int(order.lines[0].qty)
        coupons = self.env['az.coupon'].search([('partner_id', '=', order.partner_id.id)])
        used_page_ids = coupons.mapped('page_ids').filtered(lambda p: p.state == 'used')
        sored_used_page_ids = used_page_ids.sorted(key=lambda p: p.date_used, reverse=True)
        last_used_pages = sored_used_page_ids[:qty]

        page_list = []
        total_price = 0
        for page in last_used_pages:
            coupon_book_id = page.coupon_book_id.id
            page_count = page.coupon_book_id.page_count
            coupon_book_product = self.env['coupon.book.product'].search([('page_count', '=', page_count)],
                                                                         limit=1)
            product = coupon_book_product.product_id
            price = product.lst_price
            unit_price = price / page_count if page_count > 0 else 0  # Avoid division by zero

            page_list.append({
                'page_code': page.code,
                'page_count': page_count,
                'coupon_book_id': coupon_book_id,
                'product_id': product.id,
                'price': price,
                'unit_price': unit_price
            })
            total_price += unit_price
            page.state = 'used'
            page.date_used = fields.Datetime.now()
            page.pos_session_id = order.session_id
        # Prepare the move dictionary
        move_vals = {
            'journal_id': 3,  # Set the journal
            'date': order.date_order,  # Set the date
            'ref': order.pos_reference,  # Reference to the order name
            'line_ids': [],
            'move_type': 'entry',  # Specify the move type as 'entry'
        }
        debit_account = self.env['account.account'].search([('code', '=', '500005')], limit=1)
        credit_account = self.env['account.account'].search([('code', '=', '500001')], limit=1)
        move_line_debit = {
            'name': product_id.display_name,
            'account_id': debit_account.id,
            'debit': total_price,
            'credit': 0.0,
            'quantity': qty,
        }

        move_line_credit = {
            'name': product_id.display_name,
            'account_id': credit_account.id,
            'debit': 0.0,
            'credit': total_price,
            'quantity': qty,
        }

        # Duplicate the line and change the product_id to 4

        move_vals = {
            'journal_id': 3,  # Set the journal
            'date': order.date_order,  # Set the date
            'ref': order.pos_reference,  # Reference to the order name
            'line_ids': [],
            'move_type': 'entry',  # Specify the move type as 'entry'
        }
        debit_account = self.env['account.account'].search([('code', '=', '500005')], limit=1)
        credit_account = self.env['account.account'].search([('code', '=', '500001')], limit=1)
        move_line_debit = {
            'name': product_id.display_name,
            'account_id': debit_account.id,
            'debit': total_price,
            'credit': 0.0,
            'quantity': qty,
        }

        move_line_credit = {
            'name': product_id.display_name,
            'account_id': credit_account.id,
            'debit': 0.0,
            'credit': total_price,
            'quantity': qty,
        }

        move_vals['line_ids'].append((0, 0, move_line_debit))
        move_vals['line_ids'].append((0, 0, move_line_credit))

        return move_vals

    def update_coupon(self, order):
        # Add the POS Order ID to the coupon
        # Update full product name for each line in the order
        for line in order.lines:
            line.full_product_name = line.product_id.display_name

        # Define the terms to be searched and replaced
        terms_to_check = ['Order', 'طلب']
        reference = order.pos_reference

        # Check and replace terms
        for term in terms_to_check:
            if term in reference:
                reference = reference.replace(term, '').strip()
                break  # Exit the loop once the term is found and replaced

        # Search for coupons based on the cleaned reference
        coupons = self.env['az.coupon'].search([('receipt_number', '=', reference)])

        # Update coupon with the order id
        for coupon in coupons:
            coupon.pos_order_id = order.id

    def __create_invoice(self, move_vals):
        self.ensure_one()
        new_move = self.env['account.move'].sudo().with_company(self.company_id).with_context(
            default_move_type=move_vals['move_type']).create(move_vals)
        message = _(
            "This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                      self.id, self.name)
        new_move.message_post(body=message)
        if self.config_id.cash_rounding:
            rounding_applied = float_round(self.amount_paid - self.amount_total,
                                           precision_rounding=new_move.currency_id.rounding)
            rounding_line = new_move.line_ids.filtered(lambda line: line.is_rounding_line)
            if rounding_line and rounding_line.debit > 0:
                rounding_line_difference = rounding_line.debit + rounding_applied
            elif rounding_line and rounding_line.credit > 0:
                rounding_line_difference = -rounding_line.credit + rounding_applied
            else:
                rounding_line_difference = rounding_applied
            if rounding_applied:
                if rounding_applied > 0.0:
                    account_id = new_move.invoice_cash_rounding_id.loss_account_id.id
                else:
                    account_id = new_move.invoice_cash_rounding_id.profit_account_id.id
                if rounding_line:
                    if rounding_line_difference:
                        rounding_line.with_context(check_move_validity=False).write({
                            'debit': rounding_applied < 0.0 and -rounding_applied or 0.0,
                            'credit': rounding_applied > 0.0 and rounding_applied or 0.0,
                            'account_id': account_id,
                            'price_unit': rounding_applied,
                        })

                else:
                    self.env['account.move.line'].with_context(check_move_validity=False).create({
                        'debit': rounding_applied < 0.0 and -rounding_applied or 0.0,
                        'credit': rounding_applied > 0.0 and rounding_applied or 0.0,
                        'quantity': 1.0,
                        'amount_currency': rounding_applied,
                        'partner_id': new_move.partner_id.id,
                        'move_id': new_move.id,
                        'currency_id': new_move.currency_id if new_move.currency_id != new_move.company_id.currency_id else False,
                        'company_id': new_move.company_id.id,
                        'company_currency_id': new_move.company_id.currency_id.id,
                        'is_rounding_line': True,
                        'sequence': 9999,
                        'name': new_move.invoice_cash_rounding_id.name,
                        'account_id': account_id,
                    })
            else:
                if rounding_line:
                    rounding_line.with_context(check_move_validity=False).unlink()
            if rounding_line_difference:
                existing_terms_line = new_move.line_ids.filtered(
                    lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                if existing_terms_line.debit > 0:
                    existing_terms_line_new_val = float_round(
                        existing_terms_line.debit + rounding_line_difference,
                        precision_rounding=new_move.currency_id.rounding)
                else:
                    existing_terms_line_new_val = float_round(
                        -existing_terms_line.credit + rounding_line_difference,
                        precision_rounding=new_move.currency_id.rounding)
                existing_terms_line.write({
                    'debit': existing_terms_line_new_val > 0.0 and existing_terms_line_new_val or 0.0,
                    'credit': existing_terms_line_new_val < 0.0 and -existing_terms_line_new_val or 0.0,
                })

                new_move._recompute_payment_terms_lines()

        # /\_/\
        # ( ◕‿◕ )
        #  >   <
        # Beginning: Ehab
        for line in new_move.invoice_line_ids:
            if line.product_id.id == 4:
                line.write({'account_id': 151})

        # ______ (｡◔‿◔｡) ________ End of code
        return new_move

    def _create_invoice(self, move_vals):
        coupon_book = None
        coupon_page = None
        for line in self.lines:
            if line.product_id.id in (37, 38):
                coupon_book = True
            if line.price_unit == 0:
                coupon_page = True

        if coupon_book:
            move_vals = self.add_bottles(move_vals)
            return self.__create_invoice(move_vals)
        elif coupon_page:
            move_vals = self.coupon_page_move(move_vals)
            return self.__create_invoice(move_vals)
        # Coupon Page is handlded in create_account_moves_coupon_page
        elif not coupon_page:
            return super(PosOrder, self)._create_invoice(move_vals)
