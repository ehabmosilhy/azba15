{
    'name': "Administrative Communications",
    'version': '15.0.1.0.0',
    'depends': [
        'base',
        'hr',
        'barcodes',
        'ejad_erp_base',
        'report_xlsx',
    ],
    'author': "CVC",
    'description': """
    """,
    'data': [
        'security/ac_operation_security.xml',
        'security/ir.model.access.csv',

        'data/operation_sequence.xml',
        'data/ac_data.xml',
        'wizard/ac_operation_save_view.xml',
        'wizard/ac_operation_comment_view.xml',
        'wizard/ac_operation_transfer_view.xml',
        'report/ac_operation_barcode_report.xml',
        'report/ac_operation_barcode_report1.xml',
        'report/ac_operation_barcode_report3.xml',
        'report/ac_operation_report.xml',
        'views/ac_operation_view.xml',
        'views/ac_operation_move_view.xml',
        'views/ac_generalization.xml',
        'views/ac_settings.xml',
        'views/res_config_settings_views.xml',
        # 'views/assets.xml',
        'wizard/ac_reporting_view.xml',
        'wizard/ac_reporting_receive_statement_view.xml',
        'wizard/ac_reporting_transactions_statement_view.xml',
        'wizard/ac_operation_report_view.xml',
        'report/ac_external_layout.xml',
        'report/report_ac_template.xml',
        'report/report_operation_template.xml',
        'report/report_operation_move_template.xml',
        'report/reporting_receive_statement.xml',

    ],
    'qweb': ['static/src/xml/pdf_viewer.xml'],
    "assets": {"web.assets_backend": ["ejad_erp_administrative_communications/static/src/js/pdf_viewer.js"]
               },
    'application': True
}
