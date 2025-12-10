from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_aging_type = fields.Selection(
        selection_add=[],
        default_model='account.aged.partner.balance.report.handler',
    )
    
    default_show_aging_buckets = fields.Boolean(
        default_model='account.aged.partner.balance.report.handler',
    )
    
    default_aging_bucket_count = fields.Integer(
        default_model='account.aged.partner.balance.report.handler',
    )
    
    default_aging_bucket_duration = fields.Integer(
        default_model='account.aged.partner.balance.report.handler',
    )