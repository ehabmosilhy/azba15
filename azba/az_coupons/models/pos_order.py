# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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
        # 🧐 Check if the product name contains 'book' or 'دفتر'
        created_coupons = []
        product = self.env['product.product'].browse(product_id)

        # Fetch the settings
        config = self.env['res.config.settings'].search([], limit=1)
        # Find the page count for the given product_id
        coupon_page_count = next(
            (line.page_count for line in config.coupon_book_product_ids if line.product_id.id == product_id), 0)
        # 🔄 If the product has coupon pages, create coupons
        if coupon_page_count > 0:
            for i in range(qty):
                id = self.env['az.coupon'].create({
                    'name': product.name,
                    'page_count': coupon_page_count,
                    'product_id': product_id
                    , 'receipt_number': receipt_number
                })
                created_coupons.append(id.code)

        return created_coupons

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
                    else:
                        coupon_book.state = 'partial'

        return sorted(used_coupons)  # Return the list of used coupon codes

    @api.model
    def create(self, values):
        session = self.env['pos.session'].browse(values['session_id'])
        values = self._complete_values_from_session(session, values)
        order = super(PosOrder, self).create(values)

        # Send WhatsApp message
        self.send_whatsapp_message(order)
        self.update_coupon(order)
        return order

    def update_coupon(self, order):
        for line in order.lines:
            line.full_product_name = line.product_id.display_name
        reference = order.pos_reference.replace('Order', '').strip()
        coupons = self.env['az.coupon'].search([('receipt_number', '=', reference)])
        for coupon in coupons:
            coupon.pos_order_id = order.id

    """
    def send_whatsapp_message(self, order):
        # TODO: Hardcoded - convert to settings settings
        import requests
        body = f"Order has been made \n Partner: {order.partner_id.name} \n  Session: {order.session_id.name}"
        data = {
            'To': 'whatsapp:+971527006631',
            'From': 'whatsapp:+14155238886',
            'Body': body,
        }

        response = requests.post(
            'https://api.twilio.com/2010-04-01/Accounts/ACe163c62ab44430affdf900abef670659/Messages.json',
            data=data,
            auth=('ACe163c62ab44430affdf900abef670659', '588fb1681095b0bba077163f521a69d5'),
        )
    """

    @api.model
    def send_whatsapp_message(self, order):
        qty = 0
        for line in order.lines:
            if line.product_id.id == 4 and line.price_subtotal == 0:
                qty = int(line.qty)
        if not qty:
            return
        partner = order.partner_id
        coupons = self.env['az.coupon'].search([('partner_id', '=', partner.id)])
        remaining_coupons = len(coupons.mapped('page_ids').filtered(lambda p: p.state == 'valid'))
        last_used_coupons = coupons.mapped('page_ids').filtered(lambda p: p.state == 'used').sorted(
            key=lambda p: p.date_used, reverse=True)[:qty]
        last_used_coupons = last_used_coupons.mapped('code')

        import requests
        IrConfigParam = self.env['ir.config_parameter'].sudo()
        to_number = partner.mobile
        user_sender = "auth-mseg" #IrConfigParam.get_param('az_coupons.sms_user_sender')
        api_key = "395D8B0ABD3F882431C2452FA3B3360B" #IrConfigParam.get_param('az_coupons.sms_api_key')
        username = "samehelsawy" #IrConfigParam.get_param('az_coupons.sms_username')

        # if not all([to_number, user_sender, api_key, username]):
        #     return
            # raise ValueError("Please configure all SMS settings in the Coupons Settings.")

        body = (
            f"Dear {partner.name} \n A quantity of <{qty}> Bottles has been exchanged for coupon(s) "
            f"{last_used_coupons}.\nYou still have <{remaining_coupons}> valid coupons.\n"
            f"{'-' * 50}\n"
            f"عميلنا العزيز/ "
            f"{partner.name} \n"
            f"تم استبدال عدد "
            f"<{qty}>"
            f" قوارير فى مقابل الكوبونات"
            f" {last_used_coupons} "
            f"\n"
            f"يتبقى لديك عدد "
            f"<{remaining_coupons}>"
            f"كوبون صالح للاستخدام"
        )

        data = {
            'userName': username,
            'apiKey': api_key,
            'numbers': to_number,
            'userSender': user_sender,
            'msg': body,
            'msgEncoding': 'UTF8',
            'timeToSend': 'now',
            'exactTime': '',
            'reqBulkId': 'false',
            'reqFilter': 'true',
        }

        response = requests.post(
            'https://www.msegat.com/gw/sendsms.php',
            data=data,
        )

        if response.status_code != 200:
            raise ValueError("Failed to send SMS message. Response: %s" % response.text)

        # WhatsApp section commented out
        # IrConfigParam = self.env['ir.config_parameter'].sudo()
        # to_number = IrConfigParam.get_param('az_coupons.whatsapp_to_number')
        # from_number = IrConfigParam.get_param('az_coupons.whatsapp_from_number')
        # account_sid = IrConfigParam.get_param('az_coupons.twilio_account_sid')
        # auth_token = IrConfigParam.get_param('az_coupons.twilio_auth_token')

        # if not all([to_number, from_number, account_sid, auth_token]):
        #     raise ValueError("Please configure all WhatsApp settings in the Coupons Settings.")

        # data = {
        #     'To': f'whatsapp:{to_number}',
        #     'From': f'whatsapp:{from_number}',
        #     'Body': body,
        # }

        # response = requests.post(
        #     f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json',
        #     data=data,
        #     auth=(account_sid, auth_token),
        # )

        # if response.status_code != 201:
        #     raise ValueError("Failed to send WhatsApp message. Response: %s" % response.text)

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
