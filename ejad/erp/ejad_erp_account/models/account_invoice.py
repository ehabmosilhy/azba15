# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_is_zero, float_compare, pycompat
from datetime import datetime


class AccountInvoice(models.Model):
    _inherit = "account.move"

    # @api.onchange('payment_term_id', 'date_invoice')
    # def _onchange_payment_term_date_invoice(self):
    #     date_invoice = self.date_invoice
    #     if not date_invoice:
    #         date_invoice = fields.Date.context_today(self)
    #     if self.payment_term_id:
    #         pterm = self.payment_term_id
    #         pterm_list = \
    #         pterm.with_context(currency_id=self.company_id.currency_id.id).compute(value=1, date_ref=date_invoice)[0]
    #         if max(line[0] for line in pterm_list):
    #             self.date_due = max(line[0] for line in pterm_list)
    #     elif self.date_due and (date_invoice > self.date_due):
    #         self.date_due = date_invoice

    # @api.onchange('partner_id', 'company_id')
    # def _onchange_partner_id(self):
    #     account_id = False
    #     payment_term_id = False
    #     fiscal_position = False
    #     bank_id = False
    #     warning = {}
    #     domain = {}
    #     company_id = self.company_id.id
    #     p = self.partner_id if not company_id else self.partner_id.with_context(force_company=company_id)
    #     type = self.type
    #     if p:
    #         rec_account = p.property_account_receivable_id
    #         pay_account = p.property_account_payable_id
    #         if not rec_account and not pay_account:
    #             action = self.env.ref('account.action_account_config')
    #             msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
    #             raise RedirectWarning(msg, action.id, _('Go to the configuration panel'))
    #
    #         if type in ('out_invoice', 'out_refund'):
    #             account_id = rec_account.id
    #             payment_term_id = p.property_payment_term_id.id
    #         else:
    #             account_id = pay_account.id
    #             payment_term_id = p.property_supplier_payment_term_id.id
    #
    #         delivery_partner_id = self.get_delivery_partner_id()
    #         fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id, delivery_id=delivery_partner_id)
    #
    #         # If partner has no warning, check its company
    #         if p.invoice_warn == 'no-message' and p.parent_id:
    #             p = p.parent_id
    #         if p.invoice_warn != 'no-message':
    #             # Block if partner only has warning but parent company is blocked
    #             if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
    #                 p = p.parent_id
    #             warning = {
    #                 'title': _("Warning for %s") % p.name,
    #                 'message': p.invoice_warn_msg
    #                 }
    #             if p.invoice_warn == 'block':
    #                 self.partner_id = False
    #
    #     self.account_id = account_id
    #     self.payment_term_id = payment_term_id
    #     #self.date_due = False
    #     self.fiscal_position_id = fiscal_position
    #
    #     if type in ('in_invoice', 'out_refund'):
    #         bank_ids = p.commercial_partner_id.bank_ids
    #         bank_id = bank_ids[0].id if bank_ids else False
    #         self.partner_bank_id = bank_id
    #         domain = {'partner_bank_id': [('id', 'in', bank_ids.ids)]}
    #
    #     res = {}
    #     if warning:
    #         res['warning'] = warning
    #     if domain:
    #         res['domain'] = domain
    #     return res

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('accountant_approval', 'Accountant Approval'),
    #     ('open', 'Confirmed'),
    #     ('paid', 'Paid'),
    #     ('cancel', 'Cancelled'),
    # ], string='Status', index=True, readonly=True, default='draft',
    #     tracking=True, copy=False,
    #     help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
    #          " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
    #          " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
    #          " * The 'Cancelled' status is used when user cancel invoice.")
    report = fields.Char('البيان')
    invoice_report_html = fields.Html('خطاب المطالبة المالية', readonly=True)
    report_generated = fields.Boolean('Is Report Generated')
    refund_reason = fields.Char('سبب استيراد الرسوم الدراسية')
    is_pay_by_custody = fields.Boolean(string="هل دفع بواسطة عهدة؟",default=False,states={'draft': [('readonly', False)]})
    custody_partner_id = fields.Many2one('res.partner', string='المورد', change_default=True,
                                readonly=True, states={'draft': [('readonly', False)]},
                                 tracking=True)
    partner_id = fields.Many2one( readonly=True, states={'draft': [('readonly', False)], 'accountant_approval': [('readonly', False)]},
                                 tracking=True)
    invoice_date_due = fields.Date(default=fields.Date.context_today)
    invoice_date = fields.Date(default=fields.Date.context_today)

    out_invoice_not_exceed_limit_state = fields.Selection([
        ('accountant', 'أخصائي مالي'),
        ('procurements_unit', 'مسؤول المشتريات'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('accepted', 'مقبول'),
        ('refused', 'مرفوض')
    ], 'Status', index=True, default="accountant", readonly=True, copy=False, tracking=True)

    out_invoice_exceed_limit_state = fields.Selection([
        ('executive_authority', 'الجهة المنفذة'),
        ('departments_manager', 'مدراء الوحدات الإدارية'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('accepted', 'مقبول'),
        ('refused', 'مرفوض')
    ], 'Status', index=True, default="executive_authority", readonly=True, copy=False, tracking=True)

    is_total_amount_exceed_limit = fields.Boolean(compute="_compute_is_total_amount_exceed_limit", store=True,)

    @api.depends('amount_total')
    def _compute_is_total_amount_exceed_limit(self):
        for rec in self:
            if rec.amount_total >= 100000:
                rec.is_total_amount_exceed_limit = True
            else:
                rec.is_total_amount_exceed_limit = False

    def action_accountant(self):
        for rec in self:
            if not rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_not_exceed_limit_state': 'procurements_unit'})

    def action_direct_purchase_procurements_unit(self):
        for rec in self:
            if not rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_not_exceed_limit_state': 'support_services_manager'})

    def action_executive_authority(self):
        for rec in self:
            if rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_exceed_limit_state': 'departments_manager'})

    def action_departments_manager(self):
        for rec in self:
            if rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_exceed_limit_state': 'support_services_manager'})

    def action_support_services_manager(self):
        for rec in self:
            if not rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_not_exceed_limit_state': 'office_leader'})
            elif rec.is_total_amount_exceed_limit:
                rec.write({'out_invoice_exceed_limit_state': 'office_leader'})

    def action_office_leader(self):
        if self.mapped('line_ids.payment_id') and any(
                post_at == 'bank_rec' for post_at in self.mapped('journal_id.post_at')):
            raise UserError(_(
                "A payment journal entry generated in a journal configured to post entries only when payments are reconciled with a bank statement cannot be manually posted. Those will be posted automatically after performing the bank reconciliation."))
        self.post()
        if not self.is_total_amount_exceed_limit:
            self.write({'out_invoice_not_exceed_limit_state': 'accepted'})
        elif self.is_total_amount_exceed_limit:
            self.write({'out_invoice_exceed_limit_state': 'accepted'})

    @api.onchange('is_pay_by_custody')
    def set_partnar_custody(self):
        for inv in self:
            if inv.is_pay_by_custody == True and inv.type == 'in_invoice' and inv.state in ['draft', 'accountant_approval']:
                inv.custody_partner_id = inv.partner_id.id
                inv.partner_id = self.env.user.partner_id.id
            if inv.is_pay_by_custody == False and inv.custody_partner_id and inv.type == 'in_invoice' and inv.state in ['draft', 'accountant_approval']:
                inv.partnet_id = inv.custody_partner_id.id
                inv.custody_partner_id = False


    def action_invoice_accountant_approval(self):
        self.state = 'accountant_approval'

    # def action_invoice_open(self):
    #     self.state = 'draft'
    #     # lots of duplicate calls to action_invoice_open, so we remove those already open
    #     to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
    #     if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
    #         raise UserError(_("Invoice must be in draft state in order to validate it."))
    #     if to_open_invoices.filtered(
    #             lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
    #         raise UserError(_(
    #             "You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
    #     to_open_invoices.action_date_assign()
    #     to_open_invoices.action_move_create()
    #     return to_open_invoices.invoice_validate()

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
        self.invoice_report_html = partner_id.nomination_report_recipient + self.company_id.inv_report_header \
            .replace('()', partner_id.nomination_no or '', 1) \
            .replace('()', str(datetime.strptime(partner_id.nomination_date, '%Y-%m-%d').strftime('%d-%m-%Y')) or '', 1) + '''
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
