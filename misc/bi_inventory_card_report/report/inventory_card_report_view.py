# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
import operator
from datetime import datetime, date
from odoo.tools.float_utils import float_round


class StockCardReportTemplate(models.AbstractModel):
    _name = 'report.bi_inventory_card_report.inventory_card_report_template'
    _description = 'Stock Card Report Template'

    # def _get_product_detail(self, data):
    #     # 📅 Retrieve date range for filtering stock moves
    #     start_date_data = data.get('date_from')
    #     end_date_data = data.get('date_to')
    #     location_id = data.get('location_id') and data.get('location_id').id
    #     warehouse_id = data.get('warehouse_id') and data.get('warehouse_id').id
    #
    #     # 🆔 Depending on the report type, fetch product IDs
    #     report_by = data.get('report_by')
    #     if report_by == 'product_category':
    #         product_category_ids = data.get('product_category_ids')
    #         domain = [('categ_id', 'in', product_category_ids.ids)]
    #     else:
    #         product_ids = data.get('product_ids')
    #         domain = [('id', 'in', product_ids.ids)]
    #
    #     # 🛒 Fetch all products at once
    #     products = self.env['product.product'].search(domain)
    #
    #     # 🔄 Fetch all relevant stock moves at once, filtering by date and state
    #     stock_move_domain = [
    #         ('move_id.date', '>=', start_date_data),
    #         ('move_id.date', '<=', end_date_data),
    #         ('state', '=', 'done'),
    #         ('product_id', 'in', products.ids),
    #         '|', ('location_id', '=', location_id), ('location_dest_id', '=', location_id)
    #     ]
    #     if warehouse_id:
    #         stock_move_domain += ['|', ('move_id.warehouse_id', '=', warehouse_id),
    #                               ('move_id.warehouse_id', '=', False)]
    #     all_stock_moves = self.env['stock.move.line'].search(stock_move_domain)
    #
    #     # 📊 Process stock moves to calculate balance and prepare report lines
    #     lines = []
    #     for product in products:
    #         # Filter moves for the current product without querying the database
    #         product_moves = all_stock_moves.filtered(lambda m: m.product_id.id == product.id)
    #         balance = 0.0
    #
    #         for move in product_moves:
    #             move_date = move.date
    #             qty_done = move.qty_done
    #
    #             # Adjust balance based on move type
    #             if move.location_id.usage == 'inventory' or move.picking_type_id.code == 'incoming':
    #                 balance += qty_done
    #             elif move.picking_type_id.code == 'outgoing':
    #                 balance -= qty_done
    #
    #             # 📝 Create a report line
    #             line = {
    #                 'origin': move.origin or move.reference,
    #                 'move_date': move_date,
    #                 'product_id': move.product_id,
    #                 'in_qty': qty_done if balance >= 0 else 0.0,
    #                 'out_qty': -qty_done if balance < 0 else 0.0,
    #                 'balance': balance,
    #                 'category': move.product_id.categ_id if report_by == 'product_category' else None
    #             }
    #             lines.append(line)
    #
    #     # ⏱️ Sort lines by move date
    #     sorted_lines = sorted(lines, key=lambda x: x['move_date'])
    #
    #     # 🏁 Return the sorted lines
    #     return sorted_lines

    def _get_final_balance(self, location_id, start_date_data, product_ids):
        final_balance_sql = """
          SELECT
              product_id,
              quantity
          FROM
              stock_quant
          WHERE
              product_id IN %s
              and location_id = %s
          """
        final_balance_params = (tuple(product_ids), location_id)
        self.env.cr.execute(final_balance_sql, final_balance_params)
        return {row[0]: row[1] for row in self.env.cr.fetchall()}

    def _get_initial_balance(self, location_id, start_date_data, product_ids):
        initial_balance_sql = """
          SELECT
              product_id,
              SUM(CASE WHEN location_dest_id = %s THEN product_qty ELSE 0 END) -
              SUM(CASE WHEN location_id = %s THEN product_qty ELSE 0 END) as initial_balance
          FROM
              stock_move
          WHERE
              date < %s AND
              state = 'done' AND
              product_id IN %s
          GROUP BY
              product_id
          """
        initial_balance_params = (location_id, location_id, start_date_data, tuple(product_ids))
        self.env.cr.execute(initial_balance_sql, initial_balance_params)
        return {row[0]: row[1] for row in self.env.cr.fetchall()}

    def _get_product_detail(self, data):
        # Retrieve date range for filtering stock moves
        start_date_data = data.get('date_from')
        end_date_data = data.get('date_to')
        location_id = data.get('location_id') and data.get('location_id').id
        warehouse_id = data.get('warehouse_id') and data.get('warehouse_id').id

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

        # Get the initial balance for each product
        initial_balances = self._get_initial_balance(location_id, start_date_data, product_ids)
        final_balances = self._get_final_balance(location_id, start_date_data, product_ids)

        balance_dict = {product_id:
                            {'initial_balance': initial_balances.get(product_id, 0.0),
                             'final_balance': final_balances.get(product_id, 0.0)} for product_id in product_ids
                        }

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

        lines = []
        balance_dict = {product_id:
                            {'initial_balance': initial_balances.get(product_id, 0.0),
                             'final_balance': final_balances.get(product_id, 0.0)
                             } for product_id in product_ids}
        for product_id in product_ids:
            balance_dict[product_id]['total_in'] = 0
            balance_dict[product_id]['total_out'] = 0
        # we make another balance dictionary because we need the first one to be fixed
        balances = {product_id:
                        {'initial_balance': initial_balances.get(product_id, 0.0)} for product_id in product_ids}
        for move in stock_moves:
            in_out = None
            product_id = move['product_id']
            balance = balances[product_id]['initial_balance']

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
            elif move['picking_type_code'] == None:
                balance = move['qty_done']
            balances[product_id]['initial_balance'] = balance

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
        # balance_dict[product_id]['final_balance'] = balance_dict[product_id]['initial_balance'] + \
        #                                             balance_dict[product_id]['total_in'] - balance_dict[product_id][
        #                                                 'total_out']

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
        if len(sorted_lines)<2:
            for product in sorted_lines[0].items():

                '''
                {'balance': 9908.0, 'in_qty': 0.0, 
                'move_date': datetime.datetime(2023, 12, 28, 5, 38, 20), 
                'origin': 'S02/INT/01518', 
                'out_qty': 162.0, 
                'product_id': product.product(20,)}
                '''
                line={'product_id':self.env['product.product'].browse(product[0]),
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
            'get_product_detail': self._get_product_detail,
        }
        return docargs
