from odoo import models, fields


class CreditLimitCategory(models.Model):
    _name = 'credit.limit.category'
    _description = 'Credit Limit Category'

    name = fields.Char(string='Category Name', required=True)
    credit_limit = fields.Integer(string='Credit Limit', required=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit_category_id = fields.Many2one('credit.limit.category', string='Credit Limit Category')