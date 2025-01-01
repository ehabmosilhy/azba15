from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = "res.company"


    l10n_sa_api_mode = fields.Selection(
        [('sandbox', 'Sandbox'), ('preprod', 'Simulation (Pre-Production)'), ('prod', 'Production')],
        help="Specifies which API the system should use", required=False,
        default='', copy=False)

