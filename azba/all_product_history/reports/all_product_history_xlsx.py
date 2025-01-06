# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)

_logger = logging.getLogger(__name__)


class ReportAllProductHistoryXlsx(models.AbstractModel):
    _name = "report.all_product_history.report_all_product_history_xlsx"
    _description = "All Product History XLSX"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, objects):
        self._define_formats(workbook)
        for product in objects.product_ids:
            for ws_params in self._get_ws_params(workbook, data, product):
                ws_name = ws_params.get("ws_name")
                ws_name = self._check_ws_name(ws_name)
                ws = workbook.add_worksheet(ws_name)
                generate_ws_method = getattr(self, ws_params["generate_ws_method"])
                generate_ws_method(workbook, ws, ws_params, data, objects, product)

    def _get_report_values(self, docids, data=None):
        wizard_id = data["wizard_id"]
        report = self.env["report.all.product.history"].browse(wizard_id)
        report._compute_results()
        return {
            "doc_ids": docids,
            "doc_model": "all.product.history.wizard",
            "docs": report,
            "date_from": report.date_from,
            "date_to": report.date_to,
        }

    def _get_ws_params(self, wb, data, product):
        filter_template = {
            "1_date_from": {
                "header": {"value": "Date from"},
                "data": {
                    "value": self._render("date_from"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            "2_date_to": {
                "header": {"value": "Date to"},
                "data": {
                    "value": self._render("date_to"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            "3_location": {
                "header": {"value": "Location"},
                "data": {
                    "value": self._render("location"),
                    "format": FORMATS["format_tcell_center"],
                },
            },
        }
        initial_template = {
            "1_ref": {
                "data": {"value": "Initial Balance", "format": FORMATS["format_tcell_center"]},
                "colspan": 4,
            },
            "2_balance": {
                "data": {
                    "value": self._render("initial_balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                }
            },
        }
        all_product_history_template = {
            "1_initial": {
                "header": {"value": "Initial Balance"},
                "data": {
                    "value": self._render("initial_balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 25,
            },
            "2_input": {
                "header": {"value": "In"},
                "data": {
                    "value": self._render("input"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 25,
            },
            "3_output": {
                "header": {"value": "Out"},
                "data": {
                    "value": self._render("output"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 25,
            },
            "4_balance": {
                "header": {"value": "Final Balance"},
                "data": {
                    "value": self._render("balance"),
                    "format": FORMATS["format_tcell_amount_right"],
                },
                "width": 25,
            },
        }

        ws_params = {
            "ws_name": product.name,
            "generate_ws_method": "_all_product_history_report",
            "title": "All Product History - {}".format(product.name),
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list_initial": [k for k in sorted(initial_template.keys())],
            "col_specs_initial": initial_template,
            "wanted_list": [k for k in sorted(all_product_history_template.keys())],
            "col_specs": all_product_history_template,
        }
        return [ws_params]

    def _all_product_history_report(self, wb, ws, ws_params, data, objects, product):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])

        self._set_column_width(ws, ws_params)

        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )

        product_line = objects.results.filtered(lambda l: l.product_id == product)
        if product_line:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "initial_balance": product_line.initial_balance,
                    "input": product_line.product_in,
                    "output": product_line.product_out,
                    "balance": product_line.balance,
                },
                default_format=FORMATS["format_tcell_amount_right"],
            )
        else:
            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    "initial_balance": "",
                    "input": "",
                    "output": "",
                    "balance": "",
                },
                default_format=FORMATS["format_tcell_amount_right"],
            )
