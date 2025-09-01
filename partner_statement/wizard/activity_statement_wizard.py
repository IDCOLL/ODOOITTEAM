# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from dateutil.relativedelta import relativedelta
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ActivityStatementWizard(models.TransientModel):
    """Activity Statement wizard."""

    _inherit = "statement.common.wizard"
    _name = "activity.statement.wizard"
    _description = "Activity Statement Wizard"

    @api.model
    def _get_date_start(self):
        return (
            fields.Date.context_today(self).replace(day=1) - relativedelta(days=1)
        ).replace(day=1)

    date_start = fields.Date(required=True, default=_get_date_start)

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        super().onchange_aging_type()
        if self.aging_type == "months":
            self.date_start = self.date_end.replace(day=1)
        else:
            self.date_start = self.date_end - relativedelta(days=30)

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        _logger.info(f"Activity Statement Export - Data: {data}")
        return self.env.ref(
            "partner_statement.action_print_activity_statements"
        ).report_action(self.ids, data=data)

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update({"date_start": self.date_start})
        
        _logger.info(f"Activity Statement Wizard - Prepared data: {res}")
        
        # Debug: Check if partner has any move lines at all
        partner_ids = self._context.get('active_ids', [])
        if partner_ids:
            self.env.cr.execute("""
                SELECT COUNT(*) as count, MIN(date) as min_date, MAX(date) as max_date
                FROM account_move_line l 
                JOIN account_move m ON l.move_id = m.id
                WHERE l.partner_id IN %s AND m.state = 'posted'
            """, (tuple(partner_ids),))
            
            result = self.env.cr.fetchone()
            _logger.info(f"Partner {partner_ids} has {result[0]} posted move lines "
                        f"between {result[1]} and {result[2]}")
        
        return res