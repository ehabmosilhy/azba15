# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    benefit_account_id = fields.Many2one("account.account", string="الدليل المحاسبي", required=False)

    journal_bank_id = fields.Many2one('account.journal', string='Payment Method bank', required=False,
                                      domain=[('type', 'in', ('bank', 'cash'))])
    journal_cash_id = fields.Many2one('account.journal', string='Payment Method Cash', required=False,
                                      domain=[('type', 'in', ('bank', 'cash'))])
    emp_account_id = fields.Many2one('account.account', string="Employees Accounts ")
    journal_total_id = fields.Many2one('account.journal', string='Journal Type ID', required=False, )

    advance_emp_account_id = fields.Many2one('account.account', string="Advance Employees Accounts ")
    advance_journal_total_id = fields.Many2one('account.journal', string='Advance Journal Type', required=False,)

    max_amount_require_director_approval = fields.Float(string="مبلغ حد موافقة الرئيس", default=100000)


# adding CoA setting to end of service from hr settingc
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    benefit_account_id = fields.Many2one("account.account", string="الدليل المحاسبي",
                                         related='company_id.benefit_account_id', readonly=False)
    journal_bank_id = fields.Many2one('account.journal', string='Payment Method bank',
                                      related='company_id.journal_bank_id', readonly=False,
                                      domain=[('type', 'in', ('bank', 'cash'))])
    journal_cash_id = fields.Many2one('account.journal', string='Payment Method Cash', readonly=False,
                                      related='company_id.journal_cash_id',
                                      domain=[('type', 'in', ('bank', 'cash'))])
    emp_account_id = fields.Many2one('account.account', string="Employees Accounts ",
                                     related='company_id.emp_account_id', readonly=False)
    journal_total_id = fields.Many2one('account.journal', string='Journal Type', related='company_id.journal_total_id',
                                       readonly=False)
    max_amount_require_director_approval = fields.Float(string="مبلغ حد موافقة الرئيس",
                                                        related='company_id.max_amount_require_director_approval',
                                                        readonly=False)
    advance_emp_account_id = fields.Many2one('account.account', string="Advance Employees Accounts ",
                                             related='company_id.advance_emp_account_id', readonly=False, )
    advance_journal_total_id = fields.Many2one('account.journal', string='Advance Journal Type',
                                               related='company_id.advance_journal_total_id', readonly=False)
