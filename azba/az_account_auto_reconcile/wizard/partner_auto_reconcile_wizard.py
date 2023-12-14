from odoo import models, fields, api

class PartnerAutoReconcileWizard(models.TransientModel):
    _name = 'partner.auto.reconcile.wizard'
    _description = 'Partner Auto Reconcile Wizard'

    partner_ids = fields.Many2many('res.partner', string="Partners")

    def execute_auto_reconcile(self):
        failed_customers = []
        for partner in self.partner_ids:
            try:
                _error=partner.auto_reconcile()
                if _error:
                    failed_customers.append(_error)
                else:
                    partner.last_reconcile_date = fields.Datetime.now()
            except Exception as e:
                mail_values = {
                    'author_id': self.env.user.partner_id.id,
                    'email_from': (
                            self.company_id.partner_id.email_formatted
                            or self.env.user.email_formatted
                            or self.env.ref('base.user_root').email_formatted
                    ),
                    'email_to': [ 3],
                    'body_html': "Failed Customers in Auto Reconcile" + str(failed_customers),
                    'subject': "Auto Reconcile",
                }
                self.env['mail.mail'].sudo().create(mail_values)

