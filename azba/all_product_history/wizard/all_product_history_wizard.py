# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AllProductHistoryWizard(models.TransientModel):
    _name = "all.product.history.wizard"
    _description = "All Product History Wizard"

    date_range_id = fields.Many2one(comodel_name="date.range", string="Period")
    date_from = fields.Date(string="Start Date")
    date_to = fields.Date(string="End Date")
    product_ids = fields.Many2many(
        comodel_name="product.product", string="Products", required=True
    )

    @api.onchange("date_range_id")
    def _onchange_date_range_id(self):
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    def button_export_html(self):
        self.ensure_one()
        action = self.env.ref("all_product_history.action_report_all_product_history_html")
        vals = action.sudo().read()[0]
        context = vals.get("context", {})
        if context:
            context = safe_eval(context)
        model = self.env["report.all.product.history"]
        report = model.create(self._prepare_all_product_history())
        context["active_id"] = report.id
        context["active_ids"] = report.ids
        vals["context"] = context
        return vals

    def button_export_pdf(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def button_export_xlsx(self):
        self.ensure_one()
        report_type = "xlsx"
        return self._export(report_type)

    def _prepare_all_product_history(self):
        self.ensure_one()
        return {
            "date_from": self.date_from,
            "date_to": self.date_to or fields.Date.Context_today(self),
            "product_ids": [(6, 0, self.product_ids.ids)],
        }

    def _export(self, report_type):
        model = self.env["report.all.product.history"]
        report = model.create(self._prepare_all_product_history())
        return report.print_report(report_type)
