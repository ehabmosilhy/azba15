# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "res.partner"

    def auto_reconcile(self):
        try:
            partner = self
            # Get the Due balance of the partner and exclude the most recent invoice from reconciliation
            due = int(partner.total_due)  # ignore the change
            un_reconciled_lines = partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company).sorted(
                key='id', reverse=True)
            indi = 0

            # Loop until the recent invoices' sum is bigger than the amount due, the due gets smaller in every iteration
            # The amount could be negative
            excluded = []
            while due > 0 and indi < len(un_reconciled_lines):
                line = un_reconciled_lines[indi]
                amount = line.amount_residual_currency if line.currency_id else line.amount_residual
                if amount > 0:
                    due -= amount
                    if due >= amount:
                        excluded.append(line.id)
                indi += 1
            # the pointer indi is now at the last recent invoice, we will reconcile the older invoices
            lines_to_reconcile = un_reconciled_lines.filtered(lambda l: l.id not in excluded)
            if len(lines_to_reconcile.ids) >= 2:
                data = [{'id': None, 'type': None, 'mv_line_ids': lines_to_reconcile.ids, 'new_mv_line_dicts': []}]
                self.env['account.reconciliation.widget'].sudo().process_move_lines(data)
        except Exception as e:
            _logger.critical(f"::::>>>>> Customer {self.name} , Error: {e}")

    def auto_reconcile_all(self):
        customers = self.env['res.partner'].search([('customer_rank', '>', 0),
                                                    ('id', 'in',
                                                     self.env['account.move'].search([]).mapped('partner_id').ids)])
        i=0
        for customer in customers:
            try:
                # print (f"Now working on {customer.name}")
                i+=1
                customer.auto_reconcile()
                _logger.info(f"::::::::  Customer {i}/{len(customers)}  Done::: {customer.name}")

            except Exception as e:
                _logger.critical(f"::::>>>>> Customer {customer.name} , Error: {e}")
                print(f"::::>>>>> Customer {customer.name} , Error: {e}")
