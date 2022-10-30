# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = 'stock.picking'
    _description = 'Stock Picking'
    _inherit = ['stock.picking']
    _order = 'name'

    purchase_representative_id = fields.Many2one(related="purchase_requisition_id.employee_id",
                                                 string='مندوب المشتريات')
    employee_id = fields.Many2one(related="purchase_requisition_id.employee_id", string='الموظف')
    purchase_requisition_id = fields.Many2one('purchase.requisition.request')
    show_employee_validate = fields.Boolean('show employee validation', compute='_compute_show_validate')
    quality_approved_by_employee = fields.Boolean('Quality Approved By Employee')
    quality_approved_by_stock_manger = fields.Boolean('Quality Approved By Stock Manager')
    quality_refused_by_employee = fields.Boolean('Quality Refused By Employee')
    quality_refused_by_stock_manger = fields.Boolean('Quality Refused By Stock Manager')
    quality_approved_by_purchase_representative = fields.Boolean('Quality Approved By Purchase Representative')
    quality_refused_by_purchase_representative = fields.Boolean('Quality refused By Purchase Representative')
    is_operation_quality_check = fields.Boolean(related='picking_type_id.is_quality_check')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('employee_validation', 'Validated By Employee'),
        ('product_quality_check', 'Products Quality Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed.\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows).\n"
             " * Waiting: if it is not ready to be sent because the required products could not be reserved.\n"
             " * Ready: products are reserved and ready to be sent. If the shipping policy is 'As soon as possible' this happens as soon as anything is reserved.\n"
             " * Done: has been processed, can't be modified or cancelled anymore.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    @api.depends('state', 'is_locked', 'purchase_requisition_id')
    def _compute_show_validate(self):
        for picking in self:

            if self.purchase_requisition_id and picking.state == 'assigned':
                picking.show_validate = False
                picking.show_employee_validate = True

            elif self.purchase_requisition_id and picking.state == 'employee_validation':
                picking.show_validate = True
                picking.show_employee_validate = False
            elif self._context.get('planned_picking') and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned') or not picking.is_locked:
                picking.show_validate = False
            else:
                picking.show_validate = True
                picking.show_employee_validate = False

    def button_employee_validation(self):
        print('fff')
        if not self.env.user.id == self.purchase_representative_id.user_id.id:
            raise UserError("يجب ان يقوم بتأكيد الاستلام الموظف نفسه")

        for line in self.move_lines:
            if not line.product_id.is_assert:
                continue;
            employee_custody = self.env['employee.custody.request'].create({
                'employee_id': self.employee_id.id,
                'product_id': line.product_id.id,
                'product_quantity': line.quantity_done,
                'stock_picking_id': self.id,
                'state': 'employee_validation',
            })
        self.state = 'employee_validation'

    def action_get_custody_lines(self):
        action = self.env.ref('ejad_erp_hr.action_employee_custody_request').read([])[0]
        action['domain'] = [('stock_picking_id', '=', self.id)]
        return action

    @api.onchange('purchase_requisition_id')
    def _on_change_purchase_requisition(self):
        self.purchase_representative_id = self.purchase_requisition_id.employee_id.id

    def action_approve_quality(self):

        if self.env.user.id == self.employee_id.id:
            self.quality_approved_by_employee = True
            self.quality_refused_by_employee = False

            self.message_post(body=_("تمت موافقة جهة الطلب على جودة المنتجات"))
        if self.env.user.id == self.purchase_representative_id.id:
            self.quality_approved_by_purchase_representative = True
            self.quality_refused_by_purchase_representative = False

            self.message_post(body=_("تمت موافقة مندوب المشتريات على جودة المنتجات"))

        if self.env.user.has_group('ejad_erp_base.group_inventory_department'):
            self.quality_approved_by_stock_manger = True
            self.quality_refused_by_stock_manger = False

            self.message_post(body=_("تمت موافقة مدير المستودعات على جودة المنتجات"))

        if self.quality_approved_by_employee and self.quality_approved_by_stock_manger:
            self.state = 'product_quality_check'

    def action_refuse_quality(self):

        if self.env.user.id == self.employee_id.id:
            self.quality_refused_by_employee = True
            self.quality_approved_by_employee = False

            self.message_post(body=_("تم رفض جهة الطلب للجودة"))

        if self.env.user.id == self.purchase_representative_id.id:
            self.quality_refused_by_purchase_representative = True
            self.quality_approved_by_purchase_representative = False

            self.message_post(body=_("تم رفض مندوب المشتريات للجودة"))

        if self.env.user.has_group('ejad_erp_base.group_inventory_department'):
            self.quality_refused_by_stock_manger = True
            self.quality_approved_by_stock_manger = False
            self.message_post(body=_("تم رفض مدير المستودعات للجودة"))

        if self.quality_refused_by_employee and self.quality_refused_by_purchase_representative \
                and self.quality_refused_by_stock_manger:
            self.state = 'cancel'
