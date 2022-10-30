# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_max_amount = fields.Float(default_model='purchase.requisition.request', default=5000,

                                      string="المبلغ الأقصى للشراء المباشر")
    default_pr_max_amount = fields.Float(default_model='purchase.requisition', default=5000,

                                         string="المبلغ الذي يحتاج موافقة اللجنة")


class PurchaseSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_max_amount = fields.Float(default_model='purchase.requisition.request',
                                      related='company_id.default_max_amount',

                                      string="المبلغ الأقصى للشراء المباشر")
    default_pr_max_amount = fields.Float(default_model='purchase.requisition',
                                         related='company_id.default_pr_max_amount',
                                         string="المبلغ الذي يحتاج موافقة اللجنة")
