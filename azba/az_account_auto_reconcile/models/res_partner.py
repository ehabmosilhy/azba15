# -*- coding: utf-8 -*-
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "res.partner"
    last_reconcile_date = fields.Datetime(string="Last Reconcile Date")

    def auto_reconcile(self):
        try:
            partner = self
            due = int(partner.total_due)  # Assuming total_due is a field that exists and is an integer
            un_reconciled_lines = partner.unreconciled_aml_ids.filtered(
                lambda l: l.company_id == self.env.company).sorted(key='id', reverse=True)
            excluded = []
            for line in un_reconciled_lines:
                amount = line.amount_residual_currency if line.currency_id else line.amount_residual
                if amount > 0 and due > 0:
                    due -= amount
                    if due >= 0:
                        excluded.append(line.id)

            lines_to_reconcile = un_reconciled_lines.filtered(lambda l: l.id not in excluded)
            if len(lines_to_reconcile.ids) >= 2:
                data = [{'id': None, 'type': None, 'mv_line_ids': lines_to_reconcile.ids, 'new_mv_line_dicts': []}]
                self.env['account.reconciliation.widget'].sudo().process_move_lines(data)
        except Exception as e:
            _logger.critical(f"Critical error during auto reconciliation for customer {self.name}: {str(e)}")
            return (self.name, "Reconciliation failed due to an internal error.")

    def auto_reconcile_all(self):
        MIN_CUSTOMER_RANK = 1
        customers = self.env['res.partner'].search([
            ('customer_rank', '>', MIN_CUSTOMER_RANK),
            ('id', 'in', self.env['account.move'].search([]).mapped('partner_id').ids)
        ])
        failed_customers = []
        for customer in customers:
            result = customer.auto_reconcile()
            if result:
                failed_customers.append(result)

        if failed_customers:
            _logger.critical(f"Failed Customers: {failed_customers}")
            notification_ids = [(0, 0, {'res_partner_id': 3, 'notification_type': 'inbox'})]
            self.message_post(
                body='Failed Customers: ' + str(failed_customers),
                subject='Auto Reconciliation Failures',
                message_type='notification',
                subtype_xmlid='mail.mt_note',
                notification_ids=notification_ids
            )


