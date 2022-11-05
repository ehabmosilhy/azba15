from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"
    _order = "display_name"

    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'code')
    def _compute_display_name(self):
        for partner in self:
            partner.display_name = f'[{partner.code}] {partner.name}' if partner.code else partner.name or ''


    english_name = fields.Char()
    code = fields.Char(string="الكود Code")
    district = fields.Many2one("geography.district", string="الحي District")
    # is_delegate = fields.Boolean('Is delegate', default=False)
    display_name = fields.Char(compute='_compute_display_name')


    # def _get_name(self):
    #     """ Utility method to allow name_get to be overrided without re-browse the partner """
    #     partner = self
    #     name = f'[{partner.code}] {partner.name}' if partner.code else partner.name or ''
    #
    #     return name
