from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.payment"

    delegate_id = fields.Many2one('hr.employee', string="المندوب")
