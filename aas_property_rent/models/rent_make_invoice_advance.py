# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RentAdvancePaymentInv(models.TransientModel):
    _name = "rent.advance.payment.inv"
    _description = "Rent Advance Payment Invoice"

    advance_payment_method = fields.Selection([
        ('fixed', 'Down payment (fixed amount)'),
        ('percentage', 'Down payment (percentage)'),
        ], string='Create Invoice', default='fixed', required=True,
        )
    property_id = fields.Many2one('property')
    amount = fields.Float('Down Payment Amount', digits='Account', help="The percentage of amount to be invoiced in advance, taxes excluded.")
    fixed_amount = fields.Float('Down Payment Amount (Fixed)', help="The fixed amount to be invoiced in advance, taxes excluded.")
    deposit_account_id = fields.Many2one("account.account", string="Deposit Account", domain=[('deprecated', '=', False),('user_type_id.name', '=', 'Current Liabilities')],
        help="Account used for deposits")
    credit_account_id = fields.Many2one("account.account", string="Credit Account", domain=[('deprecated', '=', False)])

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            amount = self.default_get(['amount']).get('amount')
            return {'value': {'amount': amount}}
        return {}

    def _prepare_invoice_values(self, order, name, amount, journal):
        return {
	            'journal_id': journal.id,
	            'partner_id': order.tenant_id.id,
	            'date': fields.Date.today(),
	            'ref': order.name,
	            'invoice_origin': order.name,
	            'move_type': 'out_invoice',
                'property_rent_id' : order.id,
                'is_deposit' : True,
	            'invoice_line_ids': [(0, 0, {
                    'name': order.tenant_id.name, 
                    'account_id': self.deposit_account_id.id,
                    'price_unit': amount
                })],
                # 'line_ids': [(0, 0, {
	            #     'name': name,
	            #     'partner_id': order.tenant_id.id,
	            #     'account_id': self.credit_account_id.id,
	            #     'debit': 0.0,
	            #     'credit': amount,
	            #     'tax_line_id': False,
	            # }), (0, 0, {
	            #     'name': name,
	            #     'account_id': self.deposit_account_id.id,
	            #     'debit': amount,
	            #     'credit': 0.0,
	            #     'tax_line_id': False,
	            # })]
	        }

    def _get_advance_details(self, order):
        context = {'lang': order.tenant_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.offered_price * self.amount / 100
            name = _("Deposit of %s%%") % (self.amount)
        else:
            amount = self.fixed_amount
            name = _('Deposit')
        del context

        return amount, name

    def _create_invoice(self, order, amount):
        if (self.advance_payment_method == 'percentage' and self.amount <= 0.00) or (self.advance_payment_method == 'fixed' and self.fixed_amount <= 0.00):
            raise UserError(_('The value of the deposit amount must be positive.'))

        amount, name = self._get_advance_details(order)
        journal= self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        invoice_vals = self._prepare_invoice_values(order, name, amount, journal)
        entry = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        entry.message_post_with_view('mail.message_origin_link',
                    values={'self': entry, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        order.is_deposit_created = True
        order.deposit = True
        entry.action_post()
        return entry

    def create_deposits(self):
        rent_orders = self.env['property.rent'].browse(self._context.get('active_ids', []))
        for order in rent_orders:
            amount,name = self._get_advance_details(order)
            self._create_invoice(order, amount)   
        # if self._context.get('open_invoices', False):
        #     return rent_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}

