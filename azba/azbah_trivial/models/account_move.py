from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"
    manual_ref = fields.Char(string="إذن التسليم")
