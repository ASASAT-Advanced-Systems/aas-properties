from odoo import models, fields,_

class PropertyTag(models.Model):
    _name = "property.tag"
    _description = "Property Tag"
    _order = "name"

    name = fields.Char(required=True, string ="Title", translate=True)
    color = fields.Integer()
    _sql_constraints = [
        ('unique_name', 'UNIQUE(name)',
         _('The tag name must be unique'))]