# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError
from lxml import etree


class ACOperationTransferLine(models.Model):
    _name = 'wiz.ac.operation.transfer.line'
    _description = 'wiz ac operation transfer line'

    transfer_ref = fields.Reference(
        selection=[('hr.employee', 'موظف'), ('hr.department', 'إدارة')],
        string='وجهة الإحالة', required=True)
    department_deadline_date = fields.Datetime('تاريخ انجاز المعاملة')
    is_readonly_date = fields.Boolean('Is Readonly')
    # is_readonly_date = fields.Boolean('Is Readonly', compute="_readonly_date")
    parent_id = fields.Many2one('wiz.ac.operation.transfer')
    transfer_guidance = fields.Many2one('ac.transfer.guidance', string='التوجيه', required=True)
    notes = fields.Text('التعليق', required=False)

    
    @api.onchange('destination')
    def onchange_destination(self):
        for rec in self:
            if not rec.destination:
                rec.department_id = False
                rec.assigned_employee_id = False
            elif rec.destination == 'department':
                rec.assigned_employee_id = False
            elif rec.destination == 'employee':
                rec.department_id = False


    @api.depends('transfer_ref')
    def _readonly_date(self):
        if self.transfer_ref:
            if self.transfer_ref._name == 'hr.employee':
                self.is_readonly_date = True
                self.department_deadline_date = False
            else:
                self.is_readonly_date = False


class ACOperationTransfer(models.Model):
    _name = 'wiz.ac.operation.transfer'
    _description = 'wiz ac operation transfer'

    line_ids = fields.One2many('wiz.ac.operation.transfer.line', 'parent_id', string="التفاصيل")
    department_id = fields.Many2many(comodel_name="hr.department", string="الإدارات المعنية")
    assigned_employee_id = fields.Many2one('hr.employee', string='الموظف')
    destination = fields.Selection([('department', 'إلى إدارات'),
                                    ('employee', 'إلى موظف'),
                                    ('global_out', 'إلى الصادر العام')], string='وجهة الإحالة', required=False)
    transfer_guidance = fields.Many2one('ac.transfer.guidance', string='التوجيه', required=False)
    notes = fields.Text('التعليق', required=False)
    is_multi_guidance = fields.Boolean('متعدد؟')

    
    def action_transfer_operation(self):
        self.ensure_one()
        template = self.env.ref(
            'ejad_erp_administrative_communications.ac_mail_template',
            raise_if_not_found=False)
        oper_obj = self.env['ac.operation']
        oper_move_obj = self.env['ac.operation.move']
        message_obj = self.env['mail.message']
        followers_obj = self.env['mail.followers']
        notification_obj = self.env['mail.notification']
        users_obj = self.env['res.users']
        operation_ids = oper_obj.browse(self.env.context.get('active_ids'))
        host = self.env.user.company_id.host or 'localhost:8069'
        for operation_id in operation_ids:
            if self.env.user.has_group('ejad_erp_administrative_communications.access_sign_operations'):
                operation_id.write({'sign_data': fields.Date.today(),
                                    'is_sign_completed': True,
                                    'sign_user_id': self.env.user.id,
                                    })

        if not self.is_multi_guidance:
            for operation_id in operation_ids:

                if operation_id.department_id or operation_id.assigned_employee_id:
                    src = operation_id.department_id and 'الإدارة : ' + operation_id.department_id.name or 'الموظف : ' + (operation_id.assigned_employee_id.name or ' ')
                else:
                    src = 'الوارد العام'
                if self.destination == 'department' and self.department_id:
                    msg = "المعاملة الآن عند الإدارات : "
                    for d in self.department_id:
                        move_data = {'type': 'transfer',
                                     'date': datetime.today(),
                                     'operation_id': operation_id.id,
                                     'user_id': self.env.user.id,
                                     'src_name': src,
                                     'src_dep_id': operation_id.department_id.id or False,
                                     'old_employee_id': operation_id.assigned_employee_id.id or False,
                                     'dest_dep_id': d.id,
                                     'dest_name': 'الإدارة : ' + d.name,
                                     'transfer_guidance': self.transfer_guidance.id,
                                     'notes': self.notes or  ' '}
                        oper_move_obj.create(move_data)

                        msg += (" , " + d.name)

                    operation_id.write({'message': msg})
                    operation_id.write({'state': 'open'})
                    operation_id.write({'department_id': self.department_id and (self.department_id[0]).id or False})
                    operation_id.write({'assigned_employee_id': False})
                    operation_id.write({'is_department_inbox': True})
                    operation_id.write({'state_detailed': 'department_inbox'})

                    action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_department_in').id
                    msg_data = {
                        'subject': 'إحالة معاملة',
                        'date': datetime.today(),
                        'body': 'لقد تم إحالة هذه المعاملة : ' +
                                '<a href="http://' + host + '/web#id=' + str(operation_id.id) +
                                '&view_type=form&action=' + str(action_id) +
                                '&model=ac.operation">' + str(operation_id.subject) + '</a>' +
                                ' إلى إدارتكم قصد : ' +
                                '<br/><b>' + self.transfer_guidance.name + '</b><br/>' +
                                'التعليق : ' + (self.notes or " "),
                        # 'res_id': operation_id.id,
                        # 'model': 'ac.operation',
                        'message_type': 'notification'
                    }
                    msg_id = message_obj.create(msg_data)


                    list_users = []
                    for dd in self.department_id:
                        for emp in dd.member_ids:
                            if emp.user_id:
                                list_users.append(emp.user_id)
                                for eeemp in emp.search([('parent_id', '=', emp.id)]):
                                    if eeemp.user_id.has_group('ejad_erp_administrative_communications.access_no_manager'):
                                        if eeemp.user_id and eeemp.user_id not in list_users:
                                            list_users.append(eeemp.user_id)
                    #print('#   ',list_users)
                    llink = '<a href="http://' + host + '/web#id=' + str(operation_id.id) + '&view_type=form&action=' + str(
                        action_id) + '&model=ac.operation">' + ' رابط المعاملة ' + str(operation_id.subject) + '</a>'
                    for usr in list_users:
                        if usr.has_group('ejad_erp_administrative_communications.group_department_incoming') or usr.has_group('ejad_erp_administrative_communications.access_no_manager'):
                            if len(followers_obj.search([('res_model', '=', 'ac.operation'),
                                                                      ('res_id', '=', operation_id.id),
                                                                      ('partner_id', '=', usr.partner_id.id)])) == 0:
                                reg = {
                                    'res_id': operation_id.id,
                                    'res_model': 'ac.operation',
                                    'partner_id': usr.partner_id.id
                                }

                                followers_obj.create(reg)

                            notif_data = {
                                'mail_message_id': msg_id.id,
                                'res_partner_id': usr.partner_id.id,
                                'is_read': False,
                                'notification_type': 'email'
                            }
                            notification_obj.create(notif_data)
                            if template:
                                template.send_mail(operation_id.id, force_send=True, email_values={'body_html': llink,'email_to':usr.partner_id.email})


                    #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in_general').read()[0]
                    #return True
                    continue

                elif self.destination == 'employee' and self.assigned_employee_id:
                    move_data = {
                        'type': 'transfer',
                        'date': datetime.today(),
                        'operation_id': operation_id.id,
                        'src_dep_id': operation_id.department_id.id or False,
                        'old_employee_id': operation_id.assigned_employee_id.id or False,
                        'new_employee_id': self.assigned_employee_id.id,
                        'src_name': src,
                        'dest_name': 'الموظف : ' + self.assigned_employee_id.name,
                        'user_id': self.env.user.id,
                        'transfer_guidance': self.transfer_guidance.id,
                        'notes': self.notes or ' '
                    }
                    oper_move_obj.create(move_data)

                    msg = "المعاملة الآن عند الموظف : " + (self.assigned_employee_id.name or '') + \
                          "   الذي يتبع للإدارة : " + (self.assigned_employee_id.department_id.name or '')

                    operation_id.write({'message': msg})
                    operation_id.write({'state': 'open'})
                    operation_id.write({'department_id': False})
                    operation_id.write({'assigned_employee_id': self.assigned_employee_id.id})
                    operation_id.write({'is_employee_inbox': True})
                    operation_id.write({'state_detailed': 'employee_inbox'})

                    if len(followers_obj.search([('res_model', '=', 'ac.operation'),
                                                              ('res_id', '=', operation_id.id),
                                                              ('partner_id', '=', self.assigned_employee_id.user_id.partner_id.id)])) == 0:
                        reg = {
                            'res_id': operation_id.id,
                            'res_model': 'ac.operation',
                            'partner_id': self.assigned_employee_id.user_id.partner_id.id
                        }

                        followers_obj.create(reg)

                    action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').id
                    msg_data = {
                        'subject': 'إحالة معاملة',
                        'date': datetime.today(),
                        'body': 'لقد تم إحالة هذه المعاملة : ' +
                                '<a href="http://' + host + '/web#id=' + str(operation_id.id) +
                                '&view_type=form&action=' + str(action_id) +
                                '&model=ac.operation">' + str(operation_id.subject) + '</a>' +
                                ' لكم قصد : ' +
                                '<br/><b>' + self.transfer_guidance.name + '</b><br/>' +
                                'التعليق : ' + (self.notes or ''),
                        # 'res_id': operation_id.id,
                        # 'model': 'ac.operation',
                        'message_type': 'notification',
                    }
                    msg_id = message_obj.create(msg_data)

                    notif_data = {
                        'mail_message_id': msg_id.id,
                        'res_partner_id': self.assigned_employee_id.user_id.partner_id.id,
                        'is_read': False,
                        'notification_type': 'email'
                    }
                    notification_obj.create(notif_data)
                    llink = '<a href="http://' + host + '/web#id=' + str(operation_id.id) + '&view_type=form&action=' + str(
                        action_id) + '&model=ac.operation">' + ' رابط المعاملة '+ str(operation_id.name) + '</a>'
                    if template:
                        template.send_mail(operation_id.id, force_send=True,
                                           email_values={'body_html': llink, 'email_to': self.assigned_employee_id.user_id.partner_id.email})
                    #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').read()[0]
                    #return True
                    continue

                elif self.destination == 'global_out':
                    if operation_id.type == 'internal':
                        raise UserError(_("لا يمكن إحالة معاملة داخلية إلى الصادر العام !"))

                    if operation_id.department_id:
                        move_data = {'type': 'transfer',
                                     'date': datetime.today(),
                                     'operation_id': operation_id.id,
                                     'user_id': self.env.user.id,
                                     'src_name': src,
                                     'src_dep_id': operation_id.department_id.id or False,
                                     'old_employee_id': operation_id.assigned_employee_id.id or False,
                                     # 'dest_dep_id': self.department_id.id,
                                     'dest_name': 'الصادر العام ',
                                     'transfer_guidance': self.transfer_guidance.id,
                                     'notes': self.notes or ' '}
                        oper_move_obj.create(move_data)

                        msg = "المعاملة الآن عند الصادر العام "

                        operation_id.write({'message': msg})
                        operation_id.write({'state': 'open'})
                        operation_id.write({'department_id': False})
                        operation_id.write({'assigned_employee_id': False})
                        operation_id.write({'is_global_outbox': True})
                        operation_id.write({'state_detailed': 'global_outbox'})

                        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_department_in').id
                        msg_data = {
                            'subject': 'إحالة معاملة',
                            'date': datetime.today(),
                            'body': 'لقد تم إحالة هذه المعاملة : ' +
                                    '<a href="http://' + host + '/web#id=' + str(operation_id.id) +
                                    '&view_type=form&action=' + str(action_id) +
                                    '&model=ac.operation">' + str(operation_id.subject) + '</a>' +
                                    ' إلى الصادر العام قصد : ' +
                                    '<br/><b>' + self.transfer_guidance.name + '</b><br/>' +
                                    'التعليق : ' + self.notes or "/",
                            # 'res_id': operation_id.id,
                            # 'model': 'ac.operation',
                            'message_type': 'notification'
                        }
                        msg_id = message_obj.create(msg_data)

                        users_ids = users_obj.search([])
                        llink = '<a href="http://' + host + '/web#id=' + str(
                            operation_id.id) + '&view_type=form&action=' + str(
                            action_id) + '&model=ac.operation">' + ' رابط المعاملة ' + str(operation_id.subject) + '</a>'
                        for usr in users_ids:
                            if usr.has_group('ejad_erp_administrative_communications.group_general_outgoing'):
                                if len(followers_obj.search([('res_model', '=', 'ac.operation'),
                                                                          ('res_id', '=', operation_id.id),
                                                                          ('partner_id', '=', usr.partner_id.id)])) == 0:
                                    reg = {
                                        'res_id': operation_id.id,
                                        'res_model': 'ac.operation',
                                        'partner_id': usr.partner_id.id
                                    }

                                    followers_obj.create(reg)

                                    notif_data = {
                                        'mail_message_id': msg_id.id,
                                        'res_partner_id': usr.partner_id.id,
                                        'is_read': False,
                                        'notification_type': 'email'
                                    }
                                    notification_obj.create(notif_data)
                                    if template:
                                        template.send_mail(operation_id.id, force_send=True,
                                                           email_values={'body_html': llink,
                                                                         'email_to': usr.partner_id.email})

                        #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_out_general').read()[0]
                        #return True
                        continue
                    else:
                        raise UserError(_("لا يمكن إحالة المعاملة إلى الصادر العام إلا إذا كانت في وارد أو صادر الإدارة !"))
                else:
                    raise UserError(_("الرجاء التأكد من البيانات !"))

        else:
            if not self.line_ids:
                raise UserError(_("الرجاء إدخال بيانات !"))
            for operation_id in operation_ids:
                if operation_id.department_id or operation_id.assigned_employee_id:
                    src = operation_id.department_id and 'الإدارة : ' + \
                          operation_id.department_id.name or 'الموظف : ' + \
                          (operation_id.assigned_employee_id.name or ' ')
                else:
                    src = 'الوارد العام'
                departments_name = []
                departments_ids = []
                employees_name = []

                for lline in self.line_ids:

                    if lline.transfer_ref._name == 'hr.department':
                        departments_name.append(lline.transfer_ref.name)
                        departments_ids.append(lline.transfer_ref.id)

                        move_data = {'type': 'transfer',
                                     'date': datetime.today(),
                                     'date_deadline': lline.department_deadline_date,
                                     'operation_id': operation_id.id,
                                     'user_id': self.env.user.id,
                                     'src_name': src,
                                     'src_dep_id': operation_id.department_id.id or False,
                                     'old_employee_id': operation_id.assigned_employee_id.id or False,
                                     'dest_dep_id': lline.transfer_ref.id,
                                     'dest_name': 'الإدارة : ' + lline.transfer_ref.name,
                                     'transfer_guidance': lline.transfer_guidance.id,
                                     'notes': lline.notes or ' '}
                        oper_move_obj.create(move_data)

                        operation_id.write({'state': 'open'})
                        operation_id.write({'department_id': lline.transfer_ref.id})
                        operation_id.write({'assigned_employee_id': False})
                        operation_id.write({'is_department_inbox': True})
                        operation_id.write({'state_detailed': 'department_inbox'})

                        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_department_in').id
                        msg_data = {
                            'subject': 'إحالة معاملة',
                            'date': datetime.today(),
                            'body': 'لقد تم إحالة هذه المعاملة : ' +
                                    '<a href="http://' + host + '/web#id=' + str(operation_id.id) +
                                    '&view_type=form&action=' + str(action_id) +
                                    '&model=ac.operation">' + str(operation_id.subject) + '</a>' +
                                    ' إلى إدارتكم قصد : ' +
                                    '<br/><b>' + lline.transfer_guidance.name + '</b><br/>' +
                                    'التعليق : ' + (lline.notes or " "),
                            # 'res_id': operation_id.id,
                            # 'model': 'ac.operation',
                            'message_type': 'notification'
                        }
                        msg_id = message_obj.create(msg_data)


                        list_users = []
                        for emp in lline.transfer_ref.member_ids:
                            if emp.user_id:
                                list_users.append(emp.user_id)
                                for eeemp in emp.search([('parent_id', '=', emp.id)]):
                                    if eeemp.user_id.has_group('ejad_erp_administrative_communications.access_no_manager'):
                                        if eeemp.user_id and eeemp.user_id not in list_users:
                                            list_users.append(eeemp.user_id)

                        llink = '<a href="http://' + host + '/web#id=' + str(operation_id.id) + '&view_type=form&action=' + str(
                            action_id) + '&model=ac.operation">' + ' رابط المعاملة ' + str(operation_id.subject) + '</a>'
                        for usr in list_users:
                            if usr.has_group('ejad_erp_administrative_communications.group_department_incoming') or usr.has_group('ejad_erp_administrative_communications.access_no_manager'):
                                if len(followers_obj.search([('res_model', '=', 'ac.operation'),
                                                                          ('res_id', '=', operation_id.id),
                                                                          ('partner_id', '=', usr.partner_id.id)])) == 0:
                                    reg = {
                                        'res_id': operation_id.id,
                                        'res_model': 'ac.operation',
                                        'partner_id': usr.partner_id.id
                                    }

                                    followers_obj.create(reg)

                                notif_data = {
                                    'mail_message_id': msg_id.id,
                                    'res_partner_id': usr.partner_id.id,
                                    'is_read': False,
                                    'notification_type': 'email'
                                }
                                notification_obj.create(notif_data)
                                if template:
                                    template.send_mail(operation_id.id, force_send=True, email_values={'body_html': llink,'email_to':usr.partner_id.email})


                        #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in_general').read()[0]
                        #return True
                        continue

                    elif lline.transfer_ref._name == 'hr.employee':
                        employees_name.append(lline.transfer_ref.name)

                        move_data = {
                            'type': 'transfer',
                            'date': datetime.today(),
                            'operation_id': operation_id.id,
                            'src_dep_id': operation_id.department_id.id or False,
                            'old_employee_id': operation_id.assigned_employee_id.id or False,
                            'new_employee_id': lline.transfer_ref.id,
                            'src_name': src,
                            'dest_name': 'الموظف : ' + lline.transfer_ref.name,
                            'user_id': self.env.user.id,
                            'transfer_guidance': lline.transfer_guidance.id,
                            'notes': lline.notes or ' '
                        }
                        oper_move_obj.create(move_data)

                        operation_id.write({'state': 'open'})
                        operation_id.write({'department_id': False})
                        operation_id.write({'assigned_employee_id': lline.transfer_ref.id})
                        operation_id.write({'is_employee_inbox': True})
                        operation_id.write({'state_detailed': 'employee_inbox'})

                        if len(followers_obj.search([
                            ('res_model', '=', 'ac.operation'),
                            ('res_id', '=', operation_id.id),
                            ('partner_id', '=', lline.transfer_ref.user_id.partner_id.id)
                        ])) == 0:
                            reg = {
                                'res_id': operation_id.id,
                                'res_model': 'ac.operation',
                                'partner_id': lline.transfer_ref.user_id.partner_id.id
                            }

                            followers_obj.create(reg)

                        action_id = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').id
                        msg_data = {
                            'subject': 'إحالة معاملة',
                            'date': datetime.today(),
                            'body': 'لقد تم إحالة هذه المعاملة : ' +
                                    '<a href="http://' + host + '/web#id=' + str(operation_id.id) +
                                    '&view_type=form&action=' + str(action_id) +
                                    '&model=ac.operation">' + str(operation_id.subject) + '</a>' +
                                    ' لكم قصد : ' +
                                    '<br/><b>' + lline.transfer_guidance.name + '</b><br/>' +
                                    'التعليق : ' + (lline.notes or ''),
                            # 'res_id': operation_id.id,
                            # 'model': 'ac.operation',
                            'message_type': 'notification',
                        }
                        msg_id = message_obj.create(msg_data)

                        notif_data = {
                            'mail_message_id': msg_id.id,
                            'res_partner_id': lline.transfer_ref.user_id.partner_id.id,
                            'is_read': False,
                            'notification_type': 'email'
                        }
                        notification_obj.create(notif_data)
                        llink = '<a href="http://' + host + '/web#id=' + str(operation_id.id) + '&view_type=form&action=' + str(
                            action_id) + '&model=ac.operation">' + ' رابط المعاملة '+ str(operation_id.name) + '</a>'
                        if template:
                            template.send_mail(operation_id.id, force_send=True,
                                               email_values={'body_html': llink, 'email_to': lline.transfer_ref.user_id.partner_id.email})
                        #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in').read()[0]
                        #return True
                        continue

                    else:
                        raise UserError(_("الرجاء التأكد من البيانات !"))

                msg = "المعاملة الآن عند "
                if len(departments_name):
                    msg += 'الادارات : '
                    for dep in departments_name:
                        msg += dep + ', '

                if len(employees_name):
                    msg += 'الموظفين : '
                    for emp in employees_name:
                        msg += emp + ', '
                operation_id.write({
                    'message': msg,
                    'department_ids': [(6, 0, departments_ids)]
                })

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ACOperationTransfer, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                      toolbar=toolbar,
                                                                      submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='department_id']")
        d_obj = self.env['hr.department']
        for node in nodes:
            if self.env.user.has_group('ejad_erp_administrative_communications.group_operation_all_department'):
                node.set('domain', str([('id', '!=', -1)]))
            else:
                ddomain= []
                employee = self.env.user.employee_ids and self.env.user.employee_ids[0] or False
                if employee:
                    if self.env.user.has_group(
                        'ejad_erp_administrative_communications.group_operation_own_department'):
                        ddomain.append(employee.department_id.id)
                    if self.env.user.has_group(
                        'ejad_erp_administrative_communications.group_operation_up_department'):
                        ddomain.append(employee.department_id.parent_id.id)
                    if self.env.user.has_group(
                        'ejad_erp_administrative_communications.group_operation_down_department'):
                        for d in d_obj.search([('id', 'child_of', employee.department_id.id or [])]):
                            ddomain.append(d.id)
                    if self.env.user.has_group(
                        'ejad_erp_administrative_communications.group_operation_level_department'):
                        if employee.department_id.parent_id:
                            for d in d_obj.search([('parent_id', '=', employee.department_id.parent_id.id)]):
                                ddomain.append(d.id)
                    if self.env.user.has_group(
                        'ejad_erp_administrative_communications.group_operation_first_department'):
                        if employee.department_id:
                            for d in d_obj.search([('parent_id', '=', employee.department_id.id)]):
                                ddomain.append(d.id)
                node.set('domain', str([('id', 'in', ddomain)]))
        res['arch'] = etree.tostring(doc)
        return res
