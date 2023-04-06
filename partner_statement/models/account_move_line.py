from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    account_internal_type = fields.Selection(
        store=True, related='account_id.acount_type', string="Internal Type", readonly=True)
