# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    pos_config_ids = fields.Many2many('pos.config', 'pos_detail_configs', default=None)

    def generate_report(self):
        c = self.pos_config_ids
        configs = [(p.id, p.name, p.employee_ids.mapped("name")) for p in c]
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids,
                'configs': configs}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)
