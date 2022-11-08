from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"
    date_relation_start = fields.Date()
