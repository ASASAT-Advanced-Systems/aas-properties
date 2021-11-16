from odoo import api, fields, models,_


class ResPartner(models.Model):
    _inherit = 'res.partner'

    national_id =       fields.Char(string='National ID', required=True)
    national_address =  fields.Char(string='shortened national address', required=True)
    property_ids =      fields.One2many("property", "property_owner_id", string="Properties")
    property_count =    fields.Integer(compute="_compute_property_count",string="Property Count")
    num_properties =    fields.Text(compute='_count_properties', string='Owner has:', readonly=True, store=True)
    bank_account_ids =  fields.One2many(comodel_name='bank.account', inverse_name='owner_id',string="Bank Account")

    @api.depends('property_ids')
    def _compute_property_count(self):
        for owner in self:
            owner.property_count = self.env['property'].search_count(
                [('id', 'in', owner.property_ids.ids)])

    def action_show_properties(self):
        self.ensure_one()
        return {
            "name": "Property",
            "type": "ir.actions.act_window",
            "res_model": "property",
            "view_mode": "tree,form",
            "domain": [('id', 'in', self.property_ids.ids)],
            'context': {'search_default_type': True},
        }

    @api.depends('property_ids')
    def _count_properties(self):
        for owner in self:
            owner.num_properties = ""
            SubPropTypes = dict.fromkeys(owner.mapped(
                'property_ids.property_type_id.name'))
            for key in SubPropTypes:
                SubPropTypes[key] = 0

            for key in SubPropTypes:
                for record in owner.property_ids:
                    if record.property_type_id.name == key:
                        SubPropTypes[key] += 1
                owner.num_properties += f'{SubPropTypes[key]}\t{key}(s) \n'


class BankAccount(models.Model):
    _name = "bank.account"
    _description = "this class is for having multiple accounts for each owner"

    bank_account = fields.Char(string="Bank Account")
    name = fields.Selection(string='Bank', selection=[(
          'ncb', 'The National Commercial Bank'),
         ('sabb', 'The Saudi British Bank (SABB)'), 
         ('sib', 'Saudi Investment Bank'), 
         ('alinma', 'Alinma bank'), 
         ('fransi', 'Banque Saudi Fransi'), 
         ('riyad', 'Riyad Bank'), 
         ('samba', 'Samba Financial Group (Samba)'), 
         ('alawwal', 'Alawwal bank'),
         ('alrajhi', 'Al Rajhi Bank'), 
         ('arabbank', 'Arab National Bank'), 
         ('albilad', 'Bank AlBilad'), 
         ('aljazira', 'Bank AlJazira'), 
         ('snb', 'Saudi National Bank')])

    owner_id = fields.Many2one("res.partner", invisible=True, string="Owner")
