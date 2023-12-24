# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Akhilesh N S(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, api


class ValidateLotNumber(models.Model):
    _name = 'serial_no.validation'

    @api.model
    def validate_lots(self, lots, pos_config_id):
        processed = []
        LotObj = self.env['stock.production.lot']
        for lot in lots:
            lot_id = LotObj.search([('name', '=', lot)], limit=1)
            # Ehab: Check qty in this location
            if lot_id:
                picking_type_id = self.env['pos.config'].search([('id', '=', pos_config_id)]).picking_type_id
                location_id = picking_type_id.default_location_src_id

                stock_quant = self.env['stock.quant'].search(
                    [('lot_id', '=', lot_id.id), ('location_id', '=', location_id.id)])
                qty = stock_quant.quantity if stock_quant else 0
            else:
                qty = 0
            try:
                if qty > 0 and lot not in processed:
                    processed.append(lot)
                    continue
                else:
                    if lot in processed:
                        return ['duplicate', lot]
                    else:
                        return ['no_stock', lot]
            except Exception:
                return ['except', lot]
        return True
