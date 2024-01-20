# -*- coding: utf-8 -*-

from odoo import models, api


class ledgerReportTemplate(models.AbstractModel):
    _name = 'report.az_account_reports.ledger_report_template'
    _description = 'Ledger Report Template'

    def get_ledger_detail(self, data):
        # Retrieve date range for filtering account moves
        company_id = data.get('company_id')
        start_date = data.get('date_from')
        end_date = data.get('date_to')

        # Depending on the report type, construct the account IDs SQL
        account_ids = data.get('account_ids')[0] if  data.get('account_ids') else None
        account_ids_clause = ""
        params = [company_id]

        if account_ids:
            account_move_sql = f"""
                SELECT
                    aa.name AS account_name,
                    p.code,
                    p.name AS name,
                    SUM(aml.debit) AS period_debit,
                    SUM(aml.credit) AS period_credit,
                    COALESCE(pd.total_debit_before, 0) AS before_period_debit,
                    COALESCE(pd.total_credit_before, 0) AS before_period_credit,
                    aml.account_id,
                    0 as final_debit,
                    0 as final_credit
                FROM
                    account_move_line aml
                    LEFT JOIN account_account aa ON aml.account_id = aa.id
                    LEFT JOIN res_partner p ON aml.partner_id = p.id
                    LEFT JOIN (
                        SELECT
                            partner_id,
                            account_id,
                            SUM(debit) AS total_debit_before,
                            SUM(credit) AS total_credit_before
                        FROM
                            account_move_line
                        WHERE
                            date < '{start_date}' 
                            AND (display_type NOT IN ('line_section', 'line_note') OR display_type IS NULL)
                            AND parent_state = 'posted'
                            AND (company_id IS NULL OR company_id ={company_id})
                        GROUP BY
                            partner_id, account_id
                    ) pd ON aml.partner_id = pd.partner_id AND aml.account_id = pd.account_id
                WHERE
                    (aml.display_type NOT IN ('line_section', 'line_note') OR aml.display_type IS NULL)
                    AND aml.parent_state = 'posted'
                    AND (aml.company_id IS NULL OR aml.company_id ={company_id})
                    AND aml.date BETWEEN '{start_date}' AND '{end_date}'
                    and aml.account_id = {account_ids}
                GROUP BY
                    aml.account_id, aa.name, p.id, p.name, pd.total_debit_before, pd.total_credit_before
                ORDER BY
                    aa.name, p.name;
            """


        # Construct the SQL to fetch all relevant account moves
        else:
            account_move_sql = f"""
                SELECT
                aa.name,
                aa.code,
                    min(aml.id) AS id,
                    count(aml.id) AS account_id_count,
                    min(aml.date) AS date,
                    sum(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.debit ELSE 0 END) AS period_debit,
                    sum(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.credit ELSE 0 END) AS period_credit,
                    sum(CASE WHEN aml.date <'{start_date}' THEN aml.debit ELSE 0 END) AS before_period_debit,
                    sum(CASE WHEN aml.date < '{start_date}' THEN aml.credit ELSE 0 END) AS before_period_credit,
                     sum(aml.debit) AS final_debit,
                sum(aml.credit) AS final_credit,
                    aml.account_id
                FROM
                    account_move_line aml
                LEFT JOIN
                    account_account aa ON aml.account_id = aa.id
                LEFT JOIN
                    res_company rc ON aa.company_id = rc.id
                WHERE
                    (aml.display_type NOT IN ('line_section', 'line_note') OR aml.display_type IS NULL)
                    AND aml.parent_state = 'posted'
                    AND (aml.company_id IS NULL OR aml.company_id IN (%s))
                    {account_ids_clause}
                GROUP BY
                    aml.account_id,
                    aa.name,
                    aa.code
                ORDER BY
                    aa.code
            """
        # Execute the SQL query
        self.env.cr.execute(account_move_sql, tuple(params))
        account_moves = self.env.cr.dictfetchall()

        # sums = {
        #     'period_debit': 0,
        #     'period_credit': 0,
        #     'before_period_debit': 0,
        #     'before_credit': 0,
        # }
        # for move in account_moves:
        #     sums['period_debit'] += move.get('period_debit', 0)
        #     sums['period_credit'] += move.get('period_credit', 0)
        #     sums['before_debit'] += move.get('before_debit', 0)
        #     sums['before_credit'] += move.get('before_credit', 0)
        #
        # account_moves.append(sums)

        return account_moves

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id'][0]
        account_ids = data['form']['account_ids']

        data = {
            'date_from': date_from,
            'date_to': date_to,
            'account_ids': account_ids,
            'company_id': company_id,
        }
        docargs = {
            'doc_model': 'az.ledger.report',
            'data': data,
            'get_ledger_detail': self.get_ledger_detail,
        }
        return docargs
