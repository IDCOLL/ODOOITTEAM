from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # Note: In Odoo 17, account_type is already available directly on account_id.account_type
    # No additional fields needed