from odoo import fields, models, tools


class ReportPropertySale(models.Model):
    _name = "property.sale.report"
    _description = "Sales Analysis"
    _auto = False

    sale_order_id = fields.Integer(string='ID', readonly=True)
    property_id = fields.Many2one('property', string='Properties', readonly=True)
    customer_id = fields.Many2one("res.partner", string="Customers", readonly=True)
    property_type_id = fields.Many2one('property.type', string='Type', readonly=True)
    property_city = fields.Char(string='City', readonly=True)
    date = fields.Date(string='Date', readonly=True)

    # property_sale_state = fields.Selection(
    #     string='sale State',
    #     selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('sale order', 'sale Order'),
    #                 ('canceled', 'Canceled'), ('on hold', 'On Hold')],
    #     default='quotation',
    #     readonly=True)
    

    property_state = fields.Selection(
        selection=[('available', 'Available'),('not available (reserved)', 'Reserved'), ('not available', 'Not Available'), ],
        string='Property State',
        readonly=True)
    # sale_order_state = fields.Selection(
    #     string='sale State',
    #     selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('sale order', 'sale Order'),
    #                 ('canceled', 'Canceled'), ('on hold', 'On Hold'), ('end', 'End')],
    #     default='quotation',
    #     readonly=True)
    sale_order_state = fields.Selection(
        string='sale State',
        selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('sale order', 'sale Order'),
                    ('canceled', 'Canceled'), ('on hold', 'On Hold')],
        default='quotation',
        readonly=True)

    property_offered_price = fields.Float(string='Offered Price', readonly=True)
    property_expected_sale_price = fields.Float(string='Exp. sale Price', readonly=True)
    # avg_expected_sale_price =  fields.Float(string='Avg. Expected sale Price', readonly=True)
    # deposit = fields.Boolean(string='Deposit' ,readonly=True)
    # deposit_amount = fields.Float(string='Deposit Amount', readonly=True)

    def _select(self):
        select_str = """
            SELECT
                r.id as id,
                r.id as sale_order_id,
                p.id as property_id,
                t.id as customer_id,
                pt.id as property_type_id,
                p.city as property_city,
                r.date as date,
                p.state as property_state,
                r.state as sale_order_state,
                p.expected_sale_price as property_expected_sale_price,
                r.offered_price as property_offered_price
        """
        return select_str

    def _from(self):
        from_str = """
            FROM 
                property_sale r
                    left outer join property p on (p.id=r.property_id)
                        left outer join property_type pt on (pt.id=p.property_type_id) 
                    left outer join res_partner t on (t.id=r.customer_id)
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
                r.date,
                p.state,
                r.state
        """
        
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE view %s as (%s %s %s)
        """ % (self._table, self._select(), self._from(), self._group_by()))
