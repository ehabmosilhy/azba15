# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tools import float_repr, float_compare
from odoo import api, fields, models, tools, _
import psycopg2
import logging
import urllib.parse

_logger = logging.getLogger(__name__)


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
        product_template_id = 3733  # TODO: Hardcode - settings
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
                        used_coupons.add(coupon_book.code)  # Add ID and code to the list
                    # 🏁 If this coupon book is exhausted, mark it as used
                    if not self.env['az.coupon.paper'].search(
                            [('coupon_book_id', '=', coupon_book.id), ('state', '=', 'valid')]):
                        coupon_book.state = 'used'

        return used_coupons  # Return the list of used coupon IDs and codes

    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        order = super(PosOrder, self).create(values)
        self.create_coupon(order, values)

        # Send WhatsApp message
        self.send_whatsapp_message(order)

        return order

    def send_whatsapp_message(self, order):
        # message = f"Hi {order.partner_id.name},\nYour order {order.name} amounting {order.amount_total} {order.currency_id.symbol} is confirmed. Thank you for your purchase!"
        # mobile = '+971527006631'  # Test number
        #
        # # Encode the message for URL
        # encoded_message = urllib.parse.quote(message)
        #
        # # Construct the WhatsApp URL
        # url = f"https://api.whatsapp.com/send?phone={mobile}&text={encoded_message}"
        #
        # # Log the message in Odoo
        # order.partner_id.message_post(body=message)
        #
        # # Return action to open WhatsApp in a new tab
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url,
        #     'target': 'new',
        # }
        # from twilio.rest import Client
        #
        # account_sid = 'ACe163c62ab44430affdf900abef670659'
        # auth_token = '588fb1681095b0bba077163f521a69d5'
        # client = Client(account_sid, auth_token)
        #
        # message = client.messages.create(
        #     from_='whatsapp:+14155238886',
        #     body='Your appointment is coming up on July 21 at 3PM',
        #     to='whatsapp:+971527006631'
        # )
        #
        # print(message.sid)

        import requests

        data = {
            'To': 'whatsapp:+971527006631',
            'From': 'whatsapp:+14155238886',
            'Body': 'Hi Ehab!',
        }

        response = requests.post(
            'https://api.twilio.com/2010-04-01/Accounts/ACe163c62ab44430affdf900abef670659/Messages.json',
            data=data,
            auth=('ACe163c62ab44430affdf900abef670659', '588fb1681095b0bba077163f521a69d5'),
        )



    @api.model
    def _process_order(self, order, draft, existing_order):
        """Create or update an pos.order from a given dictionary.

        :param dict order: dictionary representing the order.
        :param bool draft: Indicate that the pos_order is not validated yet.
        :param existing_order: order to be updated or False.
        :type existing_order: pos.order.
        :returns: id of created/updated pos.order
        :rtype: int
        """
        order = order['data']
        pos_session = self.env['pos.session'].browse(order['pos_session_id'])
        if pos_session.state == 'closing_control' or pos_session.state == 'closed':
            order['pos_session_id'] = self._get_valid_session(order).id

        pos_order = False
        if not existing_order:
            pos_order = self.create(self._order_fields(order))
        else:
            pos_order = existing_order
            pos_order.lines.unlink()
            order['user_id'] = pos_order.user_id.id
            pos_order.write(self._order_fields(order))

        pos_order = pos_order.with_company(pos_order.company_id)
        self = self.with_company(pos_order.company_id)
        self._process_payment_lines(order, pos_order, pos_session, draft)

        #  /\_/\
        # ( ◕‿◕ )
        #  >   <
        # Beginning: Ehab
        # Prevent Making Invoice or stock move for coupon papers

        no_invoice = False
        for line in order['lines']:
            if line[2]['product_id'] == 3562:  # TODO: Hardcode - Settings
                no_invoice = True
        # ______ (｡◔‿◔｡) ________ End of code

        if not draft:
            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            # ______ (｡◔‿◔｡) _____
            if not no_invoice:
                pos_order._create_order_picking()
                pos_order._compute_total_cost_in_real_time()
            # ______ (｡◔‿◔｡) ________ End of code

        if not draft and pos_order.to_invoice and pos_order.state == 'paid' and  (
        hasattr(pos_order, 'invoice_id')) and not pos_order.invoice_id:
            pos_order._create_invoice()

        if pos_order.to_invoice and pos_order.state == 'paid' and not no_invoice:  # ______ (｡◔‿◔｡) _____
            pos_order._generate_pos_order_invoice()

        # ______ (｡◔‿◔｡) ________ End of code

        return pos_order.id
