# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import datetime


class PosOrder(models.Model):
    _inherit = "pos.order"

    # 📜 Function to create a coupon based on the order lines
    def create_coupon(self, order, values):
        # 🎨 Loop through each line in the order
        for line in values['lines']:
            product = line[2]
            # 🧐 Check if the product name contains 'book' or 'دفتر'
            if 'book' in product['full_product_name'].lower() or 'دفتر' in product['full_product_name'].lower():
                product_id = self.env['product.product'].browse(product['product_id'])
                coupon_paper_count = product_id.coupon_paper_count
                # 🔄 If the product has coupon papers, create coupons
                if coupon_paper_count > 0:
                    for i in range(product['qty']):
                        self.env['az.coupon'].create({
                            'name': product['full_product_name'],
                            'page_count': coupon_paper_count,
                            'pos_order_id': order.id,
                            'partner_id': order.partner_id.id,
                            'product_id': product_id.id
                        })

    # 📄 Function to handle papers based on order values
    def handle_papers(self, values):
        product_template_id = 3733  # 🆔 Hardcoded product template ID
        product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)])
        partner_id = values['partner_id']
        new_lines = values['lines'][::]
        # 🛠 Loop through each line in the order values
        for line in values['lines']:
            if line[2]['product_id'] == product_id.id:
                qty = line[2]['qty']  # 📏 Get the quantity of the product

                # 🔍 Count the total valid coupon papers for this partner
                total_valid_papers = self.env['az.coupon.paper'].search_count(
                    [('coupon_book_id.partner_id', '=', partner_id), ('state', '=', 'valid')]
                )

                # 🚫 Raise an error if the requested quantity exceeds total valid papers
                if qty > total_valid_papers:
                    raise ValueError(
                        f"Requested quantity ({qty}) exceeds the total number of valid coupon papers ({total_valid_papers}).")

                # ♻️ Loop until all quantities are handled
                while qty > 0:
                    # 📚 Get the oldest valid coupon book for this partner
                    coupon_book = self.env['az.coupon'].search(
                        [('partner_id', '=', partner_id), ('state', '=', 'valid')],
                        order='id asc', limit=1
                    )

                    if not coupon_book:
                        break  # 🚪 Exit loop if no valid coupon book is found

                    # 📝 Get the required number of coupon papers from the coupon book
                    coupon_papers = self.env['az.coupon.paper'].search(
                        [('coupon_book_id', '=', coupon_book.id), ('state', '=', 'valid')],
                        order='id asc', limit=qty
                    )

                    if not coupon_papers:
                        break  # 🚪 Exit loop if no valid coupon papers are found

                    # ✅ Update the state of each paper to 'used'
                    for paper in coupon_papers:
                        paper.state = 'used'
                        qty -= 1  # 📉 Decrease the remaining quantity

                    # 🏁 If this coupon book is exhausted, mark it as used
                    if not self.env['az.coupon.paper'].search(
                            [('coupon_book_id', '=', coupon_book.id), ('state', '=', 'valid')]):
                        coupon_book.state = 'used'

                # ✨ Add a new line with the coupon product
                new_lines = self.add_coupon_product_line(new_lines, line[2]['qty'])
        values['lines'] = new_lines
        return values

    # ➕ Function to add a new line with the coupon product
    def add_coupon_product_line(self, new_lines, qty):
        coupon_product_template_id = 4  # 🆕 Hardcoded new product template ID
        coupon_product_id = self.env['product.product'].search([('product_tmpl_id', '=', coupon_product_template_id)])
        import copy
        new_line = copy.deepcopy(new_lines[-1])
        new_line[2]['id'] += 1
        new_line[2]['name'] = new_line[2]['name'][0:6] + str(int(new_line[2]['name'][6:]) + 1)
        new_line[2]['full_product_name'] = "استبدال قارورة مياه/5 جالون"
        new_line[2]['product_id'] = coupon_product_id.id

        new_lines.append(new_line)
        return new_lines

    @api.model
    def create(self, values):
        values = self.handle_papers(values)  # 🖋 Handle papers for the order

        session = self.env['pos.session'].browse(values['session_id'])  # 📅 Get the POS session
        values = self._complete_values_from_session(session, values)  # ✍ Complete order values from session
        order = super(PosOrder, self).create(values)  # 🌟 Create the order

        self.create_coupon(order, values)  # 🎁 Create coupons for the order

        return order  # 🔄 Return the created order
