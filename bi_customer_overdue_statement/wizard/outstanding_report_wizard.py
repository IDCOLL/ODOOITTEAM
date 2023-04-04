# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

from odoo import models, fields, api, _
import io
from odoo.exceptions import except_orm
from datetime import datetime
import collections
import base64
try:
	import xlwt
except ImportError:
	xlwt = None

class outstanding_report_wizard(models.TransientModel):
	_name = 'outstanding.report.wizard'
	_description = "Outstanding Report Wizard"

	journal_id = fields.Many2one('account.journal', domain=[('type', '=', 'sale')])
	start_date = fields.Date(string='Start Date', required=True)
	end_date = fields.Date(string='End Date', required=True)


	@api.onchange('end_date')
	def onchange_enddate(self):
		if self.start_date and self.end_date:

			if self.start_date > self.end_date:
				raise except_orm('Invalid Action!', 'From date cannot be greater that to date.')

	def print_outstanding_report(self):
		res_partner_obj =  self.env['res.partner']
		journal_account_obj = self.env['account.journal']
		if self.journal_id:
			unique_journal_records = [{'id':self.journal_id.id}]
		else:
			self._cr.execute("select distinct id from account_journal where type='sale'")
			unique_journal_records = self._cr.dictfetchall()
		list_of_due_months = []
		last_group_data = {}
		list_of_dict = []
		dict_of_months = {}
		custom_month = []
		list_of_month = []

		for journal_id in unique_journal_records:
			self._cr.execute('select distinct partner_id from account_move where (journal_id=%s) and invoice_date_due between (%s) and (%s)', (journal_id['id'], self.start_date, self.end_date))
			uniq_partner_records = self._cr.dictfetchall()
			final_group_data = {}
			for partner in uniq_partner_records:
				self._cr.execute("select * from account_move where invoice_date_due between (%s) and (%s) and (journal_id=%s) and partner_id = (%s) and state != 'paid' order by invoice_date_due ASC", (self.start_date, self.end_date , journal_id['id'], partner['partner_id']))
				invoice_ids = self._cr.dictfetchall()
				for invoice in invoice_ids:
					list_of_month.append(invoice['invoice_date_due'])

					a = sorted(list_of_month, key=lambda x: datetime.strptime(str(x), '%Y-%m-%d'))
					inv_due_month = str(datetime.strptime(str(invoice['invoice_date_due']), '%Y-%m-%d').strftime("%B"))+ str(datetime.strptime(str(invoice['invoice_date_due']),'%Y-%m-%d').year)
					list_of_due_months.append(inv_due_month)
					dict_of_months.update({inv_due_month: datetime.strptime(str(invoice['invoice_date_due']), '%Y-%m-%d').month})

					b = (sorted(dict_of_months.items(), key = lambda kv:(kv[1], kv[0]))) 
					grand_total = 0
					if invoice['amount_residual'] == 0.0:
						amt = ''
					else:
						amt = invoice['amount_residual']
					data_dictionary = {'inv_number':invoice['name'],
									   'due_date': invoice['invoice_date_due'],
									   inv_due_month:amt,
									   'total': amt,
									   'journal_id': invoice['journal_id'],
									   'invoice_date': invoice['invoice_date'],
									   }
					if amt != '':
						grand_total += amt
					list_of_dict.append(data_dictionary)
				sorted_dict = sorted(list_of_dict, key= lambda k: k ['due_date'])
				if sorted_dict != []:
					final_group_data.update({partner['partner_id']:sorted_dict})
				list_of_dict = []
				if final_group_data:
					last_group_data.update({journal_id['id']: final_group_data})
		
		if list_of_month:
			od = collections.OrderedDict(sorted(dict_of_months.items()))
			for i in b:
				custom_month.append(i[0])
			list_of_due_months = custom_month
			last_group_data = collections.OrderedDict(sorted(last_group_data.items()))
			list_months_total_dict = []
			# getting total journal wise
			for key1,data1 in last_group_data.items():
				dict_of_month_total = {}
				for key,value in od.items():
					self._cr.execute("select sum(amount_residual),invoice_date_due  from account_move where Extract(month from invoice_date_due)=(%s) and journal_id=(%s) group by invoice_date_due",(value,key1))
					record = self._cr.dictfetchall()
					total =0
					for value in record:
						total = total + value.get('sum')
					dict_of_month_total.update({key: total})
				list_months_total_dict.append({key1:dict_of_month_total})
		else:
			list_months_total_dict = None
			last_group_data = None
			custom_month = None
		if self._context.get('type') == 'pdf':
			data = {'list_months_total_dict': list_months_total_dict,
					'last_group_data': last_group_data,
					'list_of_due_months':custom_month,
					'jounal_name':self.journal_id.name}
			datas = {
				'ids': self._ids,
				'model': 'account.move',
				'form': data,
			}

			return self.env.ref('bi_customer_overdue_statement.report_outstanding_print').report_action(self,data=datas)

		filename = 'Outstanding invoice Details report.xls'
		workbook = xlwt.Workbook()
		style = xlwt.XFStyle()
		tall_style = xlwt.easyxf('font:height 720;')  # 36pt
		# Create a font to use with the style
		font = xlwt.Font()
		font.name = 'calibri'
		font.bold = True
		font.height = 200
		style.font = font
		index = 1
		row = 0
		worksheet = workbook.add_sheet('Sheet 1')

		worksheet.write(row, 1,'Invoice Date',style)
		col = 2
		for months_cols in list_of_due_months:
			worksheet.write(row , col, months_cols, style)
			col +=1
		worksheet.write(row, col, 'Total', style)
		worksheet.write(row, col +1 , 'Due Date',style)
		if last_group_data:
			for data1, values in last_group_data.items():
				worksheet.write(row, 0 ,journal_account_obj.browse(data1).name, style)
				for data2,vals in values.items():
					if vals != []:
						worksheet.write(row+1, 0, res_partner_obj.browse(data2).name)
						row = row +1
					for val in vals:
						row = row +1
						worksheet.write(row, 0, val['inv_number'])
						worksheet.write(row, 1, str(val['invoice_date']))
						col =2

						for month in list_of_due_months:

							if val.get(month) != None:
								worksheet.write(row, col, val[month])
							else:
								worksheet.write(row,col, '')
							col = col  +1

						worksheet.write(row, col , val['total'])
						worksheet.write(row, col+1,'DUE DATE - ' +str(val['due_date']))
						row = row + 0
				row = row + 1
				col = 2
				for values in list_months_total_dict:
					for key,value in values.items():
						if  key == data1:
							for months in list_of_due_months:
								if value.get(months) != None:
									if value.get(months)!= '':
										worksheet.write(row, col, value.get(months),style)
										col = col +1


		fp = io.BytesIO()
		workbook.save(fp)
		export_id = self.env['outstanding.report.excel'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
		fp.close()
		res = {
			'view_mode': 'form',
			'res_id': export_id.id,
			'res_model': 'outstanding.report.excel',
			'type': 'ir.actions.act_window',
			'target':'new'
		}
		return res


class outstanding_report_excel(models.TransientModel):

	_name = "outstanding.report.excel"
	_description = "Outstanding Report Excel"


	excel_file = fields.Binary('Excel Report for outstanding invoice', readonly =True)
	file_name = fields.Char('Excel File', size=64)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:# 

