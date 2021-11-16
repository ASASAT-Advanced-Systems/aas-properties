from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError


class PropertyRent(models.Model):
    _inherit = "property.rent"

    def unlink(self):
        for record in self:
            if(record.state in ["rent order" , "reserved" ] and record.property_id.property_sale_state not in ["reserved","sold"]):
                record.property_id.property_rent_state = "available"

        unlink_rent = super(PropertyRent, self).unlink()
        return unlink_rent

    def action_set_confirm(self):
        if (self.property_id.property_sale_state in ["reserved","sold"]):
            raise Warning( _("This Property Has Been Already Reserved for Sale or Sold!")) 

        return super(PropertyRent, self).action_set_confirm()


    
    def action_set_reserve(self):
        if (self.property_id.property_sale_state in ["reserved","sold"]):
            raise Warning( _("This Property Has Been Already Reserved for Sale or Sold!")) 

        return super(PropertyRent, self).action_set_reserve()


    def action_set_cancel(self):
        for record in self:
            if(record.state in ["rent order" , "reserved" ] and record.property_id.property_sale_state not in ["reserved","sold"]):
                record.property_id.property_rent_state = "available"

        return super(PropertyRent, self).action_set_cancel()

    