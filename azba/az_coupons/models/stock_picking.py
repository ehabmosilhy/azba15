# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"
    coupon_purchase_id = fields.Many2one('coupon.purchase', string="coupon Purchase")

    def update_move_lines_commands(self, move_lines_commands):
        indi = 0
        for line in self.picking_id.move_ids_without_package:
            if line.product_id == self.product_id:
                break
            indi += 1
        paper_count = self.picking_id.move_ids_without_package[indi].product_packaging_id.qty
        indi = 0
        coupon_serial = int(self.next_serial) * int(paper_count) - (paper_count - 1)
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
        #  /\_/\
        # ( ◕‿◕ )
        #  >   <

        # Calculate the number of packages needed
        demand = int(self.move_ids_without_package[0].quantity_done)
        paper_count = int(self.move_ids_without_package[0].product_packaging_id.qty)
        num_packages_needed = int(demand / paper_count)
        move_line_ids = [move_line_ids[i:i + paper_count] for i in range(0, len(move_line_ids), paper_count)]
        for i in range(num_packages_needed):
            pack = self._put_in_pack(move_line_ids[i], create_package_level=create_package_level)
        return pack

    def button_validate(self):
        p = self.package_level_ids
        if not p:
            self.add_packs()
        res = super(StockPicking, self).button_validate()

        return True

    def add_packs(self):
        lines = []
        for line in self.move_line_ids_without_package:
            line_dict = (0, 0, {
                'package_id': self.env['stock.quant.package'].search([('name', '=', line.lot_id.name)]).id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'is_done': True,
            })
            lines.append(line_dict)
        self.write({'package_level_ids': lines})


class StockMoveLine(models.Model):
    _inherit = 'stock.picking'

    # @api.onchange('move_line_ids_without_package')
    # def _onchange_lot_id(self):
    #     if self.move_line_ids:
    #         for line in self.move_line_ids:
    #             if not isinstance(self.id, int):
    #                 self_id = int(str(self.id).split('_')[1])
    #             else:
    #                 self_id = int(self.id)
    #
    #             if not isinstance(line.id, int):
    #                 line_id = int(str(line.id).split('_')[1])
    #             else:
    #                 line_id = int(line.id)
    #
    #             if line.product_id == self.product_id and line_id > self_id:
    #                 next_id = str(int(self.lot_id.name) + 1)
    #
    #                 next_lot = self.env['stock.production.lot'].search([('name', '=', next_id)], limit=1)
    #                 previous_lot_name = line.lot_id.name
    #                 next_lot_name= self.env['stock.production.lot'].search([('name', '=', next_id)], limit=1).name
    #                 line.lot_id = next_lot

    @api.onchange('move_line_ids_without_package')
    def _onchange_lot_id(self):
        if self.move_line_ids:
            for i in range(len(self.move_line_ids)):
                current_line = self.move_line_ids[i]
                if not isinstance(self.id, int):
                    self_id = int(str(self.id).split('_')[1])
                else:
                    self_id = int(self.id)

                if not isinstance(current_line.id, int):
                    current_line_id = int(str(current_line.id).split('_')[1])
                else:
                    current_line_id = int(current_line.id)

                if current_line.product_id == self.product_id and current_line_id > self_id:
                    for j in range(i + 1, len(self.move_line_ids)):
                        next_line = self.move_line_ids[j]
                        if next_line.product_id == current_line.product_id:
                            next_id = str(int(current_line.lot_id.name) + 1)
                            next_lot = self.env['stock.production.lot'].search([('name', '=', next_id)], limit=1)
                            if next_lot:
                                next_line.lot_id = next_lot
