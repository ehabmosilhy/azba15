# -*- coding: utf-8 -*-
{
    "name": """Gantt Native Web view""",
    "summary": """Added support Gantt Chart Widget View""",
    "category": "Project",
    "images": ['static/description/banner.gif'],
    "version": "15.0.0.0.1",
    "description": """
        Main Module for Gantt Native
        
    """,

    "author": "Viktor Vorobjov",
    "license": "OPL-1",
    "website": "https://straga.github.io",
    "support": "vostraga@gmail.com",
    "live_test_url": "https://demo13.garage12.eu",
    "price": 299.00,
    "currency": "EUR",

    "depends": [
        "web", "web_widget_time_delta"
    ],
    "external_dependencies": {"python": [], "bin": []},
    "data": [
        # 'views/web_gantt_src.xml',
    ],
    "demo": [],
    'assets': {
        'web.assets_backend': [
            '/web_gantt_native/static/src/css/gantt_native.css',
            '/web_gantt_native/static/src/css/gantt_native_ztree.css',
            '/web_gantt_native/static/src/lib/twix.js',
            '/web_gantt_native/static/src/lib/jquery.ztree.core.js',
            '/web_gantt_native/static/src/lib/jquery.ztree.exedit.js',
            '/web_gantt_native/static/src/js/native_gantt_view.js',
            '/web_gantt_native/static/src/js/native_gantt_controller.js',
            '/web_gantt_native/static/src/js/native_gantt_model.js',
            '/web_gantt_native/static/src/js/native_gantt_renderer.js',
            '/web_gantt_native/static/src/js/gantt_tool_field.js',
            '/web_gantt_native/static/src/js/gantt_pager.js',
            '/web_gantt_native/static/src/js/gantt_timeline_head.js',
            '/web_gantt_native/static/src/js/gantt_timeline_data.js',
            '/web_gantt_native/static/src/js/gantt_tool_tip.js',
            '/web_gantt_native/static/src/js/gantt_tool_hint.js',
            '/web_gantt_native/static/src/js/gantt_timeline_arrow_draw.js',
            '/web_gantt_native/static/src/js/gantt_timeline_arrow.js',
            '/web_gantt_native/static/src/js/gantt_timeline_ghost.js',
            '/web_gantt_native/static/src/js/gantt_timeline_bar_summary.js',
            '/web_gantt_native/static/src/js/gantt_timeline_bar_first.js',
            '/web_gantt_native/static/src/js/gantt_timeline_header.js',
            '/web_gantt_native/static/src/js/gantt_timeline_scroll.js',
            '/web_gantt_native/static/src/js/gantt_timeline_info.js',
            '/web_gantt_native/static/src/js/gantt_timeline_res_level.js',
            '/web_gantt_native/static/src/js/gantt_timeline_res_bar.js',
            '/web_gantt_native/static/src/js/gantt_timeline_bar_docs.js',
            '/web_gantt_native/static/src/js/gantt_item_options.js',
            '/web_gantt_native/static/src/js/gantt_item_ztree.js',
            '/web_gantt_native/static/src/js/gantt_item_action.js',
            '/web_gantt_native/static/src/js/gantt_item_info.js',
            '/web_gantt_native/static/src/js/native_gantt_data.js',
        ],
        'web.assets_qweb': [
            '/web_gantt_native/static/src/xml/*.xml',
        ],
    },

    "post_load": None,
    "pre_init_hook": None,
    "post_init_hook": None,
    "installable": True,
    "auto_install": False,
    "application": False,
}
