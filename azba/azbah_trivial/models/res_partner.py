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
    main_config_id=fields.Many2one("pos.config",string="Main Config المسار الرئيسى")

    _sql_constraints = [('code_uniq', 'unique (code)', """Code must be unique هذا الكود موجود من قبل!""")]

    def name_get(self):
        result = []
        for rec in self:
            if rec.code:
                result.append((rec.id, '[%s] - %s' % (rec.code, rec.name)))
            else:
                result.append((rec.id, '%s' % (rec.name)))
        return result

    def map_config_to_tags(self,configs):
        # Add all configs to categories table
        for conf in configs:
            cat_id = self.env['res.partner.category'].search([('name', '=', conf.name)])
            if not cat_id:
                cat_id = self.env['res.partner.category'].create({'name': conf.name})

    @api.onchange('main_config_id')
    def onchange_main_config_id(self):
        configs = self.env['pos.config'].search([])
        all_config_names = configs.mapped("name")

        # make sure all configs exist in categories
        self.map_config_to_tags(configs)

        for rec in self:
            # get non pos.config tags, which are not pos.configs ليست مسارات
            cat_ids = [cat_id.id for cat_id in rec.category_id if cat_id.name not in all_config_names]

            # Add the main config
            for conf in rec.main_config_id:
                cat_id = self.env['res.partner.category'].search([('name', '=', conf.name)])
                if not cat_id:
                    cat_id = self.env['res.partner.category'].create({'name': conf.name})
                cat_ids.append(cat_id.id)
            cat_ids = list(set(cat_ids))
            rec.category_id = [(6, 0, cat_ids)]




