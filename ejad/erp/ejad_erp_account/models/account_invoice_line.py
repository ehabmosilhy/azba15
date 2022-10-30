# -*- coding: utf-8 -*-


#################################################################################

from odoo import api, fields, models, _

class AccountInvoiceline(models.Model):
    _inherit =  "account.move.line"


    partner_id = fields.Many2one('res.partner', string='طالب', )


class AccountInvoice(models.Model):
    _inherit = "account.move"

    is_company = fields.Boolean(string='compagny',
                               store=True,
                               related='partner_id.is_company')
    uni_id = fields.Char(string='الرقم الجامعي', related='partner_id.uni_id', store=True)
class AccountInvoice(models.Model):
    _inherit = "account.move.line"

    is_company = fields.Boolean(string='compagny',
                               store=True,
                               related='partner_id.is_company')

    partner_id1 = fields.Many2one('res.partner', string='Partner',
        store=True,  related_sudo=False)
    uni_id = fields.Char(string='الرقم الجامعي', related='partner_id1.uni_id', store=True)

    


