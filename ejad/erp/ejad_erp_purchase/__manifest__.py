{
    'name': "ERP Purchase",
    'version': '15.0.0.1',
    'depends': [
        'base',
        'purchase', 'purchase_requisition',
        'hr',
        'stock',
        'uom',

    ],
    'author': "CVC",
    'description': """
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',

        'data/purchase_requisition_request_data.xml',

        'data/mail_template.xml',

        'wizard/purchase_report.xml',
        'wizard/purchase_requisition_refuse_view.xml',
        'wizard/material_price_report.xml',
        'wizard/po_report_user.xml',

        'views/res_config_settings_views.xml',
        # 'views/account_invoice.xml',
        'views/product_view.xml',
        'views/purchase_order.xml',
        'views/res_partner.xml',
        'views/category_name_views.xml',

        'report/nauss_report.xml',
        'report/nauss_external_layout.xml',
        'report/purchase_requisition_report.xml',
        'report/report_material_price.xml',
        'report/report_purchase_department.xml',
        'report/report_purchase_user.xml',
        'report/purchase_order_templates.xml',
        'report/purchase_quotation_templates.xml',
        'report/report_purchaserequisition.xml',
        'report/purchase_requisition_request_report.xml',
	    'views/hr_employee.xml',
    ]
}
