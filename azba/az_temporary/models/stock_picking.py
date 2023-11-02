from odoo import fields, models, api


class AccountBankStatement(models.Model):
    _inherit = 'stock.picking'

    # The field date_done needs to be read-writeable because it is used for enetering old data
    date_done = fields.Datetime(readonly=False)