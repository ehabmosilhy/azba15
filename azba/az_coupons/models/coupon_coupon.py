# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

from datetime import datetime


class Coupon(models.Model):
    _inherit = 'coupon.coupon'

    paper_ids = fields.One2many('coupon.coupon.paper', 'coupon_book_id', string='Papers')

    @api.model
    def _generate_code(self):
        """Generate a code in the format YYMMSSS where:

        - YY: Last two digits of the year
        - MM: Two-digit month
        - SSS: A 3-digit serial number incremented from the last coupon.

        """
        current_year = datetime.now().year % 100  # Last two digits of the year
        current_month = datetime.now().month  # Two-digit month

        # Find the last generated code
        last_coupon = self.search([], order='id desc', limit=1)

        if last_coupon and last_coupon.code:
            last_serial = int(last_coupon.code[-3:])  # Extract the last 3 digits as serial number
            new_serial = last_serial + 1
        else:
            new_serial = 1  # Start with 001 if no previous coupon exists

        # Format the components into a string
        code = f"{current_year:02d}{current_month:02d}{new_serial:03d}"

        return code

    @api.model
    def create(self, vals):
        vals['code'] = self._generate_code()
        new_coupon = super(Coupon, self).create(vals)

        # Generate 20 coupon.coupon.paper records
        paper_vals_list = [{
            'code': f"{new_coupon.code}-{i:03d}",
            'coupon_book_id': new_coupon.id
        } for i in range(1, 21)]

        self.env['coupon.coupon.paper'].create(paper_vals_list)

        return new_coupon
