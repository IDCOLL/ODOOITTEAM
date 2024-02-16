# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
from odoo import api, fields, models, _
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta
import base64

	
class Res_Partner(models.Model):
	_inherit = 'res.partner'
	
	def _get_amounts_and_date_amount(self):
		user_id = self._uid
		filter_amount_due = 0.0
		filter_amount_overdue = 0.0
		filter_supplier_amount_due = 0.0
		filter_supplier_amount_overdue = 0.0
		
		company = self.env['res.users'].browse(user_id).company_id
		current_date = fields.Date.today()

		for partner in self:
			partner.do_process_monthly_statement_filter()
			partner.do_process_weekly_statement_filter()

			filter_date = current_date
			supp_filter_date = current_date 

			if partner.statement_to_date :
				filter_date = partner.statement_to_date

			if partner.vendor_statement_to_date :
				supp_filter_date = partner.vendor_statement_to_date

			amount_due = amount_overdue = 0.0
			supplier_amount_due = supplier_amount_overdue = 0.0

			for aml in partner.balance_invoice_ids:
				if aml.company_id == partner.env.company:
					date_maturity = aml.invoice_date_due or aml.date
					amount_due += aml.result
					if date_maturity:
						if date_maturity <= current_date :
							amount_overdue += aml.result
			
			partner.payment_amount_due_amt = amount_due
			partner.payment_amount_overdue_amt = amount_overdue
			
			for aml in partner.supplier_invoice_ids:
				date_maturity = aml.invoice_date_due or aml.date
				supplier_amount_due += aml.result
				if date_maturity:
					if date_maturity <= current_date:
						supplier_amount_overdue += aml.result
			partner.payment_amount_due_amt_supplier = supplier_amount_due
			partner.payment_amount_overdue_amt_supplier = supplier_amount_overdue
			
			for aml in partner.customer_statement_line_ids:
				if aml.invoice_date_due != False:
					date_maturity = aml.invoice_date_due
					filter_amount_due += aml.result
					if date_maturity:
						if date_maturity <= filter_date:
							filter_amount_overdue += aml.result
			partner.filter_payment_amount_due_amt = filter_amount_due
			partner.filter_payment_amount_overdue_amt = filter_amount_overdue
			
			for aml in partner.vendor_statement_line_ids:
				date_maturity = aml.invoice_date_due
				filter_supplier_amount_due += aml.result
				if date_maturity:
					if date_maturity <= supp_filter_date:
						filter_supplier_amount_overdue += aml.result
			partner.filter_payment_amount_due_amt_supplier = filter_supplier_amount_due
			partner.filter_payment_amount_overdue_amt_supplier = filter_supplier_amount_overdue
			
			
			monthly_amount_due_amt = monthly_amount_overdue_amt = 0.0
			for aml in partner.monthly_statement_line_ids:
				date_maturity = aml.invoice_date_due
				monthly_amount_due_amt += aml.result
				if date_maturity:
					if date_maturity <= current_date:
						monthly_amount_overdue_amt += aml.result
			partner.monthly_payment_amount_due_amt = monthly_amount_due_amt
			partner.monthly_payment_amount_overdue_amt = monthly_amount_overdue_amt


			weekly_amount_due_amt = weekly_amount_overdue_amt = 0.0
			for aml in partner.weekly_statement_line_ids:
				date_maturity = aml.invoice_date_due
				weekly_amount_due_amt += aml.result
				if date_maturity:
					if date_maturity <= current_date:
						weekly_amount_overdue_amt += aml.result
			partner.weekly_payment_amount_due_amt = weekly_amount_due_amt
			partner.weekly_payment_amount_overdue_amt = weekly_amount_overdue_amt
					

	@api.depends('customer_statement_line_ids')
	def compute_days_filter(self):
		today = fields.date.today()
		for partner in self:
			partner.first_thirty_day_filter = 0
			partner.thirty_sixty_days_filter = 0
			partner.sixty_ninty_days_filter = 0
			partner.ninty_plus_days_filter = 0
			from_date = partner.statement_from_date 
			to_date = partner.statement_to_date
			move_line = self.env['account.move.line']
			domain = [('account_id.account_type' ,'=','asset_receivable'),('partner_id','=',partner.id),('move_id.state','in',['posted'])]
			if from_date:
				domain.append(('date_maturity', '>=', from_date))

			if to_date:
				domain.append(('date_maturity', '<=', to_date))

			for ml in move_line.search(domain):
				if to_date and ml.date_maturity:
					diff = to_date - ml.date_maturity
				elif ml.date_maturity:
					diff = fields.date.today() - ml.date_maturity
				else:
					diff = fields.date.today() - fields.date.today()

				if diff.days >= 0 and diff.days <= 30:
					partner.first_thirty_day_filter = partner.first_thirty_day_filter + ml.amount_residual

				elif diff.days > 30 and diff.days<=60:
					partner.thirty_sixty_days_filter = partner.thirty_sixty_days_filter + ml.amount_residual

				elif diff.days > 60 and diff.days<=90:
					partner.sixty_ninty_days_filter = partner.sixty_ninty_days_filter + ml.amount_residual
				else:
					if diff.days > 90  :
						partner.ninty_plus_days_filter = partner.ninty_plus_days_filter + ml.amount_residual
		return

	def compute_days(self):
		today = fields.date.today()
		for partner in self:
			partner.first_thirty_day = 0
			partner.thirty_sixty_days = 0
			partner.sixty_ninty_days = 0
			partner.ninty_plus_days = 0

			moves = self.env['account.move'].search([('partner_id','=',partner.id), ('state', 'in', ['posted'])]) 
			for mv in moves:
				for ml in mv.line_ids :
					if ml.account_id.account_type =='asset_receivable':
						if ml.date_maturity:
							diff = today - ml.date_maturity 
						else:
							diff = today - today
						if diff.days >= 0 and diff.days <= 30:
							partner.first_thirty_day = partner.first_thirty_day + ml.amount_residual

						elif diff.days > 30 and diff.days<=60:
							partner.thirty_sixty_days = partner.thirty_sixty_days + ml.amount_residual

						elif diff.days > 60 and diff.days<=90:
							partner.sixty_ninty_days = partner.sixty_ninty_days + ml.amount_residual
						else:
							if diff.days > 90  :
								partner.ninty_plus_days = partner.ninty_plus_days + ml.amount_residual
		return

	def compute_days_custom(self):
		today = fields.date.today()
		for partner in self:
			partner.first_thirty_days_custom = 0
			partner.thirty_sixty_days_custom = 0
			partner.sixty_ninty_days_custom = 0
			partner.ninty_plus_days_custom = 0

			moves = self.env['account.move'].search([('partner_id','=',partner.id), ('state', 'in', ['posted'])]) 
			domain = [('account_id.account_type' ,'=','asset_receivable'),('partner_id','=',partner.id)]
		
			for mv in moves:
				for ml in mv.line_ids:
					if ml.account_id.account_type =='asset_receivable':
						if self.custom_from_date and self.custom_to_date and ml.date_maturity:
							if ml.date_maturity >= self.custom_from_date and ml.date_maturity <= self.custom_to_date:
								if ml.account_id.account_type =='asset_receivable':
									if ml.date_maturity:
										diff = today - ml.date_maturity 
									else:
										diff = today - today
									if diff.days >= 0 and diff.days <= 30:
										partner.first_thirty_days_custom = partner.first_thirty_days_custom + ml.amount_residual
									elif diff.days > 30 and diff.days<=60:
										partner.thirty_sixty_days_custom = partner.thirty_sixty_days_custom + ml.amount_residual

									elif diff.days > 60 and diff.days<=90:
										partner.sixty_ninty_days_custom = partner.sixty_ninty_days_custom + ml.amount_residual
									else:
										if diff.days > 90  :
											partner.ninty_plus_days_custom = partner.ninty_plus_days_custom + ml.amount_residual
		return


	@api.depends('ninty_plus_days','sixty_ninty_days','thirty_sixty_days','first_thirty_day')
	def compute_total(self):
		for partner in self:
			partner.total = 0.0
			partner.total = partner.ninty_plus_days + partner.sixty_ninty_days + partner.thirty_sixty_days + partner.first_thirty_day
		return		
	@api.depends('ninty_plus_days_custom','sixty_ninty_days_custom','thirty_sixty_days_custom','first_thirty_days_custom')
	def compute_total_custom(self):
		for partner in self:
			partner.custom_total = 0.0
			partner.custom_total = partner.ninty_plus_days_custom + partner.sixty_ninty_days_custom + partner.thirty_sixty_days_custom + partner.first_thirty_days_custom
		return

	@api.depends('ninty_plus_days_filter','sixty_ninty_days_filter','thirty_sixty_days_filter','first_thirty_day_filter')
	def compute_total_filter(self):
		for partner in self:
			partner.total_filter = 0.0
			partner.total_filter = partner.ninty_plus_days_filter + partner.sixty_ninty_days_filter + partner.thirty_sixty_days_filter + partner.first_thirty_day_filter
		return
		

	supplier_invoice_ids = fields.One2many('account.move', 'partner_id', 'Supplier move lines', domain=[('move_type', 'in', ['in_invoice','in_refund','entry']),('state', 'in', ['posted'])]) 
	balance_invoice_ids = fields.One2many('account.move', 'partner_id', 'Customer move lines', domain=[('move_type', 'in', ['out_invoice','out_refund','entry']),('state', 'in', ['posted'])]) 
	
	monthly_statement_line_ids = fields.One2many('monthly.statement.line', 'partner_id', 'Monthly Statement Lines')
	weekly_statement_line_ids = fields.One2many('weekly.statement.line', 'partner_id', 'Weekly Statement Lines')

	customer_statement_line_ids = fields.One2many('bi.statement.line', 'partner_id', 'Customer Statement Lines')
	vendor_statement_line_ids = fields.One2many('bi.vendor.statement.line', 'partner_id', 'Supplier Statement Lines')
	custom_statement_line_ids = fields.One2many('custom.statement.line', 'partner_id', 'Custom Statement Lines')

	payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Balance Due")
	payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Total Overdue Amount",store=True)
	payment_amount_due_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Supplier Balance Due")
	payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Total Supplier Overdue Amount")
	filter_payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Filter Balance Due")
	filter_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Filter Total Overdue Amount")
	monthly_payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string=" Filter Monthly Balance Due")
	monthly_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Filter Total Monthly Overdue Amount")
	
	weekly_payment_amount_due_amt = fields.Float(compute='_get_amounts_and_date_amount', string="Filter Weekly Balance Due")
	weekly_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Filter Weekly Total Overdue Amount")
	

	filter_payment_amount_due_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount', string="Filter Supplier Balance Due")
	filter_payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
												  string="Filter Total Supplier Overdue Amount")
	first_thirty_days_custom = fields.Float(string="0-30 custom",compute="compute_days_custom")
	thirty_sixty_days_custom= fields.Float(string="30-60 custom",compute="compute_days_custom")
	sixty_ninty_days_custom = fields.Float(string="60-90 custom",compute="compute_days_custom")
	ninty_plus_days_custom = fields.Float(string="90+ custom",compute="compute_days_custom")
	custom_total = fields.Float(string="Total custom",compute="compute_total_custom")
	
	
	first_thirty_day = fields.Float(string="0-30",compute="compute_days")
	thirty_sixty_days = fields.Float(string="30-60",compute="compute_days")
	sixty_ninty_days = fields.Float(string="60-90",compute="compute_days")
	ninty_plus_days = fields.Float(string="90+",compute="compute_days")
	total = fields.Float(string="Total",compute="compute_total")
	first_thirty_day_filter = fields.Float(string="0-30 filter",compute="compute_days_filter")
	thirty_sixty_days_filter = fields.Float(string="30-60 filter",compute="compute_days_filter")
	sixty_ninty_days_filter = fields.Float(string="60-90 filter",compute="compute_days_filter")
	ninty_plus_days_filter = fields.Float(string="90+ filter",compute="compute_days_filter")
	total_filter = fields.Float(string="Filter Total",compute="compute_total_filter")

	statement_from_date = fields.Date('From Date')
	statement_to_date = fields.Date('To Date')
	custom_from_date = fields.Date('Custom From Date')
	custom_to_date = fields.Date('Custom To Date')

	today_date = fields.Date(default=fields.Date.today())
	vendor_statement_from_date = fields.Date('Supplier From Date')
	vendor_statement_to_date = fields.Date('Supplier To Date')

	initial_bal = fields.Float(string='Initial Balance',readonly=True)
	initial_supp_bal = fields.Float(string='Initial Supplier Balance',readonly=True)
	opt_statement = fields.Boolean('Opt Statement', default=False)


	def do_process_statement_filter(self):
		account_invoice_obj = self.env['account.move'] 
		statement_line_obj = self.env['bi.statement.line']
		account_payment_obj = self.env['account.payment']
		inv_list = []
		for record in self:
			from_date = record.statement_from_date 
			to_date = record.statement_to_date

			if from_date:
				final_initial_bal = 0.0 

				in_bal = account_invoice_obj.search([('partner_id','=',record.id), \
					('move_type', 'in', ['out_invoice','out_refund']), ('state', 'in', ['posted']), \
					('invoice_date', '<', from_date),])
				
				for inv in in_bal :
					final_initial_bal += inv.amount_residual

				entry = account_invoice_obj.search([('partner_id','=',record.id), \
					('move_type', 'in', ['entry']), ('state', 'in', ['posted']), \
					('date', '<', from_date),])
				
				for move in entry :
					final_initial_bal += move.amount_residual

				in_pay_bal = account_payment_obj.search([('partner_id','=',record.id), \
					('state', 'in', ['posted', 'reconciled']),('date', '<', from_date), \
					('partner_type', '=', 'customer')])

				for pay in in_pay_bal :
					final_initial_bal -= pay.amount

				if final_initial_bal:
					record.write({'initial_bal':final_initial_bal})


			domain_payment = [('partner_type', '=', 'customer'), ('state', 'in', ['posted', 'reconciled']), ('partner_id', '=', record.id)]
			domain = [('move_type', 'in', ['out_invoice','out_refund']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			domain_entry = [('journal_id.name','!=','Inventory Valuation'),('move_type', 'in', ['entry']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			if from_date:
				domain.append(('invoice_date', '>=', from_date))
				domain_payment.append(('date', '>=', from_date))
				domain_entry.append(('date', '>=', from_date))

			if to_date:
				domain.append(('invoice_date', '<=', to_date))
				domain_payment.append(('date', '<=', to_date))
				domain_entry.append(('date', '<=', to_date))
				 
				 
			lines_to_be_delete = statement_line_obj.search([('partner_id', '=', record.id)])
			lines_to_be_delete.unlink()
			
			
			move_entry = account_invoice_obj.search(domain_entry)
			invoices = account_invoice_obj.search(domain)
			payments = account_payment_obj.search(domain_payment)
			if invoices:
				for invoice in invoices.sorted(key=lambda r: r.name):
					vals = {
							'partner_id':invoice.partner_id.id or False,
							'state':invoice.state or False,
							'invoice_date':invoice.invoice_date,
							'invoice_date_due':invoice.invoice_date_due,
							'result':invoice.result or 0.0,
							'name':invoice.name or '',
							'amount_total':invoice.amount_total or 0.0,
							'credit_amount':invoice.credit_amount or 0.0,
							'invoice_id' : invoice.id,
					}
					test = statement_line_obj.create(vals)
			if move_entry :
				for invoice in move_entry.sorted(key=lambda r: r.name):
					vals = {
							'partner_id':invoice.partner_id.id or False,
							'state':invoice.state or False,
							'invoice_date':invoice.invoice_date,
							'result':invoice.result or 0.0,
							'name':invoice.name or '',
							'amount_total':invoice.amount_total or 0.0,
							'credit_amount':invoice.credit_amount or 0.0,
							'invoice_id' : invoice.id,
					}
					test = statement_line_obj.create(vals)
						
	def do_process_vendor_statement_filter(self):
		account_invoice_obj = self.env['account.move'] 
		vendor_statement_line_obj = self.env['bi.vendor.statement.line']
		account_payment_obj = self.env['account.payment']
		for record in self:
			from_date = record.vendor_statement_from_date 
			to_date = record.vendor_statement_to_date

			if from_date:
					
				final_initial_bal = 0.0 

				in_bal = account_invoice_obj.search([('partner_id','=',record.id), \
					('move_type', 'in', ['in_invoice','in_refund']),('state', 'in', ['posted']),('invoice_date', '<', from_date)])
				for inv in in_bal :
					final_initial_bal += inv.amount_residual
				entry = account_invoice_obj.search([('partner_id','=',record.id), \
					('move_type', 'in', ['entry']), ('state', 'in', ['posted']), \
					('date', '<', from_date),])
				
				for move in entry :
					final_initial_bal += move.amount_residual

				in_pay_bal = account_payment_obj.search([('partner_id','=',record.id), \
					('state', 'in', ['posted', 'reconciled']),('date', '<', from_date), \
					('partner_type', '=', 'supplier')])

				for pay in in_pay_bal :
					final_initial_bal -= pay.amount

				if final_initial_bal:
					record.write({'initial_supp_bal':-final_initial_bal})
	
			domain_payment = [('partner_type', '=', 'supplier'), ('state', 'in', ['posted', 'reconciled']), ('partner_id', '=', record.id)]
			domain = [('move_type', 'in', ['in_invoice','in_refund']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			domain_entry = [('journal_id.name','!=','Inventory Valuation'),('move_type', 'in', ['entry']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			
			if from_date:
				domain.append(('invoice_date', '>=', from_date))
				domain_payment.append(('date', '>=', from_date))
				domain_entry.append(('date', '>=', from_date))

			if to_date:
				domain.append(('invoice_date', '<=', to_date))
				domain_payment.append(('date', '<=', to_date))
				domain_entry.append(('date', '<=', to_date))
				 
				 
			lines_to_be_delete = vendor_statement_line_obj.search([('partner_id', '=', record.id)])
			lines_to_be_delete.unlink()
			
			move_entry = account_invoice_obj.search(domain_entry)
			invoices = account_invoice_obj.search(domain)
			payments = account_payment_obj.search(domain_payment)
			if invoices:
				for invoice in invoices.sorted(key=lambda r:r.name):
					vals = {
						'partner_id':invoice.partner_id.id or False,
						'state':invoice.state or False,
						'invoice_date':invoice.invoice_date,
						'invoice_date_due':invoice.invoice_date_due,
						'result':invoice.result or 0.0,
						'name':invoice.name or '',
						'amount_total':invoice.amount_total or 0.0,
						'credit_amount':invoice.credit_amount or 0.0,
						'invoice_id' : invoice.id,
					}
					vendor_statement_line_obj.create(vals)

			if move_entry :
				for invoice in move_entry.sorted(key=lambda r: r.name):
					vals = {
							'partner_id':invoice.partner_id.id or False,
							'state':invoice.state or False,
							'invoice_date':invoice.invoice_date,
							'result':invoice.result or 0.0,
							'name':invoice.name or '',
							'amount_total':invoice.amount_total or 0.0,
							'credit_amount':invoice.credit_amount or 0.0,
							'invoice_id' : invoice.id,
					}
					vendor_statement_line_obj.create(vals)				

	def do_send_statement_filter(self):
		unknown_mails = 0
		for partner in self:
			partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
			if not partners_to_email and partner.email:
				partners_to_email = [partner]
			if partners_to_email:
				for partner_to_email in partners_to_email:
					mail_template_id = self.env.ref('bi_customer_overdue_statement.email_template_customer_statement_filter')
					mail_template_id.send_mail(partner_to_email.id)
				if partner not in partner_to_email:
					msg = _('Customer Filter Statement email sent to %s' % ', '.join(['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
					partner.message_post(body=msg)
		return unknown_mails
				
	
	def _cron_send_overdue_statement(self):
		partners = self.env['res.partner'].search([('opt_statement','=',False)])
		company = self.env.user.company_id
		if company.send_overdue_statement :
			partners.do_partner_mail()
		return True
	
	def _cron_send_customer_monthly_statement(self):
		partners = self.env['res.partner'].search([])
		company = self.env.user.company_id
		if company.auto_monthly_statement  and company.send_statement:
			partners.customer_monthly_send_mail()
		
		return True

	def _cron_send_customer_weekly_statement(self):
		partners = self.env['res.partner'].search([])
		company = self.env.user.company_id
		today = date.today()

		if company.auto_weekly_statement and company.weekly_days and company.send_statement:
			if int(company.weekly_days) == int(today.weekday()) :
				partners.customer_weekly_send_mail()

		return True

	def do_partner_mail(self):
		unknown_mails = 0
		for partner in self:
			partner.payment_amount_overdue_amt = None
			partner._get_amounts_and_date_amount()
			if partner.payment_amount_overdue_amt == 0.00:
				pass
			else:

				if partner.email:
					template = self.env.user.company_id.overdue_statement_template_id
					if not template :
						template = self.env.ref('bi_customer_overdue_statement.email_template_customer_over_due_statement')

					report = self.env.ref('bi_customer_overdue_statement.report_customer_overdue_print')

					attachments = []
					report_name = template._render_field('report_name', [partner.id])[partner.id]
					
					report_service = report.report_name

					if report.report_type in ['qweb-html', 'qweb-pdf']:
						result, report_format = self.env['ir.actions.report']._render_qweb_pdf(report, [partner.id])
					else:
						res = self.env['ir.actions.report']._render(report, [partner.id])
						if not res:
							raise UserError(_('Unsupported report type %s found.', report.report_type))
						result, report_format = res

					# TODO in trunk, change return format to binary to match message_post expected format
					result = base64.b64encode(result)
					if not report_name:
						report_name = 'report.' + report_service
					ext = "." + report_format
					if not report_name.endswith(ext):
						report_name += ext

					author = ''

					attachments.append((report_name, result))

					template.sudo().with_context(monthly_attachments=attachments).send_mail(partner.id)

					msg = _('Customer Overdue Statement email sent to %s-%s' % (partner.name, partner.email) )

					partner.message_post(body=msg)
				else:
					unknown_mails += 1


		return unknown_mails


	def do_process_monthly_statement_filter(self):
		account_invoice_obj = self.env['account.move'] 
		statement_line_obj = self.env['monthly.statement.line']
		for record in self:
 
			today = date.today()
			d = today - relativedelta(months=1)

			start_date = date(d.year, d.month,1)
			end_date = date(today.year, today.month,1) - relativedelta(days=1)
			
			from_date = str(start_date)
			to_date = str(end_date)
			
			domain = [('move_type', 'in', ['out_invoice','out_refund']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			if from_date:
				domain.append(('invoice_date', '>=', from_date))
			if to_date:
				domain.append(('invoice_date', '<=', to_date))
				 
				 
			
			invoices = account_invoice_obj.search(domain)
			for invoice in invoices.sorted(key=lambda r: r.name):
				vals = {
						'partner_id':invoice.partner_id.id or False,
						'state':invoice.state or False,
						'invoice_date':invoice.invoice_date,
						'invoice_date_due':invoice.invoice_date_due,
						'result':invoice.result or 0.0,
						'name':invoice.name or '',
						'amount_total':invoice.amount_total or 0.0,
						'credit_amount':invoice.credit_amount or 0.0,
						'invoice_id' : invoice.id,
					}
				exist_line = statement_line_obj.search([('invoice_id', '=', invoice.id)])
				exist_line.write(vals)
				if not exist_line:
					ob = statement_line_obj.create(vals) 

	def do_process_weekly_statement_filter(self):
		account_invoice_obj = self.env['account.move'] 
		statement_line_obj = self.env['weekly.statement.line']
		for record in self:
			today = date.today()

			start_date = today + timedelta(-today.weekday(), weeks=-1)
			end_date = today + timedelta(-today.weekday() - 1)

			
			from_date = str(start_date)
			to_date = str(end_date)
			
			
			domain = [('move_type', 'in', ['out_invoice','out_refund']), ('state', 'in', ['posted']), ('partner_id', '=', record.id)]
			if from_date:
				domain.append(('invoice_date', '>=', from_date))
			if to_date:
				domain.append(('invoice_date', '<=', to_date))
				 
				 			
			invoices = account_invoice_obj.search(domain)

			for invoice in invoices.sorted(key=lambda r: r.name):
				vals = {
						'partner_id':invoice.partner_id.id or False,
						'state':invoice.state or False,
						'invoice_date':invoice.invoice_date,
						'invoice_date_due':invoice.invoice_date_due,
						'result':invoice.result or 0.0,
						'name':invoice.name or '',
						'amount_total':invoice.amount_total or 0.0,
						'credit_amount':invoice.credit_amount or 0.0,
						'invoice_id' : invoice.id,
					}
				exist_line = statement_line_obj.search([('invoice_id', '=', invoice.id)])
				exist_line.write(vals)
				if not exist_line:
					ob = statement_line_obj.create(vals) 
		
	def customer_monthly_send_mail(self):
		unknown_mails = 0
		for partner in self:
			partner.monthly_payment_amount_due_amt = None
			partner._get_amounts_and_date_amount()	
			if partner.opt_statement == False:
				if partner.monthly_payment_amount_due_amt == 0.00:
					pass
				else:
					if partner.email:
						template = self.env.user.company_id.monthly_template_id

						report = self.env.ref('bi_customer_overdue_statement.report_customer_monthly_print')

						attachments = []
						report_name = template._render_field('report_name', [partner.id])[partner.id]
						
						report_service = report.report_name

						if report.report_type in ['qweb-html', 'qweb-pdf']:
							result, report_format = self.env['ir.actions.report']._render_qweb_pdf(report, [partner.id])
						else:
							res = self.env['ir.actions.report']._render(report, [partner.id])
							if not res:
								raise UserError(_('Unsupported report type %s found.', report.report_type))
							result, report_format = res

						# TODO in trunk, change return format to binary to match message_post expected format
						result = base64.b64encode(result)
						if not report_name:
							report_name = 'report.' + report_service
						ext = "." + report_format
						if not report_name.endswith(ext):
							report_name += ext

						author = ''

						attachments.append((report_name, result))

						template.sudo().with_context(monthly_attachments=attachments).send_mail(partner.id)

						msg = _('Customer Monthly Statement email sent to %s-%s' % (partner.name, partner.email) )

						partner.message_post(body=msg)
					else:
						unknown_mails += 1
		return unknown_mails

	def customer_weekly_send_mail(self):
		unknown_mails = 0
		for partner in self:
			partner.weekly_payment_amount_due_amt = None
			partner._get_amounts_and_date_amount()	
			if partner.opt_statement == False:
				if partner.weekly_payment_amount_due_amt == 0.00:
					pass
				else:
					if partner.email:
						template = self.env.user.company_id.weekly_template_id

						report = self.env.ref('bi_customer_overdue_statement.report_customer_weekly_print')

						attachments = []
						report_name = template._render_field('report_name', [partner.id])[partner.id]
						report_service = report.report_name

						if report.report_type in ['qweb-html', 'qweb-pdf']:
							result, report_format = self.env['ir.actions.report']._render_qweb_pdf(report, [partner.id])
						else:
							res = self.env['ir.actions.report']._render(report, [partner.id])
							if not res:
								raise UserError(_('Unsupported report type %s found.', report.report_type))
							result, report_format = res

						# TODO in trunk, change return format to binary to match message_post expected format
						result = base64.b64encode(result)
						if not report_name:
							report_name = 'report.' + report_service
						ext = "." + report_format
						if not report_name.endswith(ext):
							report_name += ext

						author = ''

						attachments.append((report_name, result))

						template.with_context(monthly_attachments=attachments).send_mail(partner.id)

						msg = _('Customer Monthly Statement email sent to %s-%s' % (partner.name, partner.email) )

						partner.message_post(body=msg)
					else:
						unknown_mails += 1
		return unknown_mails
	
	def customer_send_mail(self):
		unknown_mails = 0
		for partner in self:
			partners_to_email = [child for child in partner.child_ids if child.type == 'invoice' and child.email]
			if not partners_to_email and partner.email:
				partners_to_email = [partner]

			if partners_to_email:
				for pe in partners_to_email:
					mail_template_id = self.env.ref('bi_customer_overdue_statement.email_template_customer_statement')
					mail_template_id.send_mail(pe.id)

				if partner not in partners_to_email:
					msg = _('Customer Statement email sent to %s' % ', '.join(['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
					partner.message_post(body=msg)
		return unknown_mails
	
	
	def do_button_print(self):
		return self.env.ref('bi_customer_overdue_statement.report_customer_overdue_print').report_action(self)
	
	def do_button_print_statement(self):
		return self.env.ref('bi_customer_overdue_statement.report_customert_print').report_action(self)
	
	def do_button_print_vendor_statement(self):
		return self.env.ref('bi_customer_overdue_statement.report_supplier_print').report_action(self)
		   
				
	def do_print_statement_filter(self):
		return self.env.ref('bi_customer_overdue_statement.report_customer_statement_filter_print').report_action(self)
	
	
	def do_print_vendor_statement_filter(self):
		return self.env.ref('bi_customer_overdue_statement.report_supplier_filter_print').report_action(self)
	
	def do_customer_statement_mail(self):
		account_invoice_obj = self.env['account.move'] 
		statement_line_obj = self.env['custom.statement.line']
		amount_due = amount_overdue = 0.0

		for partner in self:
			if partner.email :
				
				mail_template_id = self.env.ref('bi_customer_overdue_statement.email_template_customer_statement_custom_')

				if self._context.get('overdue_duration'):
					to_date = fields.date.today()
					from_date = to_date - relativedelta(days=30)
					if self._context.get('overdue_duration') == 'custom':
						from_date = self._context.get('from_date')
						to_date = self._context.get('to_date')
					else:
						_duration = self._context.get('overdue_duration')
						to_date = fields.date.today()
						if _duration == '3m':
							from_date = to_date - relativedelta(months=3)
						else:
							from_date = to_date - relativedelta(days=int(_duration))

					domain = [('move_type', 'in', ['out_invoice','out_refund']), ('state', '=','posted'), ('partner_id', '=', partner.id)]
					if from_date:
						domain.append(('invoice_date', '>=', from_date))
					if to_date:
						domain.append(('invoice_date', '<=', to_date))

					partner.sudo().write({
						'custom_from_date' : from_date,
						'custom_to_date' : to_date
					})
						 
					lines_to_be_delete = statement_line_obj.search([('partner_id', '=', partner.id)])
					lines_to_be_delete.unlink()
					
					invoices = account_invoice_obj.search(domain)
					for invoice in invoices.sorted(key=lambda r: r.name):
						vals = {
								'partner_id':invoice.partner_id.id or False,
								'state':invoice.state or False,
								'date_invoice':invoice.invoice_date,
								'date_due':invoice.invoice_date_due,
								'number':invoice.name or '',
								'result':invoice.result or 0.0,
								'name':invoice.name or '',
								'amount_total':invoice.amount_total or 0.0,
								'credit_amount':invoice.credit_amount or 0.0,
								'invoice_id' : invoice.id,
							}
						statement_line_obj.create(vals) 
					if invoices:
						mail_template_id.send_mail(partner.id)
						msg = _('Statement sent to %s - %s' % (partner.name, partner.email))
						partner.message_post(body=msg)