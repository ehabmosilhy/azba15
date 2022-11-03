from odoo import models, api, fields, _ 
from werkzeug.routing import ValidationError


class delegate(models.Model):

    _inherit = 'account.move'
    delegate_id = fields.Many2one('res.partner', tracking=True, domain = [('is_delegate', '=', True)])
