# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResUsers(models.Model):

    _inherit = 'res.users'

    invoice_partner_ids = fields.Many2many('multi.partners.service', string="خدمات فواتير المصروفات متعددة الموردين")
    barcode_department = fields.Char('اسم الادارة')

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_nomination_report_to(self):
        header_html = '''<div><b>  سعادة مدير عام الإدارة العامة للشؤون الإدارية والمالية </b></div>

        '''
        return header_html

    company_type_nauss = fields.Selection(string='نوع', selection=[('person', 'طالب'), ('company', 'جهة')] )

    college = fields.Char('College')
    uni_id = fields.Char('University ID')
    identify_number = fields.Char('Identify ID')
    supplier_id = fields.Char('Supplier ID')
    nomination_no = fields.Char('رقم خطاب الترشيح')
    nomination_date = fields.Date('تاريخ خطاب الترشيخ')
    nomination_report_recipient = fields.Html('توجيه الخطاب', default=get_nomination_report_to)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10000):
        args = args or []
        if name:
            domain = ['|', '|', '|', '|', '|', '|', ('nomination_no', 'ilike', name), ('display_name', 'ilike', name),
                      ('ref', '=', name), ('email', '=', name), ('college', 'ilike', name), ('uni_id', 'ilike', name),
                      ('identify_number', 'ilike', name)]
        else:
            domain = []
        p = self.search(domain + args, limit=limit)
        return p.name_get()
