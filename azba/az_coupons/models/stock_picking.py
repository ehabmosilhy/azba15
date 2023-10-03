# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockMove(models.Model):
    _inherit = "stock.move"
    # TODO: Delete the following line
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")

    def _generate_serial_numbers(self, next_serial_count=False):
        """ This method will generate `lot_name` from a string (field
        `next_serial`) and create a move line for each generated `lot_name`.
        """
        self.ensure_one()
        lot_names = self.env['stock.production.lot'].generate_lot_names(self.next_serial,
                                                                        next_serial_count or self.next_serial_count)
        move_lines_commands = self._generate_serial_move_line_commands(lot_names)

        move_lines_commands = self.update_move_lines_commands(move_lines_commands)

        self.write({'move_line_ids': move_lines_commands})
        return True

    def update_move_lines_commands(self, move_lines_commands):
        indi = 0
        for line in self.picking_id.move_ids_without_package:
            if line.product_id == self.product_id:
                break
            indi += 1
        paper_count = self.picking_id.move_ids_without_package[indi].product_packaging_id.qty
        indi = 0
        coupon_serial = int(self.next_serial) * int(paper_count) - (paper_count-1)
        for line in move_lines_commands:
            line[2]['lot_name'] = coupon_serial + indi
            indi += 1
        return move_lines_commands



class StockPicking(models.Model):
    _inherit = "stock.picking"
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")

    def _put_in_pack(self, move_line_ids, create_package_level=True):
        packages = self.env['stock.quant.package']  # Initialize a set of packages
        for ml in move_line_ids:
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_is_zero(ml.qty_done, precision_digits=precision_digits):
                ml.qty_done = ml.product_uom_qty

            # Calculate the number of packages needed
            paper_count = self.move_ids_without_package.product_packaging_id.qty
            num_packages_needed = int(ml.qty_done / paper_count)
            remainder_qty = ml.qty_done % paper_count

            # Create packages based on the calculated quantity
            for _ in range(num_packages_needed):
                package = self.env['stock.quant.package'].create({})
                packages |= package  # Add the package to the set of packages

            # Update the move line with the remaining quantity
            ml.write({'qty_done': remainder_qty})

        # Distribute move lines among packages
        for package in packages:
            move_lines_to_pack = move_line_ids.filtered(lambda ml: not ml.result_package_id)
            if move_lines_to_pack:
                # Set the package type if not already set
                if not package.package_type_id:
                    package_type = move_lines_to_pack[0].move_id.product_packaging_id.package_type_id
                    if len(package_type) == 1:
                        package.package_type_id = package_type

                # Determine the default destination location and update location_dest_id
                default_dest_location = move_lines_to_pack._get_default_dest_location()
                move_lines_to_pack.location_dest_id = default_dest_location._get_putaway_strategy(
                    product=move_lines_to_pack[0].product_id,
                    quantity=sum(move_lines_to_pack.mapped('product_uom_qty')),
                    package=package)
                move_lines_to_pack.write({'result_package_id': package.id})

        if create_package_level:
            # Create package level records
            for pick in self:
                package_level = self.env['stock.package_level'].create({
                    'package_id': packages.ids,
                    'picking_id': pick.id,
                    'location_id': False,
                    'location_dest_id': move_line_ids.mapped('location_dest_id').id,
                    'move_line_ids': [(6, 0, move_line_ids.ids)],
                    'company_id': pick.company_id.id,
                })

        return packages
