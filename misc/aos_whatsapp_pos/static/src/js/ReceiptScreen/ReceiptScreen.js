/*odoo.define('aos_whatsapp_pos.ReceiptScreen', function(require) {
    'use strict';

    const { useRef } = owl.hooks;
    //const { is_whatsapp } = require('web.utils');
    const { useListener } = require('web.custom_hooks');
    const { useContext } = owl.hooks;
    const { Printer } = require('point_of_sale.Printer');
    const PosComponent = require('point_of_sale.PosComponent');
    const OrderManagementScreen = require('point_of_sale.OrderManagementScreen');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const contexts = require('point_of_sale.PosContext');

    const WhatsAppPosResReceiptScreen = ReceiptScreen =>
        class extends ReceiptScreen {
            constructor() {
                super(...arguments);
                this.orderReceiptWhatsApp = useRef('order-receipt');
                const order = this.currentOrder;
                const client = order.get_client();
            	const orderName = order.get_name();
                //this.orderUiState = useContext(order.uiState.ReceiptScreen);
                this.orderUiState.inputWhatsapp = this.orderUiState.inputWhatsapp || (client && client.whatsapp) || '';
                this.orderUiState.inputMessage = 'Dear *' + client.name + '*, Here is your electronic ticket for the '+ orderName +'.';
                //console.log('===inputWhatsapp=111=',this.orderUiState.inputWhatsapp,client)
                //this.is_whatsapp = is_whatsapp;
            }
            async onSendWhatsapp() {
                try {
                    await this._sendWhatsappToCustomer();
                    this.orderUiState.whatsappSuccessful = true;
                    this.orderUiState.whatsappNotice = 'Whatsapp sent.'
                } catch (error) {
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = 'Sending Whatsapp failed. Please try again.'
                }
                //console.log('=onSendWhatsapp=',this._sendWhatsappToCustomer())
            }
            
            async _sendWhatsappToCustomer() {
            	const printer = new Printer();
            	const receiptString = this.orderReceipt.comp.el.outerHTML;
            	const ticketImage = await printer.htmlToImg(receiptString);
            	const order = this.currentOrder;
            	const client = order.get_client();
            	const orderName = order.get_name();
            	const orderClient = { order: order, whatsapp: this.orderUiState.inputWhatsapp, message: this.orderUiState.inputMessage, name: client ? client.name : this.orderUiState.inputWhatsapp };
            	const order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
                await this.rpc({
                    model: 'pos.order',
                    method: 'action_whatsapp_to_customer',
                    args: [[order_server_id], orderName, orderClient, ticketImage],
                });
            }
        };

    Registries.Component.extend(ReceiptScreen, WhatsAppPosResReceiptScreen);

    return ReceiptScreen;
});*/

// BiProductScreen js

odoo.define('aos_whatsapp_pos.ReceiptScreen', function(require) {
	"use strict";
	
	const { useRef } = owl.hooks;
	const { useListener } = require('web.custom_hooks');
	const { Printer } = require('point_of_sale.Printer');
	const { useContext } = owl.hooks;
	const Registries = require('point_of_sale.Registries');
	const ReceiptScreen = require('point_of_sale.ReceiptScreen');
	const contexts = require('point_of_sale.PosContext');

	const WhatsappReceiptScreen = (ReceiptScreen) =>
		class extends ReceiptScreen {
			constructor() {
				super(...arguments);
				let self = this;
                //this.orderReceiptWhatsApp = useRef('order-receipt');
                const order = this.currentOrder;
                const client = order.get_client();
            	const orderName = order.get_name();
				//const order = this.currentOrder;
				//this.orderUiState.inputWhatsapp = this.orderUiState.inputWhatsapp || (client && client.whatsapp) || '';
                //this.orderUiState.inputMessage = 'Dear *' + (client && client.name || 'Customer') + '*, Here is your electronic ticket for the '+ orderName +'.';
				//this.is_whatsapp = is_whatsapp;
				//setTimeout(async () => await this.onSendWhatsapp(), 0);
				/*let config = this.env.pos.config;
				let stock_update = this.env.pos.company.point_of_sale_update_stock_quantities;
				if (config.pos_display_stock === true && stock_update == 'real' && 
					(config.pos_stock_type == 'onhand' || config.pos_stock_type == 'available'))
				{
					order.get_orderlines().forEach(function (line) {
						var product = line.product;
						product['bi_on_hand'] -= line.get_quantity();
						product['bi_available'] -= line.get_quantity();
						product.qty_available -= line.get_quantity();
						self.load_product_qty(product);
					}) 
				}
				this.env.pos.set("is_sync",true);*/
				const pos_config = this.env.pos.config;
				let message = pos_config.whatsapp_default_message.replace("_CUSTOMER_", client && client.name || 'Customer');
				//console.log('==WhatsappReceiptScreen=1=',order)
				//console.log('==WhatsappReceiptScreen=2=',pos_config.whatsapp_default_message)
                this.orderUiState = useContext(order.uiState.ReceiptScreen);
                this.orderUiState.inputWhatsapp = this.orderUiState.inputWhatsapp || (client && client.whatsapp) || '';
                this.orderUiState.inputMessage = message + ' ' + orderName +'.';
			}
			async is_whatsapp(value) {
                const order = this.currentOrder;
                const config = this.env.pos.config;
				// console.log('==value==',value)
	            var result = await this.rpc({
	                model: 'pos.order',
	                method: 'get_number_exist',
	                args: [[], config, order, value],
	            });	
	            return result;
	        }
            async onSendWhatsapp() {
                // const config = this.env.pos.config;
                // const config = this.env.pos.config;
                // if (!config.whatsapp_server_id) {
                //     this.orderUiState.whatsappSuccessful = false;
                //     this.orderUiState.whatsappNotice = this.env._t('Whatsapp server should define first!.');
                //     return;
                // }
				// let whatsapp = await this.is_whatsapp(this.orderUiState.inputWhatsapp);
                // if (!whatsapp) {
                //     this.orderUiState.whatsappSuccessful = false;
                //     this.orderUiState.whatsappNotice = this.env._t('Whatsapp number is empty / not exist.');
                //     return;
                // }
                try {
                    await this._sendWhatsappToCustomer();
                    this.orderUiState.whatsappSuccessful = true;
                    this.orderUiState.whatsappNotice = 'Whatsapp sent.'
                } catch (error) {
					console.log('error',error)
                    this.orderUiState.whatsappSuccessful = false;
                    this.orderUiState.whatsappNotice = 'Sending Whatsapp failed. Please try again.'
                }
                //console.log('=onSendWhatsapp=',this._sendWhatsappToCustomer())
            }
            
            async _sendWhatsappToCustomer() {
				//console.log('START=xx>')
                const printer = new Printer(null, this.env.pos);
                const receiptString = this.orderReceipt.comp.el.outerHTML;
                const ticketImage = await printer.htmlToImg(receiptString);
				const order = this.currentOrder;
				const client = order.get_client();
				const orderName = order.get_name();
				const orderClient = { order: order, whatsapp: this.orderUiState.inputWhatsapp, message: this.orderUiState.inputMessage, name: client ? client.name : this.orderUiState.inputWhatsapp };
				const order_server_id = this.env.pos.validated_orders_name_server_id_map[orderName];
				await this.rpc({
                    model: 'pos.order',
                    method: 'action_whatsapp_to_customer',
                    args: [[order_server_id], orderName, orderClient, ticketImage],
                });
				//console.log('END=>')
            }
			/*mounted() {
                setTimeout(async () => {
                    let images = this.orderReceipt.el.getElementsByTagName('img');
                    for(let image of images) {
                        await image.decode();
                    }
                    await this.handleAutoPrint();
                }, 0);
                $('.pos-receipt-header').hide();
            }*/

			/*load_product_qty(product){
				let product_qty_final = $("[data-product-id='"+product.id+"'] #stockqty");
				product_qty_final.html(product['bi_on_hand'])

				let product_qty_avail = $("[data-product-id='"+product.id+"'] #availqty");
				product_qty_avail.html(product['bi_available']);
			}*/
		};

	Registries.Component.extend(ReceiptScreen, WhatsappReceiptScreen);

	return ReceiptScreen;

});

