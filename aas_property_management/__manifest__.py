{
    'name': 'aas_property_management',
    'depends': [
        'base',
        'mail',
        'web_dashboard'
    ],
    'data': [
        'data/property_cron.xml',
        'data/unit_data.xml',
        'data/type_data.xml',
        'data/tag_data.xml',
        'views/bank_account_views.xml',
        'views/property_type_views.xml',
        'views/property_unit_views.xml',
        'views/property_tag_views.xml',
        'views/property_views.xml',
        'views/res_partner_views.xml',
        'report/property_report_templates.xml',
        'report/property_report_views.xml',
        'views/property_menus.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
