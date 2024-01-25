from odoo import models, fields, api
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _fix_date(self, _move, picking, picking_out, _date):
        picking.date = _date
        picking.date_done
        picking.scheduled_date
        picking_out.date
        picking_out.date_done
        picking_out.scheduled_date
        _move.date = _date

    def get_serial(self, direction):
        last_picking = self.env['stock.picking'].search([
            ('name', 'like', f'S01/{direction.upper()}/X%')
        ], order='name desc', limit=1)

        if last_picking:
            last_count = int(last_picking.name.split('X')[-1])
            count = last_count + 1
        else:
            count = 1

        picking_name = f"S01/{direction.upper()}/X{str(count).zfill(4)}"
        return picking_name

    def action_solve_all_invoices(self):
        excluded_ids = sorted([252615,309713,197524,188653,187511,178693,176535,174604,161080,198559,154013,268762,132386,267511,267220,267210,266861,266376,266369,122170,121320,264511,102956,88269,79262,72766,261018,257539,36083,252272,251164])
        bills = self.env['account.move'].search([('invoice_origin', '=', False),
                                                 ('batch_purchase_id', '=', False)
                                                 ,('state', '=', 'posted')
                                                 ,('invoice_date', '!=', False)
                                                 ,('journal_id', '=',2) # Journal for Vendor Bills
                                                 , ('id', 'not in',excluded_ids )
                                                 ])
        for record in bills:
            try:
                record.action_create_stock_transfer(record)
            except Exception as e:
                # Roll back the transaction in case of an exception
                self.env.cr.rollback()
                print(f"Invoice: {record.name} - {record.id} - Error: {str(e)}")
                continue


    def action_create_stock_transfer(self, rec=None):

        if not rec:
            rec=self
        for record in rec:
            if not record.invoice_origin and not record.batch_purchase_id:
                    # Access move lines associated with the account move
                    move_lines = record.invoice_line_ids
                    picking_type = self.env['stock.picking.type'].search([], limit=1)  # Adjust the domain as needed

                    # Create the initial stock picking (Vendor to S1)
                    picking_vals = {
                        'move_type': 'direct',
                        'picking_type_id': picking_type.id,
                        'partner_id': record.partner_id.id,
                        'location_id': 4,  # Vendor location
                        'location_dest_id': 536,  # S1 location
                        'date': record.invoice_date,
                        'date_done': record.invoice_date,
                        'scheduled_date': record.invoice_date,
                        'origin': record.name,
                        'name': self.get_serial('IN')
                    }

                    picking = self.env['stock.picking'].create(picking_vals)
                    # print (f'record_id {record.id}')
                    # Create stock moves for the initial picking
                    for line in move_lines:
                        self.env['stock.move'].create({
                            'name': line.name or 'Vendor to S1',
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'product_uom_qty': line.quantity,
                            'quantity_done': line.quantity,
                            'date': record.invoice_date,
                            'date_deadline': record.invoice_date,
                            'picking_id': picking.id,
                            'location_id': picking.location_id.id,
                            'location_dest_id': picking.location_dest_id.id,
                        })

                    # Confirm and mark as done the initial picking
                    picking.action_confirm()
                    picking.action_assign()

                    picking.button_validate()

                    del picking_vals['partner_id']
                    # Create the subsequent stock picking (S1 to Production)
                    picking_vals.update({
                        'picking_type_id': 552,  # (الرئيسى-القديمة) (MAIN-OLD) التسلسل للخارج
                        'location_id': 536,  # S1 location
                        'location_dest_id': 5,  # Production location
                        'date': fields.Datetime.add(record.invoice_date, hours=1),
                        'date_done': fields.Datetime.add(record.invoice_date, hours=1),
                        'scheduled_date': fields.Datetime.add(record.invoice_date, hours=1),
                        'name': self.get_serial('OUT')
                    })
                    picking_out = self.env['stock.picking'].create(picking_vals)

                    # Create stock moves for the subsequent picking
                    for line in move_lines:
                        _move = self.env['stock.move'].create({
                            'name': line.name or 'S1 to Production',
                            'product_id': line.product_id.id,
                            'product_uom': line.product_uom_id.id,
                            'quantity_done': line.quantity,
                            'product_uom_qty': line.quantity,
                            'date': fields.Datetime.add(record.invoice_date, hours=1),
                            'picking_id': picking_out.id,
                            'location_id': picking_out.location_id.id,
                            'location_dest_id': picking_out.location_dest_id.id,
                        })

                    # Confirm and mark as done the subsequent picking
                    picking_out.action_confirm()
                    picking_out.action_assign()
                    picking_out.button_validate()

                    record.invoice_origin = picking_out.name
                    self._fix_date(_move, picking, picking_out, record.invoice_date)

