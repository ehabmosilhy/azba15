# -*- coding: utf-8 -*-
# (C) 2018 Smile (<https://www.smile.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import service

from ..tools import PerfLogger, profile

native_execute_cr = service.model.execute_cr


def execute_cr(cr, uid, obj, method, *args, **kw):
    logger = PerfLogger()
    logger.on_enter(cr, uid, '/xmlrpc/object', obj, method)

    try:
        import logging
        _logger = logging.getLogger(__name__)
        logger.on_leave()
        _logger.info(
            f"::::::service:::::: uid:{uid} obj: {obj}, method:{method}, args: {args}, kw: {kw} ")
    except:
        pass

    try:
        res = profile(native_execute_cr)(cr, uid, obj, method, *args, **kw)
        logger.log_call(args, kw, res)
        return res
    except Exception as e:
        logger.log_call(args, kw, err=e)
        raise
    finally:
        logger.on_leave()


service.model.execute_cr = execute_cr
