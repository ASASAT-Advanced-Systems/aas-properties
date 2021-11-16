
from odoo import models, api, fields,_

from odoo.exceptions import UserError, ValidationError


class Property(models.Model):
    _inherit = "property"

    for_rent = fields.Boolean(string=_('For Rent'))
    property_rent_state = fields.Selection(
        string='Rent State',
        selection=[('available', 'Available'),('reserved', 'Reserved'), ('rented', 'Rented'),('not available', 'Not Available') ],default="not available")

    expected_rent_price = fields.Float(string='Expected Rent Price', required=True, tracking = True)
    refundable_insurance = fields.Float(string='Refundable Insurance', help=_("Insurance amount that will be refunded at the end of the rent with no damage to the property"), tracking = True)

    def _default_commission(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.commission')
    
    def _default_administrative_fees(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.administrative_fees')
    
    def _default_service_fees(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.service_fees')
    
    def _default_service_ability(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.can_do_service')

    rent_commission = fields.Float(string = "Rent Commission (%)", default =_default_commission, tracking = True)
    rent_administrative_fees = fields.Float(string= "Rent Admistration Fees (%)", default =_default_administrative_fees, tracking = True)
    rent_service_fees = fields.Float(string = "Rent Service Fees (%)", default =_default_service_fees, tracking = True)
    can_do_service = fields.Boolean(default =_default_service_ability)
    company_responsible_for_service = fields.Boolean(string = "Company is responsiple for service", tracking = True,help="Will the company undertake maintainance and service of the property?")

    property_rent_ids = fields.One2many("property.rent", "property_id", string="Property Rent Ids")
    rents_count = fields.Integer(compute="_compute_rents_count", string="Rents Count")
    property_rent_ids_state = fields.Selection(related='property_rent_ids.state', store=True, tracking = False)
    rent_type = fields.Selection(
        string='Contract Type',
        selection=[('1', 'Annually'),
                   ('12', 'Monthly')],
        required=True,
        copy=False,
        default='1')
    is_rented = fields.Boolean(string = "Rented", default=False)
    # state = fields.Selection(
    #     string='Property State',
    #     selection=[('available', 'Available'),('not available (reserved)', 'Reserved'), ('not available', 'Not Available') ],default="not available")
        
    color = fields.Integer(compute="_change_colore_on_kanban")
    is_any_sub_for_rent=fields.Boolean(compute="_compute_is_all_sub_not_for_rent" , store=True)

    def _compute_rents_count(self):
        for property in self:
            property.rents_count = self.env['property.rent'].search_count([('id', 'in', property.property_rent_ids.ids)])

    @api.depends('property_child_ids')
    def _compute_is_all_sub_not_for_rent(self):
        for record in self:
            record.is_any_sub_for_rent = False
            SubProp = record.mapped('property_child_ids')
            for property in SubProp :
                record.is_any_sub_for_rent = record.is_any_sub_for_rent or property.for_rent
                if(record.is_any_sub_for_rent) : break
    
    # @api.onchange('state')
    # def _onchange_state(self):
    #     if(self.state == 'not available (reserved)'):
    #         self.parent_property_id.state = 'not available (reserved)'
    #         self.property_child_ids.state = 'not available (reserved)'

    #     if(self.state == 'not available'):
    #         self.parent_property_id.state = 'not available'
    #         self.parent_property_id.for_rent=False
    #         self.property_child_ids.state = 'not available'
    #         self.property_child_ids.for_rent=False

    #     if(self.state == 'available'):
    #         temp = self.mapped('property_child_ids')
    #         for prop in temp:
    #             prop.state='available'

    #     # ################################    
    #         if 'not available (reserved)' not in self.mapped('parent_property_id.property_child_ids.state'):
    #             if 'not available' not in self.mapped('parent_property_id.property_child_ids.state'):
    #                 self.parent_property_id.state = 'available'
    #                 self.parent_property_id.for_rent=True

    
    @api.onchange('for_rent',"is_mu")
    def _onchange_for_rent(self):
        if self.is_mu: 
            self.for_rent = False  
            self.property_rent_state='not available'      

        # if(self.for_rent==False  ):
        #     self.state='not available'
        #     self.expected_rent_price = 0

        elif self.for_rent:
            self.property_rent_state='available'
        else:
            self.property_rent_state='not available'      

    # @api.onchange('expected_rent_price')
    # def onchange_expected_rent_price(self):
    #     self.message_post(body=_("<b>Expected Rent Price</b> has changed to <b>%s</b>", self.expected_rent_price))

    # @api.onchange('rent_commission')
    # def onchange_rent_commission(self):
    #     self.message_post(body=_("<b>Rent Commission</b> percentage has changed to <b>%s</b>", self.rent_commission))

    # @api.onchange('rent_administrative_fees')
    # def onchange_rent_administrative_fees(self):
    #     self.message_post(body=_("<b>Rent Administrative Fees</b> percentage has changed to <b>%s</b>", self.rent_administrative_fees))

    # @api.onchange('rent_service_fees')
    # def onchange_rent_service_fees(self):
    #     self.message_post(body=_("<b>Rent Service Fees</b> percentage has changed to <b>%s</b>", self.rent_service_fees))

    # @api.onchange('company_responsible_for_service')
    # def onchange_company_responsible_for_service(self):
    #     if self.company_responsible_for_service:
    #         self.message_post(body=_("Company is responsiple for service"))
    #     else: self.message_post(body=_("Company is not responsiple for service"))
        

    @api.model
    def create(self, values):
        res = super(Property, self).create(values)
        res.property_rent_state="not available"
        if res.parent_property_id.big_parent_property_id:
            res.big_parent_property_id = res.parent_property_id.big_parent_property_id.id
        else:
            res.big_parent_property_id = res.parent_property_id.id
        if res.for_rent:
            res.property_rent_state = "available"
        return res

    @api.depends("property_rent_state")
    def _change_colore_on_kanban(self):
        for record in self:
            color = 0
            if record.property_rent_state == 'available':
                color = 7
            elif record.property_rent_state == 'not available':
                color = 1
            elif record.property_rent_state == 'reserved':
                color = 3
            elif record.property_rent_state == 'rented':
                color = 4
            else:
                color=5
            record.color = color

    def action_show_rents_history(self):
        self.ensure_one()
        return {
            "name": "Rent records",
            "type": "ir.actions.act_window",
            "res_model": "property.rent",
            "view_mode": "tree,form",
            "context": {'create': False},
            "domain": [('id', 'in', self.property_rent_ids.ids)],
        }  

    def _default_commission(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.commission')
    
    def _default_administrative_fees(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.administrative_fees')
    
    def _default_service_fees(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.service_fees')

    @api.constrains('for_rent', 'expected_rent_price')
    def _check_renting_price(self):
        for record in self:
            if ((record.expected_rent_price <= 0) and (record.for_rent)):
                raise ValidationError(_("The renting price cannot be less than or equal zero "))

    @api.constrains('property_owner_id','property_rent_ids')
    def _check_owner_eligibility(self):
        for record in self:
            if record.property_rent_ids.tenant_id == record.property_owner_id and record.property_rent_ids.state not in ['canceled', 'end']:
                raise UserError(_(f"{record.property_owner_id} cannot be assigned to {record.name} as his name is registered as a tenant to it.\nPlease Check!"))