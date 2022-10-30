# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class DynamicWorkflowCategory(models.Model):
    _name = "dynamic.workflow.category"
    _description = "Dynamic Workflow Category"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name", required=True, tracking=True)
    code = fields.Char(string="Code", tracking=True)
    code_category = fields.Char(string="Code Category", size=1, tracking=True)

    is_old = fields.Boolean('is old ?')  # to help filtering the services if it's old or new
    project_type_ids = fields.One2many("workflow.project.type", "dynamic_workflow_category_id")
    register_old_stage_ids = fields.Many2many("dynamic.workflow.stage", "dynamic_workflow_category_stage",
                                              "dynamic_workflow_category_id", "stage_id", tracking=True)

    category_level = fields.Selection([("principal", "رئيسية"), ("secondary", "فرعية")],
                                      required=True, tracking=True)

    principal_category_id = fields.Many2one("dynamic.workflow.category", string="Principal category",
                                            tracking=True)
    secondary_category_ids = fields.One2many("dynamic.workflow.category", "principal_category_id",
                                             string="Secondary categories", tracking=True)

    _sql_constraints = [("dynamic_code_unique_constraint", "unique(code_category)", "The category code must be unique !")]

    @api.model
    def create(self, values):
        if values.get("register_old_stage_ids", False):
            stage_ids = values.get("register_old_stage_ids", False)[0][2]
            self.check_validate_stages(stage_ids)
        dynamic_workflow_category = super(DynamicWorkflowCategory, self).create(values)
        return dynamic_workflow_category

    def write(self, values):
        if values.get("register_old_stage_ids", False):
            stage_ids = values.get("register_old_stage_ids", False)[0][2]
            self.check_validate_stages(stage_ids)
        res = super(DynamicWorkflowCategory, self).write(values)

        return res

    def check_validate_stages(self, stage_ids):
        stage_obj = self.env["dynamic.workflow.stage"]
        first_stage_number = 0
        last_stage_number = 0
        success_stage_number = 0
        for stage in stage_obj.browse(stage_ids):
            if stage.is_success_type:
                success_stage_number += 1
            if stage.is_refuse_type:
                last_stage_number += 1
            if stage.is_first_type:
                first_stage_number += 1
        if first_stage_number > 1:
            raise ValidationError(_("You have many first stages"))
        if first_stage_number == 0:
            raise ValidationError(_("You have to put a stage of first"))
        if success_stage_number > 1:
            raise ValidationError(_("You have many success stages"))
        if success_stage_number == 0:
            raise ValidationError(_("You have to put a stage of success"))
        if last_stage_number > 1:
            raise ValidationError(_("You have many last stages"))
        if last_stage_number == 0:
            raise ValidationError(_("You have to put stage of refuse"))
