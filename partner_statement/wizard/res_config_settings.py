from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_activity_statement = fields.Boolean(
        "Enable Activity Statements",
        group="account.group_account_manager",
        implied_group="partner_statement.group_activity_statement",
        help="Activity Statements show all transactions between two dates."
    )

    default_aging_type = fields.Selection(
        [("days", "Age by Days"), ("months", "Age by Months")],
        string="Default Aging Method",
        required=True,
        default="days",
        default_model="statement.common.wizard",
        help="Default method for aging calculations"
    )

    default_show_aging_buckets = fields.Boolean(
        string="Show Aging Buckets by Default", 
        default_model="statement.common.wizard",
        help="Show aging buckets in statements by default"
    )

    default_filter_partners_non_due = fields.Boolean(
        string="Exclude Partners with No Due Entries by Default",
        default_model="statement.common.wizard",
        help="Filter out partners with no due entries by default"
    )

    default_filter_negative_balances = fields.Boolean(
        "Exclude Negative Balances by Default", 
        default_model="statement.common.wizard",
        help="Filter out partners with negative balances by default"
    )

    group_outstanding_statement = fields.Boolean(
        "Enable Outstanding Statements",
        group="account.group_account_manager",
        implied_group="partner_statement.group_outstanding_statement",
        help="Outstanding Statements show all transactions up to a date."
    )

    def set_values(self):
        self = self.with_context(active_test=False)
        # default values fields
        IrDefault = self.env["ir.default"].sudo()
        for name, field in self._fields.items():
            if (
                name.startswith("default_")
                and hasattr(field, 'default_model')
                and field.default_model == "statement.common.wizard"
            ):
                if isinstance(self[name], models.BaseModel):
                    if self._fields[name].type == "many2one":
                        value = self[name].id
                    else:
                        value = self[name].ids
                else:
                    value = self[name]
                IrDefault.set("activity.statement.wizard", name[8:], value)
                IrDefault.set("outstanding.statement.wizard", name[8:], value)
        return super().set_values()