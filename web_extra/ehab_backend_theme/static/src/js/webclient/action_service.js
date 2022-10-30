/** @odoo-module **/
import { registry } from "@web/core/registry";

function makeActionManagerCustom(env) {
    if ("ontouchstart" in window || "onmsgesturechange" in window) {
        Object.defineProperty(env, 'isSmall', {
            get() {
                return true;
            },
        });
    }
}

export const actionServiceCustom = {
    dependencies: ["ui"],
    start(env) {
        return makeActionManagerCustom(env);
    },
};

registry.category("services").add("action_service_custom", actionServiceCustom);