from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict

class AccountPayment(models.Model):
    _inherit = "account.payment"
    delegate_id = fields.Many2one('hr.employee',string="Delegate المندوب")