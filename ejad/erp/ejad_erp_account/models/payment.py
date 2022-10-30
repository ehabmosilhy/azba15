# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from odoo.tools import pycompat
from lxml import etree
from odoo.exceptions import UserError, ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    # @api.onchange('amount', 'currency_id')
    # def _onchange_amount(self):
    #     jrnl_filters = self._compute_journal_domain_and_types()
    #     journal_types = jrnl_filters['journal_types']
    #     domain_on_types = [('type', 'in', list(journal_types))]
    #
    #     journal_domain = jrnl_filters['domain'] + domain_on_types
    #     default_journal_id = self.env.context.get('default_journal_id')
    #     if not default_journal_id:
    #         if self.journal_id.type not in journal_types:
    #             # self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)
    #             self.journal_id = False
    #     else:
    #         journal_domain = journal_domain.append(('id', '=', default_journal_id))
    #
    #     return {'domain': {'journal_id': journal_domain}}

    state = fields.Selection([
        ('draft', 'draft'),
        ('accounting', 'Accountant'),
        ('verfication', 'Expense Auditor'),
        ('account_department', 'Financial Manager'),
        ('finance_verfifcation', 'Financial Monitor'),
        ('manager', 'موافقة مدير الشؤون المالية والإدارية'),
        ('general_director_approve', 'موافقة الرئيس '),
        ('posted', 'Confirmed'),
        ('pending_delivery', 'بانتظار التسليم'),
        ('delivered', 'تم التسليم'),
        ('sent', 'Sent'),
        ('reconciled', 'Reconciled'),
        ('refuse', 'Refuse'),
        ('cancelled', 'Cancel'),
    ], string="State", default='draft', tracking=True, copy=False, )

    note = fields.Char('Notes')
    bank_ref = fields.Char('رقم السند')
    bank_ref_seq = fields.Char('Bank Reference Seq')
    cash_ref_seq = fields.Char('cash Reference Seq')
    bank_check_no = fields.Char('رقم الشيك')
    cancel_reasons = fields.Text('سبب الإلغاء')
    reversed_move = fields.Char('Reversal Entry')
    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     default='bank', string='نوع السداد')
    payment_type_customer = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)'),
                                              ('cash_deposit', 'إيداع نقدي')],
                                     default='bank', string='نوع السداد')
    report = fields.Char('البيان')
    # require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
    #                                                   compute='_compute_is_exceed_max_amount')
    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس')
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)
    create_uid = fields.Many2one('res.users',string="الموظف المسؤول")
    name = fields.Char(default=_("جديد"))

    #  TODO return back when ejad_erp_hr is upgraded
    # @api.depends('amount')
    # def _compute_is_exceed_max_amount(self):
    #     for record in self:
    #         if record.amount <= record.company_id.max_amount_require_director_approval:
    #             record.require_general_director_approve = False
    #         else:
    #             record.require_general_director_approve = True

    @api.model
    def create(self, vals):
        # Use the right sequence to set the name
        if vals['payment_type'] == 'transfer':
            sequence_code = 'account.payment.transfer'
        else:
            if vals['partner_type'] == 'customer':
                if vals['payment_type'] == 'inbound':
                    sequence_code = 'account.payment.customer.invoice'
                if vals['payment_type'] == 'outbound':
                    sequence_code = 'account.payment.customer.refund'
            if vals['partner_type'] == 'supplier':
                if vals['payment_type'] == 'inbound':
                    sequence_code = 'account.payment.supplier.refund'
                if vals['payment_type'] == 'outbound':
                    sequence_code = 'account.payment.supplier.invoice'
        vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=vals.get('payment_date')).next_by_code(
            sequence_code)
        if not vals['name'] and vals['payment_type'] != 'transfer':
            raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))
        if vals.get('payment_type2') == 'bank' and (vals.get('payment_type') == 'outbound'):
            if not self.bank_ref_seq:
                bank_ref_seq = self.env['ir.sequence'].next_by_code('payment.bank.seq')
                vals['bank_ref_seq'] = bank_ref_seq
                vals['bank_ref'] = bank_ref_seq
            else:
                vals['bank_ref'] = self.bank_ref_seq

        elif vals.get('payment_type2') == 'cash' and (vals.get('payment_type') == 'outbound'):
            if not self.cash_ref_seq:
                cash_ref_seq = self.env['ir.sequence'].next_by_code('payment.cash.seq')
                vals['cash_ref_seq'] = cash_ref_seq
                vals['bank_ref'] = cash_ref_seq
            else:
                vals['bank_ref'] = self.cash_ref_seq

        else:
            vals['bank_ref'] = vals.get('bank_ref') or False
        result = super(AccountPayment, self).create(vals)
        return result

    def write(self, values):
        for record in self:

            if values.get('payment_type2') == 'bank' and (record.payment_type == 'outbound'):
                if not record.bank_ref_seq:
                    bank_ref_seq = record.env['ir.sequence'].next_by_code('payment.bank.seq')
                    values['bank_ref_seq'] = bank_ref_seq
                    values['bank_ref'] = bank_ref_seq
                else:
                    values['bank_ref'] = record.bank_ref_seq

            elif values.get('payment_type2') == 'cash' and (record.payment_type == 'outbound'):
                if not record.cash_ref_seq:
                    cash_ref_seq = record.env['ir.sequence'].next_by_code('payment.cash.seq')
                    values['cash_ref_seq'] = cash_ref_seq
                    values['bank_ref'] = cash_ref_seq
                else:
                    values['bank_ref'] = record.cash_ref_seq

            #elif record.payment_type == 'outbound':
            #    values['bank_ref'] = values.get('bank_ref') or False

            return super(AccountPayment, record).write(values)

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconciliable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconciliable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        for rec in self:
            rec.payment_type == 'outbound'
            if any(inv.state != 'open' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            move = rec._create_payment_entry(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(
                    lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()
            if rec.payment_type == 'outbound':
                rec.write({'state': 'verfication', 'move_name': move.name})
            else:
                rec.write({'state': 'posted', 'move_name': move.name})
        return True
    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:

            if rec.state != 'draft' and rec.payment_type == 'inbound':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id)\
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids')\
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                    .reconcile()

        return True

    def action_submit(self):
        self.write({'state': 'accounting'})

    def action_accounting_approve(self):
        self.write({'state': 'verfication'})

    def post_outbound(self):
        self.write({'state': 'account_department'})

    # def action_verification_approve(self):
    #     self.write({'state': 'account_department'})

    def action_department_approve(self):
        self.write({'state': 'finance_verfifcation'})

    def action_finance_verfifcation_approve(self):
        self.write({'state': 'manager'})

    def action_manager_approve(self):
        if not self.require_general_director_approve:
            self.post()
            self.write({'state': 'pending_delivery'})
        else:
            self.write({'state': 'general_director_approve'})

    def button_general_director_approve(self):
        for record in self:
            if record.require_general_director_approve:
                self.post()
            record.state = 'pending_delivery'

    def action_delivered(self):
        self.write({'state': 'delivered'})

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(AccountPayment, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                             submenu=submenu)
        doc = etree.fromstring(result['arch'])

        if view_type == 'form':
            if self._context.get('default_payment_type'):
                payment = self._context.get('default_payment_type')

                if doc.xpath("//field[@name='state']"):

                    for state_node in doc.xpath("//field[@name='state']"):
                        # state_node = doc.xpath("//field[@name='state']")
                        if payment == 'outbound':
                            replacement_xml = """ <field name="state" widget="statusbar"
                           statusbar_visible="draft,accounting,verfication,account_department,finance_verfifcation,manager,pending_delivery,delivered"/>
                            """
                            new_state_node = etree.fromstring(replacement_xml)
                            state_node.getparent().replace(state_node, new_state_node)

        result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

    def _prepare_payment_moves(self):
        ''' Prepare the creation of journal entries (account.move) by creating a list of python dictionary to be passed
        to the 'create' method.

        Example 1: outbound with write-off:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |   900.0   |
        RECEIVABLE          |           |   1000.0
        WRITE-OFF ACCOUNT   |   100.0   |

        Example 2: internal transfer from BANK to CASH:

        Account             | Debit     | Credit
        ---------------------------------------------------------
        BANK                |           |   1000.0
        TRANSFER            |   1000.0  |
        CASH                |   1000.0  |
        TRANSFER            |           |   1000.0

        :return: A list of Python dictionary to be passed to env['account.move'].create.
        '''
        all_move_vals = []
        for payment in self:
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                liquidity_line_account = payment.journal_id.default_account_id
            else:
                counterpart_amount = -payment.amount
                liquidity_line_account = payment.journal_id.default_account_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id, payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id, payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                if payment.journal_id.currency_id == company_currency:
                    # Single-currency
                    liquidity_line_currency_id = False
                else:
                    liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====

            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'narration': self.note,
                'bank_ref': self.bank_ref,
                'bank_check_no': self.bank_check_no,
                'payment_type2': self.payment_type2,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.destination_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':
                journal = payment.destination_journal_id

                # Manage custom currency on journal for liquidity line.
                if journal.currency_id and payment.currency_id != journal.currency_id:
                    # Custom currency on journal.
                    liquidity_line_currency_id = journal.currency_id.id
                    transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id, payment.payment_date)
                else:
                    # Use the payment currency.
                    liquidity_line_currency_id = currency_id
                    transfer_amount = counterpart_amount

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'narration': self.note,
                    'bank_ref': self.bank_ref,
                    'bank_check_no': self.bank_check_no,
                    'payment_type2': self.payment_type2,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_journal_id.default_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)
        return all_move_vals

    # def _get_move_vals(self, journal=None):
    #     """ Return dict to create the payment move
    #     """
    #     journal = journal or self.journal_id
    #     if not journal.sequence_id:
    #         raise UserError(_('Configuration Error !'),
    #                         _('The journal %s does not have a sequence, please specify one.') % journal.name)
    #     if not journal.sequence_id.active:
    #         raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
    #     name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
    #     return {
    #         'name': name,
    #         'date': self.payment_date,
    #         'ref': self.communication or '',
    #         'company_id': self.company_id.id,
    #         'journal_id': journal.id,
    #         'narration': self.note,
    #         'bank_ref': self.bank_ref,
    #         'bank_check_no': self.bank_check_no,
    #         'payment_type2': self.payment_type2,
    #     }

    # def _prepare_payment_vals(self, invoices):
    #     '''Create the payment values.
    #
    #     :param invoices: The invoices that should have the same commercial partner and the same type.
    #     :return: The payment values as a dictionary.
    #     '''
    #     amount = self._compute_payment_amount(invoices) if self.multi else self.amount
    #     payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
    #     return {
    #         'journal_id': self.journal_id.id,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': self.communication,
    #         'note': self.note,
    #         'bank_ref': self.bank_ref,
    #         'payment_type_customer': self.payment_type_customer,
    #         'bank_check_no': self.bank_check_no,
    #         'payment_type2': self.payment_type2,
    #         'invoice_ids': [(6, 0, invoices.ids)],
    #         'payment_type': payment_type,
    #         'amount': abs(amount),
    #         'currency_id': self.currency_id.id,
    #         'partner_id': invoices[0].commercial_partner_id.id,
    #         'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
    #     }


    # def _create_payment_entry(self, amount):
    #     """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
    #         Return the journal entry.
    #     """
    #     aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
    #     invoice_currency = False
    #     if self.invoice_ids and all([x.currency_id == self.invoice_ids[0].currency_id for x in self.invoice_ids]):
    #         #if all the invoices selected share the same currency, record the paiement in that currency too
    #         invoice_currency = self.invoice_ids[0].currency_id
    #     debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
    #     move = self.env['account.move'].create(self._get_move_vals())
    #
    #     #Write line corresponding to invoice payment
    #     counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
    #     counterpart_aml_dict.update(self._get_counterpart_move_line_vals(self.invoice_ids))
    #     counterpart_aml_dict.update({'currency_id': currency_id})
    #     counterpart_aml = aml_obj.create(counterpart_aml_dict)
    #
    #     #Reconcile with the invoices
    #     if self.payment_difference_handling == 'reconcile' and self.payment_difference:
    #         writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
    #         amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id, invoice_currency)[2:]
    #         # the writeoff debit and credit must be computed from the invoice residual in company currency
    #         # minus the payment amount in company currency, and not from the payment difference in the payment currency
    #         # to avoid loss of precision during the currency rate computations. See revision 20935462a0cabeb45480ce70114ff2f4e91eaf79 for a detailed example.
    #         total_residual_company_signed = sum(invoice.residual_company_signed for invoice in self.invoice_ids)
    #         total_payment_company_signed = self.currency_id.with_context(date=self.payment_date).compute(self.amount, self.company_id.currency_id)
    #         if self.invoice_ids[0].type in ['in_invoice', 'out_refund']:
    #             amount_wo = total_payment_company_signed - total_residual_company_signed
    #         else:
    #             amount_wo = total_residual_company_signed - total_payment_company_signed
    #         # Align the sign of the secondary currency writeoff amount with the sign of the writeoff
    #         # amount in the company currency
    #         if amount_wo > 0:
    #             debit_wo = amount_wo
    #             credit_wo = 0.0
    #             amount_currency_wo = abs(amount_currency_wo)
    #         else:
    #             debit_wo = 0.0
    #             credit_wo = -amount_wo
    #             amount_currency_wo = -abs(amount_currency_wo)
    #         writeoff_line['name'] = self.writeoff_label
    #         writeoff_line['account_id'] = self.writeoff_account_id.id
    #         writeoff_line['debit'] = debit_wo
    #         writeoff_line['credit'] = credit_wo
    #         writeoff_line['amount_currency'] = amount_currency_wo
    #         writeoff_line['currency_id'] = currency_id
    #         writeoff_line = aml_obj.create(writeoff_line)
    #         if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
    #             counterpart_aml['debit'] += credit_wo - debit_wo
    #         if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
    #             counterpart_aml['credit'] += debit_wo - credit_wo
    #         counterpart_aml['amount_currency'] -= amount_currency_wo
    #
    #     #Write counterpart lines
    #     if not self.currency_id.is_zero(self.amount):
    #         if not self.currency_id != self.company_id.currency_id:
    #             amount_currency = 0
    #         liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
    #         liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
    #         aml_obj.create(liquidity_aml_dict)
    #
    #     #validate the payment
    #     move.post()
    #
    #     #reconcile the invoice receivable/payable line(s) with the payment
    #     self.invoice_ids.register_payment(counterpart_aml)
    #
    #     return move

    # def _get_move_vals(self, journal=None):
    #     """ Return dict to create the payment move
    #     """
    #     journal = journal or self.journal_id
    #     if not journal.sequence_id:
    #         raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
    #     if not journal.sequence_id.active:
    #         raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
    #     name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
    #     return {
    #         'name': name,
    #         'date': self.payment_date,
    #         'ref': self.communication or '',
    #         'company_id': self.company_id.id,
    #         'report':self.note,
    #         'journal_id': journal.id,
    #     }
# class nuass_account_register_payments(models.TransientModel):
    # _inherit = 'account.register.payments'
    #
    # note = fields.Char('الملاحظات')
    #
    # def _prepare_payment_vals(self, invoices):
    #     '''Create the payment values.
    #
    #     :param invoices: The invoices that should have the same commercial partner and the same type.
    #     :return: The payment values as a dictionary.
    #     '''
    #     amount = self._compute_payment_amount(invoices) if self.multi else self.amount
    #     payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
    #     return {
    #         'journal_id': self.journal_id.id,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': self.communication,
    #         'invoice_ids': [(6, 0, invoices.ids)],
    #         'payment_type': payment_type,
    #         'amount': abs(amount),
    #         'note':self.note,
    #         'currency_id': self.currency_id.id,
    #         'partner_id': invoices[0].commercial_partner_id.id,
    #         'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
    #     }
    #
    # def create_payments(self):
    #     '''Create payments according to the invoices.
    #     Having invoices with different commercial_partner_id or different type (Vendor bills with customer invoices)
    #     leads to multiple payments.
    #     In case of all the invoices are related to the same commercial_partner_id and have the same type,
    #     only one payment will be created.
    #
    #     :return: The ir.actions.act_window to show created payments.
    #     '''
    #     Payment = self.env['account.payment']
    #     payments = Payment
    #     for payment_vals in self.get_payments_vals():
    #         payment_vals.update({'payment_type2': 'bank'})
    #         payments += Payment.create(payment_vals)
    #     payments.post()
    #     for p in payments:
    #         p.write({'bank_ref': p.bank_ref_seq})
    #     return {
    #         'name': _('Payments'),
    #         'domain': [('id', 'in', payments.ids), ('state', '=', 'verfication')],
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'res_model': 'account.payment',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #     }
