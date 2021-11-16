from odoo import fields, models, tools


class ReportPropertyRent(models.Model):
    _name = "property.rent.report"
    _description = "Rents Analysis"
    _auto = False

    rent_order_id = fields.Integer(string='ID', readonly=True)
    property_id = fields.Many2one('property', string='Properties', readonly=True)
    tenant_id = fields.Many2one("res.partner", string="Tenents", readonly=True)
    property_type_id = fields.Many2one('property.type', string='Type', readonly=True)
    property_city = fields.Char(string='City', readonly=True)
    starting_date = fields.Date(string='Starting Date', readonly=True)

    property_rent_type = fields.Selection(
        string='Rent State',
        selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('rent order', 'Rent Order'),
                    ('canceled', 'Canceled'), ('on hold', 'On Hold'), ('end', 'End')],
        default='quotation',
        readonly=True)
    payment_type = fields.Selection(
        string="Payment Type",
        selection=[('12', 'Monthly'), ('4', 'Quarterly'),
                   ('2 ', 'Semiannually'), ('1', 'Annually')],
        default='1',
        readonly=True)

    property_state = fields.Selection(
        selection=[('available', 'Available'),('not available (reserved)', 'Reserved'), ('not available', 'Not Available'), ],
        string='Property State',
        readonly=True)
    rent_order_state = fields.Selection(
        string='Rent State',
        selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('rent order', 'Rent Order'),
                    ('canceled', 'Canceled'), ('on hold', 'On Hold'), ('end', 'End')],
        default='quotation',
        readonly=True)

    property_offered_price = fields.Float(string='Offered Price', readonly=True)
    property_expected_rent_price = fields.Float(string='Exp. Rent Price', readonly=True)
    # avg_expected_rent_price =  fields.Float(string='Avg. Expected Rent Price', readonly=True)
    # deposit = fields.Boolean(string='Deposit' ,readonly=True)
    # deposit_amount = fields.Float(string='Deposit Amount', readonly=True)

    def _select(self):
        select_str = """
            SELECT
                r.id as id,
                r.id as rent_order_id,
                p.id as property_id,
                t.id as tenant_id,
                pt.id as property_type_id,
                p.city as property_city,
                r.starting_date as starting_date,
                p.rent_type as property_rent_type,
                r.payment_type as payment_type,
                p.state as property_state,
                r.state as rent_order_state,
                p.expected_rent_price as property_expected_rent_price,
                r.offered_price as property_offered_price
        """
        return select_str

    def _from(self):
        from_str = """
            FROM 
                property_rent r
                    left outer join property p on (p.id=r.property_id)
                        left outer join property_type pt on (pt.id=p.property_type_id) 
                    left outer join res_partner t on (t.id=r.tenant_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                r.id,
                p.id,
                t.id,
                pt.id,
                p.city,
                r.starting_date,
                p.rent_type,
                r.payment_type,
                p.state,
                r.state
        """
        
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE view %s as (%s %s %s)
        """ % (self._table, self._select(), self._from(), self._group_by()))
