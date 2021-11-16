from odoo import models, api, fields
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    property_rent_ids = fields.One2many("property.rent", "tenant_id", string="Property Rent Ids")
    has_rents = fields.Boolean(compute = "_compute_num_of_rents", store = True)
    rents_count = fields.Integer(compute="_compute_rents_count", string="Rents Count")

    @api.depends("property_rent_ids")
    def _compute_num_of_rents(self):
        for record in self:
            record.has_rents = False
            if len(record.mapped("property_rent_ids")):
                record.has_rents = True

    def _compute_rents_count(self):
        for owner in self:
            owner.rents_count = self.env['property.rent'].search_count([('id', 'in', owner.property_rent_ids.ids)])

    def action_show_rents(self):
        self.ensure_one()
        return {
            "name": "Rent records",
            "type": "ir.actions.act_window",
            "res_model": "property.rent",
            "view_mode": "tree,form",
            "domain": [('id', 'in', self.property_rent_ids.ids)],
        }  
