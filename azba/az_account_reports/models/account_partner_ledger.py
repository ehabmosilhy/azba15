# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, _lt, fields
from odoo.tools.misc import format_date
from datetime import timedelta

from collections import defaultdict


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger"

    def _get_columns_name(self, options):
        columns = [
            {},
            # {'name': _('JRNL')},
            # {'name': _('Account')},
            {'name': _('Ref')},
            # {'name': _('Due Date'), 'class': 'date'},
            # {'name': _('Matching Number')},
            # {'name': _('Initial Balance'), 'class': 'number'},
            {'name': _('Debit'), 'class': 'number'},
            {'name': _('Credit'), 'class': 'number'}]

        if self.user_has_groups('base.group_multi_currency'):
            columns.append({'name': _('Amount Currency'), 'class': 'number'})

        columns.append({'name': _('Balance'), 'class': 'number'})

        return columns


    @api.model
    def _get_lines(self, options, line_id=None):
        offset = int(options.get('lines_offset', 0))
        remaining = int(options.get('lines_remaining', 0))
        balance_progress = float(options.get('lines_progress', 0))

        if offset > 0:
            # Case a line is expanded using the load more.
            lml=self._load_more_lines(options, line_id, offset, remaining, balance_progress)
            return lml
        else:
            # Case the whole report is loaded or a line is expanded for the first time.
            pll = self._get_partner_ledger_lines(options, line_id=line_id)



            '''
            To Remove

                options['headers'][0][2] {'name': 'Account'}
                options['headers'][0][5] {'name': 'Matching Number'}
                
                
                pll[n]['columns'][1] 'Account'
                pll[n]['columns'][4] 'Matching Number'
                
            To Change:
                pll[0]['colspan'] -> Reduce by 2
                pll[-1]['colspan'] -> Reduce by 2

            '''
            if options.get('headers'):
                options['headers'][0].pop(1)    # Jrnl
                options['headers'][0].pop(1)    # Account
                options['headers'][0].pop(2)    # Due Date
                options['headers'][0].pop(2)    # Matching Number
                options['headers'][0].pop(2)    # Due Initial Balance


                # pll[0]['colspan']-=2
                # pll[-1]['colspan']-=2
                for i in range(len(pll)):
                    print (i)
                    if pll[i].get('colspan'):
                        pll[i]['columns'].pop(0)  # Initial Balance
                        pll[i]['colspan']-=4
                    else:
                        pll[i]['columns'].pop(0)
                        pll[i]['columns'].pop(0)
                        pll[i]['columns'].pop(1)
                        pll[i]['columns'].pop(1)
                        pll[i]['columns'].pop(1)


            return pll


    @api.model
    def _get_report_name(self):
        return _('Partner Ledger كشف حساب')
