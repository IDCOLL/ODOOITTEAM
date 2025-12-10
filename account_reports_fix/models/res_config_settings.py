from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_aging_type = fields.Selection(
        selection_add=[],
        default_model='account.aged.partner.balance.report.handler',
    )