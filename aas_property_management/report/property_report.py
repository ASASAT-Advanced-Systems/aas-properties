from odoo import fields, models, tools


class ReportProperty(models.Model):
    _name = "property.report"
    _description = "Properties Analysis"
    _auto = False

    property_name = fields.Char(string='Property Title', readonly=True)

    def _select(self):
        select_str = """
            SELECT
                p.id as id,
                p.name as property_name
        """
        return select_str

    def _from(self):
        from_str = """
            FROM 
                property p
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                p.id,
                p.name
        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE or REPLACE view %s as (%s %s %s)
        """ % (self._table, self._select(), self._from(), self._group_by()))    