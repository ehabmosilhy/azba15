# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RefundReport(models.TransientModel):
    _name = 'refund.invoice.report.wizard'

    date = fields.Date('التاريخ', default=fields.Date.today(), required=True)
    invoice_id = fields.Many2one('account.move', string='invoice multi partners')
    working_place = fields.Char('جهة العمل')
    paid_amount = fields.Float('المبلغ المسدد')
    paid_amount_words = fields.Char('المبلغ المسدد كتابيا', compute='_compute_amount_to_text')
    year_and_degree = fields.Char('العام الدراسي/الدرجة')
    refund_reason = fields.Char('سبب استيراد الرسوم الدراسية')
    registration_office_report = fields.Text('قرار عمادة القبول والتسجيل')
    bank_account_name = fields.Char('اسم صاحب الاّيبان')
    bank_acc = fields.Char( string='الحساب البنكي')
    bank_name = fields.Char( string='اسم البنك')

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id.invoice_line_ids[0]:
            self.paid_amount = self.invoice_id.invoice_line_ids[0].price_subtotal
            self.year_and_degree = self.invoice_id.invoice_line_ids[0].name
            self.refund_reason = self.invoice_id.refund_reason
            self.bank_account_name = self.invoice_id.invoice_line_ids[0].partner_id1.name
        bank_acc = self.env['res.partner.bank'].search([('partner_id', '=', self.invoice_id.invoice_line_ids[0].partner_id1.id)])
        if bank_acc:
            self.bank_acc = bank_acc.acc_number
            self.bank_name = bank_acc.bank_id.name

    @api.depends('paid_amount')
    def _compute_amount_to_text(self):
        self.paid_amount_words = self.env.user.company_id.currency_id.amount_to_text(self.paid_amount).replace('Riyal','ريال')

    def print_refund_invoice_report(self):
        return self.env.ref('ejad_erp_account.account_refund_invoice_report_action').report_action(self)
