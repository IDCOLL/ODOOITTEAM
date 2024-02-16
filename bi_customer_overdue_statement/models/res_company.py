# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Company(models.Model):
	_inherit = 'res.company'
	
	send_overdue_statement = fields.Boolean("Send Overdue Customer Statement")
	overdue_days = fields.Integer("Overdue Statement Send Date")
	overdue_statement_template_id = fields.Many2one('mail.template', 'Overdue Statement Email Template',domain=[('model','=','res.partner')])


	send_statement = fields.Boolean("Send Customer Statement")

	auto_monthly_statement = fields.Boolean("Auto Monthly Statement")
	auto_weekly_statement = fields.Boolean("Auto Weekly Statement")

	weekly_days = fields.Selection([
		('0', 'Monday'),
		('1', 'Tuesday'),
		('2', 'Wednesday'),
		('3', 'Thursday'),
		('4', 'Friday'),
		('5', 'Saturday'),
		('6', 'Sunday'),
	],string="Weekly Send Day")
	statement_days = fields.Integer("Monthly Send Day")

	weekly_template_id = fields.Many2one('mail.template', 'Weekly Statement Email Template',domain=[('model','=','res.partner')])
	monthly_template_id = fields.Many2one('mail.template', 'Monthly Statement Email Template',domain=[('model','=','res.partner')])

	period = fields.Selection([('weekly', 'Weekly'),('monthly', 'Monthly'),('all', "All")],'Period',default='monthly')
	filter_statement = fields.Selection([('filter_only','View Only Filter Statements'),('all_statement','View All Statements Along With Filter Statements')],string="Filter Statement")
	


class MailTemplate(models.Model):
	_inherit = 'mail.template'

	def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None):
		res = super(MailTemplate, self).send_mail(res_id, force_send=False, raise_exception=False, email_values=None)
		
		mail = self.env['mail.mail'].browse(res)

		if self._context.get('monthly_attachments'):
			attachment_ids = []
			for attachment in self._context.get('monthly_attachments'):
				attachment_data = {
					'name': attachment[0],
					'datas': attachment[1],
					'type': 'binary',
					'res_model': 'mail.message',
					'res_id': mail.mail_message_id.id,
				}
				attach = self.env['ir.attachment'].create(attachment_data)
				attachment_ids.append(attach.id)
			self.env['mail.mail'].sudo().browse(res).attachment_ids = [(6,0,attachment_ids)]
		return res