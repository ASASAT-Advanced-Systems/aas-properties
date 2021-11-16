from odoo import api, fields, models,_


class PropertyType(models.Model):
    _name = 'property.type'
    _description = 'This model describes the type of a property'

    name = fields.Char(string='Type', default = "New Type", translate=True)
    # parent_property_type_id= fields.Many2one("property.type")
    parent_type_id=            fields.Many2one("property.type",string="Parent Type")
    child_type_ids =        fields.One2many("property.type","parent_type_id",string="Child Type")
    property_ids =          fields.One2many(comodel_name='property', inverse_name='property_type_id',string="Properties")
    property_type_line_ids= fields.Many2many('property.unit', 'rel_type_unit',string="Property Types")
    is_mu =                 fields.Boolean(string='Is Multi Unit',default=False)
    has_parent_type =   fields.Boolean(string="Property Has Parent Type")
    purpose =               fields.Selection(string="Purpose",selection=[('residential', 'Residential'),('commercial', 'Commercial'),('residentialandcommercial', 'Residential & Commercial'), ('residentialorcommercial', 'Residential or Commercial')])
    property_count =        fields.Integer(compute='_countPropertiess', store=True,string="Property Count")
    is_floor =              fields.Boolean(default=False,string="Is Floor")
    has_street_length=      fields.Boolean(string="Has Street Length")

    @api.depends('property_ids')
    def _countPropertiess(self):
        for recored in self:
            recored.property_count = len(recored.mapped("property_ids"))
    

    _sql_constraints = [
        ('check_property_type_line_ids', 'UNIQUE(property_type_line_ids)', _('A property type line must be unique'))
    ]

