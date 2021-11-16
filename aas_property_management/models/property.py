from odoo import fields, models,api,_

from odoo.osv import expression
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class Property(models.Model):
    _name = "property"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "property"

    name =                      fields.Char(required=True,string="Property Title", copy =False)
    is_floor =                  fields.Boolean(string="Is Floor", related = "property_type_id.is_floor", store = True)
    floor_num =                 fields.Integer(string="Floor Number",help="The floor number which the property is located in")
    north_dirction =            fields.Boolean(string = "North")
    east_dirction =             fields.Boolean(string = "East")
    west_dirction =             fields.Boolean(string = "West")
    south_dirction =            fields.Boolean(string = "South")
    north_dirction_length =     fields.Float(string="North dirction length",help=_("the length of the street on the property"))
    east_dirction_length =      fields.Float(string="East direction length",help=_("the length of the street on the property"))
    west_dirction_length =      fields.Float(string="West direction length",help=_("the length of the street on the property"))
    south_dirction_length =     fields.Float(string="South direction length",help=_("the length of the street on the property"))
    has_street_length_related=  fields.Boolean(string="Has Street Length",related="property_type_id.has_street_length")
    is_confirmed =              fields.Boolean(string="Confirmed")
    deed_number = 	            fields.Char(string="Deed Number")

    property_area=              fields.Float(string="Area")
    property_building_area =    fields.Float(string="Property Building Area")
    state =                     fields.Selection(string='State', selection=[('draft', 'Draft'),('confirmed', 'Confirmed')],default="draft")
    purpose =                   fields.Selection(string="Property Purpose",selection=[('residential', 'Residential'),('commercial', 'Commercial'),('residentialandcommercial', 'Residential & Commercial')])
    residential_type=           fields.Selection(string="Residential Type",selection=[('families', 'Families'),('singles', 'Singles')])
    parent_property_id=         fields.Many2one("property",string="Property Parent" )
    big_parent_property_id=     fields.Many2one("property",string="Property Big Parent")
    property_type_id =          fields.Many2one("property.type",string="Property Type")
    property_type_name_related= fields.Char(related="property_type_id.name",string="Property Type")
    property_manager_id =       fields.Many2one("res.users", string="Property Manager", default=lambda self: self.env.user,readonly=True)
    property_construction_date= fields.Date(string="Property Construction Date")
    property_building_age =     fields.Integer(readonly=True,compute="_compute_building_age",string="Property Building Age")
    property_tag_ids =          fields.Many2many("property.tag",  string = "Features")
    property_line_ids =         fields.One2many("property.line", "property_id", string = "Property Lines")
    property_child_ids=         fields.One2many("property","parent_property_id",string="Sub properties")
    residential_child_ids=      fields.One2many("property", "parent_property_id",string="Sub properties", domain=lambda self: [('purpose', '=', 'residential')])
    commercial_child_ids=       fields.One2many("property", "parent_property_id",string="Sub properties", domain=lambda self: [('purpose', '=', 'commercial')])
    street =                    fields.Char(string="Property Street")
    parent_street =             fields.Char(compute="_compute_from_parent", string="Property Street")
    street2 =                   fields.Char(string="Property Street2")
    parent_street2 =            fields.Char(compute="_compute_from_parent", string="Property Street2")
    city=                       fields.Char(string="Property City" )
    parent_city=                fields.Char(compute="_compute_from_parent", string="Property location city")
    district=                   fields.Char(string="Property District" )
    parent_district=            fields.Char(compute="_compute_from_parent", string="Property District" )
    zip =                       fields.Char(string="Property ZIP" )
    parent_zip =                fields.Char(compute="_compute_from_parent", string="Property ZIP" )
    country_id =                fields.Many2one('res.country', string='Country', ondelete='restrict')
    parent_country_id =         fields.Many2one(compute="_compute_from_parent", string='Country')
    parent_type =               fields.Many2one(related = "parent_property_id.property_type_id", store = True,string="Property Type")
    property_owner_id=          fields.Many2one("res.partner" ,string = "Property Owner",required=True)
    num_subProperties =         fields.Text(compute = '_countSubProperties', string ='Parent property has:', readonly=True, store = True)
    is_mu =                     fields.Boolean(string='Is Multi Unit',default=False ,help="Does the property has sup properties?")
    is_mu_related =             fields.Boolean(related="property_type_id.is_mu",string='Is Multi Unit')
    has_parent_type_related=    fields.Boolean(related="property_type_id.has_parent_type") #to indicate if the type could have a parent
    search_by_lines =           fields.Char(compute="_compute_search_by_lines", search='_search_by_lines')

    _sql_constraints = [
        ('unique_type_deed_number', 'unique (deed_number)', _('There is already a property with this deed number!')),
        ('unique_name', 'unique (name)', _('There is a property with the same name!'))
    ]

    def action_set_confirmed(self):
        self.state = 'confirmed'
        self.is_confirmed=True
        self.message_post(body=_("%s's state has changed to <b>Confirmed</b>", self.name))
        return True
    
    def action_reset_confirmed(self):
        self.state = 'draft'
        self.is_confirmed=False
        self.message_post(body=_("%s's state has changed to <b>Draft</b>", self.name))
        return True
        
    @api.onchange('is_confirmed')
    def onchange_is_confirmed(self):
        if self.is_confirmed: self.state = 'confirmed'
        else : self.state = 'draft'

    def cron_check_building_age(self):
        properties = self.env['property'].search([])
        for property in properties:
            property.property_building_age=relativedelta(fields.Date.today(),property.property_construction_date).years if property.property_construction_date else 0
 
    @api.depends('property_construction_date')
    def _compute_building_age(self):
        for property in self:
            property.property_building_age=relativedelta(fields.Date.today(),property.property_construction_date).years if property.property_construction_date else 0


    @api.depends('property_line_ids')
    def _compute_search_by_lines(self):
        for property in self:
            search = ""
            for line in property.property_line_ids:
                search += f"{line.property_unit_id.name}={line.property_unit_qty},{line.property_unit_id.name},"
            no_spaces = str.lower(search[:-1]).split(" ")
            property.search_by_lines = "".join(no_spaces)   

    def _search_by_lines(self, operator, value):
        ids = []
        for property in self.env['property'].search([]):
            terms = property.search_by_lines.split(',')
            to_lower = str.lower(value)
            no_tabs = to_lower.split('\t')
            no_spaces = "".join(no_tabs).split(' ')
            vals = "".join(no_spaces).split(',')
            result = all(val in terms for val in vals)
            if result:
                ids.append(property.id)
        return [('id', 'in', ids)]
                    
    @api.model
    def create(self, values):
        res = super(Property, self).create(values)
        if res.parent_property_id.big_parent_property_id:
            res.big_parent_property_id = res.parent_property_id.big_parent_property_id.id   
        else:
            res.big_parent_property_id = res.parent_property_id.id 

        if  not self.property_line_ids :
            property_lines = [(5, 0, 0)]
            for line in self.property_type_id.property_type_line_ids:
                data = {
                    'property_id' : self.id,
                    'property_unit_id' : line,
                    'property_unit_qty' : 1
                }
                property_lines.append((0, 0, data))
            self.property_line_ids = property_lines
        return res        
    
    @api.constrains('purpose', 'property_type_id')
    def _check_purpose(self):
        for record in self:
            if (record.property_type_id.purpose == "commercial" and (record.purpose == "residential" or  record.purpose == "residentialandcommercial")):
                raise ValidationError(_("This type can only be commercial !"))
            if (record.property_type_id.purpose == "residential" and ( record.purpose == "commercial" or  record.purpose == "residentialandcommercial")):
                raise ValidationError(_("This type can only be residential !"))

    @api.depends('property_child_ids')
    def _countSubProperties(self):
        for property in self:
            property.num_subProperties = ""
            SubPropTypes = dict.fromkeys(property.mapped('property_child_ids.property_type_id.name'))
            for key in SubPropTypes:
                SubPropTypes[key] = 0
            
            for key in SubPropTypes:
                for record in property.property_child_ids:
                    if record.property_type_id.name == key:
                        SubPropTypes[key] += 1
                property.num_subProperties += f'{SubPropTypes[key]}\t{key}(s) \n'

    @api.depends('big_parent_property_id', 'parent_property_id')
    def _compute_from_parent(self):
        for property in self:
            if property.big_parent_property_id:
                property.street = property.big_parent_property_id.street
                property.street2 = property.big_parent_property_id.street2
                property.city = property.big_parent_property_id.city
                property.district = property.big_parent_property_id.district
                property.zip = property.big_parent_property_id.zip
                property.country_id = property.big_parent_property_id.country_id.id
                property.property_construction_date = property.big_parent_property_id.property_construction_date
                property.parent_street = property.big_parent_property_id.street
                property.parent_street2 = property.big_parent_property_id.street2
                property.parent_city = property.big_parent_property_id.city
                property.parent_district = property.big_parent_property_id.district
                property.parent_zip = property.big_parent_property_id.zip
                property.parent_country_id = property.big_parent_property_id.country_id.id
                # property.parent_type = property.big_parent_property_id.property_type_id.id
                property.property_owner_id = property.big_parent_property_id.property_owner_id.id
            elif property.parent_property_id:
                property.street = property.parent_property_id.street
                property.street2 = property.parent_property_id.street2
                property.city = property.parent_property_id.city
                property.district = property.parent_property_id.district
                property.zip = property.parent_property_id.zip
                property.country_id = property.parent_property_id.country_id.id
                property.property_construction_date = property.parent_property_id.property_construction_date
                property.parent_street = property.parent_property_id.street
                property.parent_street2 = property.parent_property_id.street2
                property.parent_city = property.parent_property_id.city
                property.parent_district = property.parent_property_id.district
                property.parent_zip = property.parent_property_id.zip
                property.parent_country_id = property.parent_property_id.country_id.id
                # property.parent_type = property.parent_property_id.property_type_id.id
                property.big_parent_property_id = property.parent_property_id.id
                property.property_owner_id = property.parent_property_id.property_owner_id.id
            else:
                property.parent_street = False
                property.parent_street2 = False
                property.parent_city = False
                property.parent_district = False
                property.parent_zip = False
                property.parent_country_id = False
                # property.parent_type = False

    # @api.depends('property_child_ids')
    # def _compute_property_childs(self):
    #     for property in self:
    #         property.residential_child_ids = [(6, 0, property.property_child_ids.filtered(lambda child: child.purpose == 'residential').ids)]
    #         property.commercial_child_ids = [(6, 0, property.property_child_ids.filtered(lambda child: child.purpose == 'commercial').ids)]

    @api.onchange('purpose', 'parent_type')
    def set_domain_for_property_type_id(self):
        if self.purpose == 'residentialandcommercial':
            if (self.parent_type.id  == False):
                class_obj =self.env['property.type'].search([('purpose', '=', 'residentialandcommercial')])
            else:
                class_obj =self.env['property.type'].search([('purpose', '=', 'residentialandcommercial'),('parent_type_id', "=", self.parent_type.id)])
        elif self.purpose == 'residential':
            if (self.parent_type.id  == False):
                class_obj =self.env['property.type'].search([('purpose', 'in', ['residential','residentialandcommercial','residentialorcommercial'])])
            else:
                class_obj =self.env['property.type'].search([('purpose', 'in', ['residential','residentialandcommercial','residentialorcommercial']),('parent_type_id', "=", self.parent_type.id)])
        elif self.purpose == 'commercial':
            if (self.parent_type.id  == False):
                class_obj =self.env['property.type'].search([('purpose', 'in', ['commercial','residentialandcommercial','residentialorcommercial'])])
            else:
                class_obj =self.env['property.type'].search([('purpose', 'in', ['commercial','residentialandcommercial','residentialorcommercial']),('parent_type_id', "=", self.parent_type.id)])
        else:
            class_obj = self.env['property.type'].search([('purpose', '=', False)])

        type_list = []
        for data in class_obj:
            type_list.append(data.id)

        res = {}
        res['domain'] = {'property_type_id': [('id', 'in', type_list)]}
        return res

    # @api.onchange('property_child_ids')
    # def _onchange_property_child_ids(self):
    #     self.ensure_one()
    #     residential_ids = []
    #     commercial_ids = []
    #     for child in self.mapped('property_child_ids'):
    #         if child.purpose == 'residential':
    #             residential_ids.append(child.id)
    #         elif child.purpose == 'commercial':
    #             commercial_ids.append(child.id)
    #     self.residential_child_ids = [(6, 0, residential_ids)]        
    #     self.commercial_child_ids = [(6, 0, commercial_ids)]        

    # @api.onchange('residential_child_ids')
    # def _onchange_residential_child_ids(self):
    #     self.ensure_one()
    #     commercial_ids = self.property_child_ids.filtered(lambda child: child.purpose == 'commercial').ids
    #     self.property_child_ids = [(6, 0, commercial_ids + self.residential_child_ids.ids)]


    # @api.onchange('commercial_child_ids')
    # def _onchange_commcial_child_ids(self):
    #     self.ensure_one()
    #     residential_ids = self.property_child_ids.filtered(lambda child: child.purpose == 'residential').ids
    #     self.property_child_ids = [(6, 0, residential_ids + self.commercial_child_ids.ids)]

    @api.onchange("property_type_id")
    def _onchange_type_id(self):
        self.property_line_ids = [(5, 0, 0)]
        property_lines = [(5, 0, 0)]
        for line in self.property_type_id.property_type_line_ids:
            data = {
                'property_id' : self.id,
                'property_unit_id' : line,
                'property_unit_qty' : 1
            }
            property_lines.append((0, 0, data))
        self.property_line_ids = property_lines
        self.is_mu=False





    # @api.depends('has_rooms','has_kitchen','has_bathroom','has_living_room','has_garden','has_garage')
    # def _compute_has_facilities(self):
    #     for record in self :
    #         record.has_facilities = record.has_rooms or record.has_kitchen or record.has_bathroom or record.has_living_room or record.has_garden or record.has_garage

    # # @api.onchange("for_sale",'for_rent','has_rooms','has_kitchen','has_bathroom','has_living_room','has_garden','has_garage')
    # @api.onchange('has_rooms','has_kitchen','has_bathroom','has_living_room','has_garden','has_garage')
    # def _onchange_for_sale(self):
    #     # if(self.for_sale==False):
    #     #     self.expected_sale_price=0
    #     # if(self.for_rent==False):
    #     #     self.expected_rent_price=0
    #     if(self.has_rooms==False):
    #         self.num_rooms=0
    #     if(self.has_kitchen==False):
    #         self.num_kitchen=0
    #     if(self.has_bathroom==False):
    #         self.num_bathroom=0  
    #     if(self.has_living_room==False):
    #         self.num_living_room=0
    #     if(self.has_garden==False):
    #         self.num_garden=0
    #     if(self.has_garage==False):
    #         self.num_garage=0

    # @api.constrains('has_rooms','has_kitchen','has_bathroom','has_living_room','has_garden','has_garage')
    # def _check_description(self):
    #     for record in self:
    #         if ((record.num_rooms <= 0 )and  (record.has_rooms)):
    #             raise ValidationError("number of rooms cannot be less than or equal zero ")
    #         if ((record.num_kitchen <= 0 )and  (record.has_kitchen)):
    #             raise ValidationError("number of kitchens cannot be less than or equal zero ")
    #         if ((record.num_bathroom <= 0 )and  (record.has_bathroom)):
    #             raise ValidationError("number of bathroom cannot be less than or equal zero ")
    #         if ((record.num_living_room <= 0 )and  (record.has_living_room)):
    #             raise ValidationError("number of  living rooms be less than or equal zero ")
    #         if ((record.num_garden <= 0 )and  (record.has_garden)):
    #             raise ValidationError("number of gardens cannot be less than or equal zero ")
    #         if ((record.num_garage <= 0 )and  (record.has_garage)):
    #             raise ValidationError("number of garages cannot be less than or equal zero ")
	       
    @api.constrains('parent_property_id')
    def _check_parent(self):
        for record in self:
            if (record.parent_property_id.id == record.id):
                raise ValidationError(_("A property cannot be a parent of itself !!"))

              

    '''This method should be implemented when inheriting the property model in the sales or rent module'''
    # @api.constrains('for_sale','expected_sale_price','for_rent','expected_rent_price')
    # def _check_selling_and_renting_price(self):
    #     for record in self:
    #         if ((record.expected_sale_price <= 0 )and  (record.for_sale)):
    #             if ((record.expected_rent_price <= 0 )and  (record.for_rent)):
    #                 raise ValidationError("The selling and the renting prices cannot be less than or equal zero ")
    #             raise ValidationError("the selling price  cannot be less than or equal zero ")
    #         if ((record.expected_rent_price <= 0 )and  (record.for_rent)):
    #             raise ValidationError("the renting price cannot be less than or equal zero ")
    #
    

class PropertyLine(models.Model):
    _name = "property.line"
    _description = "property lines"

    property_id = fields.Many2one("property" , ondelete='cascade',string="Property")
    property_unit_id =  fields.Many2one("property.unit", string = "Unit")
    property_unit_qty =  fields.Integer(string = "Quantity", default = 1)
    sequence = fields.Integer('Sequence', default=2, help="Used to order stages. Lower is better.")

