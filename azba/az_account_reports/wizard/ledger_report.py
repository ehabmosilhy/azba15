# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import  ValidationError
import xlwt
import base64
import io

class LedgerReport(models.TransientModel):
    _name = "az.ledger.report"
    _description = "Ledger Report"

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    company_id = fields.Many2one('res.company',string="Company", default=lambda self: self.env.company
                                 , required=True)
    account_ids = fields.Many2one("account.account", string="Accounts")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date must be greater than start date!")

    def get_ledger_report(self):
        [data] = self.read()
        datas = {
             'ids': [1],
             'model': 'az.ledger.report',
             'form': data
        }
        action = self.env.ref('az_account_reports.ledger_report_action_view').report_action(self, data=datas)
        return action

    def get_ledger_detail(self, data):
        # Retrieve date range for filtering account moves
        data= data['form']
        company_id = data.get('company_id')[0]
        start_date = data.get('date_from')
        end_date = data.get('date_to')

        # Depending on the report type, construct the account IDs SQL
        account_ids = data.get('account_ids')[0] if data.get('account_ids') else None
        account_ids_clause = ""
        params = [company_id]

        if account_ids:
            account_move_sql = f"""
                      SELECT
                          account.name AS account_name,
                          partner.code,
                          partner.name AS name,
                          COALESCE(SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.debit ELSE 0 END), 0) AS period_debit,
                          COALESCE(SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.credit ELSE 0 END), 0) AS period_credit,
                          COALESCE(pd.total_debit_before, 0) AS before_period_debit,
                          COALESCE(pd.total_credit_before, 0) AS before_period_credit,
                          aml.account_id,
                          0 as final_debit,
                          0 as final_credit
                      FROM
                          account_move_line aml
                          LEFT JOIN account_account account ON aml.account_id = account.id
                          LEFT JOIN res_partner partner ON aml.partner_id = partner.id
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
                                  AND (company_id IS NULL OR company_id = {company_id})
                              GROUP BY
                                  partner_id, account_id
                          ) pd ON aml.partner_id = pd.partner_id AND aml.account_id = pd.account_id
                      WHERE
                          (aml.display_type NOT IN ('line_section', 'line_note') OR aml.display_type IS NULL)
                          AND aml.parent_state = 'posted'
                          AND (aml.company_id IS NULL OR aml.company_id = {company_id})
                          AND (aml.date BETWEEN '{start_date}' AND '{end_date}' OR aml.date < '{start_date}')
                          AND aml.account_id = {account_ids}
                      GROUP BY
                          aml.account_id, account.name, partner.id, partner.name, pd.total_debit_before, pd.total_credit_before
                      ORDER BY
                          partner.code;
                  """

            # Construct the SQL to fetch all relevant account moves
        else:
            account_move_sql = f"""
                      SELECT
                          aa.name,
                          aa.code,
                          MIN(aml.id) AS id,
                          COUNT(aml.id) AS account_id_count,
                          MIN(aml.date) AS date,
                          SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.debit ELSE 0 END) AS period_debit,
                          SUM(CASE WHEN aml.date BETWEEN '{start_date}' AND '{end_date}' THEN aml.credit ELSE 0 END) AS period_credit,
                          SUM(CASE WHEN aml.date < '{start_date}' THEN aml.debit ELSE 0 END) AS before_period_debit,
                          SUM(CASE WHEN aml.date < '{start_date}' THEN aml.credit ELSE 0 END) AS before_period_credit,
                          SUM(aml.debit) AS final_debit,
                          SUM(aml.credit) AS final_credit,
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
                          AND (aml.date BETWEEN '{start_date}' AND '{end_date}' OR aml.date < '{start_date}')
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

        sums = {
            'period_debit': 0,
            'period_credit': 0,
            'before_period_debit': 0,
            'before_period_credit': 0,
        }
        for move in account_moves:
            sums['period_debit'] += move.get('period_debit', 0)
            sums['period_credit'] += move.get('period_credit', 0)
            sums['before_period_debit'] += move.get('before_debit', 0)
            sums['before_period_debit'] += move.get('before_credit', 0)

        account_moves.append(sums)

        return account_moves

    def get_ledger_report_xls(self):

        data = {
            'form': self.read()[0],
        }

        filename = 'Ledger Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("Sheet 1", cell_overwrite_ok=True)
        # make worksheet right to left
        worksheet.cols_right_to_left = True
        worksheet.col(0).width = 5000
        style_header = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: vert centre, horiz center;pattern: pattern solid, pattern_fore_colour gray25;")

        style_line_heading = xlwt.easyxf(
            "font: name Liberation Sans, bold on;align: horiz centre; pattern: pattern solid, pattern_fore_colour gray25;")
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 500
        worksheet.col(0).width = 6000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        line = 0
        worksheet.write_merge(line, line, 0, 9, "أرصدة الأستاذ المساعد", style=style_header)
        line += 1
        if self.account_ids:
            worksheet.write_merge(line, line, 0, 9, "الحساب: " + self.account_ids.name, style=style_header)
            line += 1
        worksheet.write_merge(line, line, 0, 9, "التاريخ: من " + str(self.date_from) + " === إلى " + str(self.date_to), style=style_header)
        line += 1
        worksheet.write_merge(line, line, 0, 1, "", style=style_line_heading)
        worksheet.write_merge(line, line, 2, 3, "ما قبله", style=style_line_heading)
        worksheet.write_merge(line, line, 4, 5, "خلال الفترة", style=style_line_heading)
        worksheet.write_merge(line, line, 6, 7, "الإجمالى", style=style_line_heading)
        worksheet.write_merge(line, line, 8, 9, "الرصيد", style=style_line_heading)
        line += 1
        worksheet.write(line, 0, "كود", style=style_line_heading)
        worksheet.write(line, 1, "اسم الحساب", style=style_line_heading)
        worksheet.write(line, 2, "مدين", style=style_line_heading)
        worksheet.write(line, 3, "دائن", style=style_line_heading)
        worksheet.write(line, 4, "مدين", style=style_line_heading)
        worksheet.write(line, 5, "دائن", style=style_line_heading)
        worksheet.write(line, 6, "مدين", style=style_line_heading)
        worksheet.write(line, 7, "دائن", style=style_line_heading)
        worksheet.write(line, 8, "مدين", style=style_line_heading)
        worksheet.write(line, 9, "دائن", style=style_line_heading)
        line += 1

        vals = self.get_ledger_detail(data)


        style_normal_right = xlwt.easyxf("font: name Liberation Sans; align: horiz right;")
        style_bold_right = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: vert centre, horiz center;pattern: pattern solid, pattern_fore_colour gray25;")

        # Initialize sum variables before the loop
        sum_before_period_debit = 0
        sum_before_period_credit = 0
        sum_period_debit = 0
        sum_period_credit = 0
        sum_total_debit = 0
        sum_total_credit = 0
        sum_balance_debit = 0
        sum_balance_credit = 0

        for ledger in vals:
            if not ledger.get('code') and not ledger.get('name'):
                continue
            worksheet.write(line, 0, ledger.get('code'), style=style_normal_right)
            worksheet.write(line, 1, ledger.get('name'), style=style_normal_right)
            worksheet.write(line, 2, ledger.get('before_period_debit', 0), style=style_normal_right)
            worksheet.write(line, 3, ledger.get('before_period_credit', 0), style=style_normal_right)
            worksheet.write(line, 4, ledger.get('period_debit', 0), style=style_normal_right)
            worksheet.write(line, 5, ledger.get('period_credit', 0), style=style_normal_right)

            total_debit = ledger.get('before_period_debit', 0) + ledger.get('period_debit', 0)
            total_credit = ledger.get('before_period_credit', 0) + ledger.get('period_credit', 0)

            balance_credit = max(total_credit - total_debit, 0)
            balance_debit = max(total_debit - total_credit, 0)

            worksheet.write(line, 6, total_debit, style=style_normal_right)
            worksheet.write(line, 7, total_credit, style=style_normal_right)
            worksheet.write(line, 8, balance_debit, style=style_normal_right)
            worksheet.write(line, 9, balance_credit, style=style_normal_right)

            sum_before_period_debit += ledger.get('before_period_debit', 0)
            sum_before_period_credit += ledger.get('before_period_credit', 0)
            sum_period_debit += ledger.get('period_debit', 0)
            sum_period_credit += ledger.get('period_credit', 0)
            sum_total_debit += total_debit
            sum_total_credit += total_credit
            sum_balance_debit += balance_debit
            sum_balance_credit += balance_credit
            line += 1

        # Write the summation line
        worksheet.write(line, 1, 'Total', style=style_bold_right)
        worksheet.write(line, 2, sum_before_period_debit, style=style_bold_right)
        worksheet.write(line, 3, sum_before_period_credit, style=style_bold_right)
        worksheet.write(line, 4, sum_period_debit, style=style_bold_right)
        worksheet.write(line, 5, sum_period_credit, style=style_bold_right)
        worksheet.write(line, 6, sum_total_debit, style=style_bold_right)
        worksheet.write(line, 7, sum_total_credit, style=style_bold_right)
        worksheet.write(line, 8, sum_balance_debit, style=style_bold_right)
        worksheet.write(line, 9, sum_balance_credit, style=style_bold_right)

        balance = sum_balance_debit-sum_balance_credit
        if balance>0:
            cell = 8
        else:
            cell = 9
        line += 2
        worksheet.write(line, 7, "الرصيد", style=style_bold_right)
        worksheet.write(line, cell, abs(balance), style=style_bold_right)


        fp = io.BytesIO()
        workbook.save(fp)

        export_id = self.env['excel.report'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res