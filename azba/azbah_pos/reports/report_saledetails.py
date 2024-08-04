# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta

import pytz

from odoo import api, fields, models, tools, _
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)

class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'
    _description = 'Point of Sale Details'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        """ Serialise the orders of the requested time period, configs, and sessions.

        :param date_start: The datetime to start, default today 00:00:00.
        :type date_start: str.
        :param date_stop: The datetime to stop, default date_start + 23:59:59.
        :type date_stop: str.
        :param config_ids: POS Config IDs to include.
        :type config_ids: list of int.
        :param session_ids: POS Session IDs to include.
        :type session_ids: list of int.

        :returns: dict -- Serialised sales.
        """
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        if session_ids:
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            date_start, date_stop = self._get_date_range(date_start, date_stop)
            domain = AND([domain,
                          [('date_order', '>=', fields.Datetime.to_string(date_start)),
                           ('date_order', '<=', fields.Datetime.to_string(date_stop))]])

        if config_ids:
            domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['pos.order'].search(domain)
        user_currency = self.env.company.currency_id

        total, products_sold, taxes = self._process_orders(orders, user_currency)

        payments = self._get_payments(orders.ids)
        cash_details = self._get_cash_details(date_start, date_stop, config_ids)

        return {
            'cashes': cash_details['cashes'],
            'credits': cash_details['credits'],
            'debits': cash_details['debits'],
            'total_cash': cash_details['total_cash'],
            'total_credit': cash_details['total_credit'],
            'total_debit': cash_details['total_debit'],
            'total_debit_and_cash': cash_details['total_cash'] + cash_details['total_debit'],
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': self._get_sorted_products(products_sold),
        }

    @api.model
    def _get_date_range(self, date_start, date_stop):
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
            today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
            date_start = today.astimezone(pytz.timezone('UTC'))

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
            if date_stop < date_start:
                date_stop = date_start + timedelta(days=1, seconds=-1)
        else:
            date_stop = date_start + timedelta(days=1, seconds=-1)

        return date_start, date_stop

    def _process_orders(self, orders, user_currency):
        total = 0.0
        products_sold = {}
        taxes = {}

        for order in orders:
            total += self._convert_amount(order, user_currency)

            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                line_taxes = self._compute_taxes(line)
                self._update_taxes(taxes, line_taxes, line.price_subtotal_incl)

        return total, products_sold, taxes

    def _convert_amount(self, order, user_currency):
        if user_currency != order.pricelist_id.currency_id:
            return order.pricelist_id.currency_id._convert(
                order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
        return order.amount_total

    def _compute_taxes(self, line):
        currency = line.order_id.session_id.currency_id
        if line.tax_ids_after_fiscal_position:
            return line.tax_ids_after_fiscal_position.sudo().compute_all(
                line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty,
                product=line.product_id, partner=line.order_id.partner_id or False)
        return None

    def _update_taxes(self, taxes, line_taxes, price_subtotal_incl):
        if line_taxes:
            for tax in line_taxes['taxes']:
                taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount': 0.0, 'base_amount': 0.0})
                taxes[tax['id']]['tax_amount'] += tax['amount']
                taxes[tax['id']]['base_amount'] += tax['base']
        else:
            taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount': 0.0, 'base_amount': 0.0})
            taxes[0]['base_amount'] += price_subtotal_incl

    def _get_payments(self, order_ids):
        if order_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment
                JOIN pos_payment_method AS method ON payment.payment_method_id = method.id
                WHERE payment.pos_order_id IN %s
                GROUP BY method.name
            """, (tuple(order_ids),))
            return self.env.cr.dictfetchall()
        return []

    def _get_cash_details(self, date_start, date_stop, config_ids):
        payments_cash_sql = """
                SELECT p.payment_date, o.pos_reference, p.amount, m.id AS payment_method_id, m.name,
                       CONCAT('[', partner.code, '] ', partner.name) AS partner_name, p.session_id, o.name
                FROM pos_payment p
                JOIN pos_payment_method m ON p.payment_method_id = m.id
                JOIN pos_order o ON o.id = p.pos_order_id
                JOIN pos_session s ON p.session_id = s.id
                JOIN pos_config c ON c.id = s.config_id
                JOIN res_partner partner ON o.partner_id = partner.id
                WHERE p.payment_date BETWEEN %s AND %s AND c.id IN %s
                ORDER BY p.payment_date, m.name
                """.replace(',)', ')')

        self.env.cr.execute(payments_cash_sql, (date_start, date_stop, tuple(config_ids)))
        payments_cash = self.env.cr.dictfetchall()

        return self._process_cash_details(payments_cash)

    def _process_cash_details(self, payments_cash):
        cashes, credits, debits = [], [], []
        total_cash, total_credit, total_debit = 0, 0, 0

        for payment in payments_cash:
            if payment['payment_method_id'] in [3, 8]:
                if payment['amount'] > 0:
                    credits.append(payment)
                    total_credit += float(payment['amount'])
                elif payment['amount'] < 0:
                    debits.append(payment)
                    total_debit += float(payment['amount'])
            elif payment['payment_method_id'] in [1, 7]:
                cashes.append(payment)
                total_cash += float(payment['amount'])

        for debit in debits:
            cash_to_remove = next((cash for cash in cashes if
                                   debit['pos_reference'] == cash['pos_reference'] and
                                   debit['amount'] == cash['amount'] * -1), None)
            if cash_to_remove:
                cashes.remove(cash_to_remove)
                total_cash -= float(cash_to_remove['amount'])

        return {
            'cashes': cashes,
            'credits': credits,
            'debits': debits,
            'total_cash': total_cash,
            'total_credit': total_credit,
            'total_debit': total_debit,
        }

    def _get_sorted_products(self, products_sold):
        return sorted([{
            'product_id': product.id,
            'product_name': product.name,
            'code': product.default_code,
            'quantity': qty,
            'price_unit': price_unit,
            'discount': discount,
            'uom': product.uom_id.name
        } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids))
        return data
