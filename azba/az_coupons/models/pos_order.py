# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json

from odoo import api, fields, models, tools, _
import psycopg2
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    # 📜 Function to create a coupon based on the order lines
    @api.model
    def create_coupon(self, receipt_number, product_id, qty):
        # 🎨 Loop through each line in the order
        created_coupons = []
        product = self.env['product.product'].browse(product_id)

        coupon_page_count = self.env['coupon.book.product'].search([('product_id', '=', product_id)],
                                                                   limit=1).page_count

        # 🔄 If the product has coupon pages, create coupons
        if coupon_page_count > 0:
            for i in range(qty):
                id = self.env['az.coupon'].create({
                    'name': product.name,
                    'page_count': coupon_page_count,
                    'product_id': product_id,
                    'receipt_number': receipt_number
                })
                created_coupons.append(id.code)

        return created_coupons

    def remove_from_stock(self, partner_id, pos_session_id, page_count):
        # get the location bound by the session
        location_id = self.env['pos.session'].browse(
            pos_session_id).config_id.picking_type_id.default_location_src_id
        picking_type_id = self.env['pos.session'].browse(pos_session_id).config_id.picking_type_id
        dest_location_id = picking_type_id.default_location_dest_id

        # get the product with the same page_count from coupon_book_product_ids
        product = self.env['coupon.book.product'].search([
            ('page_count', '=', page_count),
        ], limit=1).product_id

        location_id, dest_location_id = dest_location_id, location_id
        # create a stock move
        # First, create the stock.picking record
        stock_picking = self.env['stock.picking'].create({
            'partner_id': partner_id,  # Add the partner_id if required
            'location_id': location_id.id,
            'location_dest_id': dest_location_id.id,
            'picking_type_id': picking_type_id.id,  # Define the picking type (e.g., internal, outgoing, incoming)
            'origin': f"Used Coupon Book - {product.id}",
            'state': 'draft',
        })

        # Then, create the stock.move record and link it to the stock.picking
        stock_move = self.env['stock.move'].create({
            'name': f"Used Coupon Book - {product.id}",
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
            'location_id': location_id.id,
            'location_dest_id': dest_location_id.id,
            'picking_id': stock_picking.id,  # Link the move to the picking
            'state': 'draft',
        })

        # Confirm the picking to change its state to 'done'
        stock_picking.action_confirm()
        stock_picking.action_assign()
        for move in stock_picking.move_lines:
            move.quantity_done = move.product_uom_qty
        stock_picking.button_validate()

        return stock_picking

    # 📄 Function to handle pages based on order values
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

        # Rest of your handle_pages method...
        partner_id = values['partner_id']
        used_coupons = []  # List to store the codes of used coupons

        for line in values['lines']:
            if line[2]['product_id'] == product_id.id:
                qty = line[2]['qty']  # Get the quantity of the product

                while qty > 0:
                    # Get the oldest valid or partial coupon book for this partner
                    coupon_book = self.env['az.coupon'].search(
                        [('partner_id', '=', partner_id), ('state', '!=', 'used')],
                        order='id asc', limit=1
                    )

                    if not coupon_book:
                        break  # Exit loop if no valid or partial coupon book is found

                    # Get the required number of coupon pages from the coupon book
                    coupon_pages = self.env['az.coupon.page'].search(
                        [('coupon_book_id', '=', coupon_book.id), ('state', '!=', 'used')],
                        order='id asc', limit=qty
                    )

                    if not coupon_pages:
                        break  # Exit loop if no valid coupon pages are found

                    # Update the state of each page to 'used'
                    for page in coupon_pages:
                        page.state = 'used'
                        page.date_used = fields.Datetime.now()
                        page.pos_session_id = values['pos_session_id']
                        qty -= 1  # Decrease the remaining quantity
                        used_coupons.append(page.code)  # Add code to the list

                    # Check the state of the coupon book after updating the pages
                    valid_pages_left = self.env['az.coupon.page'].search_count(
                        [('coupon_book_id', '=', coupon_book.id), ('state', '!=', 'used')]
                    )

                    if valid_pages_left == 0:
                        coupon_book.state = 'used'
                        # remove one from stock
                        self.remove_from_stock(partner_id, values['pos_session_id'], coupon_book.page_count)

                    else:
                        coupon_book.state = 'partial'

        return sorted(used_coupons)  # Return the list of used coupon codes

    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        order = super(PosOrder, self).create(values)

        self.update_coupon(order)
        # Send WhatsApp message
        self.send_whatsapp_message(order)
        return order

    def update_coupon(self, order):
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

    def format_to_whatsapp_number(self, mobile_number):
        import re

        # Remove any non-numeric acters
        mobile_number = re.sub(r'\D', '', mobile_number)

        # Check and remove leading '00'
        if mobile_number.startswith('00'):
            mobile_number = mobile_number[2:]

        # Check and remove leading '+'
        if mobile_number.startswith('+'):
            mobile_number = mobile_number[1:]

        # Ensure it starts with '966'
        if mobile_number.startswith('966'):
            # Remove any '0' after '966'
            if mobile_number[3] == '0':
                mobile_number = '966' + mobile_number[4:]
        else:
            # Handle other cases where the number might not start with '966'
            # You might want to add specific logic for these cases
            mobile_number = '966' + mobile_number

        return mobile_number

    @api.model
    def send_whatsapp_message(self, order):
        partner = order.partner_id

        whatsapp_number = partner.mobile
        if not whatsapp_number:
            return

        qty = 0
        for line in order.lines:
            if line.product_id.id == 4 and line.price_subtotal == 0:
                qty = int(line.qty)
        if not qty:
            return
        coupons = self.env['az.coupon'].search([('partner_id', '=', partner.id)])
        remaining_coupons = len(coupons.mapped('page_ids').filtered(lambda p: p.state == 'valid'))
        last_used_coupons = coupons.mapped('page_ids').filtered(lambda p: p.state == 'used').sorted(
            key=lambda p: p.date_used, reverse=True)[:qty]
        last_used_coupons = last_used_coupons.mapped('code')

        import requests
        to_number = self.format_to_whatsapp_number(whatsapp_number)
        from_number = "whatsapp:966593120000"
        messaging_service_sid = "MGbf7e1ca8d7581693a55d09285733d1cc"  # Messaging Service SID

        account_sid = "AC2d38454d87a1d186927a4488eed3842f"  # IrConfigParam.get_param('az_coupons.twilio_account_sid')
        auth_token = "74a21fd14e6f7a72f004a93a1c8dff90"  # IrConfigParam.get_param('az_coupons.twilio_auth_token')

        variables = {
            "1": partner.name,
            "2": str(qty),
            "3": str(last_used_coupons),
            "4": str(remaining_coupons)
        }

        variables = json.dumps(variables, ensure_ascii=False, indent=2)

        payload = {
            'ContentSid': 'HX0a9f3d367c6163eb0f00bd4cd0e3897f',
            'To': f'whatsapp:{to_number}',
            'From': from_number,
            # 'Body': body,
            'MessagingServiceSid': messaging_service_sid,
            'ContentVariables': variables
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()}'
        }

        response = requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json',
            headers=headers,
            data=payload,
        )

        if not str(response.status_code).startswith('2'):
            raise ValueError("Failed to send WhatsApp message. Response: %s" % response.text)

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

        #  /\_/\
        # ( ◕‿◕ )
        #  >   <
        # Beginning: Ehab
        # Prevent Making Invoice or stock move for coupon pages
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        coupon_page_product_id = IrConfigParam.get_param('az_coupons.coupon_page_product')
        if not coupon_page_product_id:
            raise UserError(_("Coupon Page Product is not set in the settings. Please configure it first."))

        coupon_page_product_id = int(coupon_page_product_id)

        new_lines = []
        no_invoice = False
        for line in order['lines']:
            if line[2]['product_id'] == coupon_page_product_id:
                no_invoice = True
            else:
                new_lines.append(line)
        order['lines'] = new_lines
        # ______ (｡◔‿◔｡) ________ End of code

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

        if not draft:
            try:
                pos_order.action_pos_order_paid()
            except psycopg2.DatabaseError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            # ______ (｡◔‿◔｡) _____
            # if not no_invoice:
            pos_order._create_order_picking()
            pos_order._compute_total_cost_in_real_time()
            # ______ (｡◔‿◔｡) ________ End of code

        if not draft and pos_order.to_invoice and pos_order.state == 'paid' and (
                hasattr(pos_order, 'invoice_id')) and not pos_order.invoice_id:
            pos_order._create_invoice()

        if pos_order.to_invoice and pos_order.state == 'paid' and not no_invoice:  # ______ (｡◔‿◔｡) _____
            pos_order._generate_pos_order_invoice()

        # ______ (｡◔‿◔｡) ________ End of code

        return pos_order.id
