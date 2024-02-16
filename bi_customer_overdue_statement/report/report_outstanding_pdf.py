# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
################################################################################

import time
from odoo import api, models, _

class report_outstanding_pdf(models.AbstractModel):
	_name = 'report.bi_customer_overdue_statement.report_outstanding_pdf'
	_description = "Report Outstanding Pdf"


	def _get_report_values(self,doc_ids, data=None):
		docargs = {
				   'doc_ids': self.ids,
				   'docs': self,
				   'data' : data,
				   'time': time,
				   'get_partner' : self._get_partner,
				   }
		return docargs

	def _get_partner(self, partner):
		abc = self.env['res.partner'].browse(int(float(partner))).name
		return abc
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
