from odoo import models, api, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_credit_limit(self, partner, amount_total):
        # Check if the payment term is credit
        is_credit_payment = self.payment_term_id and self.payment_term_id.name == 'Credit'  # Update this condition based on your actual credit payment term

        if is_credit_payment and partner.credit_limit_category_id:
            if (amount_total + partner.total_due) > partner.credit_limit_category_id.credit_limit:
                raise ValidationError(_("The total amount exceeds the customer's credit limit."))

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        partner = order.partner_id
        self._check_credit_limit(partner, order.amount_total)
        return order

    def write(self, vals):
        result = super(SaleOrder, self).write(vals)
        partner = self.partner_id
        self._check_credit_limit(partner, self.amount_total)
        return result


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _check_credit_limit(self, partner, amount_total):
        # Check if the payment term is credit
        is_credit_payment = self.invoice_payment_term_id and self.invoice_payment_term_id.name == 'Credit'  # Update this condition based on your actual credit payment term

        if is_credit_payment and partner.credit_limit_category_id:
            if (amount_total + partner.total_due) > partner.credit_limit_category_id.credit_limit:
                raise ValidationError(_("The total amount exceeds the customer's credit limit."))

    @api.model
    def create(self, vals):
        invoice = super(AccountMove, self).create(vals)
        if vals.get('move_type', '') in ['out_invoice', 'out_refund']:
            partner = invoice.partner_id
            amount_total = invoice.amount_total
            invoice._check_credit_limit(partner, amount_total)
        return invoice

    def write(self, vals):
        result = super(AccountMove, self).write(vals)
        if self.filtered(lambda m: m.move_type in ['out_invoice', 'out_refund']):
            for move in self:
                partner = move.partner_id
                amount_total = move.amount_total
                move._check_credit_limit(partner, amount_total)
        return result
