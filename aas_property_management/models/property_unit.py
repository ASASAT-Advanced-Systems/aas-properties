from odoo import fields, models,api,_

class PropertyUnit(models.Model):
    _name =         "property.unit"
    _description = 'This model describes the unit of a property'
    _order =        "name"
    name =          fields.Char(string="Unit Title", translate=True)
    _sql_constraints = [
        ('unique_name', 'unique (name)', _('unit already exists! , write another name!!')),
    ] 
