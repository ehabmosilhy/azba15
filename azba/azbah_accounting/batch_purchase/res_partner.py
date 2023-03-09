# -*- coding: utf-8 -*-
from odoo import models, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    # When Creating a new vendor, assign its code
    @api.model_create_multi
    def create(self, vals_list):
        source = self.env.context.get('source')
        if source == 'vendor':
            last_vendor = self.env['res.partner'].search([('code', 'ilike', 'v%')], order='id desc', limit=1)
            if last_vendor:
                new_code = 'V'+str(int(last_vendor.code[1:]) + 1).zfill(4)
                vals_list[0]['code'] = new_code
                vals_list[0]['company_type'] = 'company'
                vals_list[0]['is_company'] = True
                return super().create(vals_list)
