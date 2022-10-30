/** @odoo-module **/
import { lostConnectionHandler, rpcErrorHandler } from '@web/core/errors/error_handlers';
import { UncaughtPromiseError } from "@web/core/errors/error_service";
const { ConnectionLostError, RPCError } = require('@web/core/network/rpc_service');
const { browser } = require("@web/core/browser/browser");
import { registry } from "@web/core/registry";
const errorHandlerRegistry = registry.category("error_handlers");

// -----------------------------------------------------------------------------
// Lost connection errors
// -----------------------------------------------------------------------------
let connectionLostNotifRemove = null;
/**
 * @param {OdooEnv} env
 * @param {UncaughError} error
 * @param {Error} originalError
 * @returns {boolean}
 */
export function lostConnectionHandlerCustom(env, error, originalError) {
    if (!(error instanceof UncaughtPromiseError)) {
        return false;
    }
    if (originalError instanceof ConnectionLostError) {
        if (connectionLostNotifRemove) {
            // notification already displayed (can occur if there were several
            // concurrent rpcs when the connection was lost)
            return true;
        }
        connectionLostNotifRemove = $('<div class="oe_cu_indicator_warning">' + ("Trying to reconnect... ") + '<i class="fa fa-refresh fa-spin"></i></div>').fadeIn("slow");
        connectionLostNotifRemove.prependTo("html");
        $('html').addClass('__indicator');
        let delay = 2000;
        browser.setTimeout(function checkConnection() {
            env.services
                .rpc("/web/webclient/version_info", {})
                .then(function() {
                    connectionLostNotifRemove.animate({ backgroundColor: '#00aa00', opacity: 1 }, 1000);
                    connectionLostNotifRemove.removeClass('oe_cu_indicator_warning')
                        .addClass('oe_cu_indicator_sucsess')
                        .html(("You are back online"))
                        .delay(2000).slideUp('slow', function() {
                            $(this).remove();
                            $('html').removeClass('__indicator');
                        });
                    connectionLostNotifRemove = null;
                    connectionLostNotifRemove();
                })
                .catch(() => {
                    // exponential backoff, with some jitter
                    delay = delay * 1.5 + 500 * Math.random();
                    browser.setTimeout(checkConnection, delay);
                });
        }, delay);
        return true;
    }
}

function legacyRPCErrorHandlerCustom(env, error, originalError) {
    if (
        originalError &&
        originalError.legacy &&
        originalError.message &&
        (originalError.message instanceof RPCError ||
            originalError.message instanceof ConnectionLostError)
    ) {
        const event = originalError.event;
        originalError = originalError.message;
        if (event.isDefaultPrevented()) {
            // in theory, here, event was already handled
            error.unhandledRejectionEvent.preventDefault();
            return true;
        }
        event.preventDefault();
        if (originalError instanceof ConnectionLostError) {
            return lostConnectionHandlerCustom(env, error, originalError);
        }
        return rpcErrorHandler(env, error, originalError);
    }
    return false;
}
errorHandlerRegistry.remove('legacyRPCErrorHandler')
errorHandlerRegistry.add("legacyRPCErrorHandler", legacyRPCErrorHandlerCustom, { sequence: 2 });
errorHandlerRegistry.remove('lostConnectionHandler')
errorHandlerRegistry.add("lostConnectionHandler", lostConnectionHandlerCustom, { sequence: 98 });