# -*- coding: utf-8 -*-
from odoo import fields, models, api, exceptions


class PosCommissionWizard(models.TransientModel):
    _name = 'pos.commission.wizard'
    _description = 'POS Commission Wizard'

    start_date = fields.Datetime(string='تاريخ البداية', required=True)
    end_date = fields.Datetime(string='تاريخ النهاية', required=True)
    config_id = fields.Many2one('pos.config', string='المسار', required=True)

    def retail_azbah(self, data=0, collection=0):
        #  (500, 501, 502, 503, 504, 505, 506, 513, 515, 519): "retail_azbah",  # قطاعي عذبة كرتون
        products = data
        return products

    def wholesale_halaka(self):
        #  (508, 509, 805): "wholesale_halaka",  # كرتون جملة داخل الحلقة
        pass

    def wholesale_outside_halaka(self):
        #  (511, 512, 813): "wholesale_outside_halaka",  # كرتون جملة خارج الحلقة
        pass

    def retail_hala(self):
        #  (800, 801, 802, 803, 804, 806, 807, 808): "retail_hala"  # كرتون قطاعى حلا
        pass

    def calculate_commission(self, qty):
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
                 SELECT conf.id,tmpl.code,  tmpl.name as product_name, employee.name as employee, conf.name as config, SUM(line.qty) as qty
                 FROM pos_order o
                 INNER JOIN pos_session session ON session.id = o.session_id
                 INNER JOIN pos_config conf ON conf.id = session.config_id
                 INNER JOIN pos_order_line line ON line.order_id = o.id
                 INNER JOIN hr_employee employee ON o.employee_id = employee.id
                 inner join product_product product on product.id = line.product_id 
                 inner join product_template tmpl on product.product_tmpl_id = tmpl.id
                 {where_clause}
                 GROUP BY conf.id, conf.name, employee.name,  tmpl.name, tmpl.code
                 HAVING SUM(line.qty) > 0;
             """

        self.env.cr.execute(sql, params)

        data = self.env.cr.dictfetchall()

        # data = data[0]
        print (data)
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
            commission = self.calculate_commission(qty)

        data = {'start_date': start_date, 'end_date': end_date, 'config_id': config_id,
                'commission': commission, 'qty':qty}

        return data

    def generate_pdf_report(self):
        data = self._prepare_report_data()
        datas = {
            "wizard": self.read()[0],  # This includes the 'docs'
            "data": data,
        }
        return self.env.ref('az_pos_commission.commission_report_pdf_action').report_action(self, data=datas)
