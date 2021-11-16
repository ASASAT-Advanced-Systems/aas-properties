{

    'name': 'aas_property_sale',
    'depends': [
        'aas_property_management',
        'account_accountant'
    ],
    'data': [
        'views/sale_make_invoice_advance_views.xml',
        'views/property_sale_views.xml',
        'views/property_paymentline.xml',
        'data/property_sale_sequence.xml',
        'views/property_views.xml',
        'views/res_partner_views.xml',
        'report/property_sale_report_views.xml',
        'report/property_report_templates.xml',
        'report/property_report_inherit_templates.xml',
        'report/property_report_views.xml',
        'views/property_sale_menus.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
