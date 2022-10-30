# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class PurchaseRequisitionRequest(models.Model):
    _inherit = "purchase.requisition"

    @api.depends('line_ids')
    def _get_total_amount(self):
        for rec in self:
            if rec.line_ids:
                for line in rec.line_ids:
                    rec.total_amount += line.amount_total
            else:
                rec.total_amount = 0

    @api.model
    def get_report_conditions(self):
        conditions_html = '''<div>شروط التسليم : التنسيق مع إدارة المشتريات وكلية العلوم الجنائية 
                            <br/>
                            موعد التسليم : شهرين ونص من تاريخ استلام التعميد
                            <br/>
                            شرط جزائي :يحسم 2% عن كل أسبوع تأخير
                            <br/>
                            مكان التسليم : جامعة نايف للعلوم الأمنية 
        
                            </div>'''

        return conditions_html

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('in_progress', 'مؤكد'),
        ('std_committee', 'اللجنة الدائمة'),
        ('open', 'مفتوح'),
        ('request_refund', 'تعويض مالي'),
        ('purchase_accountant', 'محاسب المشتريات'),
        ('purchase_manager', 'مدير قسم المشتريات'),
        ('finance_department', 'الإدارة المالية'),
        ('financial_audit_unit', 'وحدة المراجعة المالية'),
        ('general_director', 'الرئيس '),
        ('done', 'منتهي'),
        ('cancel', 'ملغى')
    ],
        'Status', track_visibility='onchange', required=True, copy=False, default='draft')

    direct_purchase_not_exceed_limit_state = fields.Selection([
        ('direct_manager', 'المدير المباشر'),
        ('procurements_unit', 'مسؤول المشتريات'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('accepted', 'مقبول'),
        ('refused', 'مرفوض')
    ], 'Status', index=True, default="direct_manager", readonly=True, copy=False, tracking=True)
    direct_purchase_exceed_limit_state = fields.Selection([
        ('departments_manager', 'مدراء الوحدات الإدارية'),
        ('procurements_unit', 'مسؤول المشتريات'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('accepted', 'مقبول'),
        ('refused', 'مرفوض')
    ], 'Status', index=True, default="departments_manager", readonly=True, copy=False, tracking=True)
    is_total_amount_exceed_limit = fields.Boolean(compute="_compute_is_total_amount_exceed_limit", store=True,compute_sudo=True)
    rfp_attachment = fields.Binary('مرفق كراسة الشروط والمواصفات RFP')
    rfq_attachment = fields.Binary('مرفق عرض السعر RFQ')
    attachment_requisition_ids = fields.One2many(comodel_name="purchase.requisition.attachments",
                                           inverse_name="requisition_id",
                                           string="المرفقات")
    tree_state = fields.Selection([
        ('departments_manager', 'مدراء الوحدات الإدارية'),
        ('direct_manager', 'المدير المباشر'),
        ('procurements_unit', 'مسؤول المشتريات'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('accepted', 'مقبول'),
        ('refused', 'مرفوض')
    ], 'Status',compute="_compute_is_total_amount_exceed_limit",compute_sudo=True)

    is_internal_purchase = fields.Boolean()
    project_id_purchase = fields.Many2one('project.project', string="Project", index=True,)
    # todo add domain in initiative moduel
    # project_id_purchase = fields.Many2one('project.project', string="Project", required=True, index=True,
    #                                       domain="[('type_project', '=', False)]")
    contract_attach = fields.Binary('مرفق العقد')
    contract_filename = fields.Char('مرفق العقد')
    letter_attach = fields.Binary('مرفق خطاب الترسية')
    letter_filename = fields.Char('مرفق خطاب الترسية')
    other_attach = fields.Binary('مرفق أخرى')
    other_filename = fields.Char('مرفق أخرى')
    rfp_attach = fields.Binary('RFP مرفق')
    rfp_filename = fields.Char('مرفق RFP')
    rfq_attach = fields.Binary('مرفق RFQ')
    rfq_filename = fields.Char('مرفق RFQ')
    rfi_attach = fields.Binary('مرفق RFI')
    rfi_filename = fields.Char('مرفق RFI')
    evaluate_attach = fields.Binary('مرفق التقييم')
    evaluate_filename = fields.Char('مرفق التقييم')
    lunch_attach = fields.Binary('مرفق نموذج طرح المشروع')
    lunch_filename = fields.Char('مرفق نموذج طرح المشروع')
    charter_attach = fields.Binary('مرفق ميثاق المشروع')
    charter_filename = fields.Char('مرفق ميثاق المشروع')

    def write(self, vals):
        self = self.sudo()
        obj = super(PurchaseRequisitionRequest, self).write(vals)
        if not vals.get('type_id') == self.env.ref('purchase_requisition.type_single').id:
            self.save_doc_in_documents()
        return obj

    @api.model
    def create(self, vals):
        result = super(PurchaseRequisitionRequest, self).create(vals)
        if not vals.get('type_id') == self.env.ref('purchase_requisition.type_single').id:
            result.save_doc_in_documents()
        return result

    def get_document_folder(self, folder_name, parent_folder):
        folder = self.env['documents.folder'].sudo().search([
            ('name', '=', folder_name),
            ('is_office_project_folder', '=', True),
            ('parent_folder_id', '=', parent_folder)], limit=1)

        return folder

    def save_doc_in_documents(self):
        self = self.sudo()
        if not self.type_id.id == self.env.ref('purchase_requisition.type_single').id:

            for rec in self:
                project_folder = False
                parent_contract_folder = False
                parent_rfp_folder = False
                doc_id = False
                attach = False
                project_folder = self.env['documents.folder'].search([
                    ('name', '=', rec.project_id_purchase.name),
                    ('is_office_project_folder', '=', True),
                    ('initiative_id', '=', rec.project_id_purchase.id)], limit=1)
                if project_folder:
                    parent_contract_folder = self.env['documents.folder'].search([
                        ('name', '=', 'العقد'),
                        ('is_office_project_folder', '=', True),
                        ('parent_folder_id', '=', project_folder.id)], limit=1)
                    parent_rfp_folder = self.env['documents.folder'].search([
                        ('name', '=', 'كراسة الشروط'),
                        ('is_office_project_folder', '=', True),
                        ('parent_folder_id', '=', project_folder.id)], limit=1)

                if parent_contract_folder:
                    if rec.contract_attach:
                       folder_name = 'العقد'
                       v_filename = rec.contract_filename
                       folder = self.get_document_folder(folder_name, parent_contract_folder.id)
                       rec.save_new_attach('contract_attach', folder,v_filename)
                    if rec.letter_attach:
                       folder_name = 'خطاب الترسية'
                       v_filename = rec.letter_filename
                       folder = self.get_document_folder(folder_name, parent_contract_folder.id)
                       rec.save_new_attach('letter_attach',folder,v_filename)
                    if rec.other_attach:
                       folder_name = 'أخرى'
                       v_filename = rec.other_filename
                       folder = self.get_document_folder(folder_name ,parent_contract_folder.id)
                       rec.save_new_attach('other_attach', folder,v_filename)
                if parent_rfp_folder:
                    if rec.rfp_attach:
                        folder_name = 'RFP'
                        v_filename = rec.rfp_filename
                        folder = self.get_document_folder(folder_name, parent_rfp_folder.id)
                        rec.save_new_attach('rfp_attach', folder,v_filename)
                    if rec.rfq_attach:
                        folder_name = 'RFQ'
                        v_filename = rec.rfq_filename
                        folder = self.get_document_folder(folder_name, parent_rfp_folder.id)
                        rec.save_new_attach('rfq_attach', folder,v_filename)
                    if rec.rfi_attach:
                        folder_name = 'RFI'
                        v_filename = rec.rfi_filename
                        folder = self.get_document_folder(folder_name, parent_rfp_folder.id)
                        rec.save_new_attach('rfi_attach', folder,v_filename)
                    if rec.evaluate_attach:
                        folder_name = 'التقييم'
                        v_filename = rec.evaluate_filename
                        folder = self.get_document_folder(folder_name, parent_rfp_folder.id)
                        rec.save_new_attach('evaluate_attach', folder,v_filename)
                    if rec.lunch_attach:
                        folder_name = 'نموذج طرح المشروع'
                        v_filename = rec.lunch_filename
                        folder = self.get_document_folder(folder_name, parent_rfp_folder.id)
                        rec.save_new_attach('lunch_attach', folder,v_filename)
                if rec.charter_attach:
                    folder = self.env['documents.folder'].search([
                        ('name', '=', 'ميثاق المشروع'),
                        ('is_office_project_folder', '=', True),
                        ('parent_folder_id', '=', project_folder.id)], limit=1)
                    v_filename = rec.charter_filename
                    rec.save_new_attach('charter_attach', folder,v_filename)
        else:
            return False

    def save_new_attach(self ,v_field,v_folder,v_filename):
        self = self.sudo()
        if not self.type_id.id == self.env.ref('purchase_requisition.type_single').id:
            attach = self.env['ir.attachment'].sudo().search(
                [('res_model', '=', self._name), ('res_id', '=', self.id), ('res_field', '=', v_field)], limit=1)
            if attach:
                doc = self.env['documents.document'].sudo().search(
                    [('res_model', '=', 'documents.document'), ('folder_id', '=', v_folder.id),
                     ('attachment_id.res_field', '=', v_field), ])
                if not doc:
                    doc = self.env['documents.document'].sudo().create({
                        'folder_id': v_folder.id,
                        'res_id': self.id,
                        'res_model': 'documents.document',
                        'owner_id': self.env.user.id,
                        'type': 'binary',
                        'favorited_ids': self.env.user,
                    })
                new_attach = attach.sudo().copy(
                    {'res_model': 'documents.document', 'res_id': doc.id, 'res_field': v_field, 'name': v_filename})
                doc.attachment_id = new_attach.id
                # doc.name = new_attach.name

                return new_attach

        else:
            return False

    @api.depends('total_amount')
    def _compute_is_total_amount_exceed_limit(self):
        for rec in self:
            if rec.total_amount >= 100000:
                rec.is_total_amount_exceed_limit = True
                rec.tree_state = rec.direct_purchase_exceed_limit_state
            else:
                rec.is_total_amount_exceed_limit = False
                rec.tree_state = rec.direct_purchase_not_exceed_limit_state

    def get_users(self, group_name):
        user_ids = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group(group_name):
                user_ids.append(user.id)
        if len(user_ids) > 0:
            return user_ids
        else:
            raise ValidationError(('لم يتم تخصيص الشخص المعني للمرحلة القادمة'))

    def add_followers(self, group_name):
        partners = []
        users = self.env['res.users'].search([])
        for user in users:
            if user.has_group(group_name):
                partners.append(user.partner_id.id)
        self.message_subscribe(partner_ids=partners)

    def action_manager(self):
        self = self.sudo()
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError(_("You cannot confirm agreement '%s' because there is no product line.") % self.name)
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without price.'))
                if requisition_line.product_qty <= 0.0:
                    raise UserError(_('You cannot confirm the blanket order without quantity.'))
                requisition_line.create_supplier_info()
        if not self.is_total_amount_exceed_limit and self.direct_purchase_not_exceed_limit_state == 'direct_manager':
            self.write({'direct_purchase_not_exceed_limit_state': 'procurements_unit'})
        elif self.is_total_amount_exceed_limit and self.direct_purchase_exceed_limit_state == 'departments_manager':
            self.write({'direct_purchase_exceed_limit_state': 'procurements_unit'})
        # Set the sequence number regarding the requisition type
        if self.name == 'New':
            if self.is_quantity_copy != 'none':
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
            else:
                self.name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')

        self.with_context({}).activity_feedback(['mail.mail_activity_data_todo'],
                                               feedback='تم اكمال المهمة بنجاح شكرا لك')
        for user in self.get_users('ejad_erp_purchase.purchase_requisition_procurements_unit'):
            self.with_context({}).activity_schedule('mail.mail_activity_data_todo',
                                  user_id=user,
                                  res_id=self.id)
            self.add_followers('ejad_erp_purchase.purchase_requisition_procurements_unit')

    def action_direct_purchase_procurements_unit(self):
        for rec in self.sudo():
            if not rec.is_total_amount_exceed_limit:
                rec.write({'direct_purchase_not_exceed_limit_state': 'support_services_manager'})
            elif rec.is_total_amount_exceed_limit:
                rec.write({'direct_purchase_exceed_limit_state': 'support_services_manager'})

            rec.with_context({}).activity_feedback(['mail.mail_activity_data_todo'],
                                                    feedback='تم اكمال المهمة بنجاح شكرا لك')
            for user in rec.get_users('ejad_erp_purchase.purchase_support_services_manage'):
                rec.with_context({}).activity_schedule('mail.mail_activity_data_todo',
                                                        user_id=user,
                                                        res_id=self.id)
                rec.add_followers('ejad_erp_purchase.purchase_support_services_manage')

    def action_support_services_manager(self):
        for rec in self.sudo():
            if not rec.is_total_amount_exceed_limit:
                rec.write({'direct_purchase_not_exceed_limit_state': 'office_leader'})
            elif rec.is_total_amount_exceed_limit:
                rec.write({'direct_purchase_exceed_limit_state': 'office_leader'})

            rec.with_context({}).activity_feedback(['mail.mail_activity_data_todo'],
                                                   feedback='تم اكمال المهمة بنجاح شكرا لك')
            for user in rec.get_users('ejad_erp_purchase.purchase_office_leader'):
                rec.with_context({}).activity_schedule('mail.mail_activity_data_todo',
                                                       user_id=user,
                                                       res_id=self.id)
                rec.add_followers('ejad_erp_purchase.purchase_office_leader')

    def action_office_leader(self):
        """
        Generate all purchase order based on selected lines, should only be called on one agreement at a time
        """
        self = self.sudo()
        if any(purchase_order.state in ['draft', 'sent', 'to approve'] for purchase_order in
               self.mapped('purchase_ids')):
            raise UserError(_('You have to cancel or validate every RfQ before closing the purchase requisition.'))
        for requisition in self:
            for requisition_line in requisition.line_ids:
                requisition_line.supplier_info_ids.unlink()
        if not self.is_total_amount_exceed_limit:
            self.write({'direct_purchase_not_exceed_limit_state': 'accepted'})
        elif self.is_total_amount_exceed_limit:
            self.write({'direct_purchase_exceed_limit_state': 'accepted'})

        self.with_context({}).activity_feedback(['mail.mail_activity_data_todo'],
                                               feedback='تم اكمال المهمة بنجاح شكرا لك')

    def action_refused_direct_purchase(self):
        # try to set all associated quotations to cancel state
        for requisition in self.sudo():
            for requisition_line in requisition.line_ids:
                requisition_line.supplier_info_ids.unlink()
            requisition.purchase_ids.button_cancel()
            for po in requisition.purchase_ids:
                po.message_post(body=_('Cancelled by the agreement associated to this quotation.'))
            if not requisition.is_total_amount_exceed_limit:
                requisition.write({'direct_purchase_not_exceed_limit_state': 'refused'})
            elif requisition.is_total_amount_exceed_limit:
                requisition.write({'direct_purchase_exceed_limit_state': 'refused'})

            requisition.with_context({}).activity_feedback(['mail.mail_activity_data_todo'],
                                                    feedback='تم اكمال المهمة بنجاح شكرا لك')

    employee_id = fields.Many2one('hr.employee', string="الموظف الطالب")
    employee_department_id = fields.Many2one('hr.department', string="الجهة الطالبة",
                                             related='employee_id.department_id', readonly=True)

    type_id = fields.Many2one(string="النوع")
    custom_type = fields.Selection(related="type_id.custom_type", string="نوع العملية", store=True)
    pr_max_amount = fields.Float(string="المبلغ الذي يحتاج موافقة اللجنة")
    salesperson_user_current = fields.Boolean(compute="_is_salesperson_current")
    require_committee = fields.Boolean("يحتاج إلى قرار اللجنة ؟", compute="_require_committee")
    committee_decision_attachment_id = fields.Binary(string="قرار اللجنة",
                                                     states={'std_committee': [('required', True)]})
    committee_decision_filename = fields.Char()
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    total_amount = fields.Float(string="الاجمالي", compute="_get_total_amount")
    report_introduction = fields.Html('مقدمة خطاب التعميد')
    report_conditions = fields.Html('الشروط والأحكام', default=get_report_conditions)
    name = fields.Char(readonly=True)
    origin = fields.Char(readonly=True)

    @api.onchange('name', 'origin', 'schedule_date', 'ordering_date')
    def onchange_report_introduction(self):
        report_introduction = '''<div>   حيث رسى الإختيار على شركتكم بناء على محضر الترسية رقم''' \
                              + str(self.name) + '''بتاريخ''' + str(self.ordering_date) \
                              + '''وبناء على عرضكم رقم''' + str(self.origin) + '''بتاريخ''' + str(self.schedule_date) \
                              + '''نأمل توريد المطلوب وفق  الشروط التالية:''' \
                              + ''' </div>'''
        print(report_introduction)
        self.report_introduction = report_introduction

    @api.depends('line_ids', 'total_amount')
    def _require_committee(self):
        if self.total_amount < self.company_id.default_pr_max_amount:
            self.require_committee = False
        else:
            self.require_committee = True

    @api.depends('user_id')
    def _is_salesperson_current(self):
        if self.env.uid == self.user_id.id:
            self.salesperson_user_current = True
        else:
            self.salesperson_user_current = False

    def action_to_committee(self):
        self.state = 'std_committee'

    def action_done(self):
        """
        Generate all purchase order based on selected lines, should only be called on one agreement at a time
        """
        if any(purchase_order.state in ['draft', 'sent', 'to approve'] for purchase_order in
               self.mapped('purchase_ids')):
            raise UserError(_('You have to cancel or validate every RfQ before closing the purchase requisition.'))
        self.write({'state': 'done'})

    def action_to_purchase_accountant(self):
        self.state = 'purchase_accountant'

    def action_to_purchase_manager(self):
        self.state = 'purchase_manager'

    def action_to_financial_audit_unit(self):
        self.state = 'financial_audit_unit'

    def action_to_general_director(self):
        self.state = 'general_director'


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    @api.depends('product_qty', 'price_unit')
    def _get_total_amount(self):
        for rec in self:
            rec.amount_total = rec.price_unit * rec.product_qty

    amount_total = fields.Float(string="الاجمالي", compute="_get_total_amount")


class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.type"

    custom_type = fields.Selection([
        ('tender', 'تعميد'),
        ('direct', 'شراء مباشر')
    ], string="نوع العملية")


class PurchaseRequisitionAttachmnet(models.Model):
    _name = "purchase.requisition.attachments"
    _description = "المرفقات"

    name = fields.Char(string='اسم المرفق', required=True, translate=True)
    attachment_id = fields.Binary(string="المرفق", required=True)
    attachment_filename = fields.Char(string='اسم المرفق')
    requisition_id = fields.Many2one(comodel_name='purchase.requisition')
