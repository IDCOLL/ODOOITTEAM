from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_activity_statement = fields.Boolean(
        "Enable Activity Statements",
        implied_group="partner_statement.group_activity_statement",
        help="Activity Statements show all transactions between two dates."
    )

    group_outstanding_statement = fields.Boolean(
        "Enable Outstanding Statements",
        implied_group="partner_statement.group_outstanding_statement",
        help="Outstanding Statements show all transactions up to a date."
    )

    default_aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Default Aging Method",
        default="days",
        config_parameter="partner_statement.default_aging_type",
        help="Default method for aging calculations"
    )

    default_show_aging_buckets = fields.Boolean(
        string="Show Aging Buckets by Default", 
        config_parameter="partner_statement.default_show_aging_buckets",
        help="Show aging buckets in statements by default"
    )

    default_filter_partners_non_due = fields.Boolean(
        string="Exclude Partners with No Due Entries by Default",
        config_parameter="partner_statement.default_filter_partners_non_due",
        help="Filter out partners with no due entries by default"
    )

    default_filter_negative_balances = fields.Boolean(
        "Exclude Negative Balances by Default", 
        config_parameter="partner_statement.default_filter_negative_balances",
        help="Filter out partners with negative balances by default"
    )