from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rent_commission = fields.Float(string="Default Commission Percentage", config_parameter='property_rent.commission')
    rent_administrative_fees = fields.Float(string="Default Administrative Fees Percentage", config_parameter='property_rent.administrative_fees')
    rent_service_fees = fields.Float(string="Default Service Fees Percentage", config_parameter='property_rent.service_fees')
    rent_tax_id = fields.Many2one('account.tax', string='Tax', domain=[('type_tax_use',  '=', 'sale')], config_parameter='property_rent.rent_tax_id')
    rent_payment_tax = fields.Float(string="Rent Payments Tax Percentage", config_parameter='property_rent.rent_payment_tax')

    rent_comm_admin_account_id = fields.Many2one("account.account", string="Commission and Administrative Fees Account", config_parameter='property_rent.comm_admin_account_id', domain=[('deprecated', '=', False),('user_type_id.name', 'in', ['Income','Current Liabilities', 'التزامات جارية','الدخل'])])

    renew_period = fields.Integer(string="Renew Period", config_parameter='property_rent.renew_period', default = 60)

    can_do_service = fields.Boolean(string="The company can undertake services and maintainance", config_parameter='property_rent.can_do_service')
    rent_service_account_id = fields.Many2one("account.account", string="Service Fees Account", config_parameter='property_rent.service_account_id', domain=[('deprecated', '=', False),('user_type_id.name', 'in', ['Income','Current Liabilities', 'التزامات جارية','الدخل'])])

    _sql_constraints = [
        ('check_commission', 'CHECK(rent_commission >= 0)', _('The Commission must be positive')),
        ('check_administrative_fees', 'CHECK(rent_administrative_fees >= 0)', _('The Administrative Fees must be positive')),
        ('check_service_fees', 'CHECK(rent_service_fees >= 0)', _('The Service Fees must be positive')),
        ('check_renew_period', 'CHECK(renew_period >= 0)', _('The Renew Period must be positive')),
        ('check_rent_tax', 'CHECK(rent_tax >= 0)', _('The Rent Tax must be positive'))
         ]

        