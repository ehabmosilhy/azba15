/** @odoo-module **/
odoo.define('whatsapp', function (require) {
    'use strict';

    var core = require('web.core');
    var rpc = require('web.rpc');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var Widget = require('web.Widget');
    var _t = core._t;
    

    var SendWhatsAppButton = Widget.extend({
        template: 'SendWhatsAppButton',
        events: {
            'click a.login_as': 'login_as',
        },
        login_as: function() {                        
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                name: _t('Compose Message'),
                views: [[false, 'form']],
                res_model: 'whatsapp.compose.message',
                target: 'new',
            });
        }
    });
    
    // var SendWhatsAppButton = Widget.extend({
    //     template: 'SendWhatsAppButton',
    //     events: {
    //         'click a.login_back': 'login_back',
    //     },
    //     login_back: function() {                        
    //         this.do_action({
    //             type: 'ir.actions.act_url',
    //             url: '/web/login_back',
    //             target: 'self'
    //         });
    //     }
    // });
                
    if (odoo.debug && session.is_system)
    	SystrayMenu.Items.push(SendWhatsAppButton);
    
    // if (session.impersonate)
    // 	SystrayMenu.Items.push(LoginBack);

});

// import { registerPatch } from '@mail/model/model_core';
// import core from 'web.core';

// registerPatch({
//     name: 'Chatter',
//     recordMethods: {
//         onClickSendWhatsapp() {
//             console.log('==messaging==',this.thread.model,this.thread.id,this.thread.id)
//             const partner_ids = this.thread.followers.map(follower => follower.partner.id)
//             const action = {
//                 type: 'ir.actions.act_window',
//                 res_model: 'whatsapp.compose.message',
//                 view_mode: 'form',
//                 views: [[false, 'form']],
//                 name: this.env._t("Send Whatsapp"),
//                 target: 'new',
//                 context: {
//                     active_ids: [this.thread.id],
//                     active_model: this.thread.model,
//                     default_subject: this.thread.name,
//                     default_partner_ids: partner_ids,
//                 },
//             };
//             this.env.services.action.doAction(
//                 action,
//                 {
//                     onClose: async () => {
//                         if (!this.exists() && !this.thread) {
//                             return;
//                         }
//                         this.reloadParentView();
//                     },
//                 }
//             );
//         },
//     },
// });
