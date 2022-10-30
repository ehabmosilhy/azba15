# -*- coding: utf-8 -*-

import logging
import random

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import pycompat
from lxml import etree


_logger = logging.getLogger(__name__)


class EmployeeCustody(models.Model):
    _name = 'employee.custody.request'
    _description = 'Custody Request'
    _inherit = ['mail.thread']
    _order = 'name'

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_custodies'):
            domain += [('id', '!=', -1)]
        elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.department_id', 'child_of',
                        self.env.user.employee_ids and
                        self.env.user.employee_ids[
                            0].department_id.id or [])]
        elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.user_id', '=', self.env.user.id)]
        elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
            domain += [('employee_id.user_id', '=', self.env.user.id)]
        else:
            domain += [('id', '=', -1)]
        res = super(EmployeeCustody, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_custodies'):
            domain += [('id', '!=', -1)]
        elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.department_id', 'child_of',
                        self.env.user.employee_ids and
                        self.env.user.employee_ids[
                            0].department_id.id or [])]
        elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.user_id', '=', self.env.user.id)]
        elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
            domain += [('employee_id.user_id', '=', self.env.user.id)]
        else:
            domain += [('id', '=', -1)]
        res = super(EmployeeCustody, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeCustody, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                      submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='employee_id']")
        for node in nodes:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                node.set('domain', str([('id', '!=', -1)]))
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                node.set('domain', str(['|', ('parent_id.user_id', '=', self.env.user.id), ('department_id', 'child_of',
                                                                                            self.env.user.employee_ids and
                                                                                            self.env.user.employee_ids[
                                                                                                0].department_id.id or [])]))
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                node.set('domain',
                         str(['|', ('parent_id.user_id', '=', self.env.user.id), ('user_id', '=', self.env.user.id)]))
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                node.set('domain', str([('user_id', '=', self.env.user.id)]))
            else:
                node.set('domain', str([('id', '=', -1)]))
        res['arch'] = etree.tostring(doc)
        return res
    # record.message_post(body='test', force_send=True,
    #                     subject='test', subtype='mt_comment', message_type='notification')
    name = fields.Char('رقم العهدة', readonly=True)
    Custody_date = fields.Date('تاريخ العهدة')
    employee_id = fields.Many2one('hr.employee', string='الموظف')
    product_id = fields.Many2one('product.product', string='المنتج')
    product_quantity = fields.Float('الكمية')
    stock_picking_id = fields.Many2one('stock.picking',string='المستودع')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('employee_validation', 'Validated By Employee'),
        ('cancel', 'Custody Canceled'),
    ],
        'Status', readonly=True, tracking=True, copy=False, default='draft')


    @api.model
    def _get_random_token(self):
        """Generate a 20 char long pseudo-random string of digits for barcode
        generation.

        A decimal serialisation is longer than a hexadecimal one *but* it
        generates a more compact barcode (Code128C rather than Code128A).

        Generate 8 bytes (64 bits) barcodes as 16 bytes barcodes are not
        compatible with all scanners.
         """
        return pycompat.text_type(random.getrandbits(64))

    barcode = fields.Char(default=_get_random_token, readonly=True, copy=False)

    _sql_constraints = [
        ('barcode_custody_uniq', 'unique(barcode, name)', "Barcode should be unique per custody")
    ]

    def _init_column(self, column_name):
        """ to avoid generating a single default barcoe when installing the module,
            we need to set the default row by row for this column """
        if column_name == "barcode":
            _logger.debug("Table '%s': setting default value of new column %s to unique values for each row",
                          self._table, column_name)
            self.env.cr.execute("SELECT id FROM %s WHERE barcode IS NULL" % self._table)
            custody_ids = self.env.cr.dictfetchall()
            query_list = [{'id': reg['id'], 'barcode': self._get_random_token()} for reg in custody_ids]
            query = 'UPDATE ' + self._table + ' SET barcode = %(barcode)s WHERE id = %(id)s;'
            self.env.cr._obj.executemany(query, query_list)
            self.env.cr.commit()

        else:
            super(EmployeeCustody, self)._init_column(column_name)


    def button_employee_validation(self):
        for record in self:
            if not self.env.user.id == self.employee_id.user_id.id:
                raise UserError("يجب ان يقوم بتأكيد الاستلام الموظف نفسه")

            record.state = 'employee_validation'


    def button_custody_cancel(self):
        for record in self:
            record.state = 'cancel'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.custody')
        result = super(EmployeeCustody, self).create(vals)

        return result