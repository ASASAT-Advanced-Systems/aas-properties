from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_commission = fields.Float("Default Commission Percentage", config_parameter='property_sale.commission')
    sale_administrative_fees = fields.Float("Default Administrative Fees Percentage", config_parameter='property_sale.administrative_fees')

    sale_comm_admin_account_id = fields.Many2one("account.account", string="Commission and Administrative Fees Account", config_parameter='property_sale.comm_admin_account_id', domain=[('deprecated', '=', False),('user_type_id.name', 'in', ['Income','Current Liabilities', 'التزامات جارية','الدخل'])])
    sale_tax_id = fields.Many2one('account.tax', string='Tax', domain=[('type_tax_use',  '=', 'sale')], config_parameter='property_sale.sale_tax_id')


    _sql_constraints = [
        ('check_commission', 'CHECK(sale_commission >= 0)',
         _('The Commission must be positive')),
         ('check_administrative_fees', 'CHECK(sale_administrative_fees >= 0)',
         _('The Administrative Fees must be positive')),
         ('check_sale_tax', 'CHECK(sale_tax >= 0)',
         _('The Rent Tax must be positive'))
         ]


