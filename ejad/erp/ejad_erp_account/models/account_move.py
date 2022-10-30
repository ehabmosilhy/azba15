# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    bank_ref = fields.Char('رقم السند')
    bank_check_no = fields.Char('رقم الشيك')
    reverse_request_id = fields.Many2one('reverse.entry.request', string='Revere Entry Request')
    report = fields.Char('البيان')
    bank_account_info = fields.Text('معلومات الحساب البنكي')
    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     string='نوع السداد')

    # invoice field
    invoice_report = fields.Char('البيان')
    invoice_report_html = fields.Html('خطاب المطالبة المالية', readonly=True)
    report_generated = fields.Boolean('Is Report Generated')
    refund_reason = fields.Char('سبب استيراد الرسوم الدراسية')
    is_pay_by_custody = fields.Boolean(string="هل دفع بواسطة عهدة؟", default=False,
                                       states={'draft': [('readonly', False)]})
    custody_partner_id = fields.Many2one('res.partner', string='المورد', change_default=True,
                                         readonly=True, states={'draft': [('readonly', False)]},
                                         tracking=True)
    partner_id = fields.Many2one(readonly=True,
                                 states={'draft': [('readonly', False)], 'accountant_approval': [('readonly', False)]},
                                 tracking=True)
    date_due = fields.Date(default=fields.Date.context_today)
    date_invoice = fields.Date(default=fields.Date.context_today)

    @api.constrains('bank_ref')
    def _check_bank_reference(self):
        for record in self:
            if self.bank_ref:
                if self.env['account.move'].search([('bank_ref', '=', self.bank_ref),
                                                    ('id', '!=', self.id)]):
                    raise ValidationError(_(
                        'Bank reference should be unique number and  %s already used in other journal entry)') % record.bank_ref)

    def invoice_report_print(self):
        return self.env.ref('ejad_erp_account.account_invoice_report_action').report_action(self)

    def generate_html_invoice_report(self):

        table_lines = ''
        total_amount = 0
        seq = 0
        for line in self.invoice_line_ids:
            seq = seq + 1
            total_amount += line.price_unit
            table_lines += '''
                        <tr> 
                        <td> 
                        <span>''' \
                           + str(seq) + '''
                        </span>
                        </td>
                        <td> 
                        <span>''' \
                           + str(line.partner_id1.uni_id or '') + '''
                        </span>
                        </td>
                        <td> 
                        <span>''' \
                           + str(line.partner_id1.name or '') + '''
                        </span>
                        </td>
                         <td> 
                        <span>''' \
                           + str(line.name or '') + '''
                        </span>
                        </td>
                         <td> 
                        <span>''' \
                           + str(line.price_unit or '') + '''
                        </span>
                        </td>
                         <td> 
                        <span>''' \
                           + str(line.partner_id1.identify_number or '') + '''
                        </span>
                        </td>
                        </tr>'''
        partner_id = self.invoice_line_ids[0].partner_id1
        if not partner_id:
            raise UserError(_('الرجاء إضافة الجهة/الطالب لبنود الفاتورة'))

        self.invoice_report_html = partner_id.nomination_report_recipient + self.company_id.inv_report_header \
            .replace('()', partner_id.nomination_no or '', 1) \
            .replace('()', partner_id.nomination_date and str(datetime.strptime(str(partner_id.nomination_date), '%Y-%m-%d').strftime('%d-%m-%Y')) or '',
                     1) + '''
                         <table class="table table-bordered">
                        <thead>
                            <tr>
                                <th class="text-center">#</th>
                                <th class="text-center">الرقم الجامعي</th>
                                <th class="text-center">اسم الطالب</th>
                                <th class="text-center">برنامج الدراسة</th>
                                <th class="text-center">الرسوم الدراسية</th>
                                <th class="text-center">السجل المدني</th>
                            </tr>
                        </thead>''' + table_lines + '''
                    </table> ''' + '''

                    للدراسة لدى الجامعة وحيث لم يردنا حتي تاريخه إشعار بتسديد المبلغ المستحق وقدرة 
                    ''' + str(self.currency_id.amount_to_text(total_amount)) + ' ''(''' + \
                                   str(total_amount) + '''ريال لاغير (''' + self.company_id.inv_report_footer
