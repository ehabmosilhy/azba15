from datetime import time, datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import models, api, fields, _


class SaleAdvancePaymentInv(models.Model):
    _inherit = 'sale.order'
    _description = "Sales Advance Payment Invoice"
    _order = 'date_order desc, id desc'
    _check_company_auto = True


    delegate = fields.Many2one('res.partner', tracking=True, string="Delegate")


    def _prepare_invoice(self):
        values= super(SaleAdvancePaymentInv, self)._prepare_invoice()


        values.update( {

            'delegate_id': self.delegate.id,

        })
        return values



