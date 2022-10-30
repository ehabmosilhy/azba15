# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, pycompat


class AccountInvoice(models.Model):
    _inherit = "res.company"

    @api.model
    def get_invoice_report_header(self):
        header_html = '''
        <div>السلام عليكم ورحمة الله وبركاته</div>
        </br/> تهدي جامعة نايف العربية للعلوم الأمنية أطيب تحياتها لكم ، وإشارة إلى خطابكم رقم() 
        بتاريخ () المتضمن ترشيح :
        
        '''
        return header_html

    @api.model
    def get_invoice_report_footer(self):
        footer_html = '''<div>نأمل من سعادتكم التوجه بتسديد المبلغ المستحق بإيداعه مباشرة في حساب الجامعة
         لدى البنك العربي الوطني اّيبان رقم: (SA 7530 4001 0805 2323 8400 24) وتزويدنا بتفاصيل المبلغ المسدد، شاكرين لكم ثقتكم وتعاونكم مع الجامعة.
         </div>
         <div class="text-center"> وتقبلوا تحياتي وتقديري،،،</div> 
        '''
        return footer_html

    bank_report_footer = fields.Html('تذييل  خطاب البنك')
    address_bank_report = fields.Text('العنوان لخطاب البنك')
    inv_report_header = fields.Html('مقدمة خطاب المطالبة المالية', default=get_invoice_report_header)
    inv_report_footer = fields.Html('تذييل خطاب المطالبة المالية', default=get_invoice_report_footer)
    sign_payment_order_report = fields.Many2one('report.signature', string='أمر اعتماد الصرف')
    sign_refund_invoice_report_reg = fields.Many2one('report.signature',
                                                     string='طلب استيراد رسوم دراسية-الفبول والتسجيل')
    sign_refund_invoice_report_finance = fields.Many2one('report.signature',
                                                         string='طلب استيراد رسوم دراسية-الإدارة المالية')


class ReportSignature(models.Model):
    _name = "report.signature"

    name = fields.Char(string='الاسم')
    signature = fields.Html(string='تنسيق التوقيع')
