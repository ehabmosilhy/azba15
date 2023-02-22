from odoo import fields, models


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    license_number = fields.Char()
    license_start_date = fields.Date()
    license_end_date = fields.Date()
    inspection_date = fields.Date()
