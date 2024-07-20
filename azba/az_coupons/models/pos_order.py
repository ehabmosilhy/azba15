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
    @api.model
    def handle_papers(self, values):
        product_template_id = 3733  # 🆔 Hardcoded product template ID
        product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template_id)])
        partner_id = values['partner_id']
        used_coupons = set()  # List to store the IDs and codes of used coupons

        for line in values['lines']:
            if line[2]['product_id'] == product_id.id:
                qty = line[2]['qty']  # 📏 Get the quantity of the product

                # 🔍 Count the total valid coupon papers for this partner
                total_valid_papers = self.env['az.coupon.paper'].search_count(
                    [('coupon_book_id.partner_id', '=', partner_id), ('state', '=', 'valid')]
                )

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
                        used_coupons.add( coupon_book.code)  # Add ID and code to the list
                    # 🏁 If this coupon book is exhausted, mark it as used
                    if not self.env['az.coupon.paper'].search(
                            [('coupon_book_id', '=', coupon_book.id), ('state', '=', 'valid')]):
                        coupon_book.state = 'used'


        return used_coupons  # Return the list of used coupon IDs and codes

    def make_invoice(self, values):
        lines = values['lines']
        for line in lines:
            if line[2]['product_id'] == 4: # قارورة مياه 5 جالون
                # get list price of coupon book product.template 40
                list_price = self.env['product.template'].browse(40).list_price
                list_price=list_price/20
                line[2]['price_unit'] = list_price
                line[2]['price_subtotal'] = list_price * line[2]['qty']
                line[2]['tax_ids'] = [[6, False, []]]

        return values


    @api.model
    def create(self, values):

        session = self.env['pos.session'].browse(values['session_id'])  # 📅 Get the POS session
        values = self._complete_values_from_session(session, values)  # ✍ Complete order values from session
        values = self.make_invoice(values) # to calculate price of pages
        order = super(PosOrder, self).create(values)  # 🌟 Create the order

        self.create_coupon(order, values)  # 🎁 Create coupons for the order

        return order  # 🔄 Return the created order
