{

    'name': 'aas_property_rent',
    'depends': [
        'aas_property_management',
        'account_accountant',
    ],
    'data': [
        'views/rent_make_invoice_advance_views.xml',
        'data/property_rent_cron.xml',
        'views/property_rent_views.xml',
        'views/property_paymentline.xml',
        'data/property_rent_sequence.xml',
        'views/property_views.xml',
        'views/res_partner_views.xml',
        'report/property_rent_report_views.xml',
        'report/property_report_templates.xml',
        'report/property_report_inherit_templates.xml',
        'report/property_report_views.xml',
        'views/property_rent_menus.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
