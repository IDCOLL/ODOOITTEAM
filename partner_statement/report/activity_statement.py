# Copyright 2018 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ActivityStatement(models.AbstractModel):
    """Model of Activity Statement"""

    _inherit = "statement.common"
    _name = "report.partner_statement.activity_statement"
    _description = "Partner Activity Statement"

    def _get_account_type_mapping(self, account_type):
        """Map old account types to new Odoo 17 account types"""
        mapping = {
            'receivable': 'asset_receivable',
            'payable': 'liability_payable'
        }
        return mapping.get(account_type, account_type)

    def _get_account_display_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)
        
        # Map to correct account type for Odoo 17
        mapped_account_type = self._get_account_type_mapping(account_type)
        
        _logger.info("=== ACTIVITY STATEMENT DEBUG ===")
        _logger.info(f"Company ID: {company_id}")
        _logger.info(f"Partner IDs: {partner_ids}")
        _logger.info(f"Date Start: {date_start}")
        _logger.info(f"Date End: {date_end}")
        _logger.info(f"Original Account Type: {account_type}")
        _logger.info(f"Mapped Account Type: {mapped_account_type}")

        query = """
            SELECT m.name AS move_id, l.partner_id, l.date,
                   COALESCE(l.name, '/') as name,
                   COALESCE(l.ref, '') as ref,
                   COALESCE(l.blocked, false) as blocked, 
                   l.currency_id, 
                   l.company_id,
                   l.debit,
                   l.credit,
                   l.debit - l.credit as amount,
                   COALESCE(l.date_maturity, l.date) as date_maturity,
                   COALESCE(l.currency_id, c.currency_id) AS currency_id
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_account acc ON (l.account_id = acc.id)
            JOIN res_company c ON (c.id = l.company_id)
            WHERE l.partner_id IN %s
                AND acc.account_type = %s
                AND l.date BETWEEN %s AND %s
                AND m.state = 'posted'
                AND c.id = %s
            ORDER BY l.date, l.id
        """

        self.env.cr.execute(query, (
            partners, mapped_account_type, date_start, date_end, company_id
        ))
        
        results = self.env.cr.dictfetchall()
        _logger.info(f"Query found {len(results)} records")
        
        for row in results:
            res[row.pop("partner_id")].append(row)
            
        _logger.info(f"Final result: {len([item for sublist in res.values() for item in sublist])} total lines")
        _logger.info("=== END ACTIVITY STATEMENT DEBUG ===")
        
        return res

    def _get_account_initial_balance(
        self, company_id, partner_ids, date_start, account_type
    ):
        res = defaultdict(list)
        partners = tuple(partner_ids)
        mapped_account_type = self._get_account_type_mapping(account_type)
        
        query = """
            SELECT l.partner_id,
                   COALESCE(l.currency_id, c.currency_id) AS currency_id,
                   SUM(l.debit - l.credit) AS balance
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_account acc ON (l.account_id = acc.id)
            JOIN res_company c ON (c.id = l.company_id)
            WHERE l.partner_id IN %s
                AND acc.account_type = %s
                AND l.date < %s
                AND m.state = 'posted'
                AND c.id = %s
            GROUP BY l.partner_id, COALESCE(l.currency_id, c.currency_id)
        """
        
        self.env.cr.execute(query, (
            partners, mapped_account_type, date_start, company_id
        ))
        
        for row in self.env.cr.dictfetchall():
            res[row['partner_id']].append(row)
        
        return res

    @api.model
    def _get_report_values(self, docids, data=None):
        _logger.info(f"_get_report_values called with docids: {docids}, data: {data}")
        
        if not data:
            data = {}
        if "company_id" not in data:
            wiz = self.env["activity.statement.wizard"].with_context(
                active_ids=docids, model="res.partner"
            )
            data.update(wiz.create({})._prepare_statement())
        data["amount_field"] = "amount"
        
        _logger.info(f"Final data for report: {data}")
        
        return super()._get_report_values(docids, data)