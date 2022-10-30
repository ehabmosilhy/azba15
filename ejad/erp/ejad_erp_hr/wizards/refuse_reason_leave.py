# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class LeaverefuseWizard(models.TransientModel):
    _name = "leave.refuse.wizard"

    refuse_message = fields.Text(string="Reason Message", required=True)

    def refuse_reason(self):
        self = self.sudo()
        context = dict(self._context or {})
        active_id = context.get("active_id", False)
        leave_id = self.env["hr.leave"].search([("id", "=", active_id)])
        leave_id.write({'state1': 'refuse',"refuse_message": self.refuse_message})
        leave_id.action_refuse()
        if leave_id.employee_id:
            template_leave_refuse = self.env.ref("ejad_erp_hr.hr_leave_refuse_notify_employee_mail_template")

            try:

                self.env['mail.template'].sudo().browse(template_leave_refuse.id).send_mail(leave_id.id)
                leave_id.message_post(body=("لقد تم الرفض على طلب الاجازة %s") % (
                leave_id.holiday_status_id.name), message_type='email',
                                  subject='لقد تم الرفض على طلب الاجازة')
            except:
                pass

        return {"type": "ir.actions.act_window_close"}
