# -*- coding: utf-8 -*-

from datetime import datetime
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ReportReceivablePartnerLedger(models.AbstractModel):
    _name = 'report.ejad_ejad_erp_account.report_training_courses'

    def _lines(self, data, partner):
        if data['form']['courses_ids']:
            courses_ids = data['form']['courses_ids']

        else:
            courses_ids = self.env['product.template'].search(
                [('categ_id', 'child_of', self.env.ref('ejad_ejad_erp_account.product_category_trqining').id)]).ids

        domain = []
        if data['form']['date_from']:
            domain += [('invoice_id.date_invoice', '>=', data['form']['date_from'])]
        if data['form']['date_to']:
            domain += [('invoice_id.date_invoice', '<=', data['form']['date_to'])]

        invoice_lines = self.env['account.invoice.line'].search(
            [('invoice_id.state', 'in', ['open', 'paid']),
             ('product_id', 'in', courses_ids),
             ('invoice_id.partner_id', 'child_of', partner.id),
             ] + domain)
        invoice_lines = sorted(invoice_lines, key=lambda x: x.product_id.name)

        return invoice_lines

    def sum_partner_courses(self, data, partner):
        sum = []
        total_courses = 0.0
        total_remaining = 0.0
        invoice_lines = self._lines(data, partner)
        invoice_ids = [line.invoice_id.id for line in invoice_lines]
        invoice_ids = list(set(invoice_ids))
        invoice_ids = self.env['account.invoice'].browse(invoice_ids)

        for line in invoice_ids:
            total_courses += line.amount_total
            total_remaining += line.residual
        total_paid = total_courses - total_remaining
        sum.extend((total_courses, total_paid, total_remaining))

        return sum

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
            partners = self.env['res.partner'].browse(partner_ids)

        else:
            if data['form']['courses_ids']:
                courses_ids = data['form']['courses_ids']
            else:
                courses_ids = self.env['product.template'].search(
                    [('categ_id', 'child_of', self.env.ref('ejad_ejad_erp_account.product_category_trqining').id)]).ids

            domain = []
            if data['form']['date_from']:
                domain += [('invoice_id.date_invoice', '>=', data['form']['date_from'])]
            if data['form']['date_to']:
                domain += [('invoice_id.date_invoice', '<=', data['form']['date_to'])]

            invoice_lines = self.env['account.invoice.line'].search(
                [('invoice_id.state', 'in', ['open', 'paid']),
                 ('product_id', 'in', courses_ids),
                 ] + domain)

            partner_ids = [line.invoice_id.partner_id.id for line in invoice_lines]
            partner_ids = list(set(partner_ids))
            partners = self.env['res.partner'].browse(partner_ids)
            if data['form']['contact_type'] == 'company':
                partners = partners.filtered(lambda p: p.child_ids)
            elif data['form']['contact_type'] == 'student':
                partners = partners.filtered(lambda p: not p.child_ids)

        partners = sorted(partners, key=lambda x: (x.ref or '', x.name or ''))

        return {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'lines': self._lines,
            'sum_partner_courses': self.sum_partner_courses,
        }
