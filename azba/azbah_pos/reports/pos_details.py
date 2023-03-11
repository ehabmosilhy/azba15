# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    pos_config_ids = fields.Many2many('pos.config', 'pos_detail_configs', default=None)

    def _default_start_date(self):
        """ Find the earliest start_date of the latests sessions """
        # restrict to configs available to the user
        config_ids = self.env['pos.config'].search([]).ids
        # exclude configs has not been opened for 2 days
        self.env.cr.execute("""
               SELECT
               max(start_at) as start,
               config_id
               FROM pos_session
               WHERE config_id = ANY(%s)
               AND start_at > (NOW() - INTERVAL '2 DAYS')
               GROUP BY config_id
           """, (config_ids,))
        latest_start_dates = [res['start'] for res in self.env.cr.dictfetchall()]
        # earliest of the latest sessions
        d = (latest_start_dates and min(latest_start_dates) or fields.Datetime.now()).replace(hour=0, minute=1)
        return d

    start_date = fields.Datetime(required=True, default=_default_start_date)

    def generate_report(self):
        c = self.pos_config_ids
        configs = [(p.id, p.name, p.employee_ids.mapped("name")) for p in c]
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids,
                'configs': configs}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)
