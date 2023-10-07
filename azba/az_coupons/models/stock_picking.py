# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models,_
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"
    # TODO: Delete the following line
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")

    # def _generate_serial_numbers(self, next_serial_count=False):
    #     """ This method will generate `lot_name` from a string (field
    #     `next_serial`) and create a move line for each generated `lot_name`.
    #     """
    #     self.ensure_one()
    #     lot_names = self.env['stock.production.lot'].generate_lot_names(self.next_serial,
    #                                                                     next_serial_count or self.next_serial_count)
    #     move_lines_commands = self._generate_serial_move_line_commands(lot_names)
    #
    #     move_lines_commands = self.update_move_lines_commands(move_lines_commands)
    #
    #     self.write({'move_line_ids': move_lines_commands})
    #     return True

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

    def action_put_in_pack(self):
        self.ensure_one()
        if self.state not in ('done', 'cancel'):
            picking_move_lines = self.move_line_ids
            if (
                    not self.picking_type_id.show_reserved
                    and not self.immediate_transfer
                    and not self.env.context.get('barcode_view')
            ):
                picking_move_lines = self.move_line_nosuggest_ids

            move_line_ids = picking_move_lines.filtered(lambda ml:
                                                        float_compare(ml.qty_done, 0.0,
                                                                      precision_rounding=ml.product_uom_id.rounding) > 0
                                                        and not ml.result_package_id
                                                        )
            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                                                                     precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(
                    ml.qty_done, 0.0,
                    precision_rounding=ml.product_uom_id.rounding) == 0)
            if move_line_ids:
                res = self._pre_put_in_pack_hook(move_line_ids)
                if not res:
                    # 👇 ______ (｡◔‿◔｡) ________
                    res = self._put_in_pack_multi(move_line_ids)
                return res
            else:
                raise UserError(_("Please add 'Done' quantities to the picking to create a new pack."))

    def _put_in_pack_multi(self, move_line_ids, create_package_level=True):
        # Calculate the number of packages needed
        demand =int(self.move_ids_without_package.quantity_done)
        paper_count = int(self.move_ids_without_package.product_packaging_id.qty)
        num_packages_needed = int(demand / paper_count)
        # list of move_line_ids and I want to split the items into groups of x and create a dictionary with keys (0,1,2,...) each key has a value of a group
        move_line_ids = [move_line_ids[i:i + paper_count] for i in range(0, len(move_line_ids), paper_count)]
        for i in range(num_packages_needed):
            pack=self._put_in_pack(move_line_ids[i], create_package_level=create_package_level)
        return pack

    # def _put_in_pack(self, move_line_ids, create_package_level=True):
    #     # Calculate the number of packages needed
    #     demand = self.move_ids_without_package.quantity_done
    #     paper_count = self.move_ids_without_package.product_packaging_id.qty
    #     num_packages_needed = int(demand / paper_count)
    #
    #     package = False
    #     for pick in self:
    #         move_lines_to_pack = self.env['stock.move.line']
    #
    #         precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
    #         if float_is_zero(move_line_ids[0].qty_done, precision_digits=precision_digits):
    #             for line in move_line_ids:
    #                 line.qty_done = line.product_uom_qty
    #         i = 0
    #         for ml in move_line_ids:
    #             if i%paper_count == 0:
    #                 package = self.env['stock.quant.package'].create({})
    #             i=i+1
    #             if float_compare(ml.qty_done, ml.product_uom_qty,
    #                              precision_rounding=ml.product_uom_id.rounding) >= 0:
    #                 move_lines_to_pack |= ml
    #             else:
    #                 quantity_left_todo = float_round(
    #                     ml.product_uom_qty - ml.qty_done,
    #                     precision_rounding=ml.product_uom_id.rounding,
    #                     rounding_method='HALF-UP')
    #                 done_to_keep = ml.qty_done
    #                 new_move_line = ml.copy(
    #                     default={'product_uom_qty': 0, 'qty_done': ml.qty_done})
    #                 vals = {'product_uom_qty': quantity_left_todo, 'qty_done': 0.0}
    #                 if pick.picking_type_id.code == 'incoming':
    #                     if ml.lot_id:
    #                         vals['lot_id'] = False
    #                     if ml.lot_name:
    #                         vals['lot_name'] = False
    #                 ml.write(vals)
    #                 new_move_line.write({'product_uom_qty': done_to_keep})
    #                 move_lines_to_pack |= new_move_line
    #         if not package.package_type_id:
    #             package_type = move_lines_to_pack.move_id.product_packaging_id.package_type_id
    #             if len(package_type) == 1:
    #                 package.package_type_id = package_type
    #         if len(move_lines_to_pack) == 1:
    #             default_dest_location = move_lines_to_pack._get_default_dest_location()
    #             move_lines_to_pack.location_dest_id = default_dest_location._get_putaway_strategy(
    #                 product=move_lines_to_pack.product_id,
    #                 quantity=move_lines_to_pack.product_uom_qty,
    #                 package=package)
    #         move_lines_to_pack.write({
    #             'result_package_id': package.id,
    #         })
    #         if create_package_level:
    #             package_level = self.env['stock.package_level'].create({
    #                 'package_id': package.id,
    #                 'picking_id': pick.id,
    #                 'location_id': False,
    #                 'location_dest_id': move_lines_to_pack.mapped('location_dest_id').id,
    #                 'move_line_ids': [(6, 0, move_lines_to_pack.ids)],
    #                 'company_id': pick.company_id.id,
    #             })
    #     return package

    '''
    def _put_in_pack(self, move_line_ids, create_package_level=True):
        packages = self.env['stock.quant.package']  # Initialize a set of packages
        for ml in move_line_ids:
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_is_zero(ml.qty_done, precision_digits=precision_digits):
                ml.qty_done = ml.product_uom_qty

        # Calculate the number of packages needed
        demand = self.move_ids_without_package.quantity_done
        paper_count = self.move_ids_without_package.product_packaging_id.qty
        num_packages_needed = int(demand / paper_count)
        remainder_qty = demand % paper_count

        # Create packages based on the calculated quantity
        for _ in range(num_packages_needed):
            package = self.env['stock.quant.package'].create({})
            packages |= package  # Add the package to the set of packages

            # Update the move line with the remaining quantity
            # ml.write({'qty_done': remainder_qty})

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
    '''