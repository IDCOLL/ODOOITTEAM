# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
from odoo import fields, models


class account_report_partner_ledger(models.TransientModel):
	_name = "send.overdue.statement"
	_description = "Send Overdue Statement"


	confirm_text = fields.Char(default="Press Send Overdue Payment to send email notification to customer",readonly=True)

	def send_overdue_statement_customer(self):

		res = self.env['res.partner'].browse(self._context.get('active_ids',[]))
		for user in res :
			user.do_partner_mail()

		return
	
class customer_statement_wizard(models.TransientModel):
	_name = "customer.statement.wizard"
	_description = "Send Customer Statement"

	confirm_text = fields.Char(default="Press Send Customer Statement to send email notification to customer",readonly=True)
	overdue_duration = fields.Selection([
		('30','30 Days'),
		('60','60 Days'),
		('90','90 Days'),
		('3m','Quarter'),
		('custom','Custom Date Range'),
		],string="Duration", default="30", required=True)
	from_date = fields.Date('From Date')
	to_date = fields.Date('To Date')

	def send_overdue_statement_customer(self):
		res = self.env['res.partner'].browse(self._context.get('active_ids',[]))
		context = {}
		for user in res:
			context.update({
				'overdue_duration' : self.overdue_duration,
				})
			if self.overdue_duration == 'custom': 
				context.update({
					'from_date' : self.from_date,
					'to_date' : self.to_date
				})
			user.with_context(context).do_customer_statement_mail()

		return