# -*- coding: utf-8 -*-

from odoo import models, api


class LedgerReportTemplate(models.AbstractModel):
    _name = 'report.az_account_reports.ledger_report_template'
    _description = 'Ledger Report Template'

    def get_ledger_detail(self, data):
        # Retrieve date range for filtering account moves 📅
        company_id = data.get('company_id')
        start_date = data.get('date_from')
        end_date = data.get('date_to')
        account_ids = data.get('account_ids')[0] if data.get('account_ids') else None

        params = [company_id]

        if account_ids:
            account_move_sql = f"""
                SELECT
                    aa.name AS account_name,
                    p.code,
                    p.name AS name,
                    SUM(COALESCE(aml.debit, 0)) AS period_debit,
                    SUM(COALESCE(aml.credit, 0)) AS period_credit,
                    COALESCE(pd.total_debit_before, 0) AS before_period_debit,
                    COALESCE(pd.total_credit_before, 0) AS before_period_credit,
                    aa.id AS account_id,
                    SUM(COALESCE(aml.debit, 0)) + COALESCE(pd.total_debit_before, 0) AS final_debit,
                    SUM(COALESCE(aml.credit, 0)) + COALESCE(pd.total_credit_before, 0) AS final_credit
                FROM
                    account_account aa
                    LEFT JOIN res_partner p ON aa.id = p.id
                    LEFT JOIN account_move_line aml ON aa.id = aml.account_id
                    AND aml.date BETWEEN '{start_date}' AND '{end_date}'
                    AND (aml.display_type NOT IN ('line_section', 'line_note') OR aml.display_type IS NULL)
                    AND aml.parent_state = 'posted'
                    AND (aml.company_id IS NULL OR aml.company_id = {company_id})
                    LEFT JOIN (
                        SELECT
                            account_id,
                            partner_id,
                            SUM(debit) AS total_debit_before,
                            SUM(credit) AS total_credit_before
                        FROM
                            account_move_line
                        WHERE
                            date < '{start_date}'
                            AND (display_type NOT IN ('line_section', 'line_note') OR display_type IS NULL)
                            AND parent_state = 'posted'
                            AND (company_id IS NULL OR company_id = {company_id})
                        GROUP BY
                            account_id, partner_id
                    ) pd ON aa.id = pd.account_id AND p.id = pd.partner_id
                WHERE
                    aa.id = {account_ids}
                GROUP BY
                    aa.name, aa.id, p.code, p.name, pd.total_debit_before, pd.total_credit_before
                ORDER BY
                    p.code;
            """
        else:
            account_move_sql = f"""
                SELECT
                    aa.name,
                    aa.code,
                    aa.id AS account_id,
                    MIN(aml.id) AS id,
                    COUNT(aml.id) AS account_id_count,
                    MIN(aml.date) AS date,
                    SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.debit ELSE 0 END) AS period_debit,
                    SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.credit ELSE 0 END) AS period_credit,
                    SUM(CASE WHEN aml.date < '{start_date}' THEN aml.debit ELSE 0 END) AS before_period_debit,
                    SUM(CASE WHEN aml.date < '{start_date}' THEN aml.credit ELSE 0 END) AS before_period_credit,
                    SUM(aml.debit) AS final_debit,
                    SUM(aml.credit) AS final_credit
                FROM
                    account_account aa
                LEFT JOIN account_move_line aml ON aa.id = aml.account_id
                    AND (aml.display_type NOT IN ('line_section', 'line_note') OR aml.display_type IS NULL)
                    AND aml.parent_state = 'posted'
                    AND (aml.company_id IS NULL OR aml.company_id IN (%s))
                LEFT JOIN (
                    SELECT
                        account_id,
                        SUM(debit) AS total_debit_before,
                        SUM(credit) AS total_credit_before
                    FROM
                        account_move_line
                    WHERE
                        date < '{start_date}'
                        AND (display_type NOT IN ('line_section', 'line_note') OR display_type IS NULL)
                        AND parent_state = 'posted'
                        AND (company_id IS NULL OR company_id IN (%s))
                    GROUP BY
                        account_id
                ) pd ON aa.id = pd.account_id
                WHERE
                    aa.company_id IN (%s)
                GROUP BY
                    aa.name, aa.code, aa.id, pd.total_debit_before, pd.total_credit_before
                ORDER BY
                    aa.code
            """

        # Execute the SQL query 🚀
        self.env.cr.execute(account_move_sql, tuple(params))

        account_moves = self.env.cr.dictfetchall()

        # Initialize sums for the different periods 💰
        sums = {
            'period_debit': 0,
            'period_credit': 0,
            'before_period_debit': 0,
            'before_period_credit': 0,
        }

        # Calculate totals for the different periods 🧮
        for move in account_moves:
            sums['period_debit'] += move.get('period_debit', 0)
            sums['period_credit'] += move.get('period_credit', 0)
            sums['before_period_debit'] += move.get('before_debit', 0)
            sums['before_period_debit'] += move.get('before_credit', 0)

        # Append the sums to the account moves
        account_moves.append(sums)

        return account_moves

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Prepare data for the report.

        :param docids: IDs of the documents to be reported.
        :param data: Optional dictionary containing filter criteria.
        :return: Dictionary with the report data and helper methods.
        """
        # Extract filter criteria from the form data 📋
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id'][0]
        account_ids = data['form']['account_ids']

        # Prepare the data dictionary 🗂️
        data = {
            'date_from': date_from,
            'date_to': date_to,
            'account_ids': account_ids,
            'company_id': company_id,
        }

        # Prepare the arguments for the report 📊
        docargs = {
            'doc_model': 'az.ledger.report',
            'data': data,
            'get_ledger_detail': self.get_ledger_detail,
        }

        return docargs
