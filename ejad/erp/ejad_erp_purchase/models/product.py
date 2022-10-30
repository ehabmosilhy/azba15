# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    purchase_method = fields.Selection([
        ('purchase', 'حسب  الكميات المطلوبة'),
        ('receive', 'حسب الكميات المستلمة'),
    ], string="طريقة التثبت",
        help="On ordered quantities: control bills based on ordered quantities.\n"
             "On received quantities: control bills based on received quantity.", default="receive")
    tracking = fields.Selection([
        ('serial', 'حسب الرقم التسلسلي'),
        ('lot', 'حسب الرزمة'),
        ('none', 'لا يوجد تتبع')], string="طريقة التتبع", default='none', required=True)
    is_assert = fields.Boolean(string="هل يحتاج عهدة ؟")
    is_outcome = fields.Boolean(string='مخرج', default=False)

    @api.constrains('is_assert', 'tracking')
    def _check_assert(self):
        if self.is_assert and self.tracking not in ['serial', 'lot']:
            raise ValidationError(_("لا بد من تعيين تتبّع لمنتج معرّف كأصل !"))


class ProductCategory(models.Model):
    _inherit = "product.category"

    department_id = fields.Many2one('hr.department', string="الإدارة المعتمدة للطلبات")
    procurement_moderator_id = fields.Many2one('hr.employee', string="المشرف المعتمد للطلبات")
    security_group_id = fields.Many2one('res.groups', domain=[('name', 'like', 'مشرف')], string="المشرف المعتمد")
    request_type = fields.Selection([
        ('product', 'طلب مواد'),
        ('project', 'طلب مشروع'),
    ], string="نوع الطلب")

    @api.model
    def create(self, vals):
        res = super(ProductCategory, self).create(vals)
        request_type_parent = self.env['product.category'].search([('id','=',vals['parent_id'])]).request_type
        if request_type_parent:
            if vals['request_type'] != request_type_parent:
                raise ValidationError(_("لا بد من تطابق نوع الطلب مع الفئة الأم !"))
        return res


    def write(self, vals):
        res = super(ProductCategory, self).write(vals)
        if self.parent_id.request_type:
            if self.request_type:
                if self.request_type != self.parent_id.request_type:
                    raise ValidationError(_("لا بد من تطابق نوع الطلب مع الفئة الأم !"))
        return res