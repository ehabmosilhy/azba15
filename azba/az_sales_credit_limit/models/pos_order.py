from odoo import models, api, _
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, vals):
        partner_id = vals.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.credit_limit_category_id:
                credit_limit = partner.credit_limit_category_id.credit_limit
                total_amount = vals.get('amount_total')
                if total_amount > credit_limit:
                    raise UserError(_('Credit limit exceeded for partner %s') % partner.name)
        return super(PosOrder, self).create(vals)