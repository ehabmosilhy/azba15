from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = "res.partner"
    date_relation_start = fields.Date(string="تاريخ بداية التعامل")
    @api.depends('is_company', 'name', 'parent_id.display_name', 'type', 'company_name', 'code')
    def _compute_display_name(self):
        for partner in self:
            partner.display_name = f'[{partner.code}] {partner.name}' if partner.code else partner.name or ''

    english_name = fields.Char()
    code = fields.Char(string="الكود Code")
    district = fields.Char(string="الحي District")
    display_name = fields.Char(compute='_compute_display_name', store=True, readonly=False)

    pos_config_ids = fields.Many2many("pos.config", string="Routes المسارات")

    _sql_constraints = [('code_uniq', 'unique (code)', """Code must be unique هذا الكود موجود من قبل!""")]

    def name_get(self):
        result = []
        for rec in self:
            if rec.code:
                result.append((rec.id, '[%s] - %s' % (rec.code, rec.name)))
            else:
                result.append((rec.id, '%s' % (rec.name)))
        return result