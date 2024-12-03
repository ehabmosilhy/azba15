from odoo import models, api, fields
from odoo.tools import float_round

class ProductHistoryReport(models.AbstractModel):
    _name = 'report.az_inventory.report_product_history'
    _description = 'Product History Report'

    def _get_target_locations(self, doc):
        """Get target locations based on either warehouse or specific location."""
        if doc.warehouse_id:
            return self.env['stock.location'].search([
                '|',
                ('id', '=', doc.warehouse_id.lot_stock_id.id),
                ('location_id', 'child_of', doc.warehouse_id.lot_stock_id.id)
            ])
        elif doc.location_id:
            return doc.location_id
        return self.env['stock.location']

    def _get_stock_moves(self, doc):
        """Retrieve stock moves based on the wizard parameters."""
        domain = [
            ('date', '>=', doc.start_date),
            ('date', '<=', doc.end_date),
            ('state', '=', 'done'),
        ]

        target_locations = self._get_target_locations(doc)
        if target_locations:
            domain.extend([
                '|', ('location_id', 'in', target_locations.ids),
                ('location_dest_id', 'in', target_locations.ids),
            ])

        if doc.product_id:
            domain.append(('product_id', '=', doc.product_id.id))

        return self.env['stock.move.line'].search(
            domain,
            order='date asc'
        )

    def _get_current_stock(self, doc):
        """Retrieve current stock quantities based on the wizard parameters."""
        domain = [
            ('location_id.usage', '=', 'internal'),
        ]

        target_locations = self._get_target_locations(doc)
        if target_locations:
            domain.append(('location_id', 'in', target_locations.ids))

        if doc.product_id:
            domain.append(('product_id', '=', doc.product_id.id))

        return self.env['stock.quant'].search(domain)

    def _get_product_data(self, doc):
        """Get all product movements and balances."""
        target_locations = self._get_target_locations(doc)
        
        # Convert dates to datetime for comparison
        start_datetime = fields.Datetime.from_string(doc.start_date)
        end_datetime = fields.Datetime.from_string(doc.end_date)
        
        # Get current quantities from stock.quant
        quant_domain = [
            ('location_id', 'in', target_locations.ids),
            ('quantity', '!=', 0),  # Only products with quantities
        ]
        if doc.product_id:
            quant_domain.append(('product_id', '=', doc.product_id.id))
        
        quants = self.env['stock.quant'].read_group(
            quant_domain,
            ['product_id', 'quantity:sum'],
            ['product_id']
        )
        
        if not quants:
            return []
            
        # Create a map of product_id to current quantity
        current_qty_map = {
            q['product_id'][0]: q['quantity'] 
            for q in quants
        }
        
        # Get all products that have quantities
        product_ids = list(current_qty_map.keys())
        products = self.env['product.product'].browse(product_ids)
        
        # Get all moves up to end date (for period and post-period)
        move_domain = [
            ('state', '=', 'done'),
            ('product_id', 'in', product_ids),
        ]
        
        moves = self.env['stock.move.line'].search(move_domain, order='date asc')
        
        result = []
        for product in products:
            # Get moves within period
            period_moves = moves.filtered(
                lambda m: m.product_id == product and
                         start_datetime <= fields.Datetime.from_string(m.date) <= end_datetime
            )
            
            # Get moves after period end until now
            post_period_moves = moves.filtered(
                lambda m: m.product_id == product and
                         fields.Datetime.from_string(m.date) > end_datetime
            )
            
            # Calculate ins and outs during period
            period_ins = sum(period_moves.filtered(
                lambda m: m.location_dest_id.id in target_locations.ids
            ).mapped('qty_done'))
            
            period_outs = sum(period_moves.filtered(
                lambda m: m.location_id.id in target_locations.ids and 
                         m.location_dest_id.id not in target_locations.ids
            ).mapped('qty_done'))
            
            # Calculate ins and outs after period
            post_ins = sum(post_period_moves.filtered(
                lambda m: m.location_dest_id.id in target_locations.ids
            ).mapped('qty_done'))
            
            post_outs = sum(post_period_moves.filtered(
                lambda m: m.location_id.id in target_locations.ids and 
                         m.location_dest_id.id not in target_locations.ids
            ).mapped('qty_done'))
            
            # Current quantity from stock.quant
            current_qty = current_qty_map.get(product.id, 0.0)
            
            # End of period balance = current - post_ins + post_outs
            end_balance = current_qty - post_ins + post_outs
            
            # Initial balance = end_balance - period_ins + period_outs
            initial_balance = end_balance - period_ins + period_outs
            
            result.append({
                'product_code': product.product_tmpl_id.code or '',
                'product_name': product.name,
                'initial_balance': initial_balance,
                'ins': period_ins,
                'outs': period_outs,
                'current_balance': end_balance,
                'uom': product.uom_id.name,
            })
            
        # Sort results by product code then name
        return sorted(result, key=lambda x: (x['product_code'] or '', x['product_name']))

    def _get_initial_balance(self, product, start_date, target_locations):
        """Calculate the initial balance for a product before the start date."""
        domain = [
            ('date', '<', start_date),
            ('state', '=', 'done'),
            ('product_id', '=', product.id),
        ]
        
        moves = self.env['stock.move.line'].search(domain)
        
        ins = sum(moves.filtered(
            lambda m: m.location_dest_id.id in target_locations.ids
        ).mapped('qty_done'))
        
        outs = sum(moves.filtered(
            lambda m: m.location_id.id in target_locations.ids and 
                     m.location_dest_id.id not in target_locations.ids
        ).mapped('qty_done'))
        
        return ins - outs

    @api.model
    def _get_report_values(self, docids, data=None):
        """Generate values for rendering the report template."""
        if not data:
            data = {}
            
        # Get the wizard record
        if docids:
            docs = self.env['product.history.wizard'].browse(docids)
        else:
            # If no docids, try to get from data
            docs = self.env['product.history.wizard'].browse(data.get('ids', []))
            
        # If still no docs and we have form data, create a temporary wizard
        if not docs and data.get('form'):
            temp_wizard = self.env['product.history.wizard'].new(data.get('form'))
            docs = temp_wizard
            
        # Get the wizard record to use (either from docs or temp_wizard)
        wizard_record = docs[0] if docs else False
        
        if not wizard_record:
            # Return empty data if no wizard record found
            return {
                'doc_ids': docids,
                'doc_model': 'product.history.wizard',
                'docs': docs,
                'products': [],
                'precision': self.env['decimal.precision'].precision_get('Product Unit of Measure'),
            }
            
        return {
            'doc_ids': docids,
            'doc_model': 'product.history.wizard',
            'docs': docs,
            'products': self._get_product_data(wizard_record),
            'precision': self.env['decimal.precision'].precision_get('Product Unit of Measure'),
        }
