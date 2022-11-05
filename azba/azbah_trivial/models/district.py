

from odoo import fields, models


class District(models.Model):
    _name = "geography.district"
    name = fields.Char()

