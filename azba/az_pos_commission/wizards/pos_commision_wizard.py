# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions


class PosCommissionWizard(models.TransientModel):
    _name = 'pos.commission.wizard'
    _description = 'POS Commission Wizard'

    start_date = fields.Datetime(string='تاريخ البداية', required=True, default='2024-01-01 00:00:00')
    end_date = fields.Datetime(string='تاريخ النهاية', required=True, default='2025-01-01 00:00:00')
    config_id = fields.Many2one('pos.config', string='المسار', required=True)

    def carton_commission_retail_azbah(self, qty):
        if qty < 500:
            return (qty - 0) * 0.04
        elif qty < 1000:
            return 20 + (qty - 501) * 0.8
        elif qty < 1500:
            return 60 + (qty - 1001) * 0.12
        elif qty < 2000:
            return 120 + (qty - 1501) * 0.16
        elif qty < 2500:
            return 200 + (qty - 2001) * 0.2
        elif qty < 3000:
            return 300 + (qty - 2501) * 0.24
        elif qty < 3500:
            return 420 + (qty - 3001) * 0.28
        elif qty < 4000:
            return 560 + (qty - 3501) * 0.32
        elif qty < 4500:
            return 720 + (qty - 4001) * 0.36
        elif qty < 5000:
            return 900 + (qty - 4501) * 0.4
        elif qty < 5500:
            return 1100 + (qty - 5000) * 0.44
        elif qty < 6000:
            return 1320 + (qty - 5500) * 0.44
        elif qty < 6500:
            return 1540 + (qty - 6000) * 0.44
        elif qty < 7000:
            return 1760 + (qty - 6500) * 0.44
        elif qty < 7500:
            return 1980 + (qty - 7001) * 0.44
        elif qty < 8000:
            return 2200 + (qty - 7500) * 0.44
        elif qty < 8500:
            return 2420 + (qty - 8000) * 0.44
        elif qty < 9000:
            return 2640 + (qty - 8500) * 0.44
        elif qty < 9500:
            return 2860 + (qty - 9000) * 0.44
        elif qty < 10000:
            return 3080 + (qty - 9500) * 0.44
        elif qty < 10500:
            return 3300 + (qty - 10000) * 0.44
        elif qty < 11000:
            return 3615 + (qty - 10500) * 0.43
        elif qty < 11500:
            return 3520 + (qty - 11000) * 0.44
        elif qty < 12000:
            return 3740 + (qty - 11500) * 0.44
        else:
            return "Too Big!"  # Define what should happen if B2 >= 12000

    def retail_azbah(self, data=0, collection=0):
        #  (500, 501, 502, 503, 504, 505, 506, 513, 515, 519): "retail_azbah",  # قطاعي عذبة كرتون
        for line in data:
            if line['commission_category'] == 'shrink':
                line['commission'] = line['qty'] * 0.12
            elif line['commission_category'] == 'carton':
                line['commission'] = self.carton_commission_retail_azbah(line['qty'])
        return data

    def wholesale_halaka(self, data=0, collection=0):
        #  (508, 509, 805): "wholesale_halaka",  # كرتون جملة داخل الحلقة
        effort = 0
        for line in data:
            if line['commission_category'] == 'carton':
                line['commission'] = line['qty'] * 0.09
                new_line = line.copy()
                effort = line['qty'] * 2.5 / 100
        if effort:
            new_line.update({"commission_category": "effort", "commission": effort})
            data.append(new_line)
        return data

    def wholesale_outside_halaka(self, data=0, collection=0):
        #  (511, 512, 813): "wholesale_outside_halaka",  # كرتون جملة خارج الحلقة
        for line in data:
            if line['commission_category'] == 'carton':
                line['commission'] = line['qty'] * 0.09
        return data

    def retail_hala(self, data=0, collection=0):
        #  (800, 801, 802, 803, 804, 806, 807, 808): "retail_hala"  # كرتون قطاعى حلا
        for line in data:
            if line['commission_category'] == 'shrink':
                line['commission'] = line['qty'] * 0.12
            elif line['commission_category'] == 'carton':
                line['commission'] = self.carton_commission_retail_azbah(line['qty'])
        return data

    def bottle_commission(self, qty):
        if qty < 500:
            commission = (qty - 0) * 0.04
        elif qty < 1000:
            commission = 20 + (qty - 501) * 0.1016
        elif qty < 1500:
            commission = 71 + (qty - 1001) * 0.1632
        elif qty < 2000:
            commission = 152 + (qty - 1501) * 0.2248
        elif qty < 2500:
            commission = 265 + (qty - 2001) * 0.2864
        elif qty < 3000:
            commission = 408 + (qty - 2501) * 0.348
        elif qty < 3500:
            commission = 582 + (qty - 3001) * 0.4096
        elif qty < 4000:
            commission = 787 + (qty - 3501) * 0.4712
        elif qty < 4500:
            commission = 1022 + (qty - 4001) * 0.4712
        elif qty < 5000:
            commission = 1258 + (qty - 4501) * 0.4712
        elif qty < 5500:
            commission = 1494 + (qty - 5000) * 0.4712
        elif qty < 6000:
            commission = 1729 + (qty - 5500) * 0.4712
        elif qty < 6500:
            commission = 1965 + (qty - 6000) * 0.4712
        elif qty < 7000:
            commission = 2200 + (qty - 6500) * 0.4712
        elif qty < 7500:
            commission = 2436 + (qty - 7001) * 0.4712
        elif qty < 8000:
            commission = 2672 + (qty - 7500) * 0.4712
        elif qty < 8500:
            commission = 2907 + (qty - 8000) * 0.4712
        elif qty < 9000:
            commission = 3143 + (qty - 8500) * 0.4712
        elif qty < 9500:
            commission = 3378 + (qty - 9000) * 0.4712
        elif qty < 10000:
            commission = 3614 + (qty - 9500) * 0.4712
        elif qty < 10500:
            commission = 3850 + (qty - 10000) * 0.4712
        elif qty < 11000:
            commission = 4085 + (qty - 10500) * 0.4712
        elif qty < 11500:
            commission = 4321 + (qty - 11000) * 0.4712
        elif qty < 12000:
            commission = 4556 + (qty - 11500) * 0.4712
        else:
            commission = 0  # Default case if none of the conditions are met
        return round(commission)

    def _prepare_report_data(self):
        start_date = self.start_date
        end_date = self.end_date
        config_id = self.config_id.id if self.config_id else None

        where_clause = """
                 WHERE line.company_id=1 and timezone('Asia/Riyadh', timezone('UTC', o.date_order)) BETWEEN %s AND %s
             """
        params = [start_date, end_date]

        if config_id:
            where_clause += " AND conf.id = %s"
            params.append(config_id)

        sql = f"""
                 SELECT conf.id,tmpl.commission_category,  employee.name as employee, conf.name as config, SUM(line.qty) as qty
                 FROM pos_order o
                 INNER JOIN pos_session session ON session.id = o.session_id
                 INNER JOIN pos_config conf ON conf.id = session.config_id
                 INNER JOIN pos_order_line line ON line.order_id = o.id
                 INNER JOIN hr_employee employee ON o.employee_id = employee.id
                 inner join product_product product on product.id = line.product_id 
                 inner join product_template tmpl on product.product_tmpl_id = tmpl.id
                 {where_clause}
                 GROUP BY conf.id, conf.name, employee.name,  tmpl.commission_category
                 HAVING SUM(line.qty) > 0;
             """

        self.env.cr.execute(sql, params)

        data = self.env.cr.dictfetchall()

        # data = data[0]
        routes = {
            ("R500", "R501", "R502", "R503", "R504", "R505", "R506", "R513", "R515", "R519"): self.retail_azbah,
            # قطاعي عذبة كرتون
            ("R508", "R509", "R805"): self.wholesale_halaka,  # كرتون جملة داخل الحلقة
            ("R511", "R512", "R813"): self.wholesale_outside_halaka,  # كرتون جملة خارج الحلقة
            ("R800", "R801", "R802", "R803", "R804", "R806", "R807", "R808"): self.retail_hala  # كرتون قطاعى حلا
        }

        details = self.env['report.point_of_sale.report_saledetails']
        details = details.get_sale_details(date_start=start_date, date_stop=end_date, config_ids=[config_id])
        collection = abs(sum([d['amount'] for d in details['debits']]))

        for r in routes.items():
            if self.config_id.name in r[0]:
                commission = r[1](data, collection)
                break
        else:
            qty = data['qty'] if data else 0
            commission = self.bottle_commission(qty)

        return data

    def generate_pdf_report(self):
        import math
        data = self._prepare_report_data()
        for line in data:
            line['commission'] = math.ceil(line['commission']) if not isinstance(line['commission'], str) else line[
                'commission']
        datas = {
            "wizard": self.read()[0],  # This includes the 'docs'
            "data": data,
        }
        return self.env.ref('az_pos_commission.commission_report_pdf_action').report_action(self, data=datas)
