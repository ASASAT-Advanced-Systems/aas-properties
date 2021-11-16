from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    property_rent_id = fields.Many2one("property.rent")
    is_deposit = fields.Boolean(string = "Is Deposit")