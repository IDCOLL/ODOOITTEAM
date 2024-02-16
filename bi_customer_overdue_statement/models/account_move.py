# -*- coding: utf-8 -*-

import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
from lxml import etree

#----------------------------------------------------------
# Entries
#----------------------------------------------------------


class account_move(models.Model):
	
	_inherit = 'account.move'
	_order = 'invoice_date_due'
	
	def _get_result(self):
		for aml in self:
			aml.result = 0.0

			if aml.is_outbound():
				sign = -1
			else:
				sign = 1

			aml.result = sign * (abs(aml.amount_total_signed) - abs(aml.credit_amount))
	
					 

	def _get_credit(self):
		for aml in self:
			aml.credit_amount = 0.0
			aml.credit_amount = abs(aml.amount_total_signed) - abs(aml.amount_residual_signed)

	credit_amount = fields.Float(compute ='_get_credit',   string="Credit/paid")
	result = fields.Float(compute ='_get_result',   string="Balance") #'balance' field is not the same


class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	@api.model
	def _query_get(self, domain=None):
		context = dict(self._context or {})
		domain = domain or []
		if not isinstance(domain, (list, tuple)):
			domain = safe_eval(domain)

		date_field = 'date'
		if context.get('aged_balance'):
			date_field = 'date_maturity'
		if context.get('date_to'):
			domain += [(date_field, '<=', context['date_to'])]
		if context.get('date_from'):
			if not context.get('strict_range'):
				domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
			elif context.get('initial_bal'):
				domain += [(date_field, '<', context['date_from'])]
			else:
				domain += [(date_field, '>=', context['date_from'])]

		if context.get('journal_ids'):
			domain += [('journal_id', 'in', context['journal_ids'])]

		state = context.get('state')
		if state and state.lower() != 'all':
			domain += [('move_id.state', '=', state)]

		if context.get('company_id'):
			domain += [('company_id', '=', context['company_id'])]

		if 'company_ids' in context:
			domain += [('company_id', 'in', context['company_ids'])]

		if context.get('reconcile_date'):
			domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.max_date', '>', context['reconcile_date']), ('matched_credit_ids.max_date', '>', context['reconcile_date'])]

		if context.get('account_tag_ids'):
			domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

		if context.get('account_ids'):
			domain += [('account_id', 'in', context['account_ids'].ids)]

		if context.get('analytic_tag_ids'):
			domain += ['|', ('analytic_account_id.tag_ids', 'in', context['analytic_tag_ids'].ids), ('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

		if context.get('analytic_account_ids'):
			domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]
		
		if context.get('partner_ids'):
			domain += [('partner_id', '=', context['partner_ids'])]

		where_clause = ""
		where_clause_params = []
		tables = ''
		if domain:
			query = self._where_calc(domain)
			tables, where_clause, where_clause_params = query.get_sql()
		return tables, where_clause, where_clause_params
