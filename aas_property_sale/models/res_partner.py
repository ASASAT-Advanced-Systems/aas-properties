from odoo import models, api, fields
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = "res.partner"

    property_sale_ids = fields.One2many("property.sale", "customer_id")
    has_sales = fields.Boolean(compute = "_compute_num_of_sales", store = True)
    sales_count = fields.Integer(compute="_compute_sales_count")
    

    @api.depends("property_sale_ids")
    def _compute_num_of_sales(self):
        for record in self:
            record.has_sales = False
            if len(record.mapped("property_sale_ids")):
                record.has_sales = True


    def _compute_sales_count(self):
        for owner in self:
            owner.sales_count = self.env['property.sale'].search_count([('id', 'in', owner.property_sale_ids.ids)])


    def action_show_sales(self):
        self.ensure_one()
        return {
            "name": "sale records",
            "type": "ir.actions.act_window",
            "res_model": "property.sale",
            "view_mode": "tree,form",
            "domain": [('id', 'in', self.property_sale_ids.ids)],
        }  
