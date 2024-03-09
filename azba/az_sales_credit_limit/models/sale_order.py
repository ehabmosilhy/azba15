from odoo import models, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        for order in result:
            partner = order.partner_id
            if partner.credit_limit_category_id and order.amount_total > partner.credit_limit_category_id.credit_limit:
                raise ValidationError(_("The sales order amount exceeds the customer's credit limit."))
        return result

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        for order in self:
            partner = order.partner_id
            if partner.credit_limit_category_id and order.amount_total > partner.credit_limit_category_id.credit_limit:
                raise ValidationError(_("The sales order amount exceeds the customer's credit limit."))
        return result