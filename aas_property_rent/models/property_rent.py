from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta

class PropertyRent(models.Model):
    _name = "property.rent"
    # _inherit= ['mail.thread']
    _inherit= ['mail.thread', 'mail.activity.mixin']
    _description = "property_rent"

    name    = fields.Char(string = "Number" ,readonly=True , default="New")
    sequence = fields.Integer(string='Sequence', default=10)
    
    user_id                     = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)
    renewed_user_id             = fields.Many2one("res.users", string="Salesman", default=lambda self: self.env.user)
    property_id                 = fields.Many2one(comodel_name='property', string = "Property Title", domain="[('property_rent_state','in',['available'])]", ondelete='cascade')
    tenant_id                   = fields.Many2one("res.partner", string="Tenent", required = True)

    starting_date               = fields.Date(string = "Starting Date", default=fields.Date.today(), tracking = True)
    end_date                    = fields.Date(compute= "_compute_end_date", store = True)
    requires_renewal            = fields.Boolean(string = "Requires Renewal")
    asked_for_renewal           = fields.Boolean(string = "Asked for renewal")
    deposit                     = fields.Boolean(string = "Deposit")
    deposit_amount              = fields.Float(string = "Deposit Amount", compute = "_compute_deposit_ammount", store = True)
    is_invoice_created          = fields.Boolean(default = False)
    move_ids                    = fields.One2many(comodel_name = 'account.move', inverse_name = 'property_rent_id', string="Move Ids", readonly=True)
    move_ids_payment_state      = fields.Selection(string = "Move Ids Payment State", related = "move_ids.payment_state")
    expected_rent_price_related = fields.Float(related="property_id.expected_rent_price", store=True)
    offered_price               = fields.Float(string = "Offered Price", tracking = True)
    property_type_id_related    = fields.Many2one(related="property_id.property_type_id", store=True)
    property_rent_type_related  = fields.Selection(related="property_id.rent_type", store=True)
    street_related              = fields.Char(related="property_id.street", store=True)
    street2_related             = fields.Char(related="property_id.street2", store=True)
    city_related                = fields.Char(related="property_id.city", store=True)
    district_related            = fields.Char(related="property_id.district", store=True)
    zip_related                 = fields.Char(related="property_id.zip", store=True)
    country_id_related          = fields.Many2one(related="property_id.country_id", store=True)
    property_state_related      = fields.Selection(related="property_id.state", store=True)
    payment_cost_comm_ids       = fields.One2many("property.rentpaymentline","property_rent_id",ondelete='cascade',string="Payment Amount",domain=lambda self: [('is_rent_payment', '=', False)])
    payment_cost_paym_ids       = fields.One2many("property.rentpaymentline","property_rent_id",ondelete='cascade',string="Payment Amount",domain=lambda self: [('is_rent_payment', '=', True)])
    property_owner_id_related   = fields.Many2one(related="property_id.property_owner_id")
    payment_type                = fields.Selection(
        string="Payment Type",
        required=True,
        selection=[('12', 'Monthly'), ('4', 'Quarterly'),
                   ('2', 'Semiannually'), ('1', 'Annually')],
        default='1')
    state                       = fields.Selection(
        string='Rent State',
        required=True,
        copy=False,
        selection=[('quotation', 'Quotation'), ('reserved', 'Reserved'), ('rent order', 'Rent Order'),
                    ('canceled', 'Canceled'), ('on hold', 'On Hold'), ('end', 'End')],
        default='quotation')
    invoice_status              = fields.Selection(
        string='Invoice Status',
        compute = '_compute_invoice_state',
        store=True,
        copy=False,
        selection=[('nothing to invoice', 'Nothing To Invoice'), ('to invoice', 'To Invoice'), ('invoiced', 'Invoiced')],
        default='nothing to invoice')
    
    def _default_comm_admin_account_id(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.comm_admin_account_id')

    rent_comm_admin_account_id = fields.Many2one("account.account", default =_default_comm_admin_account_id)

    def _default_service_account_id(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.service_account_id')

    rent_service_account_id = fields.Many2one("account.account", default =_default_service_account_id)

    def _default_rent_tax_id(self):
        return int(self.env['ir.config_parameter'].sudo().get_param("property_rent.rent_tax_id"))

    def _default_rent_payment_tax(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_rent.rent_payment_tax')

    rent_tax_id = fields.Many2one('account.tax', string='Tax', default =_default_rent_tax_id)
    rent_payment_tax = fields.Float("Rent Payments Tax Percentage", default =_default_rent_payment_tax)
    # renew_period = fields.Integer(default =lambda self: self.env['ir.config_parameter'].sudo().get_param('property_rent.renew_period'))

    # def action_set_rent(self):
    #     for record in self:
    #         temp = record.mapped('property_id.property_rent_ids')
    #         for rent in temp:
    #             if(rent.state == 'on hold'):
    #                 rent.state = 'canceled'
    #         record.state = 'rent order'
    #     return  True
    # @api.depends('state')
    # def _computecosts(self):
    #     for record in self:
    #         record.rent_cost = ""
    #         num_of_payments = int(int(record.payment_type)/int(record.property_rent_type_related))
    #         period = int(12/num_of_payments)
    #         total_rent = record.offered_price * (1 + record.property_id.service_fees/100)
    #         price_unit= (total_rent)*((record.property_id.commission + record.property_id.administrative_fees)/100)
    #         for payment in range(period) :
    #             date_due = record.starting_date + relativedelta(months=payment*period)
    #             record.rent_cost += f'{payment+1}- {price_unit}\t{date_due}\n'
    #         record.rent_cost += f'\t \t the total is {total_rent}'

    @api.onchange('offered_price','starting_date','payment_type')
    def _onchange_for_payment_lines(self):
        self.payment_cost_comm_ids = [(5, 0, 0)]
        self.payment_cost_paym_ids = [(5, 0, 0)]
        num_of_payments = int(int(self.payment_type)/int(self.property_rent_type_related))

        period = int(12/num_of_payments)
        if not self.property_id.company_responsible_for_service:
            total_rent = self.offered_price * (1 + (self.property_id.rent_service_fees)/100)
        else:
            total_rent = self.offered_price
        price_unit=(total_rent)/num_of_payments
        tax = price_unit*self.rent_payment_tax/100
        total_amount = price_unit+tax
        date_due = self.starting_date
        paymet_costs_comm = [(5, 0, 0)]
        total_comm_fees = 0
        commission_var=(self.offered_price)*(self.property_id.rent_commission /100)
        data = {'name' : _("Commission"),'Payment_cost' :commission_var ,'tax': commission_var*self.rent_tax_id.amount/100 , 'total_amount':commission_var*(1+self.rent_tax_id.amount/100) ,'Due_Date' : date_due ,'is_rent_payment':False}
        paymet_costs_comm.append((0, 0, data))
        total_comm_fees += commission_var*(1+self.rent_tax_id.amount/100) 
        administrative_fees_var=(self.offered_price)*(self.property_id.rent_administrative_fees/100)
        data = {'name' : _("Administrative Fees"),'Payment_cost' : administrative_fees_var,'tax': administrative_fees_var*self.rent_tax_id.amount/100 , 'total_amount':administrative_fees_var*(1+self.rent_tax_id.amount/100), 'Due_Date' : date_due ,'is_rent_payment':False}
        paymet_costs_comm.append((0, 0, data))
        total_comm_fees += administrative_fees_var*(1+self.rent_tax_id.amount/100)
        if self.property_id.company_responsible_for_service:
            service_fees_var=(self.offered_price)*(self.property_id.rent_service_fees/100)
            data = {'name' : _("Service Fees"),'Payment_cost' : service_fees_var,'tax': service_fees_var*self.rent_tax_id.amount/100 , 'total_amount':service_fees_var*(1+self.rent_tax_id.amount/100),'Due_Date' : date_due ,'is_rent_payment':False}
            paymet_costs_comm.append((0, 0, data))
            total_comm_fees += service_fees_var*(1+self.rent_tax_id.amount/100)
        data = {'name' : _("Total"),'total_amount' : (total_comm_fees) ,'is_rent_payment':False }
        paymet_costs_comm.append((0, 0, data))
        self.payment_cost_comm_ids = paymet_costs_comm  

        
        paymet_costs_payments = [(5, 0, 0)]
        if(self.property_id.purpose == 'commercial'):
            total_rent*= (1+self.rent_payment_tax/100)
        if self.property_id.refundable_insurance != 0:
            date_due = self.starting_date
            data = {'name' : _("Refundable Insurance") , 'Payment_cost' : self.property_id.refundable_insurance,'total_amount' : self.property_id.refundable_insurance,'Due_Date' : date_due,'is_rent_payment':True}
            paymet_costs_payments.append((0, 0, data))
            total_rent += self.property_id.refundable_insurance
        
        for payment in range(num_of_payments) :
            date_due = self.starting_date + relativedelta(months=payment*period)
            strpayment=str(payment+1)
            if(self.property_id.purpose == 'commercial'):
                data = {'name' : _('Payment') +strpayment ,'Payment_cost' : price_unit, 'tax':tax, 'total_amount': total_amount, 'Due_Date' : date_due,'is_rent_payment':True}
            else:
                data = {'name' : _('Payment') +strpayment ,'Payment_cost' : price_unit, 'tax':0.0, 'total_amount': price_unit, 'Due_Date' : date_due,'is_rent_payment':True}

            paymet_costs_payments.append((0, 0, data))
        data = {'name' : _("Total"),'total_amount' : (total_rent) ,'is_rent_payment':True}
        paymet_costs_payments.append((0, 0, data))

        self.payment_cost_paym_ids = paymet_costs_payments
            
    

    @api.depends("state", "is_invoice_created")
    def _compute_invoice_state(self):
        for record in self:
            if record.state in ['quotation', 'reserved', 'canceled', 'on hold'] and record.is_invoice_created == False:
                record.invoice_status = 'nothing to invoice'
            elif record.state in ['rent order',  'end'] and record.is_invoice_created == False:
                record.invoice_status = 'to invoice'
            elif record.is_invoice_created == True:
                record.invoice_status = 'invoiced'
            else: record.invoice_status = False

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('aas_property_rent.property_rent') or _('New')
        create_rent = super(PropertyRent, self).create(vals)
        return create_rent

    def unlink(self):
        for record in self:
            if(record.state in ["rent order" , "reserved" ] ):
                record.property_id.property_rent_state = "available"
        unlink_rent = super(PropertyRent, self).unlink()
        return unlink_rent

    def action_set_end(self):
        self.state = "end"
        self.property_id.property_rent_state = 'available'
        self.property_id.is_rented = False
        self.asked_for_renewal = False
        self.message_post(body=_("Rent order with the number <b>%s</b> has been <b>Ended</b>", self.name))
        return True

    def action_create_invoice(self):
            for record in self:
                journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                move = record.env['account.move'].create({
                    'invoice_origin': record.name,
                    'partner_id': record.tenant_id.id,
                    'move_type': 'out_invoice',
                    'journal_id': journal.id,
                    'property_rent_id' : record.id,
                    'invoice_date_due' : fields.Date.today(),
                    'invoice_line_ids':[
                        (0,0,{ 'name': _("Commission"), 'price_unit': (record.offered_price)*(record.property_id.rent_commission/100), 'account_id': record.rent_comm_admin_account_id, 'tax_ids': record.rent_tax_id}),
                        (0,0,{ 'name': _("Administrative Fees"), 'price_unit': (record.offered_price)*(record.property_id.rent_administrative_fees/100), 'account_id': record.rent_comm_admin_account_id, 'tax_ids': record.rent_tax_id}),
                    ]
                    })
                if record.property_id.company_responsible_for_service :
                    move.write({'invoice_line_ids' : [(0,0,{ 'name': _("Service Fees"), 'price_unit': (record.offered_price)*(record.property_id.rent_service_fees/100), 'account_id': record.rent_service_account_id, 'tax_ids': record.rent_tax_id})]})
                record.is_invoice_created = True
                record.message_post(body=_("Invoice Created"))

            if self._context.get('open_invoices', False):
                return self.action_view_invoice()
            return  True

    def action_set_confirm(self):
        if(self.property_id.property_rent_state == "not available"):
            raise ValidationError(_("The Rent order Cannot be Confirmed because the property is not available"))
        for record in self:
            if record.tenant_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.tenant_id.name} as a tenant to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_rent_ids')
                for rent in temp:
                    if(rent.state == 'on hold'):
                        rent.state = 'canceled'
                record.state = 'rent order'
                self.property_id.is_rented = True
                self.property_id.property_rent_state="rented"
                record.message_post(body=_("Rent order with the number <b>%s</b> has been <b>Confirmed</b>", record.name))
                # total_rent = record.offered_price * (1 + record.property_id.service_fees/100)
                # journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                # move = record.env['account.move'].create({
                #     'partner_id': record.tenant_id.id,
                #     'move_type': 'out_invoice',
                #     'journal_id': journal.id,
                #     'property_rent_id' : record.id,
                #     'invoice_date_due' : fields.Date.today(),
                #     'invoice_line_ids':[
                #         #Below needs to be checked (calculating the payments when there is deposit)
                #         (0,0,{ 'name': "Commission", 'price_unit': (record.offered_price)*(record.property_id.commission/100), 'account_id': record.comm_admin_account_id}),
                #         (0,0,{ 'name': "Administrative Fees", 'price_unit': (record.offered_price)*(record.property_id.administrative_fees/100), 'account_id': record.comm_admin_account_id}),
                #     ]
                #     })
                # journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                # move = record.env['account.move'].create({
                #     'partner_id': record.tenant_id.id,
                #     'move_type': 'out_invoice',
                #     'journal_id': journal.id,
                #     'property_rent_id' : record.id,
                #     'invoice_date_due' : fields.Date.today(),
                #     'invoice_line_ids':[
                #         #Below needs to be checked (calculating the payments when there is deposit)
                #         (0,0,{ 'name': record.tenant_id.name, 'price_unit': (record.offered_price)*(record.property_id.administrative_fees/100)}),
                #     ]
                #     })
                # num_of_payments = int(int(record.payment_type)/int(record.property_rent_type_related))
                # period = 12/num_of_payments
                # for i in range(0, num_of_payments):
                #     journal= record.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
                #     move = record.env['account.move'].create({
                #         'partner_id': record.tenant_id.id,
                #         'move_type': 'out_invoice',
                #         'journal_id': journal.id,
                #         'property_rent_id' : record.id,
                #         'invoice_date_due' : record.starting_date + relativedelta(months=i*period),
                #         'invoice_line_ids':[
                #             #Below needs to be checked (calculating the payments when there is deposit)
                #             (0,0,{ 'name': record.tenant_id.name, 'price_unit': (total_rent - record.deposit_amount)/num_of_payments}),
                #         ]
                #     })
        return  True
        
    def action_reset_to_quotation(self):
        if(self.property_id.property_rent_state == "not available"):
            raise ValidationError(_("The Rent order Cannot be Reset to quotation because the property is not available"))
        for record in self:
            if record.tenant_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.tenant_id.name} as a tenant to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_rent_ids')
                for rent in temp:
                    if(rent.state == 'on hold'):
                        rent.state = 'quotation'
                record.state = "quotation"
                record.property_id.property_rent_state = 'available'
                record.message_post(body=_("Rent order with the number <b>%s</b> has been reset to <b>Quotation</b>", record.name))
        return True

    def action_set_reserve(self):
        if(self.property_id.property_rent_state == "not available"):
            raise ValidationError(_("The Property cannot be reserved"))

        for record in self:
            if record.tenant_id == record.property_id.property_owner_id:
                raise UserError(_(f"You cannot assign {record.tenant_id.name} as a tenant to {record.property_id.name} as he is an owner to it."))
            else:
                temp = record.mapped('property_id.property_rent_ids')
                for rent in temp:
                    if(rent.property_id == self.property_id and (rent.state not in ['canceled','end'])):
                        rent.state = 'on hold'
                record.state = 'reserved'
                record.property_id.property_rent_state = 'reserved'
                record.message_post(body=_("Rent order with the number <b>%s</b> has been <b>Reserved</b>", record.name))
        return True

    def action_set_cancel(self):
        for record in self:
            temp = record.mapped('property_id.property_rent_ids')
            for rent in temp:
                if(rent.state == 'on hold'):
                    rent.state = 'quotation'
            if(record.state == 'rent order'):
                record.property_id.is_rented = False
            record.state = 'canceled'
            record.property_id.property_rent_state = 'available'
            record.message_post(body=_("Rent order with the number <b>%s</b> has been <b>Canceled</b>", record.name))
        return True

    @api.depends("starting_date", "property_id.rent_type")
    def _compute_end_date(self):
        for record in self:
            if record.property_id.rent_type == '1': #Annually rent type
                record.end_date = record.starting_date + relativedelta(years=1)
            elif record.property_id.rent_type == '12': #Monthly rent type
                record.end_date = record.starting_date + relativedelta(months=12)

    @api.depends("move_ids.payment_state")
    def _compute_deposit_ammount(self):
        for record in self:
            if len(record.move_ids) > 0:
                for move in record.move_ids:
                    if move.is_deposit:
                        if move.payment_state in (['in_payment', 'paid']) :
                            if not record.state =='rent order':
                                record.action_set_reserve()
                                record.deposit_amount = move.amount_total
                        else:
                            record.deposit_amount = 0.0
            else:
                record.deposit_amount = 0.0

    # @api.onchange('currentTime')
    # def onchange_currentTime(self):
    #     print("I am here")

    # @api.onchange("deposit")
    # def _onchange_for_sale(self):
    #     if(self.deposit == False):
            # self.deposit_amount = 0

    # def _default_renew_period(self):
    #     print("I am here")
    #     return self.env['ir.config_parameter'].sudo().get_param('property_rent.renew_period')
    
    def cron_check_renewal(self):
        rents = self.env['property.rent'].search([])
        renew_period = int(self.env['ir.config_parameter'].sudo().get_param('property_rent.renew_period'))
        for rent in rents:
            # if rent.end_date != False and the remaining days are less than the limit, then check for renewal
            rent.requires_renewal = False
            if rent.end_date and (rent.end_date - fields.Date.today()).days < renew_period and rent.state == 'rent order':
                rent.requires_renewal = True

    def cron_check_auto_renewal(self):
        rents = self.env['property.rent'].search([])
        for rent in rents:
            if rent.end_date and (rent.end_date + relativedelta(days=1) == fields.Date.today()) and rent.asked_for_renewal:
                rent_values = rent._prepare_rent_order()
                rent.state = 'end'
                rent.property_id.is_rented = False
                rent.property_id.property_rent_state = 'reserved'
                rent.asked_for_renewal = False
                self.env['property.rent'].create(rent_values)
            elif rent.end_date and rent.end_date + relativedelta(days=1) == fields.Date.today() :
                rent.state = 'end'
                rent.property_id.is_rented = False
                rent.property_id.property_rent_state = 'available'

                
    def _prepare_rent_order(self):
        return {
            'user_id' : self.renewed_user_id,
            'property_id' : self.property_id.id,
            'tenant_id' : self.tenant_id.id,
            'starting_date' : self.end_date + relativedelta(days=1),
            # 'end_date'
            'requires_renewal' : False,
            'asked_for_renewal' : False,
            'deposit' : False,
            # 'deposit_amount'
            # 'is_deposit_created'
            # 'move_ids'
            # 'move_ids_payment_state'
            'expected_rent_price_related' : self.expected_rent_price_related,
            'offered_price' : self.offered_price,
            'property_type_id_related' : self.property_type_id_related.id,
            'property_rent_type_related' : self.property_rent_type_related,
            'street_related' : self.street_related,
            'street2_related' : self.street2_related,
            'city_related' : self.city_related,
            'district_related' : self.district_related,
            'zip_related' : self.zip_related,
            'country_id_related' : self.country_id_related,
            'property_state_related' : self.property_state_related,
            # 'payment_cost_ids' 
            'payment_type' : self.payment_type,
            'state' : 'reserved'
        }

    def action_set_renew(self):
        self.asked_for_renewal=True
        self.renewed_user_id = self.env.user.id
        self.message_post(body=_("Rent order with the number <b>%s</b> will be <b>Renewed</b> on <b>%s/%s/%s</b>", self.name, (self.end_date + relativedelta(days=1)).month ,(self.end_date + relativedelta(days=1)).day ,(self.end_date + relativedelta(days=1)).year))
        return True

    def action_cancel_renew(self):
        self.asked_for_renewal=False
        self.renewed_user_id = self.user_id
        self.message_post(body=_("Rent order with the number <b>%s</b> will <b>Not</b> be <b>Renewed</b>", self.name))
        return True
    
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
            "res_model": "property.rent",
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
    def _check_renting_price(self):
        for record in self:
            if ((record.offered_price < record.expected_rent_price_related)):
                raise ValidationError(_("The offered price cannot be less than the expected price "))

    @api.constrains('tenant_id','property_id')
    def _check_tenant_eligibility(self):
        for record in self:
            if record.tenant_id == record.property_id.property_owner_id and record.state not in ['canceled', 'end']:
                raise UserError(_(f"You cannot assign {record.tenant_id.name} as a tenant to {record.property_id.name} as he is an owner to it."))

class RentPaymentsLine(models.Model):
    _name = "property.rentpaymentline"
    _description = "property paymentline"
    
    name = fields.Char(string="Item")
    Payment_cost=fields.Float(string="Amount")
    tax = fields.Float(string="Taxes")
    total_amount = fields.Float(string="Total Amount")
    Due_Date=fields.Date(string="Due Date")
    state=fields.Selection(string="Status",default="not paid", selection=[('paid', 'Paid'),('not paid', 'Not Paid')])
    property_rent_state_related=fields.Selection(related="property_rent_id.state")
    property_rent_id=fields.Many2one("property.rent", string="Property Rent Id", ondelete='cascade')
    is_rent_payment=fields.Boolean(string="Is Rent Payment", default=False)

    def action_pay(self):
        for record in self:
            record.state="paid"
            record.property_rent_id.message_post(body=_("<b>%s</b> status changed to <b>%s</b>", record.name, record.state))
            
    def action_cancel_pay(self):
        for record in self:
            record.state="not paid"
            record.property_rent_id.message_post(body=_("<b>%s</b> status changed to <b>%s</b>", record.name, record.state))