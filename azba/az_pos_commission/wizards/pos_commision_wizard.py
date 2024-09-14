# -*- coding: utf-8 -*-
from odoo import fields, models
import math


class PosCommissionWizard(models.TransientModel):
    _name = 'pos.commission.wizard'
    _description = 'POS Commission Wizard'

    start_date = fields.Datetime(string='تاريخ البداية', required=True, default='2024-01-01 00:00:00')
    end_date = fields.Datetime(string='تاريخ النهاية', required=True, default='2024-02-01 00:00:00')
    config_id = fields.Many2many('pos.config', string='المسار')

    def _prepare_report_data(self):
        start_date = self.start_date
        end_date = self.end_date

        collection_configs = {"R500", "R501", "R502", "R503", "R504", "R505", "R506", "R513", "R515", "R519"   "R508",
                              "R509", "R805"   "R511", "R512", "R813"   "R800", "R801", "R802", "R803", "R804", "R806",
                              "R807", "R808"}
        config_names = set()
        if self.config_id:
            config_names = {c.name for c in self.config_id}
            config_id = tuple(self.config_id.ids)  # Convert to tuple
        else:
            current_company = self.env.user.company_id.id
            config_id = tuple(
                self.env['pos.config'].search([('company_id', '=', current_company)]).ids)  # Convert to tuple

        where_clause = """
                 WHERE line.company_id=1 and timezone('Asia/Riyadh', timezone('UTC', o.date_order)) BETWEEN %s AND %s
             """
        params = [start_date, end_date]

        if config_id:
            where_clause += " AND conf.id in %s"
            params.append(config_id)

        sql = f"""
                 SELECT tmpl.commission_category, employee.name as emp_name , employee.id as emp_id, conf.name as config, SUM(line.qty) as qty
                 FROM pos_order o
                 INNER JOIN pos_session session ON session.id = o.session_id
                 INNER JOIN pos_config conf ON conf.id = session.config_id
                 INNER JOIN pos_order_line line ON line.order_id = o.id
                 INNER JOIN hr_employee employee ON o.employee_id = employee.id
                 INNER JOIN product_product product ON product.id = line.product_id 
                 INNER JOIN product_template tmpl ON product.product_tmpl_id = tmpl.id
                 {where_clause}
                 GROUP BY conf.id, conf.name, employee.id,employee.name, tmpl.commission_category
                 HAVING SUM(line.qty) > 0;
             """

        self.env.cr.execute(sql, params)

        data = self.env.cr.dictfetchall()

        routes = {
            ("R500", "R501", "R502", "R503", "R504", "R505",
             "R506", "R513", "R515", "R519"): self.retail_azbah,  # قطاعي عذبة كرتون
            ("R508", "R509", "R805"): self.wholesale_halaka,  # كرتون جملة داخل الحلقة
            ("R511", "R512", "R813"): self.wholesale_outside_halaka,  # كرتون جملة خارج الحلقة
            ("R800", "R801", "R802", "R803", "R804", "R806", "R807", "R808"): self.retail_hala  # كرتون قطاعى حلا
        }
        # if config_names & collection_configs:
        collection = self.get_collection(config_id, start_date, end_date)
        data = data + collection
        for line in data:
            if not line['commission_category']:
                line['commission_category'] = 'bottle'
                line['commission'] = self.bottle_commission(line)
            else:
                for route in routes.items():
                    if 'config' in line and line['config'] in route[0]:
                        line = route[1](line)
                    break

        return data

    def generate_pdf_report(self):
        all_data = self._prepare_report_data()
        for line in all_data:
            if 'commission' in line:
                line['commission'] = math.ceil(abs(line['commission'])) if not isinstance(line['commission'], str) else line[
                    'commission']
            else:
                line['commission'] = 0
        datas = {
            "wizard": self.read()[0],  # This includes the 'docs'
            "data": all_data,
        }
        return self.env.ref('az_pos_commission.commission_report_pdf_action').report_action(self, data=datas)

    def get_collection(self, config_id, start_date, end_date):
        # get all employess that worked on all configs during the period
        where_clause = f"""
            WHERE  timezone('Asia/Riyadh', timezone('UTC', o.date_order)) BETWEEN %s AND %s
        """
        params = [start_date, end_date]
        if config_id:
            where_clause += " AND s.config_id in %s"
            params.append(config_id)

        sql = f"""
             SELECT DISTINCT o.employee_id
            FROM pos_order o inner join pos_session s on o.session_id = s.id
            {where_clause}"""

        self.env.cr.execute(sql, params)
        emps = tuple(self.env.cr.fetchall())
        emps = tuple([emp[0] for emp in emps if emp[0]])
        collection = 0

        sql_collection_cash = """
        -- Collection: pos_order
        select o.employee_id  as emp_id, emp.name as emp_name,config.name as config, sum(o.amount_total) as qty    , 'collection_cash' as commission_category
        from pos_order o
        inner join hr_employee emp         on o.employee_id = emp.id
        INNER JOIN pos_session session ON session.id = o.session_id
        INNER JOIN pos_config config ON config.id = session.config_id
        where o.state = 'done' and o.company_id=1 and timezone('Asia/Riyadh', timezone('UTC', o.date_order)) BETWEEN %s AND %s and o.employee_id in %s
        group by config.name,o.employee_id, emp.name"""

        # sql_collection_bank = """
        # -- Collection: Payment
        # select emp.id as emp_id, emp.name as emp_name, sum(p.amount)  as qty, 'collection_bank' as commission_category
        # from account_payment p
        # inner join hr_employee emp on emp.id =p.delegate_id
        # inner join account_move m on m.id = p.move_id
        # where m.company_id=1 and timezone('Asia/Riyadh', timezone('UTC', m.date)) BETWEEN %s AND %s and emp.id in %s
        # group by emp.id, emp.name
        # ;
        # """

        sql_collection_bank="""
        SELECT 
            emp.id AS emp_id, 
            emp.name AS emp_name, 
            SUM(p.amount) AS qty, 
            'collection_bank' AS commission_category,
            MAX(pc.name) AS config
        FROM 
            account_payment p
        INNER JOIN 
            hr_employee emp ON emp.id = p.delegate_id
        INNER JOIN 
            account_move m ON m.id = p.move_id
        LEFT JOIN 
            pos_order po ON po.employee_id = emp.id
        LEFT JOIN 
            pos_session ps ON ps.id = po.session_id
        LEFT JOIN 
            pos_config pc ON pc.id = ps.config_id
        WHERE 
            m.company_id = 1 
            AND timezone('Asia/Riyadh', timezone('UTC', m.date)) BETWEEN %s AND %s 
            AND emp.id IN %s
            AND timezone('Asia/Riyadh', timezone('UTC', po.date_order)) BETWEEN %s AND %s 
        GROUP BY 
            emp.id, emp.name;
        """

        params = [start_date, end_date, emps]
        self.env.cr.execute(sql_collection_cash, params)
        collection_cash = self.env.cr.dictfetchall()


        params = [start_date, end_date, emps,start_date, end_date]
        self.env.cr.execute(sql_collection_bank, params)
        collection_bank = self.env.cr.dictfetchall()

        return collection_cash + collection_bank

    def retail_azbah(self, line):
        #  (500, 501, 502, 503, 504, 505, 506, 513, 515, 519): "retail_azbah",  # قطاعي عذبة كرتون

        if line['commission_category'] == 'shrink':
            line['commission'] = line['qty'] * 0.12
        elif line['commission_category'] == 'carton':
            line['commission'] = self.carton_commission_retail_azbah(line['qty'])
        elif 'collection' in  line['commission_category']:
            line['commission'] = line['qty'] * 0.01
        return line

    def wholesale_halaka(self, line):
        #  (508, 509, 805): "wholesale_halaka",  # كرتون جملة داخل الحلقة
        effort = 0
        # if line['commission_category'] == 'carton':
        #     line['commission'] = line['qty'] * 0.09
        #     new_line = line.copy()
        #     effort = line['qty'] * 2.5 / 100
        # if effort:
        #     new_line.update({"commission_category": "effort", "commission": effort})
        #     data.append(new_line)
        if line['commission_category'] == 'carton':
            line['commission_category'] = 'carton+effort'
            line['commission'] = line['qty'] * 0.09 + line['qty'] * 2.5 / 100
        return line

    def wholesale_outside_halaka(self, line):
        #  (511, 512, 813): "wholesale_outside_halaka",  # كرتون جملة خارج الحلقة
        if line['commission_category'] == 'carton':
            line['commission'] = line['qty'] * 0.09
        elif 'collection' in  line['commission_category']:
            line['commission'] = line['qty'] * 0.005
        return line

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

    def retail_hala(self, data=0, collection=0):
        #  (800, 801, 802, 803, 804, 806, 807, 808): "retail_hala"  # كرتون قطاعى حلا
        for line in data:
            if line['commission_category'] == 'shrink':
                line['commission'] = line['qty'] * 0.12
            elif line['commission_category'] == 'carton':
                line['commission'] = self.carton_commission_retail_azbah(line['qty'])
            elif 'collection' in  line['commission_category']:
                line['commission'] = line['qty'] * 0.01
        return data

    def bottle_commission(self, line):
        qty = line['qty']
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
        return math.ceil(commission)
