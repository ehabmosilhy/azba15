# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from lxml import etree


class MultiPartnersService(models.Model):
    _name = 'multi.partners.service'

    name = fields.Char(string="اسم الخدمة", required=False)
    account_id = fields.Many2one('account.account', string="الحساب الافتراضي")
    active = fields.Boolean(default=True, string="نشط")


class AccountInvoiceMultiPartnersLine(models.Model):
    _name = 'account.invoice.multi.partners.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="الوصف",)
    partner_id = fields.Many2one('res.partner', string='المورد')
    amount = fields.Float('المبلغ')
    parent_id = fields.Many2one('account.invoice.multi.partners')
    partner_id2 = fields.Many2one('partner.invoice.multi', string="صاحب الاستحقاق")

    acc_number = fields.Text('رقم و تفاصيل الحساب البنكي')
    bank_id = fields.Many2one('res.bank', string='البنك')


    @api.onchange('partner_id2')
    def onchange_partner_id_bank_account(self):
        for rec in self:
            bank = rec.partner_id2.bank_account_id
            rec.acc_number = bank.acc_number
            rec.bank_id = bank.bank_id.id


class AccountInvoiceMultiPartners(models.Model):
    _name = 'account.invoice.multi.partners'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountInvoiceMultiPartners, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        # print(' ########    8898898')
        for node in doc.xpath("//field[@name='service_id']"):
            if self.env.user.has_group('ejad_erp_account.access_multi_partners_all_services'):
                node.set('domain', "[('id','!=',-1)]")
            elif (not self.env.user.has_group('ejad_erp_account.access_multi_partners_all_services')) and self.env.user.has_group('ejad_erp_account.access_multi_partners_specific_services'):
                service_ids = self.env.user.invoice_partner_ids and self.env.user.invoice_partner_ids.ids or []
                ddomain = "[('id', 'in', %s)]"%service_ids
                node.set('domain', ddomain)
            else:
                node.set('domain', "[('id','in',[])]")
        result['arch'] = etree.tostring(doc)
        return result

    @api.onchange('service_id')
    def onchange_service_account(self):
        for rec in self:
            rec.account_id = rec.service_id.account_id.id

    @api.depends('line_ids', 'line_ids.amount')
    def _get_total(self):
        for rec in self:
            amount = 0.00
            for line in rec.line_ids:
                amount += (line.amount or 0.00)
            rec.total = amount

    @api.model
    def _default_journal(self):
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [('type', 'in', ['purchase']),('company_id', '=', company_id)]
        return self.env['account.journal'].search(domain, limit=1)

    line_ids = fields.One2many('account.invoice.multi.partners.line', 'parent_id', string='')
    journal_id = fields.Many2one('account.journal', string='اليومية', required=True, readonly=True,
                                 states={'draft': [('readonly', False)]}, default=_default_journal)
    name = fields.Char(string='الكود', readonly=True, tracking=True, default='/')
    description = fields.Text(string="البيان", tracking=True)
    date = fields.Date(string="التاريخ", default=fields.Date.context_today, required=True, tracking=True)
    payment_date = fields.Date(string="تاريخ السداد", tracking=True)
    service_id = fields.Many2one('multi.partners.service', string="الخدمة", tracking=True,)
    account_id = fields.Many2one('account.account', string="الحساب", tracking=True)
    move_id = fields.Many2one('account.move', string="قيد السداد", tracking=True, copy=False)
    user_id = fields.Many2one('res.users', string='أنشئ بواسطة', default=lambda self: self.env.user, tracking=True)
    total = fields.Float(compute='_get_total', string='الإجمالي', store=True, tracking=True)
    payment_journal_id = fields.Many2one('account.journal', string='يومية السداد', tracking=True)
    journal_account_id = fields.Many2one('account.account', related="payment_journal_id.default_account_id",
                                          string="الحساب الدائن")
    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     default='bank', string='نوع السداد')
    bank_ref = fields.Char('رقم السند')
    bank_check_no = fields.Char('رقم الشيك')
    bank_ref_seq = fields.Char('Bank Reference Seq')
    cash_ref_seq = fields.Char('cash Reference Seq')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('confirmed', 'تأكيد'),
        ('accountant', 'مختص الحساب'),
        ('verification', 'مسؤول تدقيق المصروفات'),
        ('account_department', 'مدير الادارة المالية '),
        ('finance_monitor', 'المراقب المالي '),
        ('managerial', 'المشرف العام على الشئون الادارية و المالية'),
        ('general_director_approve', 'موافقة الرئيس '),
        ('paid', 'مدفوع'),
        ('cancel', 'تم الإلغاء'),
    ], string="State", default='draft', tracking=True, copy=False, )

    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس')
    # require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
    #                                                   compute='_compute_is_exceed_max_amount')
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)

    #  TODO return back when ejad_erp_hr is upgraded
    # @api.depends('total')
    # def _compute_is_exceed_max_amount(self):
    #     for record in self:
    #         if record.total <= record.company_id.max_amount_require_director_approval:
    #             record.require_general_director_approve = False
    #         else:
    #             record.require_general_director_approve = True

    def action_confirm(self):
        self.state = 'confirmed'

    def check_bank_cash_ref(self):
        if self.payment_type2 == 'bank':
            if not self.bank_ref_seq:
                bank_ref_seq = self.env['ir.sequence'].next_by_code('payment.bank.seq')
                self.bank_ref_seq = bank_ref_seq
                self.bank_ref = bank_ref_seq
            else:
                self.bank_ref = self.bank_ref_seq

        elif self.payment_type2 == 'cash':
            if not self.cash_ref_seq:
                cash_ref_seq = self.env['ir.sequence'].next_by_code('payment.cash.seq')
                self.cash_ref_seq = cash_ref_seq
                self.bank_ref = cash_ref_seq
            else:
                self.bank_ref  = self.cash_ref_seq

        else:
            self.bank_ref = self.bank_ref or False

    def action_accountant(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'accountant'


    def action_verification(self):
        self.state = 'verification'
        self.check_bank_cash_ref()
        for rec in self:
            if (not rec.total) or (rec.total <= 0.0):
                raise UserError(_('يجب مراجعة اليومية و الحساب أو المبلغ الاجمالي'))
        """"
        for rec in self:
            if not rec.journal_id or not rec.account_id or (not rec.total) or (rec.total <= 0.0):
                raise UserError(_('يجب مراجعة اليومية و الحساب أو المبلغ الاجمالي'))
            amount = rec.total or 0.00
            journal_id = rec.journal_id.id
            debit_account_id = rec.account_id.id
            #credit_account_id = line.loan_id.treasury_account_id.id
            lns = []

            for line in rec.line_ids:
                lns.append((0,0,
                    {
                        'name': line.name or '/',
                        'account_id': line.partner_id.property_account_payable_id.id,
                        'journal_id': journal_id,
                        'date': rec.date,
                        'debit': 0.00,
                        'partner_id': line.partner_id.id,
                        'credit': line.amount or 0.0,
                    }
                ))
            debit_vals = {
                    'name': rec.description or rec.service_id.name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': rec.date,
                    'debit': amount,
                    'credit': 0.0,
                }
            lns.append((0, 0, debit_vals))
            vals = {

                'narration': rec.description or rec.service_id.name,
                'ref': rec.name,
                'journal_id': journal_id,
                'date': rec.date,
                'line_ids': lns,
            }
            move = self.env['account.move'].create(vals)
            move.post()
            """

    def action_account_department(self):
        self.check_bank_cash_ref()
        self.state = 'account_department'

    def action_finance_monitor(self):
        self.check_bank_cash_ref()
        self.state = 'finance_monitor'

    def action_managerial(self):
        self.check_bank_cash_ref()
        self.state = 'managerial'

    def button_general_director_approve(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'general_director_approve'

    def action_register_payment(self):
        self.state = 'paid'
        for rec in self:
            if not rec.payment_journal_id or not rec.payment_date:
                raise UserError(_('يجب مراجعة يومية السداد أو تاريخ السداد'))
            amount = rec.total or 0.00
            journal_id = rec.payment_journal_id.id
            credit_account_id = rec.payment_journal_id.default_account_id.id
            #credit_account_id = line.loan_id.treasury_account_id.id
            lns = []
            debit_vals = {
                'name': rec.description or rec.service_id.name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': rec.payment_date,
                'credit': amount,
                'debit': 0.0,
            }
            lns.append((0,0,debit_vals))
            for line in rec.line_ids:
                lns.append((0,0,
                    {
                        'name': (line.name + ' ' + line.partner_id2.name) or '/',
                        'account_id': rec.account_id.id,
                        'journal_id': journal_id,
                        'date': rec.payment_date,
                        'credit': 0.00,
                        #'partner_id': line.partner_id.id,
                        'debit': line.amount or 0.0,
                    }
                ))
            vals = {

                'narration': rec.description or rec.service_id.name,
                'ref': rec.name,
                'journal_id': journal_id,
                'date': rec.payment_date,
                'line_ids': lns,
            }
            move = self.env['account.move'].create(vals)
            move.post()
            rec.move_id = move.id

    def action_cancel(self):
        self.state = 'cancel'

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError('عذرا، لايمكن المسح الا في حالة المسودة')
        return super(AccountInvoiceMultiPartners, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('journal_id', False):
            vals['name'] = (self.env['account.journal'].browse(vals['journal_id'])).sequence_id.next_by_id()
        return super(AccountInvoiceMultiPartners, self).create(vals)

class PartnerInvoiceMulti(models.Model):
    _name = 'partner.invoice.multi'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='الاسم', tracking=True)
    other_info = fields.Text(string='معلومات أخرى', tracking=True)
    active = fields.Boolean(default=True, string="نشط", tracking=True)
    bank_account_id = fields.Many2one('res.partner.bank', string="الحساب البنكي")
    supplier_id = fields.Char('رقم صاحب الاستحقاق')

