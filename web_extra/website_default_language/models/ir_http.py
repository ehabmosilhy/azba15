
import odoo
from odoo import api, models, registry, exceptions, tools, http
from odoo.addons.base.models import ir_http
from odoo.addons.base.models.ir_http import RequestUID
from odoo.addons.base.models.qweb import QWebException
from odoo.http import request
from odoo.osv import expression
from odoo.tools import config, ustr, pycompat


class IrHttpInh(models.AbstractModel):
    _inherit = ['ir.http']

    @classmethod
    def _add_dispatch_parameters(cls, func):
        super(IrHttpInh, cls)._add_dispatch_parameters(func)
        Lang = request.env['res.lang']
        # only called for is_frontend request
        if request.routing_iteration == 1:
            context = dict(request.context)
            path = request.httprequest.path.split('/')
            is_a_bot = cls.is_a_bot()
            lang_codes = [code for code, *_ in Lang.get_available()]
            nearest_lang = not func and cls.get_nearest_lang(Lang._lang_get_code(path[1]))
            if 'en' in path:
                lang_code = cls.get_nearest_lang(Lang._lang_get_code('en'))
            elif not path[1]:
                lang_code = cls.get_nearest_lang(Lang._lang_get_code('ar'))
            elif path[1] and not nearest_lang and request.lang.code == cls.get_nearest_lang(Lang._lang_get_code('en')):
                lang_code = cls.get_nearest_lang(Lang._lang_get_code('en'))
            else:
                lang_code = cls.get_nearest_lang(Lang._lang_get_code('ar'))

            cook_lang = lang_code

            cook_lang = cook_lang in lang_codes and cook_lang

            if nearest_lang:
                lang = Lang._lang_get(nearest_lang)
            else:
                nearest_ctx_lg = not is_a_bot and cls.get_nearest_lang(request.env.context.get('lang'))
                nearest_ctx_lg = nearest_ctx_lg in lang_codes and nearest_ctx_lg
                preferred_lang = Lang._lang_get(cook_lang or nearest_ctx_lg)
                lang = preferred_lang or cls._get_default_lang()

            request.lang = lang
            context['lang'] = lang._get_cached('code')

            # bind modified context
            request.context = context