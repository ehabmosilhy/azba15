from odoo import api, fields, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def write(self, values):
        payments = super(AccountPayment, self).write(values)
        if self.state == 'posted':
            self.partner_id.auto_reconcile()
        return payments
