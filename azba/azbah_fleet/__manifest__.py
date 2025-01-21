{
    "name": "Azbah Fleet",
    "version": "1.0",
    "license": "LGPL-3",
    "category": "Human Resources/Fleet",
    "sequence": 1,
    "depends": ["base", "fleet"],
    "data": [
        "reports/service_report_action.xml",
        "reports/service_report_template.xml",
        "views/fleet_vehicle.xml",
        "views/fleet_vehicle_views.xml",
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
