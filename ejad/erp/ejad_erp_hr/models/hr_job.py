import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class HRRecruitmentStage(models.Model):
    _inherit = 'hr.recruitment.stage'
    active = fields.Boolean('Active', default=True,)


class HRJobs(models.Model):
    _inherit = 'hr.applicant'
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', ondelete='restrict', tracking=True,
                               domain="['|', ('job_ids', '=', False), ('job_ids', '=', job_id)]",
                               copy=False, index=True,
                               group_expand='_read_group_stage_ids',
                               default=lambda self: self.env.ref('ejad_erp_hr.stage_job1').id)

    def action_dept_manager(self):
        for rec in self:
            rec.write({'stage_id': self.env.ref('ejad_erp_hr.stage_job2').id})

    def action_support_service_manager(self):
        for rec in self:
            rec.write({'stage_id': self.env.ref('ejad_erp_hr.stage_job3').id})

    def action_office_leader(self):
        for rec in self:
            rec.write({'stage_id': self.env.ref('ejad_erp_hr.stage_job4').id})

    def action_done(self):
        for rec in self:
            rec.write({'stage_id': self.env.ref('ejad_erp_hr.stage_job5').id})


class HRJobs(models.Model):
    _inherit = 'hr.job'

    reward_dean_of_college_center = fields.Float('مكافأة منصب عميد كلية أو عمادة مركز')
    reward_deputy_college_center = fields.Float('مكافأة منصب وكيل كلية أو وكيل مركز')
    reward_admin_college_center = fields.Float('مكافأة منصب أمين كلية او مركز')
    reward_manager_college = fields.Float('مكافأة منصب رئيس قسم علمي (كليات فقط)')
    reward_security_department = fields.Float('مكافأة قسم الأمن والسلامة (الشؤون العامة)')
    reward_reception_department = fields.Float('مكافأة قسم الإستقبال و السنترال  (الضيافة والإسكان)')
    reward_financial_department = fields.Float('مكافأة قسم الصندوق (الإدارة المالية)')
    reward_government_relation = fields.Float('مكافأة مندوب علاقات حكومية')
    reward_calling = fields.Float('مكافأة بدل اتصال (بعض الموظفين)')
    reward_passport_representative_external = fields.Float('مكافأة مندوب جوازات خارجي')
    reward_passport_representative_internal = fields.Float('مكافأة مندوب جوازات داخلي')
    reward_purchase_representative = fields.Float('مكافأة مندوب مشتريات')
    reward_revenue_collector = fields.Float('مكافأة محصل إيرادات')
    other_reward = fields.Float('مكافأة أخرى')
    food_reward = fields.Float('مكافأة طعام')
