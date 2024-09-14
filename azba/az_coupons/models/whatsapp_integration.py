# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
import json
import re
import requests
import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsAppIntegration(models.AbstractModel):
    _name = "whatsapp.integration"

    def format_to_whatsapp_number(self, mobile_number):
        # Remove any non-numeric characters
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
            mobile_number = '966' + mobile_number

        return mobile_number

    @api.model
    def send_whatsapp_message(self, order):
        partner = order.partner_id
        whatsapp_number = partner.mobile
        if not whatsapp_number or len(whatsapp_number) < 4:
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

        to_number = self.format_to_whatsapp_number(whatsapp_number)
        from_number = "whatsapp:966593120000"
        messaging_service_sid = "MGbf7e1ca8d7581693a55d09285733d1cc"

        account_sid = "AC2d38454d87a1d186927a4488eed3842f"
        auth_token = "74a21fd14e6f7a72f004a93a1c8dff90"

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
