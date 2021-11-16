from odoo import models, api, fields
from odoo.exceptions import UserError, ValidationError


class Property(models.Model):
    _inherit = "property"

    def action_set_confirmed(self):
        if(self.for_rent):
            self.property_rent_state = "available"
        if(self.for_sale):
            self.property_sale_state = "available"
        return super(Property, self).action_set_confirmed()

    def action_reset_confirmed(self):
        self.property_rent_state = "not available"
        self.property_sale_state = "not available"
        return super(Property, self).action_reset_confirmed()

    @api.model
    def create(self, values):
        res = super(Property, self).create(values)
        if res.parent_property_id.big_parent_property_id:
            res.big_parent_property_id = res.parent_property_id.big_parent_property_id.id
        else:
            res.big_parent_property_id = res.parent_property_id.id
        if not self.property_line_ids:
            property_lines = [(5, 0, 0)]
            for line in self.property_type_id.property_type_line_ids:
                data = {
                    'property_id': self.id,
                    'property_unit_id': line,
                    'property_unit_qty': 1
                }
                property_lines.append((0, 0, data))
            self.property_line_ids = property_lines
        res.property_sale_state = "not available"
        res.property_rent_state = "not available"
        return res
