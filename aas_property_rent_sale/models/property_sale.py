from odoo import models, api, fields,_
from odoo.exceptions import UserError, ValidationError,Warning


class PropertySale(models.Model):
    _inherit = "property.sale"



    def action_set_reserve(self):
        self.property_id.property_rent_state="not available"

        temp = self.mapped('property_id.property_rent_ids')
        
        for rent in temp:
            if(rent.state=="quotation"):
                rent.state = 'on hold'

            elif(rent.state == "reserved"):
                
                raise Warning( _("This Property Has Been Already Reserved for Rent Order!")) 
            elif(rent.state == "rent order"):
                
                raise Warning( _("This Property is Being Rented!")) 
                
        return super(PropertySale, self).action_set_reserve()

    def action_set_confirm(self):

        temp = self.mapped('property_id.property_rent_ids')
        for rent in temp:
            if(rent.state=="on hold"):
                rent.state = 'canceled'

        return super(PropertySale, self).action_set_confirm()



    def action_set_cancel(self):
        if(self.state in ["reserved"] and self.property_id.for_rent): 
            self.property_id.property_rent_state="available"

        temp = self.mapped('property_id.property_rent_ids')
        for rent in temp:
            if(rent.state == 'on hold' and self.state in ["reserved"]):
                rent.state = 'quotation'  
            
        return super(PropertySale, self).action_set_cancel()

    
    def unlink(self):
        
        for record in self:
            if(record.state in ["reserved"] and record.property_id.for_rent and record.property_id.property_rent_state not in ["reserved","rented"]): 
                record.property_id.property_rent_state="available"

            if(record.state in ["reserved"] ):
                record.property_id.property_sale_state = "available"

                temp = self.mapped('property_id.property_rent_ids')
                for rent in temp:
                    if(rent.state == 'on hold'):
                        rent.state = 'quotation'  
        unlink_sale = super(PropertySale, self).unlink()
        return unlink_sale

    def action_reset_to_quotation(self):
        if(self.state in ["reserved"] and self.property_id.for_rent): 
            self.property_id.property_rent_state="available"
            
        temp = self.mapped('property_id.property_rent_ids')
        for rent in temp:

            if(rent.state == 'on hold' and self.state == "reserved" ):
                rent.state = 'quotation'  
        return super(PropertySale, self).action_reset_to_quotation()
    
    # def display_warning(self):
    #     return {
    #             'warning': {'title': _('Warning'), 'message': _('Message needed.'),},
    #         }

    # @api.onchange('test')
    # def onchange_field(self):
    #     return {
    #             'warning': {'title': _('Warning'), 'message': _('Message needed.'),},
    #         }