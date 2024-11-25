from odoo import models, fields
from odoo import api, fields, models, _


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    def action_asset_modify(self):
        """ Returns an action opening the asset modification wizard.
        """
        self.ensure_one()
        new_wizard = self.env['asset.modify'].create({
            'asset_id': self.id,
            'name': 'Modify Asset',
        })
        return {
            'name': _('Modify Asset'),
            'view_mode': 'form',
            'res_model': 'asset.modify',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': new_wizard.id,
            'context': self.env.context,
        }


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    def write(self, vals):
        # Ensure method_period is a string when writing to the asset
        if 'method_period' in vals and isinstance(vals['method_period'], int):
            vals['method_period'] = str(vals['method_period'])
        return super(AssetModify, self).write(vals)

    @api.model
    def create(self, vals):
        # Ensure method_period is a string when creating
        if 'method_period' in vals and isinstance(vals['method_period'], int):
            vals['method_period'] = str(vals['method_period'])
        return super(AssetModify, self).create(vals)