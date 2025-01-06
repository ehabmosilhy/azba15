# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AllProductHistoryView(models.TransientModel):
    _name = "all.product.history.view"
    _description = "All Product History View"
    _order = "product_id"

    product_id = fields.Many2one(comodel_name="product.product")
    product_in = fields.Float()
    product_out = fields.Float()


class AllProductHistoryReport(models.TransientModel):
    _name = "report.all.product.history"
    _description = "All Product History Report"

    # Filters fields, used for data computation
    date_from = fields.Date()
    date_to = fields.Date()
    product_ids = fields.Many2many(comodel_name="product.product")
    location_id = fields.Many2one(comodel_name="stock.location")

    # Data fields, used to browse report data
    results = fields.Many2many(
        comodel_name="all.product.history.view",
        compute="_compute_results",
        help="Use compute fields, so there is nothing store in database",
    )

    def _compute_results(self):
        self.ensure_one()
        self.date_to = self.date_to or fields.Date.context_today(self)
        locations = self.env["stock.location"].search([])

        query = """
            SELECT move.product_id,
                SUM(CASE WHEN move.location_dest_id in %s THEN move.product_qty ELSE 0 END) as product_in,
                SUM(CASE WHEN move.location_id in %s THEN move.product_qty ELSE 0 END) as product_out
            FROM stock_move move
            WHERE (move.location_id in %s or move.location_dest_id in %s)
                and move.state = 'done' and move.product_id in %s
                and CAST(move.date AS date) <= %s
            GROUP BY move.product_id
            ORDER BY move.product_id
        """
        params = (
            tuple(locations.ids),
            tuple(locations.ids),
            tuple(locations.ids),
            tuple(locations.ids),
            tuple(self.product_ids.ids),
            self.date_to,
        )
        
        self._cr.execute(query, params)
        all_product_history_results = self._cr.dictfetchall()
        ReportLine = self.env["all.product.history.view"]
        self.results = [ReportLine.new(line).id for line in all_product_history_results]

    def _get_initial(self, product_id):
        """Get the total quantity for a product"""
        if not product_id:
            return 0.0
        product_line = self.results.filtered(lambda l: l.product_id.id == product_id.id)
        if not product_line:
            return 0.0
        return product_line.product_in - product_line.product_out

    def print_report(self, report_type="qweb"):
        self.ensure_one()
        action = (
            report_type == "xlsx"
            and self.env.ref("all_product_history.action_all_product_history_xlsx")
            or self.env.ref("all_product_history.action_all_product_history_pdf")
        )
        return action.report_action(self, config=False)
