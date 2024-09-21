# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import datetime


class Coupon(models.Model):
    _name = 'az.coupon'

    name = fields.Char(string='Name', readonly=True)
    page_count = fields.Integer(string='Page Count', readonly=True)

    code = fields.Char(string='Code', readonly=True)
    page_ids = fields.One2many('az.coupon.page', 'coupon_book_id', string='Pages')
    receipt_number = fields.Char(string='Receipt Number', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', readonly=True)
    partner_id = fields.Many2one(related='pos_order_id.partner_id', string='Partner', readonly=True)
    product_id = fields.Many2one(related='pos_order_id.lines.product_id', string='Product', readonly=True)

    available_count = fields.Integer(compute='_compute_available_count', string='Available')
    used_count = fields.Integer(compute='_compute_available_count', string='Used')

    partner_name = fields.Char(related='partner_id.name', string='Partner Name', readonly=True)
    partner_code = fields.Char(related='partner_id.code', string='Partner Code', readonly=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('page_ids')
    def _compute_available_count(self):
        # get the count of pages where state = 'valid'
        for coupon in self:
            coupon.available_count = self.env['az.coupon.page'].search_count(
                [('coupon_book_id', '=', coupon.id), ('state', '=', 'valid')]
            )
            coupon.used_count = self.env['az.coupon.page'].search_count(
                [('coupon_book_id', '=', coupon.id), ('state', '=', 'used')]
            )

    state = fields.Selection([
        ('valid', 'New'),
        ('partial', 'Partially Used'),
        ('used', 'Used'),
    ], required=True, default='valid')

    @api.model
    def _default_session(self):
        return self.env['pos.session'].search([], limit=1)

    session_id = fields.Many2one('pos.session', string='Session', default=_default_session)

    @api.model
    def _generate_code(self):
        """Generate a code in the format YYMMSSSS where:
        - YY: Last two digits of the year
        - MM: Two-digit month
        - SSSS: A 4-digit serial number incremented from the last coupon.
        """
        current_year = datetime.now().year % 100  # Last two digits of the year
        current_month = datetime.now().month  # Two-digit month

        # Find the last generated code
        last_coupon = self.search([], order='id desc', limit=1)

        if last_coupon and last_coupon.code:
            last_serial = int(last_coupon.code[-4:])  # Extract the last 4 digits as serial number
            new_serial = last_serial + 1
        else:
            new_serial = 1  # Start with 0001 if no previous coupon exists

        # Format the components into a string
        code = f"{current_year:02d}{current_month:02d}{new_serial:04d}"

        return code

    @api.model
    def create(self, vals):
        vals['code'] = self._generate_code()
        new_coupon = super(Coupon, self).create(vals)

        page_count = vals.get('page_count')
        # Generate 20 az.coupon.page records
        page_vals_list = [{
            'code': f"{new_coupon.code}-{i:03d}",
            'coupon_book_id': new_coupon.id
        } for i in range(1, page_count + 1)]

        self.env['az.coupon.page'].create(page_vals_list)

        return new_coupon

    def write(self, vals):
        result = super(Coupon, self).write(vals)
        if 'active' in vals:
            if vals['active']:
                # Unarchiving
                pages = self.env['az.coupon.page'].search([('coupon_book_id', '=', self.id), ('active', '=', False)])
                pages.write({'active': True})

            else:
                # Archiving
                pages = self.env['az.coupon.page'].search([('coupon_book_id', '=', self.id), ('active', '=', True)])
                pages.write({'active': False})
        return result
