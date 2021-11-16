from odoo import models, api, fields, _
from odoo.exceptions import UserError, ValidationError


class Property(models.Model):
    _inherit = "property"

    for_sale = fields.Boolean(string='For Sale')
    expected_sale_price = fields.Float(string='Expected Sale Price', required=True, tracking = True)
    property_sale_state = fields.Selection(
        string='Sale State',
        selection=[('available', 'Available'),('reserved', 'Reserved'), ('sold', 'Sold'),('not available', 'Not Available') ],default="not available")

    def _default_sale_commission(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_sale.commission')
    
    def _default_sale_administrative_fees(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_sale.administrative_fees')
    


    sale_commission = fields.Float(string = "Sale Commission (%)", default =_default_sale_commission, tracking = True)
    sale_administrative_fees = fields.Float(string = "Sale Admistration Fees (%)", default =_default_sale_administrative_fees, tracking = True)

    property_sale_ids = fields.One2many("property.sale", "property_id")
    sales_count = fields.Integer(compute="_compute_sales_count", string ="Sales Count")
    property_sale_ids_state = fields.Selection(related='property_sale_ids.state', store=True, tracking = False)
    is_sold = fields.Boolean(string = "Sold", default=False)
    # state = fields.Selection(
    #     string='Property State',
    #     selection=[('available', 'Available'),('not available (reserved)', 'Reserved'), ('not available', 'Not Available')],default="not available")

    
    color = fields.Integer('Color Index', compute="_change_colore_on_kanban")
    is_any_sub_for_sale=fields.Boolean(compute="_compute_is_all_sub_not_for_sale" , store=True)

    def _compute_sales_count(self):
        for property in self:
            property.sales_count = self.env['property.sale'].search_count([('id', 'in', property.property_sale_ids.ids)])

    @api.depends('property_child_ids')
    def _compute_is_all_sub_not_for_sale(self):
        for record in self:
            record.is_any_sub_for_sale = False
            SubProp = record.mapped('property_child_ids')
            for property in SubProp :
                record.is_any_sub_for_sale = record.is_any_sub_for_sale or property.for_sale
                if(record.is_any_sub_for_sale) : break
    
    # @api.onchange('state')
    # def _onchange_state(self):
    #     if(self.state == 'not available (reserved)'):
    #         self.parent_property_id.state = 'not available (reserved)'
    #         self.property_child_ids.state = 'not available (reserved)'

    #     if(self.state == 'not available'):
    #         self.parent_property_id.state = 'not available'
    #         self.parent_property_id.for_sale=False
    #         self.property_child_ids.state = 'not available'
    #         self.property_child_ids.for_sale=False

    #     if(self.state == 'available'):
    #         temp = self.mapped('property_child_ids')
    #         for prop in temp:
    #             prop.state='available'

    #     # ################################    
    #         if 'not available (reserved)' not in self.mapped('parent_property_id.property_child_ids.state'):
    #             if 'not available' not in self.mapped('parent_property_id.property_child_ids.state'):
    #                 self.parent_property_id.state = 'available'
    #                 self.parent_property_id.for_sale=True

    
    @api.onchange('for_sale',"is_mu")
    def _onchange_for_sale(self):
        if self.is_mu: 
            self.for_sale = False  
            self.property_sale_state='not available'      

        # if(self.for_sale==False  ):
        #     self.state='not available'
        #     self.expected_sale_price = 0
        elif self.for_sale:
            self.property_sale_state='available'
        else:
            self.property_sale_state='not available'      
            
        
    @api.model
    def create(self, values):
        res = super(Property, self).create(values)
        res.property_sale_state="not available"

        if res.parent_property_id.big_parent_property_id:
            res.big_parent_property_id = res.parent_property_id.big_parent_property_id.id
        else:
            res.big_parent_property_id = res.parent_property_id.id
        if res.for_sale:
            res.property_sale_state = "available"
        return res

    @api.depends("property_sale_state")
    def _change_colore_on_kanban(self):
        for record in self:
            color = 0
            if record.property_sale_state == 'available':
                color = 7
            elif record.property_sale_state == 'not available':
                color = 1
            elif record.property_sale_state == 'reserved':
                color = 3
            elif record.property_sale_state == 'sold':
                color = 4
            else:
                color=5
            record.color = color

    def action_show_sales_history(self):
        self.ensure_one()
        return {
            "name": "sale records",
            "type": "ir.actions.act_window",
            "res_model": "property.sale",
            "view_mode": "tree,form",
            "context": {'create': False},
            "domain": [('id', 'in', self.property_sale_ids.ids)],
        }  

    @api.constrains('for_sale', 'expected_sale_price')
    def _check_saleing_price(self):
        for record in self:
            if ((record.expected_sale_price <= 0) and (record.for_sale)):
                raise ValidationError(
                    _("The saleing price cannot be less than or equal zero"))

    # @api.constrains('property_owner_id','property_sale_ids')
    # def _check_owner_eligibility(self):
    #     for record in self:
    #         if record.property_sale_ids.customer_id == record.property_owner_id and record.property_sale_ids.state not in ['canceled']:
    #             raise UserError(f"{record.property_owner_id.name} cannot be assigned to {record.name} as his name is registered as a costumer to it.\nPlease Check!")