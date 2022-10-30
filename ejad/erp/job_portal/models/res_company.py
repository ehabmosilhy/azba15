# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    social_skype = fields.Char('Skype Account')
    social_vimeo = fields.Char('Vimeo Account', default="https://vimeo.com")
    social_rss = fields.Char('RSS Account')
    social_instagram = fields.Char(
        'Instagram Account', default='https://www.instagram.com/?hl=en')


class Website(models.Model):
    _inherit = "website"

    social_skype = fields.Char(related="company_id.social_skype")
    social_vimeo = fields.Char(related="company_id.social_vimeo")
    social_rss = fields.Char(related="company_id.social_rss")
    social_instagram = fields.Char(related="company_id.social_instagram")
