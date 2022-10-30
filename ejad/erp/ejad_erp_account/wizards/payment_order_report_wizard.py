# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from ummalqura.hijri_date import HijriDate

from odoo.exceptions import UserError


class PaymentOrder(models.TransientModel):
    _name = 'payment.order.report.wizard'

    date = fields.Date('التاريخ', default=fields.Date.today(), required=True)
    hijri_date = fields.Char('Hijri date', compute='_compute_hijri_date')
    move_id = fields.Many2one('account.move', string='قيد اليومية')
    basis_exchange = fields.Text('أساس الصرف', default="اللائحة التنفيذية للنظام المالي")
    report = fields.Text('البيان')
    user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)
    transfer_speech_no = fields.Char('رقم خطاب التحويل')
    transfer_speech_date = fields.Date('تاريخ خطاب التحويل', default=fields.Date.today())
    partner_name = fields.Char(string="صاحب الاستحقاق")
    paid_amount = fields.Float('المبلغ')
    paid_amount_words = fields.Char('المبلغ المسدد كتابيا', compute='_compute_amount_to_text')
    credit_account_id = fields.Many2one('account.account')
    debit_account_id = fields.Many2one('account.account')
    payment_name = fields.Char('رقم السداد')

    @api.onchange('move_id')
    def _onchange_move_id(self):
        if self.move_id.partner_id:
            self.partner_name = self.move_id.partner_id.name
        if self.move_id.amount_total:
            self.paid_amount = self.move_id.amount_total
        if self.move_id.report:
            self.report = self.move_id.report
        self.transfer_speech_no = self.move_id.bank_ref or self.move_id.bank_check_no or False
        for line in self.move_id.line_ids:
            if line.credit != 0:
                self.credit_account_id = line.account_id
                # self.payment_name = line.name
            elif line.debit != 0:
                self.debit_account_id = line.account_id

    # TODO
    @api.depends('date')
    def _compute_hijri_date(self):
        # hijri_date = str(HijriDate.get_hijri_date(self.date))
        hijri_date = self.date
        self.hijri_date = hijri_date

    @api.depends('paid_amount')
    def _compute_amount_to_text(self):
        self.paid_amount_words = self.env.user.company_id.currency_id.amount_to_text(self.paid_amount).replace('Riyal',
                                                                                                               'ريال ').replace(
            'Halala', 'هللة') + ' لا غير'

    def print_payment_order_report(self):
        return self.env.ref('ejad_erp_account.payment_order_report_action').report_action(self)
