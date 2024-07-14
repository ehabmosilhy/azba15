odoo.define('aos_whatsapp_pos.models', function (require) {
	const { Context } = owl;
	var models = require('point_of_sale.models');
	models.load_fields('res.partner', ['whatsapp']);
});
