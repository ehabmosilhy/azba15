from odoo import fields, models, api
from odoo.addons.azbah_trivial._packages.hijri_converter import Hijri, Gregorian
import re


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'
    vehicle_image = fields.Binary()
    license_number = fields.Char()
    insurance_status = fields.Selection([('valid', 'ساري'),
                                         ('expired', 'منتهي')])
    registration_type = fields.Char()
    license_start_date = fields.Date()
    license_end_date = fields.Date()
    inspection_date = fields.Date()
    ownership_date = fields.Date()
    license_start_date_hijri = fields.Char()
    license_end_date_hijri = fields.Char()
    inspection_date_hijri = fields.Char()
    ownership_date_hijri = fields.Char()

    def reverse_date(self, _date):
        _date = str(_date).replace('/', '-')
        _date_split = _date.split('-')
        return f"{_date_split[2]}-{_date_split[1]}-{_date_split[0]}"

    def validate(self, field_val):
        if isinstance(field_val, str):
            pattern = r"^(0?[1-9]|[12]\d|30)[/-](0?[1-9]|1[0-2])[/-]\d{4}$"
            if not re.match(pattern, field_val):
                return False
            else:
                return fields.Date.to_date(self.reverse_date(field_val))
        else:
            return field_val

    def convert(self, field_name, field_val):
        field_val = self.validate(field_val)
        if field_val:
            if 'hijri' in field_name:
                self[field_name.replace('_hijri', '')] = str(
                    Hijri(field_val.year, field_val.month, field_val.day).to_gregorian())
                self[field_name] = self[field_name].replace('-', '/')
                self._origin[field_name.replace('_hijri', '')] = self[field_name.replace('_hijri', '')]
            else:
                self[field_name + '_hijri'] = self.reverse_date(
                    Gregorian(field_val.year, field_val.month, field_val.day).to_hijri()).replace('-','/')
                self._origin[field_name + '_hijri'] = self[field_name + '_hijri']
            return True
        else:
            return False

    @api.onchange('license_start_date', 'license_end_date', 'inspection_date', 'ownership_date',
                  'license_start_date_hijri', 'license_end_date_hijri', 'inspection_date_hijri', 'ownership_date_hijri')
    def onchange_license_start_date(self):
        for _field in (
                'license_start_date', 'license_end_date', 'inspection_date', 'ownership_date',
                'license_start_date_hijri',
                'license_end_date_hijri', 'inspection_date_hijri', 'ownership_date_hijri'):
            if self[_field] != self._origin[_field]:
                field_name = _field
                field_val = self[_field]
                if self.convert(field_name, field_val):
                    self._origin[_field] = self[_field]
                    break
                else:
                    self[_field] = self._origin[_field]
                    message = f"{field_val} خطأ بالتاريخ "
                    return {'warning': {'title': "Warning", 'message': message, 'type': 'dialog'}}
