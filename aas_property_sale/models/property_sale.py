from odoo import fields, models, api,_
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class PropertySale(models.Model):
    _name = "property.sale"
    # _inherit= ['mail.thread']
    _inherit= ['mail.thread', 'mail.activity.mixin']
    _description = "property_sale"

    name    = fields.Char(string = "Number" ,readonly=True , default="New")
    sequence = fields.Integer(string='Sequence', default=10)
    
    user_id                     = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)
    property_id                 = fields.Many2one(comodel_name='property', domain="[('property_sale_state','in',['available'])]", ondelete='cascade', string = "Property")
    customer_id                   = fields.Many2one("res.partner", string="Customer", required = True)
    prev_property_owner_id         =   fields.Many2one("res.partner", string = "Previous Owner")
    date               = fields.Date(default=fields.Date.today(), tracking = True, string = "Date")
    # deposit                     = fields.Boolean()
    # deposit_amount              = fields.Float(compute = "_compute_deposit_ammount", store = True)
    is_invoice_created          = fields.Boolean(default = False)
    move_ids                    = fields.One2many(comodel_name = 'account.move', inverse_name = 'property_sale_id', readonly=True)
    move_ids_payment_state      = fields.Selection(related = "move_ids.payment_state")
    expected_sale_price_related = fields.Float(related="property_id.expected_sale_price", store=True, string ="Expected Sale Price")
    offered_price               = fields.Float(string = "Offered Price", tracking = True)
    property_type_id_related    = fields.Many2one(related="property_id.property_type_id", store=True, string ="Property Type")
    street_related              = fields.Char(related="property_id.street", store=True)
    street2_related             = fields.Char(related="property_id.street2", store=True)
    city_related                = fields.Char(related="property_id.city", store=True)
    district_related            = fields.Char(related="property_id.district", store=True)
    zip_related                 = fields.Char(related="property_id.zip", store=True)
    country_id_related          = fields.Many2one(related="property_id.country_id", store=True)
    property_state_related      = fields.Selection(related="property_id.state", store=True)
    payment_cost_comm_ids       = fields.One2many("property.salepaymentline","property_sale_id",ondelete='cascade',string="Payment Amount")
    property_owner_id_related   = fields.Many2one(related="property_id.property_owner_id", string ="Property Owner")
    owner_pay_commission        = fields.Boolean(default = False, string = "Owner pays commission and fees")
    state                       = fields.Selection(
        string='Sale Order State',
        required=True,
        copy=False,
        selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('sale order', 'Sale Order'),
                    ('canceled', 'Canceled'), ('on hold', 'On Hold')],
        default='quotation')
    invoice_status              = fields.Selection(
        string='Invoice Status',
        compute = '_compute_invoice_state',
        store=True,
        copy=False,
        selection=[('nothing to invoice', 'Nothing To Invoice'), ('to invoice', 'To Invoice'), ('invoiced', 'Invoiced')],
        default='nothing to invoice')
     
    def _default_comm_admin_account_id(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_sale.comm_admin_account_id')
    sale_comm_admin_account_id = fields.Many2one("account.account", default =_default_comm_admin_account_id)

    def _default_sale_tax_id(self):
        return int(self.env['ir.config_parameter'].sudo().get_param("property_sale.sale_tax_id"))

    sale_tax_id = fields.Many2one('account.tax', string='Tax', default =_default_sale_tax_id)
    # renew_period = fields.Integer(default =lambda self: self.env['ir.config_parameter'].sudo().get_param('property_sale.renew_period'))

    # def action_set_sale(self):
    #     for record in self:
    #         temp = record.mapped('property_id.property_sale_ids')
    #         for sale in temp:
    #             if(sale.state == 'on hold'):
    #                 sale.state = 'canceled'
    #         record.state = 'sale order'
    #     return  True
    # @api.depends('state')
    # def _computecosts(self):
    #     for record in self:
    #         record.sale_cost = ""
    #         num_of_payments = int(int(record.payment_type)/int(record.property_sale_type_related))
    #         period = int(12/num_of_payments)
    #         total_sale = record.offered_price * (1 + record.property_id.service_fees/100)
    #         price_unit= (total_sale)*((record.property_id.sale_commission + record.property_id.sale_administrative_fees)/100)
    #         for payment in range(period) :
    #             date_due = record.date + relativedelta(months=payment*period)
    #             record.sale_cost += f'{payment+1}- {price_unit}\t{date_due}\n'
    #         record.sale_cost += f'\t \t the total is {total_sale}'    

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('aas_property_sale.property_sale') or _('New')
        create_sale = super(PropertySale, self).create(vals)
        return create_sale

    def unlink(self):
        for record in self:
            if(record.state in ["reserved" ] ):
                record.property_id.property_sale_state = "available"
        unlink_sale = super(PropertySale, self).unlink()
        return unlink_sale


    @api.onchange('offered_price')
    def _onchange_for_payment_lines(self):
        self.payment_cost_comm_ids = [(5, 0, 0)]
        paymet_costs_comm = [(5, 0, 0)]
        commission_var=(self.offered_price)*(self.property_id.sale_commission /100)
        data = {'name' : _("Commission"),'Payment_cost' :commission_var, 'tax':commission_var*self.sale_tax_id.amount/100, 'total_amount':commission_var*(1+self.sale_tax_id.amount/100) }
        paymet_costs_comm.append((0, 0, data))
        administrative_fees_var=(self.offered_price)*(self.property_id.sale_administrative_fees/100)
        data = {'name' : _("Administrative Fees"),'Payment_cost' : administrative_fees_var, 'tax':administrative_fees_var*self.sale_tax_id.amount/100, 'total_amount':administrative_fees_var*(1+self.sale_tax_id.amount/100)}
        paymet_costs_comm.append((0, 0, data))
        data = {'name' : _("Total"),'total_amount' : (commission_var+administrative_fees_var)*(1+self.sale_tax_id.amount/100) }
        paymet_costs_comm.append((0, 0, data))
        self.payment_cost_comm_ids = paymet_costs_comm

    @api.depends("state", "is_invoice_created")
    def _compute_invoice_state(self):
        for record in self:
            if record.state in ['quotation', 'reserved', 'canceled', 'on hold'] and record.is_invoice_created == False:
                record.invoice_status = 'nothing to invoice'
            elif record.state in ['sale order'] and record.is_invoice_created == False:
                record.invoice_status = 'to invoice'
            elif record.is_invoice_created == True:
                record.invoice_status = 'invoiced'
            else: record.invoice_status = False

    def action_create_invoice(self):
        for record in self:
            customer = record.customer_id.id
            if record.owner_pay_commission:
                customer = record.prev_property_owner_id.id
            journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
            move = record.env['account.move'].create({
                'invoice_origin': record.name,
                'partner_id': customer,
                'move_type': 'out_invoice',
                'journal_id': journal.id,
                'property_sale_id' : record.id,
                'invoice_date_due' : fields.Date.today(),
                'invoice_line_ids':[
                    (0,0,{ 'name': _("Commission"), 'price_unit': (record.offered_price)*(record.property_id.sale_commission/100), 'account_id': record.sale_comm_admin_account_id, 'tax_ids': record.sale_tax_id}),
                    (0,0,{ 'name': _("Administrative Fees"), 'price_unit': (record.offered_price)*(record.property_id.sale_administrative_fees/100), 'account_id': record.sale_comm_admin_account_id, 'tax_ids': record.sale_tax_id}),
                ]
                })
            record.is_invoice_created = True
            record.message_post(body=_("Invoice Created"))
            
        if self._context.get('open_invoices', False):
            return self.action_view_invoice()

        return  True

    def action_set_confirm(self):
        for record in self:
            if record.customer_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.customer_id.name} as a customer to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_sale_ids')
                for sale in temp:
                    if(sale.state == 'on hold'):
                        sale.state = 'canceled'
                record.state = 'sale order'
                
                record.property_id.is_sold = True
                record.prev_property_owner_id=record.property_id.property_owner_id
                record.property_id.property_owner_id = record.customer_id
                record.property_id.for_sale = False
                record.property_id.property_sale_state = 'sold'
                record.property_id.is_confirmed = False
                record.property_id.state="draft"
                record.message_post(body= _("Sale order with number <b>%s</b> has been <b>Confirmed</b>", record.name))
                sale_ref = f"<a href='#' data-oe-model={self._name} data-oe-id={self.id}>{self.name}</a>"
                record.property_id.message_post(body=_("%s's state has changed to <b>%s</b> due to a confirmation of the <b>Sale Order %s</b>", record.property_id.name, record.property_id.state, sale_ref))
                # total_sale = record.offered_price * (1 + record.property_id.service_fees/100)
                # journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                # move = record.env['account.move'].create({
                #     'partner_id': record.customer_id.id,
                #     'move_type': 'out_invoice',
                #     'journal_id': journal.id,
                #     'pstateroperty_sale_id' : record.id,
                #     'invoice_date_due' : fields.Date.today(),
                #     'invoice_line_ids':[
                #         #Below needs to be checked (calculating the payments when there is deposit)
                #         (0,0,{ 'name': "Commission", 'price_unit': (record.offered_price)*(record.property_id.sale_commission/100), 'account_id': record.comm_admin_account_id}),
                #         (0,0,{ 'name': "Administrative Fees", 'price_unit': (record.offered_price)*(record.property_id.sale_administrative_fees/100), 'account_id': record.comm_admin_account_id}),
                #     ]
                #     })
                # journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                # move = record.env['account.move'].create({
                #     'partner_id': record.customer_id.id,
                #     'move_type': 'out_invoice',
                #     'journal_id': journal.id,
                #     'property_sale_id' : record.id,
                #     'invoice_date_due' : fields.Date.today(),
                #     'invoice_line_ids':[
                #         #Below needs to be checked (calculating the payments when there is deposit)
                #         (0,0,{ 'name': record.customer_id.name, 'price_unit': (record.offered_price)*(record.property_id.sale_administrative_fees/100)}),
                #     ]
                #     })
                # num_of_payments = int(int(record.payment_type)/int(record.property_sale_type_related))
                # period = 12/num_of_payments
                # for i in range(0, num_of_payments):
                #     journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                #     move = record.env['account.move'].create({
                #         'partner_id': record.customer_id.id,
                #         'move_type': 'out_invoice',
                #         'journal_id': journal.id,
                #         'property_sale_id' : record.id,
                #         'invoice_date_due' : record.date + relativedelta(months=i*period),
                #         'invoice_line_ids':[
                #             #Below needs to be checked (calculating the payments when there is deposit)
                #             (0,0,{ 'name': record.customer_id.name, 'price_unit': (total_sale - record.deposit_amount)/num_of_payments}),
                #         ]
                #     })
        return  True
        
    def action_reset_to_quotation(self):
        for record in self:
            if record.customer_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.customer_id.name} as a customer to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_sale_ids')
                for sale in temp:
                    if(sale.state == 'on hold'):
                        sale.state = 'quotation'

                record.state = "quotation"
                record.property_id.property_sale_state = 'available'
                record.message_post(body= _("Sale order with number <b>%s</b> has been reset to <b>Quotation</b>", record.name))
        return True

    def action_set_reserve(self):
        for record in self:
            if record.customer_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.customer_id.name} as a customer to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_sale_ids')
                for sale in temp:
                    if(sale.property_id == self.property_id and (sale.state not in ['canceled','sale order'])):
                        sale.state = 'on hold'
                record.state = 'reserved'
                record.property_id.property_sale_state = 'reserved'
                record.message_post(body= _("Sale order with number <b>%s</b> has been <b>Reserved</b>", record.name))
        return True

    def action_set_cancel(self):
        for record in self:
            temp = record.mapped('property_id.property_sale_ids')
            for sale in temp:
                if(sale.state == 'on hold'):
                    sale.state = 'quotation'
            if(record.state in ['sale order','reserved']):
                record.property_id.is_sold = False
                record.property_id.property_sale_state = 'available'
            record.state = 'canceled'
            record.message_post(body= _("Sale order with number <b>%s</b> has been <b>Canceled</b>", record.name))
        return True

    # @api.depends("move_ids.payment_state")
    # def _compute_deposit_ammount(self):
    #     for record in self:
    #         if len(record.move_ids) > 0:
    #             for move in record.move_ids:
    #                 if move.is_deposit:
    #                     if move.payment_state in (['in_payment', 'paid']) :
    #                         if not record.state =='sale order':
    #                             record.action_set_reserve()
    #                             record.deposit_amount = move.amount_total
    #                     else:
    #                         record.deposit_amount = 0.0
    #         else:
    #             record.deposit_amount = 0.0
    
    def action_view_invoice(self):
        invoices = self.mapped('move_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_invoice_origin': self.mapped('name'),
                'default_user_id': self.user_id.id,
            })
        action['context'] = context
        return action
    
    def action_show_invoices(self):
        self.ensure_one()
        return {
            "name": "Invoices",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "context": {'create': False},
            "domain": [('id', 'in', self.move_ids.ids)],
        }  

    # @api.constrains('deposit')
    # def _check_deposit(self):
        # for record in self:
        #     if ((record.deposit_amount <= 0) and (record.deposit)):
        #         raise ValidationError(
        #             "deposit amount cannot be less than or equal zero ")

    @api.constrains('offered_price')
    def _check_saleing_price(self):
        for record in self:
            if ((record.offered_price < record.expected_sale_price_related)):
                raise ValidationError(
                    _("The offered price cannot be less than the expected price"))

    @api.constrains('customer_id','property_id')
    def _check_customer_eligibility(self):
        for record in self:
            if record.customer_id == record.property_id.property_owner_id and record.state not in ['canceled','sale order']:
                raise UserError(_(f"You cannot assign {record.customer_id.name} as a customer to {record.property_id.name} as he is an owner to it."))

class SalePaymentsLine(models.Model):
    _name = "property.salepaymentline"
    _description = "property paymentline"

    name = fields.Char()
    Payment_cost=fields.Float(string="Amount")
    tax = fields.Float("Taxes")
    total_amount = fields.Float("Total Amount")
    property_sale_id=fields.Many2one("property.sale" , ondelete='cascade')
            