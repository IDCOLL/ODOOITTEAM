# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,_
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	send_overdue_statement = fields.Boolean(related='company_id.send_overdue_statement',string="Send Overdue Customer Statement",readonly=False)
	overdue_days = fields.Integer(related='company_id.overdue_days',string="Overdue Date",readonly=False)
	overdue_statement_template_id = fields.Many2one('mail.template', 'Overdue Statement  Template', related='company_id.overdue_statement_template_id', readonly=False)

	send_statement = fields.Boolean(related='company_id.send_statement',string="Send Customer Statement",readonly=False)
	
	auto_monthly_statement = fields.Boolean(related='company_id.auto_monthly_statement',readonly=False,string="Auto Monthly Statement")
	auto_weekly_statement = fields.Boolean(related='company_id.auto_weekly_statement',readonly=False,string="Auto Weekly Statement")

	weekly_days = fields.Selection([
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday'),
	],related='company_id.weekly_days',string="Weekly Send Day",readonly=False)
	statement_days = fields.Integer(related='company_id.statement_days',string="Monthly Send Day",readonly=False)
	
	weekly_template_id = fields.Many2one('mail.template', string='Weekly Statement  Template', related='company_id.weekly_template_id', readonly=False)
	monthly_template_id = fields.Many2one('mail.template', string='Monthly Statement  Template', related='company_id.monthly_template_id', readonly=False)
	
	

	@api.constrains ('statement_days')
	def _check_statement_days(self):
		if self.send_statement:
			if self.statement_days > 31 or self.statement_days <= 0:
				raise ValidationError(_('Enter Valid Statement Date Range'))
	
	@api.constrains('overdue_days')
	def _check_overdue_days(self):
		if self.send_overdue_statement:
			if self.overdue_days > 31 or self.overdue_days <= 0:
				raise ValidationError(_('Enter Valid Overdue Statement Date Range'))



	def get_values(self):
		res = super(ResConfigSettings, self).get_values()
		res.update({
			'overdue_days':int(self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.overdue_days')) or None,
			'statement_days':int(self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.statement_days')) or None,            
			'auto_weekly_statement':self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.auto_weekly_statement'),
			'auto_monthly_statement':self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.auto_monthly_statement'),
			'send_statement':self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.send_statement'),
			'send_overdue_statement':self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.send_overdue_statement'),
			'weekly_template_id':int(self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.weekly_template_id')) or None,
			'monthly_template_id':int(self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.monthly_template_id')) or None,
			'overdue_statement_template_id':int(self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.overdue_statement_template_id')) or None,
			'weekly_days':self.env['ir.config_parameter'].sudo().get_param('bi_customer_overdue_statement.weekly_days') or None,

			})

		return res


	def set_values(self):
		super(ResConfigSettings, self).set_values()
		ICPSudo = self.env['ir.config_parameter'].sudo()
		
		ICPSudo.set_param('bi_customer_overdue_statement.send_statement',self.send_statement)
		ICPSudo.set_param('bi_customer_overdue_statement.send_overdue_statement',self.send_overdue_statement)
		ICPSudo.set_param('bi_customer_overdue_statement.statement_days',self.statement_days or None)
		ICPSudo.set_param('bi_customer_overdue_statement.overdue_days',self.overdue_days or None)
		ICPSudo.set_param('bi_customer_overdue_statement.weekly_days',self.weekly_days or None)
		ICPSudo.set_param('bi_customer_overdue_statement.auto_monthly_statement',self.auto_monthly_statement)
		ICPSudo.set_param('bi_customer_overdue_statement.auto_weekly_statement',self.auto_weekly_statement)
		ICPSudo.set_param('bi_customer_overdue_statement.weekly_template_id',self.weekly_template_id.id or None)
		ICPSudo.set_param('bi_customer_overdue_statement.monthly_template_id',self.monthly_template_id.id or None)
		ICPSudo.set_param('bi_customer_overdue_statement.overdue_statement_template_id',self.overdue_statement_template_id.id or None)


		if self.send_overdue_statement:
			overdue_cron = self.env.ref('bi_customer_overdue_statement.autometic_send_overdue_statement_cron')
			overdue_cron.active = self.send_overdue_statement
			cron_datetime = self.change_cron_time(self.overdue_days)
			overdue_cron.nextcall = str(cron_datetime)
		
		if self.send_statement:
			if self.auto_monthly_statement:
				statement_cron = self.env.ref('bi_customer_overdue_statement.autometic_send_monthly_statement_cron')
				statement_cron.active = self.auto_monthly_statement
				cron_datetime = self.change_cron_time(self.statement_days)
				statement_cron.nextcall = str(cron_datetime)
	def change_cron_time(self,days):
		now = datetime.now()
		
		current_month = now.month
		current_date = now.day
		current_year = now.year
		expected_date = datetime(now.year, now.month, days,now.hour, now.minute, now.second)
		
		cron_datetime = expected_date
		
		if current_date>days:
			cron_datetime = expected_date + relativedelta(months=+1)
		return cron_datetime
	
	
