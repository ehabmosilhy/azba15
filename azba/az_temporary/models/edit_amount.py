from odoo import fields, models, api


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'
    new_amount = fields.Char("القيمة الجديدة")

    def button_edit_amount(self):
        if self.new_amount:
            self.new_amount = float(self.new_amount.replace(",", ""))
            sql = f"update account_bank_statement_line set amount={self.new_amount} where statement_id={self.id}; "
            sql2 = """
                    UPDATE account_bank_statement AS s
                    SET balance_end = (
                    SELECT SUM(amount)
                    FROM account_bank_statement_line AS l
                    WHERE l.statement_id = s.id
                   ) + s.balance_start;
            """
            sql3 = """
            update account_bank_statement set balance_end_real=balance_end; -- where balance_end_real<>balance_end;
            """

            self.env.cr.execute(sql)
            self.env.cr.execute(sql2)
            self.env.cr.execute(sql3)
