# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
import operator
from datetime import datetime, date
from odoo.tools.float_utils import float_round


class StockCardReportTemplate(models.AbstractModel):
    _name = 'report.bi_inventory_card_report.inventory_card_report_template'
    _description = 'Stock Card Report Template'

    def parse_date(self, date_string):
        return datetime.strptime(date_string, '%m/%d/%Y')

    def calculate_balance_at_date(self, movements, today_balance, target_date=None):
        # Sort movements by date in descending order
        movements.sort(key=lambda x: self.parse_date(x['date']), reverse=True)

        # Calculate the balance at the target date
        balance = today_balance
        for movement in movements:
            movement_date = self.parse_date(movement['date'])
            if target_date and movement_date < target_date:
                break
            if movement['type'] == 'reconciliation':
                balance = float(movement['amount'])
            else:
                balance -= float(movement['amount'])

        return balance

    def calculate_opening_balance(self, movements, today_balance):
        return self.calculate_balance_at_date(movements, today_balance)

    def get_today_balance(self, location_id, product_ids):
        """Retrieves the today's balance (the very last balance) of products for a given location and a list of product IDs.

        Args:
            location_id (int): The ID of the location for which the balance is requested.
            product_ids (List[int]): A list of product IDs for which the balance is requested.

        Returns:
            Dict[int, int]: A dictionary where the key is the product ID and the value is the quantity.

        Example:
            >>> location_id = 1
            >>> product_ids = [1001, 1002, 1003]
            >>> balance = self.get_today_balance(location_id, product_ids)
            >>> print(balance)
            {1001: 10, 1002: 5, 1003: 2}
        """
        today_balance_sql = """
            SELECT
                product_id,
                quantity
            FROM
                stock_quant
            WHERE
                product_id IN %s
                AND location_id = %s
        """
        today_balance_params = (tuple(product_ids), location_id)
        self.env.cr.execute(today_balance_sql, today_balance_params)
        return {row[0]: row[1] for row in self.env.cr.fetchall()}


    def get_on_hand_only(self, data):
        location_id = data['location_id'].id
        product_ids = data.get('product_ids', False)

        # Start with the base SQL query
        onhand_sql = """
            SELECT
                tmpl.code, tmpl.name,
                s.product_id,
                sum(s.quantity) as quantity
            FROM
                stock_quant s
                INNER JOIN product_product p ON p.id = s.product_id
                INNER JOIN product_template tmpl ON tmpl.id = p.product_tmpl_id
            WHERE
                s.location_id = %s
        """

        # Initialize the parameters with the location ID
        onhand_params = [location_id]

        # If product IDs are specified, add them to the query and parameters
        if product_ids:
            onhand_sql += "AND s.product_id IN %s "
            onhand_params.append(tuple(product_ids.ids))

        # Add the order by clause
        onhand_sql += "GROUP BY tmpl.code, tmpl.name, s.product_id ORDER BY tmpl.code"

        # Execute the query with the parameters
        self.env.cr.execute(onhand_sql, onhand_params)
        result = self.env.cr.dictfetchall()
        return result

    def get_product_detail(self, data):
        # Retrieve date range for filtering stock moves
        start_date_data = data.get('date_from')
        end_date_data = data.get('date_to')
        location_id = data.get('location_id') and data.get('location_id').id
        warehouse_id = data.get('warehouse_id') and data.get('warehouse_id').id

        if data.get('is_on_hand_only'):
            return self.get_on_hand_only(location_id, data.get('product_ids').ids)

        # Depending on the report type, construct the product IDs SQL
        report_by = data.get('report_by')
        if report_by == 'product_category':
            product_category_ids = tuple(data.get('product_category_ids').ids)
            product_ids_sql = "SELECT id FROM product_product WHERE categ_id IN %s"
            product_ids_params = (product_category_ids,)
        else:
            product_ids = tuple(data.get('product_ids').ids)
            product_ids_sql = "SELECT id FROM product_product WHERE id IN %s"
            product_ids_params = (product_ids,)

        # Execute SQL to fetch all product IDs
        self.env.cr.execute(product_ids_sql, product_ids_params)
        product_ids = [res[0] for res in self.env.cr.fetchall()]


        # 🔄 Construct the SQL to fetch all relevant stock moves
        stock_move_sql = f"""
        SELECT sm.id, sm.date, sm.product_id, sm.product_qty as qty_done, sml.location_id, sml.location_dest_id, pt.code as picking_type_code, sm.origin, sml.reference
        FROM stock_move_line sml
        JOIN stock_move sm ON sml.move_id = sm.id
        LEFT JOIN stock_picking_type pt ON sm.picking_type_id = pt.id
        WHERE sm.date >= %s AND sm.date <= %s
        AND sm.state = 'done'
        AND sml.product_id IN %s
        AND (sml.location_id = %s OR sml.location_dest_id = %s)
        """
        stock_move_params = (start_date_data, end_date_data, tuple(product_ids), location_id, location_id)
        if warehouse_id:
            stock_move_sql += " AND (sm.warehouse_id = %s OR sm.warehouse_id IS NULL)"
            stock_move_params += (warehouse_id,)

        # 📊 Execute SQL to fetch stock moves
        stock_move_sql += " ORDER BY sm.id"
        self.env.cr.execute(stock_move_sql, stock_move_params)
        stock_moves = self.env.cr.dictfetchall()

        # 📈 Process stock moves to calculate balance and prepare report lines

        today_balances = self.get_today_balance(location_id, product_ids)
        opening_balances = self.get_opening_balance(location_id, start_date_data, product_ids)

        balance_dict = {product_id:
                            {'opening_balance': opening_balances.get(product_id, 0.0),
                             'today_balance': today_balances.get(product_id, 0.0)} for product_id in product_ids
                        }


        lines = []
        balance_dict = {product_id:
                            {'opening_balance': opening_balances.get(product_id, 0.0),
                             'today_balance': today_balances.get(product_id, 0.0)
                             } for product_id in product_ids}
        for product_id in product_ids:
            balance_dict[product_id]['total_in'] = 0
            balance_dict[product_id]['total_out'] = 0
        # we make another balance dictionary because we need the first one to be fixed
        balances = {product_id:
                        {'opening_balance': opening_balances.get(product_id, 0.0)} for product_id in product_ids}
        moves =[]
        for move in stock_moves:
            in_out = None
            product_id = move['product_id']
            balance = balances[product_id]['opening_balance']

            # Adjust balance based on move type
            if move['picking_type_code'] in ['incoming', 'inventory'] or (
                    move['picking_type_code'] and move['location_dest_id'] == location_id):
                balance += move['qty_done']
                in_out = 'in'
                balance_dict[product_id]['total_in'] += move['qty_done']
            elif move['picking_type_code'] == 'outgoing' or (
                    move['picking_type_code'] and move['location_id'] == location_id):
                balance -= move['qty_done']
                in_out = 'out'
                balance_dict[product_id]['total_out'] += move['qty_done']
            elif move['picking_type_code'] is None:
                balance = move['qty_done']
            balances[product_id]['opening_balance'] = balance

            line = {
                'origin': move['reference'] or move['origin'],
                'move_date': move['date'],
                'product_id': self.env['product.product'].browse(move['product_id']),
                'in_qty': move['qty_done'] if in_out == 'in' else 0.0,
                'out_qty': move['qty_done'] if in_out == 'out' else 0.0,
                'balance': balance,
                # Category will be added later if needed
            }
            lines.append(line)

        # If report by category, add category to each line
        if report_by == 'product_category':
            category_sql = "SELECT id, categ_id FROM product_product WHERE id IN %s"
            self.env.cr.execute(category_sql, (tuple(product_ids),))
            category_mapping = {row[0]: row[1] for row in self.env.cr.fetchall()}
            for line in lines:
                line['category'] = category_mapping.get(line['product_id'])

        # ⏱️ Sort lines by move date
        sorted_lines = sorted(lines, key=lambda x: x['move_date'])

        sorted_lines.insert(0, balance_dict)
        if len(sorted_lines) < 2:
            # Add dummy line
            for product in sorted_lines[0].items():
                '''
                {'balance': 9908.0, 'in_qty': 0.0, 
                'move_date': datetime.datetime(2023, 12, 28, 5, 38, 20), 
                'origin': 'S02/INT/01518', 
                'out_qty': 162.0, 
                'product_id': product.product(20,)}
                '''
                line = {'product_id': self.env['product.product'].browse(product[0]),
                        'balance': 0.0,
                        'in_qty': -1,
                        'move_date': '',
                        'origin': '',
                        'out_qty': -1,
                        }
                sorted_lines.append(line)

        # 🏁 Return the sorted lines
        return sorted_lines

    @api.model
    def _get_report_values(self, docids, data=None):
        is_on_hand_only = data['form']['is_on_hand_only']
        report_by = data['form']['report_by']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        product_ids = self.env['product.product'].browse(data['form']['product_ids'])
        product_category_ids = self.env['product.category'].browse(data['form']['product_category_ids'])
        if data['form'].get('company_id'):
            company_id = self.env['res.company'].browse(data['form']['company_id'][0])
        else:
            company_id = False
        if data['form'].get('location_id'):
            location_id = self.env['stock.location'].browse(data['form']['location_id'][0])
        else:
            location_id = False
        if data['form'].get('warehouse_id'):
            warehouse_id = self.env['stock.warehouse'].browse(data['form']['warehouse_id'][0])
        else:
            warehouse_id = False
        if data['form'].get('location_id'):
            location_id = self.env['stock.location'].browse(data['form']['location_id'][0])
        else:
            location_id = False

        data = {
            'is_on_hand_only': is_on_hand_only,
            'report_by': report_by,
            'date_from': date_from,
            'date_to': date_to,
            'product_ids': product_ids,
            'company_id': company_id,
            'location_id': location_id,
            'warehouse_id': warehouse_id,
            'product_category_ids': product_category_ids
        }
        docargs = {
            'doc_model': 'stock.card.report',
            'data': data,
            'get_product_detail': self.get_product_detail,
            'get_on_hand_only': self.get_on_hand_only
        }
        return docargs
