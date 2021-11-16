from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    property_sale_id = fields.Many2one("property.sale")
    is_deposit = fields.Boolean()