# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    # Replace the original many2one field with many2many
    service_type_id = fields.Many2many(
        'fleet.service.type', 
        'fleet_service_type_rel',  # Relation table name
        'service_id',              # Column1 name (reference to this model)
        'type_id',                # Column2 name (reference to fleet.service.type)
        string='Service Types',
        required=True,
    )

    # Override name_get to show all service types
    def name_get(self):
        result = []
        for record in self:
            service_types = record.service_type_id.mapped(lambda r: '[%s] %s' % (r.code or '', r.name))
            name = ' + '.join(service_types) or _('New Service')
            result.append((record.id, name))
        return result
