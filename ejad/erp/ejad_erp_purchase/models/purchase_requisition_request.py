# -*- encoding: utf-8 -*-

from ast import literal_eval
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from datetime import datetime
from lxml import etree


class PurchaseRequisitionRequest(models.Model):
    _name = "purchase.requisition.request"
    _description = "Purchase Requisition Request"
    _inherit = ['mail.thread']
    _order = "id desc"

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_requests'):
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

        res = super(PurchaseRequisitionRequest, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_requests'):
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
        res = super(PurchaseRequisitionRequest, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseRequisitionRequest, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
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

    def _get_product_type_id(self):
        return self.env['purchase.requisition.request.product.type'].search([], limit=1)

    def _get_project_type_id(self):
        return self.env['purchase.requisition.request.project.type'].search([], limit=1)

    def _get_employee_id(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

    @api.depends('line_ids.price_unit')
    def _get_total_amount(self):
        for line in self.line_ids:
            self.total_amount += line.price_unit * line.requested_qty

    name = fields.Char(string='المعرّف', required=True, copy=False, default=_('جديد'))
    request_type = fields.Selection([
        ('product', 'طلب تأمين مواد'),
        ('project', 'طلب مشروع'),
    ], required=True, string="نوع الطلب")

    product_category_id = fields.Many2one('product.category', string="فئة المنتج", required=True)
    product_category_manager_id = fields.Many2one('hr.employee', string="المدير المعتمد",
                                    compute='get_product_category_manager_id', readonly=True,)
    product_category_security_group_users = fields.Many2many('res.users', string="موظفي المشرف المعتمد",
                                     related='product_category_id.security_group_id.users', readonly=True, related_sudo=True)
    reason = fields.Text('وصف سبب الطلب', required=True)
    date = fields.Date(string="تاريخ الطلب", default=fields.Date.context_today)
    requested_date = fields.Date(string="تاريخ الاحتياج")
    employee_id = fields.Many2one('hr.employee', track_visibility='onchange', string="الموظف", required=True, default=_get_employee_id)
    employee_department_id = fields.Many2one('hr.department',string="الجهة الطالبة",compute='get_employee_department_id',readonly=True,)
    employee_manager_id = fields.Many2one('hr.employee', string="المدير المباشر",compute='compute_get_employee_manager_id',readonly=True,)
    employee_user_id = fields.Many2one('res.users', compute="compute_get_user", string="المستخدم", required=False)
    employee_user_current = fields.Boolean(compute="_is_employee_current", compute_sudo=True)
    employee_manager_user_current = fields.Boolean(compute="_is_employee_manager_current", compute_sudo=True)
    is_category_editable = fields.Boolean(compute="_is_category_editable",store=True, compute_sudo=True)

    def get_product_category_manager_id(self):
        for rec in self:
            rec.product_category_manager_id = rec.sudo().product_category_id.department_id.manager_id.id

    def get_employee_department_id(self):
        for rec in self:
            rec.employee_department_id = rec.sudo().employee_id.department_id.id

    def compute_get_user(self):
        for rec in self:
            rec.employee_user_id = rec.sudo().employee_id.user_id.id

    def compute_get_employee_manager_id(self):
        for rec in self:
            rec.employee_manager_id = rec.sudo().employee_id.parent_id.id

    # @api.constrains('reason')
    # def _check_reason(self):
    #     for record in self:
    #         if len(record.reason) < 30:
    #             raise ValidationError("الرجاء وصف سبب الطلب في أكثر من 30 حرف.")

    @api.depends('line_ids')
    def _is_category_editable(self):
        for rec in self:
            if rec.line_ids:
                rec.is_category_editable = False
            else:
                rec.is_category_editable = True


    def _is_employee_current(self):
        if self.env.uid == self.sudo().employee_user_id.id:
            self.employee_user_current = True
        else:
            self.employee_user_current = False

    def _is_employee_manager_current(self):
        if self.env.uid == self.sudo().employee_id.parent_id.user_id.id \
             or self.user_has_groups('ejad_erp_purchase.hr_requisition_direct_manager') \
             or (self.env.uid == self.sudo().employee_id.user_id.id and self.user_has_groups(
                'ejad_erp_purchase.hr_requisition_employee_itself_direct_manager')):
            self.employee_manager_user_current = True
        else:
            self.employee_manager_user_current = False

    line_ids = fields.One2many('purchase.requisition.request.line', 'request_id', string='المواد المطلوبة',
                               states={'done': [('readonly', True)]}, copy=True)

    state = fields.Selection(
        [('draft', 'الطلب'), ('manager', 'المدير المباشر'),
          ('department', 'الإدارة المعتمدة'), ('inventory', 'إدارة المستودعات'),
          ('supervisor', 'المشرف المعتمد'), ('director', 'مدير قسم المشتريات'),
          ('accepted', 'تم انهاء التقييم'), ('refused', 'مرفوض'),
          ('canceled', 'ملغى'),('delivered', 'تم اكمال الاستلام')
        ],
        'Status', track_visibility='onchange', required=True, copy=False, default='draft')

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'purchase.requisition.request'))
    is_needed = fields.Boolean()
    is_exist = fields.Boolean()
    total_amount = fields.Float(string="الاجمالي",  compute="_get_total_amount", store=True,  compute_sudo=True)

    specifications_attachment_id = fields.Binary(string="كراس الشروط", states={'department': [('required', True)]})
    specifications_filename = fields.Char()
    purchase_representative = fields.Many2one('res.users', string='مندوب مشتريات', states={'director': [('required', True)]})
    max_amount = fields.Float(string="المبلغ الأقصى للشراء المباشر")
    department_id = fields.Many2one('hr.department', string="الإدارة المعتمدة",
                                    compute='compute_get_department_id_product_category', readonly=True)
    department_manager_user_current = fields.Boolean(compute="_is_department_manager_current",  compute_sudo=True)
    department_moderator_user_current = fields.Boolean(compute="_is_department_moderator_current", compute_sudo=True)

    def compute_get_department_id_product_category(self):
        for rec in self:
            rec.department_id = rec.sudo().product_category_id.department_id.id

    @api.depends('product_category_id')
    def _is_department_manager_current(self):
        if self.env.uid == self.sudo().department_id.manager_id.user_id.id:
            self.department_manager_user_current = True
        else:
            self.department_manager_user_current = False

    @api.depends('product_category_id')
    def _is_department_moderator_current(self):
        if self.product_category_id.security_group_id in self.env.user.groups_id:
            self.department_moderator_user_current = True
        else:
            self.department_moderator_user_current = False

    refuse_user_id = fields.Many2one('res.users', string='مرفوض من قبل', readonly=True)
    refuse_reason_id = fields.Many2one('requisition.refuse.reason', string='سبب الرفض', readonly=True)
    refuse_message = fields.Text('ملاحظات الرفض', readonly=True)
    refuse_state = fields.Selection(
        [('draft', 'الطلب'), ('manager', 'المدير المباشر'),
         ('department', 'الإدارة المعتمدة'), ('inventory', 'إدارة المستودعات'),
         ('supervisor', 'المشرف المعتمد'), ('director', 'مدير قسم المشتريات'),
         ('accepted', 'مقبول'), ('refused', 'مرفوض'),
         ('canceled', 'ملغى')
         ], string="المرحلة", readonly=True)

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                'purchase.order.requisition.request')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.requisition.request')

        result = super(PurchaseRequisitionRequest, self).create(vals)
        return result

    def action_draft_manager(self):
        self.state = 'manager'

    def action_ok_manager(self):
        self.state = 'department'

    def action_need_department(self):
        if self.line_ids:
            if self.request_type == 'product':
                self.is_needed = True
            elif self.request_type == 'project':
                self.state = 'supervisor'
        else:
            raise ValidationError('يجب إضافة مواد مطلوبة .!')

    def action_exist_department(self):
        company_id = self.env['res.company']._company_default_get('purchase.requisition.request').id
        stock_picking = self.env['stock.picking']
        picking_type_id = self.env.ref('stock.picking_type_internal')
        sp_data = {
            'company_id': company_id,
            'state': 'draft',
            'picking_type_id': picking_type_id.id,
            'scheduled_date': self.date,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'requisition_request_id': self.id,
        }
        picking_id = stock_picking.sudo().create(sp_data)
        for line in self.line_ids:
            line_data = {
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'name': line.product_id.name,
                'product_uom_qty': line.requested_qty,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
                'picking_id': picking_id.id
            }
            self.env['stock.move'].sudo().create(line_data)
        self.state = 'inventory'
        self.is_exist = True

    def action_no_exist_department(self):
        self.state = 'supervisor'

    def action_ok_supervisor(self):
        self.state = 'director'

    def action_validate(self):
        if self.request_type == 'product':
            if self.total_amount >= self.company_id.default_pr_max_amount:
                type_id = self.env.ref('ejad_erp_purchase.type_tender_exclusive').id
            else:
                type_id = self.env.ref('ejad_erp_purchase.type_single_direct').id
        else:
            type_id = self.env.ref('ejad_erp_purchase.type_tender_exclusive').id

        data_requisition = {
            'origin': self.name,
            'requisition_request_id': self.id,
            'company_id': self.company_id.id,
            'type_id': type_id,
            'employee_id': self.employee_id.id,
            'state': 'draft',
            'picking_type_id': 1
        }
        requisition_id = self.env['purchase.requisition'].create(data_requisition)
        if self.purchase_representative.id:
            requisition_id.user_id = self.purchase_representative.id
        if self.line_ids:
            for line in self.line_ids:
                data_line = {
                     'product_id': line.product_id.id,
                     'product_uom_id': line.product_uom_id.id,
                     'product_qty': line.requested_qty,
                     'price_unit': line.price_unit,
                     'requisition_id': requisition_id.id,
                     'company_id': line.company_id.id}
                self.env['purchase.requisition.line'].create(data_line)

        self.state = 'accepted'
        return {
            'view_mode': 'form',
            'res_model': 'purchase.requisition',
            'type': 'ir.actions.act_window',
            'res_id': requisition_id.id,
            'target': 'current',
        }

    def action_open_agreement(self):
        self.ensure_one()
        action = self.env.ref('purchase_requisition.action_purchase_requisition').read()[0]
        # action['domain'] = literal_eval(action['domain'])
        action['domain'] = [('requisition_request_id', '=', self.id)]
        return action

    def action_open_stock_picking(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('requisition_request_id', '=', self.id)]
        return action

    def action_order_delivered(self):
        self.state = 'delivered'


class PurchaseRequisitionRequestLine(models.Model):
    _name = "purchase.requisition.request.line"
    _description = "Purchase Requisition Request Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='المنتج', required=True, domain=[('purchase_ok', '=', True)])
    name = fields.Text(string='وصف')
    is_needed = fields.Boolean(related="request_id.is_needed")
    product_uom_id = fields.Many2one('uom.uom', string='وحدة المنتج')
    requested_qty = fields.Float('الكمية المطلوبة')
    qty_available = fields.Float('الكمية المتوفرة', related='product_id.qty_available')
    request_id = fields.Many2one('purchase.requisition.request', string='طلب الشراء', ondelete='cascade')
    company_id = fields.Many2one('res.company', related='request_id.company_id', string='Company', store=True, readonly=True, default= lambda self: self.env['res.company']._company_default_get('purchase.requisition.line'))
    price_unit = fields.Float(string='سعر الوحدة', states={'director': [('required', True)]})
    trade_mark = fields.Char('العلامة التجارية')
    state = fields.Selection( 'State', related='request_id.state')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.product_qty = 1.0


class PurchaseRequisitionRequestProductType(models.Model):
    _name = "purchase.requisition.request.product.type"
    _description = "Purchase Requisition Request Product Type"
    _order = "sequence"

    name = fields.Char(string='نوع المنتج', required=True, translate=True)
    sequence = fields.Integer(default=1)


class PurchaseRequisitionRequestProjectType(models.Model):
    _name = "purchase.requisition.request.project.type"
    _description = "Purchase Requisition Request Project Type"
    _order = "sequence"

    name = fields.Char(string='نوع المشروع', required=True, translate=True)
    sequence = fields.Integer(default=1)


class PurchaseRequisition(models.Model):
    _inherit = "purchase.requisition"

    requisition_request_id = fields.Many2one('purchase.requisition.request', string='طلب الشراء', copy=False)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    requisition_request_id = fields.Many2one('purchase.requisition.request', string='طلب الشراء', copy=False)


class RequisitionRefuseReason(models.Model):
    _name = "requisition.refuse.reason"

    name = fields.Char(string='سبب الرفض')
