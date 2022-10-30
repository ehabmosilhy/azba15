odoo.define('theme_scita.quick_view', function(require) {
    'use strict';

    var sAnimations = require('website.content.snippets.animation');
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var wSaleUtils = require('website_sale.utils');
    var WebsiteSale = publicWidget.registry.WebsiteSale;
    // var productDetail = new publicWidget.registry.productDetail();
    var core = require('web.core');
    var QWeb = core.qweb;
    var core = require('web.core');
    var config = require('web.config');
    var VariantMixin = require('website_sale.VariantMixin');
    const cartHandlerMixin = wSaleUtils.cartHandlerMixin;
    require("web.zoomodoo");
    const {extraMenuUpdateCallbacks} = require('website.content.menu');
    const dom = require('web.dom');
    var xml_load = ajax.loadXML(
        '/website_sale_stock/static/src/xml/website_sale_stock_product_availability.xml',
        QWeb
    );

    // For quickview Start
    publicWidget.registry.quickView = publicWidget.Widget.extend({
        selector: "#wrapwrap",
        events: {
            'click .quick_view_sct_btn': 'quickViewData',
            'click .cart_view_sct_btn': 'cartViewData',
        },
        quickViewData: function(ev) {
            var element = ev.currentTarget;
            var product_id = $(element).attr('data-id');
            ajax.jsonRpc('/theme_scita/shop/quick_view', 'call',{'product_id':product_id}).then(function(data) {
                var sale = new publicWidget.registry.WebsiteSale();

                    $("#shop_quick_view_modal").html(data);
                    $("#shop_quick_view_modal").modal();
                    var WebsiteSale = new publicWidget.registry.WebsiteSale();
                    WebsiteSale.init();
                    var combination = [];
                    xml_load.then(function () {
                        var $message = $(QWeb.render(
                            'website_sale_stock.product_availability',
                            combination
                        ));
                        $('div.availability_messages').html($message);
                    });
                    $(".quick_cover").css("display", "block");
                    $("[data-attribute_exclusions]").on("change", function(ev) {
                        WebsiteSale.onChangeVariant(ev);
                    });
                    $("a.js_add_cart_json").on("click", function(ev) {
                        WebsiteSale._onClickAddCartJSON(ev);
                    });
                    $("a#add_to_cart").on("click", function(ev) {
                        $(this).closest('form').submit();
                    });
                    $(document).on('change', 'input[name="add_qty"]', function(ev){
                        WebsiteSale._onChangeAddQuantity(ev);
                    });
                    $( ".list-inline-item .css_attribute_color" ).change(function(ev) {
                        var $parent = $(ev.target).closest('.js_product');
                        $parent.find('.css_attribute_color').removeClass("active");
                        $parent.find('.css_attribute_color').filter(':has(input:checked)').addClass("active");
                    });
            });
        },
        cartViewData: function(ev) {
            var element = ev.currentTarget;
            var product_id = $(element).attr('data-id');
            ajax.jsonRpc('/theme_scita/shop/cart_view', 'call',{'product_id':product_id}).then(function(data) {
                $("#shop_cart_view_modal").html(data);
                $("#shop_cart_view_modal").modal();
            });
        }
    });
    // $(document).ready(function() {
    //     $('.oe_website_sale').each(function() {
    //         var oe_website_sale = this;
    //         $(oe_website_sale).on('mouseenter', '.oe_product_cart', function() {
    //             $(this).find('div.quick_button').show();
    //             $(this).addClass('Products_style');
    //         });

    //         $(oe_website_sale).on('mouseleave', '.oe_product_cart', function() {
    //             $(this).find('div.quick_button').hide();
    //             $(this).removeClass('Products_style');
    //         });
    //         $(oe_website_sale).on('click', '.quick_button', function(e) {
                
    //             e.preventDefault();
    //             $('.product_quickview_loder').show();
    //             var $form = $(this).closest('form');
    //             var product_id = parseInt($form.find('input[type="hidden"][name="quick_id"]').first().val(), 10);
    //             ajax.jsonRpc("/shop/quickmodal/", 'call', { 'product_id': product_id })
    //             .then(function(vals) {
    //                 $(oe_website_sale).append($(vals));
    //                 $('#quick_modal').modal({backdrop: 'static', keyboard: false});

    //                 $('#quick_modal').on('hidden.bs.modal', function () {
    //                     $('#quick_modal').remove();
    //                 })


    //                 $('.oe_website_sale .quick-submit').off('click').on('click', function(event) {
    //                     if (!event.isDefaultPrevented()) {
    //                         $(this).closest('form').submit();
    //                     }
    //                 });

    //                 $('.css_attribute_color input', oe_website_sale).on('change', function() {
    //                     $('.css_attribute_color').removeClass("active");
    //                     $('.css_attribute_color:has(input:checked)').addClass("active");
    //                 });

    //                 $('#add_to_cart').click(function(){
                        
    //                     $('#product_detail').on('click', '.modal-footer button:first', function() {
    //                         console.log($(this).html());
    //                     });
    //                 });
    //                 $('.product_quickview_loder').hide();
    //             });
    //         });

    //     });
    // });
    // For quickview End
//     publicWidget.registry.WebsiteSale.include({
//         _onChangeCombination: function (){
//             this._super.apply(this, arguments);
//             VariantMixin._onChangeCombinationProd.apply(this, arguments);
//         },
//         _onClickAdd: function (ev) {
//             ev.preventDefault();
//             if (!ev.currentTarget.classList.contains('ajax-add-to-cart') && !ev.currentTarget.classList.contains('not_product_page')) {
//                 this.getCartHandlerOptions(ev);
//             }
//             return this._handleAdd($(ev.currentTarget).closest('form'));
//         },
//         _submitForm: function () {
//             const params = this.rootProduct;
//             const $product = $('#product_detail');
   

//             params.add_qty = params.quantity;
//             params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
//             params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
//             if (this.isBuyNow) {
//                 params.express = true;
//                 return wUtils.sendRequest('/shop/cart/update', params);
//             } else if (this.stayOnPageOption) {
//                 //return this._addToCartInPage(params);
//             }
// //            return this.addToCart(params);

//             var frm = this.$form
//             var variant_count = frm.find('#add_to_cart').attr('variant-count');
//             var is_product = $(".not_product_page").length;
//             var is_ajax_cart = frm.find('.a-submit').hasClass('ajax-add-to-cart');
//             var is_quick_view = frm.find('.a-submit').hasClass('quick-add-to-cart');
//             var product_id = frm.find('#add_to_cart').attr('product-id');
//             var product_product = frm.find('input[name="product_id"]').val();
//             var product_custom_attribute_values = frm.find('input[name="product_custom_attribute_values"]').val();
//             var no_variant_attribute_values = frm.find('input[name="no_variant_attribute_values"]').val();
//             if(!product_id) {
//                product_id = frm.find('.a-submit').attr('product-id');
//             }
//             if(!variant_count) {
//                variant_count = frm.find('.a-submit').attr('variant-count');
//             }
//             /** Stock availability message for ajax cart popup */
//             var combination = [];
//             xml_load.then(function () {
//                 var $message = $(QWeb.render(
//                     'website_sale_stock.product_availability',
//                     combination
//                 ));
//                 $('div.availability_messages').html($message);
//             });
//             if(is_product == 0 || is_ajax_cart || is_quick_view) {
//                 /** if product has no variant then success popup will be opened */
//                 var product_product = frm.find('input[name="product_id"]').val();
//                 var quantity = frm.find('.quantity').val();
//                 if(!quantity) {
//                    quantity = 1;
//                 }
//                 ajax.jsonRpc('/shop/cart/update_custom', 'call',{'product_id':product_product,'add_qty':quantity, 'product_custom_attribute_values':product_custom_attribute_values,'no_variant_attribute_values':no_variant_attribute_values}).then(function(data) {
//                     var ajaxCart = new publicWidget.registry.ajax_cart();
//                     if(data) {
//                         $('.ajax_cart_modal > .cart_close').trigger('click');
//                         $('.quick_view_modal > .quick_close').trigger('click');
//                         var $quantity = $(".my_cart_quantity");
//                         var old_quantity = $quantity.html();
//                         $quantity.parent().parent().removeClass('d-none');
//                         $quantity.html(parseInt(quantity) + parseInt(old_quantity)).hide().fadeIn(600);

//                         if(!product_id) {
//                             product_id = frm.find('.product_template_id').attr('value');
//                         }
//                         setTimeout(function(){
//                             ajaxCart.ajaxCartSucess(product_id, product_product);
//                             $('input[name="product_custom_attribute_values"]').remove();
//                         }, 700);
//                         /* Resize menu */
//                         setTimeout(() => {
//                             $('#top_menu').trigger('resize');
//                         }, 200);
//                     }
//                 });
//             } else {
//             /** if product has multiple variants then variant selection popup will be opened */
//                 ajax.jsonRpc('/ajax_cart_item_data', 'call',{'product_id':product_id}).then(function(data) {
//                     var WebsiteSale = new publicWidget.registry.WebsiteSale();
//                     WebsiteSale._startZoom();
//                     if($("#wrap").hasClass('js_sale'))
//                     {
//                         $("#ajax_cart_model_shop .modal-body").html(data);
//                         $("#ajax_cart_model_shop").modal({keyboard: true});
//                     } else {
//                         $("#ajax_cart_model .modal-body").html(data);
//                         $("#ajax_cart_model").modal({keyboard: true});
//                     }
//                     $('#ajax_cart_model, #ajax_cart_model_shop').removeClass('ajax-sucess');
//                     $('#ajax_cart_model, #ajax_cart_model_shop').addClass('ajax-cart-item');

//                     /** trigger click event for the variant change and qty */
//                     if (flag) {
//                         WebsiteSale.init();
//                         $(document).on('click', '.ajax_cart_content input.js_product_change', function(ev){
//                             WebsiteSale.onChangeVariant(ev);
//                         });
//                         $(document).on('change', '.ajax_cart_content .js_main_product [data-attribute_exclusions]', function(ev){
//                             WebsiteSale.onChangeVariant(ev);
//                         });
//                         $(document).on('change', '.ajax_cart_content .js_product:first input[name="add_qty"]', function(ev){
//                             WebsiteSale._onChangeAddQuantity(ev);
//                         });
//                         $(document).on('click', '.ajax_cart_content a.js_add_cart_json', function(ev){
//                             WebsiteSale._onClickAddCartJSON(ev);
//                         });
//                         flag = 0;
//                      }

//                     /** Product gallery will be refreshed */

//                     setTimeout(function(){
//                         $('.ajax_cart_content #product_detail #thumbnailSlider').show();
//                         var productDetail = new publicWidget.registry.productDetail();
//                         productDetail.productGallery();
//                         $('#mainSlider .owl-carousel').trigger('refresh.owl.carousel');
//                         $('#thumbnailSlider .owl-carousel').trigger('refresh.owl.carousel');
//                         WebsiteSale._startZoom();
//                     }, 200);
//                     $('.variant_attribute  .list-inline-item').find('.active').parent().addClass('active_li');
//                     $( ".list-inline-item .css_attribute_color" ).change(function(ev) {
//                         var $parent = $(ev.target).closest('.js_product');
//                         $parent.find('.css_attribute_color').removeClass("active");
//                         $parent.find('.css_attribute_color').parent('.list-inline-item').removeClass("active_li");
//                         $parent.find('.css_attribute_color').filter(':has(input:checked)').addClass("active");
//                         $parent.find('.css_attribute_color').filter(':has(input:checked)').parent('.list-inline-item').addClass("active_li");
//                     });
//                     setTimeout(function(){
//                         var quantity = $('.ajax_cart_content').find('.quantity').val();
//                         $('.ajax_cart_content').find('.quantity').val(quantity).trigger('change');
//                     },500);
//                 });
//             }
//         },
//         _onClickSubmit: function (ev, forceSubmit) {
//             if ($(ev.currentTarget).is('#add_to_cart, #products_grid .a-submit') && !forceSubmit) {
//                 return;
//             }
//             /** If optional products exist, then it will shows variant popup for quick view and sliders */
//             var $aSubmit = $(ev.currentTarget);
//             if (!ev.isDefaultPrevented() && !$aSubmit.is(".disabled")) {
//                 ev.preventDefault();
//                 var is_quick_view = $aSubmit.hasClass('quick-add-to-cart');
//                 if (is_quick_view || ($('#ajax_cart_template').val() == 1 && $aSubmit.parents('.te_pc_style_main').length) ) {
//                     var frm = $aSubmit.closest('form');
//                     var product_product = frm.find('input[name="product_id"]').val();
//                     var quantity = frm.find('.quantity').val();
//                     var product_custom_attribute_values = frm.find('input[name="product_custom_attribute_values"]').val();
//                     if(!quantity) {
//                        quantity = 1;
//                     }
//                     ajax.jsonRpc('/shop/cart/update_custom', 'call',{'product_id':product_product,'add_qty':quantity, 'product_custom_attribute_values':product_custom_attribute_values}).then(function(data) {
//                         var ajaxCart = new publicWidget.registry.ajax_cart();
//                         if(data) {
//                             var $quantity = $(".my_cart_quantity");
//                             var old_quantity = $quantity.html();
//                             $quantity.parent().parent().removeClass('d-none');
//                             $quantity.html(parseInt(quantity) + parseInt(old_quantity)).hide().fadeIn(600);

//                             $('.ajax_cart_modal > .cart_close').trigger('click');
//                             $('.quick_view_modal > .quick_close').trigger('click');
//                             var product_id = frm.find('.product_template_id').attr('value');
//                             setTimeout(function(){
//                                 ajaxCart.ajaxCartSucess(product_id, product_product);
//                                 $('input[name="product_custom_attribute_values"]').remove();
//                             }, 700);
//                             /* Resize menu */
//                             setTimeout(() => {
//                                 $('#top_menu').trigger('resize');
//                             }, 200);
//                         }
//                     });
//                 } else {
//                     $aSubmit.closest('form').submit();
//                     $('.ajax_cart_modal > .cart_close').trigger('click');
//                     $('.quick_view_modal > .quick_close').trigger('click');
//                 }
//             }
//             if ($aSubmit.hasClass('a-submit-disable')){
//                 $aSubmit.addClass("disabled");
//             }
//             if ($aSubmit.hasClass('a-submit-loading')){
//                 var loading = '<span class="fa fa-cog fa-spin"/>';
//                 var fa_span = $aSubmit.find('span[class*="fa"]');
//                 if (fa_span.length){
//                     fa_span.replaceWith(loading);
//                 } else {
//                     $aSubmit.append(loading);
//                 }
//             }
//         }
//     });
    // publicWidget.registry.quickView = publicWidget.Widget.extend({
    //     selector: "#wrapwrap",
    //     events: {
    //         'click .quick-view-a': 'initQuickView',
    //     },
    //     initQuickView: function(ev) {
    //         /* This method is called while click on the quick view icon
    //          and show the model and quick view data */
    //         ev.preventDefault()
    //         self = this;
    //         var element = ev.currentTarget;
    //         var product_id = $(element).attr('data-id');
    //         ajax.jsonRpc('/quick_view_item_data', 'call',{'product_id':product_id}).then(function(data) {
    //             if($("#wrap").hasClass('js_sale'))
    //             {
    //                 $("#quick_view_model_shop .modal-body").html(data);
    //                 $("#quick_view_model_shop").modal({keyboard: true});
    //             }else {
    //                 $("#quick_view_model .modal-body").html(data);
    //                 $("#quick_view_model").modal({keyboard: true});
    //             }
    //             var WebsiteSale = new publicWidget.registry.WebsiteSale();
    //             if($('#id_lazyload').length) {
    //                 $("img.lazyload").lazyload();
    //             }
    //             WebsiteSale.init();
    //             WebsiteSale._startZoom();
    //             var combination = [];
    //             xml_load.then(function () {
    //                 var $message = $(QWeb.render(
    //                     'website_sale_stock.product_availability',
    //                     combination
    //                 ));
    //                 $('div.availability_messages').html($message);
    //             });

    //             setTimeout(function(){
    //                 productDetail.productGallery();
    //                 $('#mainSlider .owl-carousel').trigger('refresh.owl.carousel');
    //                 $('#thumbnailSlider .owl-carousel').trigger('refresh.owl.carousel');
    //                 var quantity = $('.quick_view_content').find('.quantity').val();
    //                 $('.quick_view_content').find('.quantity').val(quantity).trigger('change');

    //             }, 200);
    //             setTimeout(function(){
    //                 if($(this).find('.a-submit').hasClass('out_of_stock')) {
    //                     $(this).find('.a-submit').addClass('disabled');
    //                 }
    //             }, 1000);
    //             $('.variant_attribute  .list-inline-item').find('.active').parent().addClass('active_li');
    //             $( ".list-inline-item .css_attribute_color" ).change(function(ev) {
    //                 var $parent = $(ev.target).closest('.js_product');
    //                 $parent.find('.css_attribute_color').parent('.list-inline-item').removeClass("active_li");
    //                 $parent.find('.css_attribute_color').filter(':has(input:checked)').parent('.list-inline-item').addClass("active_li");
    //             });

    //             /*$( ".list-inline-item .css_attribute_color" ).change(function() {
    //                 $('.list-inline-item').removeClass('active_li');
    //                 $(this).parent('.list-inline-item').addClass('active_li');
    //             });*/

    //             /* Attribute value tooltip */
    //             $(function () {
    //               $('[data-toggle="tooltip"]').tooltip({ animation:true, delay: {show: 300, hide: 100} })
    //             });

    //         });

    //     },
    // });
    // $('#quick_view_model_shop').on('hidden.bs.modal', function (e) {
    //     $("#quick_view_model_shop .modal-body").html('');
    // });
    // $('#quick_view_model').on('hidden.bs.modal', function (e) {
    //     $("#quick_view_model .modal-body").html('');
    // })
});;