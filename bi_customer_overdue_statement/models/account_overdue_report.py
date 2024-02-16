# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models


class ReportOverdue(models.AbstractModel):
	_inherit = 'report.account.report_overdue'

	def _get_account_move_lines(self, partner_ids):
		res = {x: [] for x in partner_ids}
		self.env.cr.execute("SELECT m.id AS m_id, m.name AS move_id, l.date, l.name, l.ref, l.date_maturity, l.partner_id, l.blocked, l.amount_currency, l.currency_id, "
			"CASE WHEN at.type = 'receivable' "
				"THEN SUM(l.debit) "
				"ELSE SUM(l.credit * -1) "
			"END AS debit, "
			"CASE WHEN at.type = 'receivable' "
				"THEN SUM(l.credit) "
				"ELSE SUM(l.debit * -1) "
			"END AS credit, "
			"CASE WHEN l.date_maturity < %s "
				"THEN SUM(l.debit - l.credit) "
				"ELSE 0 "
			"END AS mat "
			"FROM account_move_line l "
			"JOIN account_account_type at ON (l.user_type_id = at.id) "
			"JOIN account_move m ON (l.move_id = m.id) "
			"WHERE l.partner_id IN %s AND at.type IN ('receivable', 'payable') AND NOT l.reconciled AND ai.invoice_date_due < %s  GROUP BY l.date, l.name, l.ref, l.date_maturity, l.partner_id, at.type, l.blocked, l.amount_currency, l.currency_id, l.move_id, m.name, m.id ORDER BY l.date", (((fields.date.today(), ) + (tuple(partner_ids),) + (fields.date.today(), ))))
		for row in self.env.cr.dictfetchall():
			res[row.pop('partner_id')].append(row)
		return res

	@api.model
	def get_report_values(self, docids, data=None):
		totals = {}
		lines = self._get_account_move_lines(docids)
		lines_to_display = {}
		company_currency = self.env.user.company_id.currency_id
		for partner_id in docids:
			lines_to_display[partner_id] = {}
			totals[partner_id] = {}
			invoices = []
			for line_tmp in lines[partner_id]:
				line = line_tmp.copy()
				invoice = self.env['account.move'].search([('name','=',line['move_id'])])
				if invoice.type == 'out_refund':
					continue
				if invoice.id in invoices:
					continue
				else:
					invoices.append(invoice.id)
					currency = line['currency_id'] and self.env['res.currency'].browse(line['currency_id']) or company_currency
					if currency not in lines_to_display[partner_id]:
						lines_to_display[partner_id][currency] = []
						totals[partner_id][currency] = dict((fn, 0.0) for fn in ['due', 'paid', 'mat', 'total'])
					line['debit'] = invoice.amount_total
					line['credit'] = invoice.amount_residual
					lines_to_display[partner_id][currency].append(line)
					if not line['blocked']:
						totals[partner_id][currency]['due'] += line['debit']
						totals[partner_id][currency]['paid'] += line['credit']
						totals[partner_id][currency]['total'] += line['debit'] - line['credit']
		return {
			'doc_ids': docids,
			'doc_model': 'res.partner',
			'docs': self.env['res.partner'].browse(docids),
			'time': time,
			'Lines': lines_to_display,
			'Totals': totals,
			'Date': fields.date.today(),
		}
