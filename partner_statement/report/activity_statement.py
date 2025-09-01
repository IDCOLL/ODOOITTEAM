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

        # First, let's check what account types actually exist for this partner
        debug_query = """
            SELECT DISTINCT acc.account_type, acc.code, acc.name, COUNT(*) as count
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_account acc ON (l.account_id = acc.id)
            WHERE l.partner_id IN %s
                AND m.state = 'posted'
                AND l.date BETWEEN %s AND %s
            GROUP BY acc.account_type, acc.code, acc.name
            ORDER BY count DESC
        """
        self.env.cr.execute(debug_query, (partners, date_start, date_end))
        debug_results = self.env.cr.fetchall()
        _logger.info(f"Available account types for partner in date range: {debug_results}")

        # Also check without date restriction
        debug_query_all = """
            SELECT DISTINCT acc.account_type, acc.code, acc.name, COUNT(*) as count
            FROM account_move_line l
            JOIN account_move m ON (l.move_id = m.id)
            JOIN account_account acc ON (l.account_id = acc.id)
            WHERE l.partner_id IN %s
                AND m.state = 'posted'
            GROUP BY acc.account_type, acc.code, acc.name
            ORDER BY count DESC
        """
        self.env.cr.execute(debug_query_all, (partners,))
        debug_results_all = self.env.cr.fetchall()
        _logger.info(f"Available account types for partner (all dates): {debug_results_all}")

        # Try the original query first
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
        _logger.info(f"Query with {mapped_account_type} found {len(results)} records")
        
        # If no results with mapped account type, try all common account types
        if not results:
            common_types = ['asset_receivable', 'liability_payable', 'receivable', 'payable']
            for test_type in common_types:
                if test_type == mapped_account_type:
                    continue  # Already tried this one
                
                _logger.info(f"Trying account type: {test_type}")
                self.env.cr.execute(query, (
                    partners, test_type, date_start, date_end, company_id
                ))
                
                test_results = self.env.cr.dictfetchall()
                if test_results:
                    _logger.info(f"SUCCESS: Found {len(test_results)} records with account type {test_type}")
                    results = test_results
                    break
                else:
                    _logger.info(f"No results with account type {test_type}")

        # If still no results, try a broader query without account type restriction
        if not results:
            _logger.info("Trying query without account type restriction...")
            broad_query = """
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
                       COALESCE(l.currency_id, c.currency_id) AS currency_id,
                       acc.account_type
                FROM account_move_line l
                JOIN account_move m ON (l.move_id = m.id)
                JOIN account_account acc ON (l.account_id = acc.id)
                JOIN res_company c ON (c.id = l.company_id)
                WHERE l.partner_id IN %s
                    AND l.date BETWEEN %s AND %s
                    AND m.state = 'posted'
                    AND c.id = %s
                    AND acc.account_type IN ('asset_receivable', 'liability_payable', 'receivable', 'payable')
                ORDER BY l.date, l.id
                LIMIT 10
            """
            
            self.env.cr.execute(broad_query, (
                partners, date_start, date_end, company_id
            ))
            
            broad_results = self.env.cr.dictfetchall()
            _logger.info(f"Broad query found {len(broad_results)} records")
            if broad_results:
                _logger.info(f"Sample records: {broad_results[:3]}")
                # Filter results to match the requested account type logic
                if account_type == 'receivable':
                    results = [r for r in broad_results if r['account_type'] in ['asset_receivable', 'receivable']]
                elif account_type == 'payable':
                    results = [r for r in broad_results if r['account_type'] in ['liability_payable', 'payable']]
                else:
                    results = broad_results

        for row in results:
            # Remove the debug field if it exists
            if 'account_type' in row:
                del row['account_type']
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
        
        _logger.info(f"Getting initial balance for account type: {mapped_account_type}")
        
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
        
        balance_results = self.env.cr.dictfetchall()
        _logger.info(f"Initial balance query found {len(balance_results)} records")
        
        # If no results with mapped type, try other types
        if not balance_results:
            common_types = ['asset_receivable', 'liability_payable', 'receivable', 'payable']
            for test_type in common_types:
                if test_type == mapped_account_type:
                    continue
                
                self.env.cr.execute(query, (
                    partners, test_type, date_start, company_id
                ))
                
                test_balance_results = self.env.cr.dictfetchall()
                if test_balance_results:
                    _logger.info(f"Found initial balance with account type {test_type}: {len(test_balance_results)} records")
                    balance_results = test_balance_results
                    break
        
        for row in balance_results:
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