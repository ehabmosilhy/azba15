{
    'name': 'Ejad ERP Stock',
    'version': '15.0.0.1',
    'category': 'Inventory Managment',
    'description': """
    """,
    'author': 'CVC',
    'website': '',
    'depends': [
        'base',
        'hr',
        'stock',
        'purchase',

        'ejad_erp_base',
        # 'ejad_erp_hr',
        'ejad_erp_purchase',
        # 'stock_limitation',
    ],
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'wizard/inactive_products_wizard.xml',
        'wizard/products_reach_min_qty.xml',
        'data/routes_data.xml',
        'views/product_view.xml',
        'views/view_stock_picking.xml',
        # 'views/view_stock_inventory.xml',
        'views/view_stock_scrap.xml',
        # 'views/hr_employee.xml',
        'views/view_stock_picking_type.xml',
        'reports/inventory_transfer_report.xml',
        'reports/inactive_product_report.xml',
        'reports/product_reach_min_qty_report.xml',
        # 'reports/report_deliveryslip.xml',
        #  'reports/product_barcode.xml',

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'Other proprietary'
}
