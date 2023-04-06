# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Partner Statement SA",
    "version": "16.0.1",
    "category": "Accounting & Finance",
    "summary": "Customer Statements South Africa",
    "author": "THE IT TEAM",
    "website": "https://www.the-it-team.co.za",
    "license": "AGPL-3",
    "depends": ["account"],
    "external_dependencies": {"python": ["dateutil"]},
    "data": [
        "security/statement_security.xml",
        "security/ir.model.access.csv",
        "views/activity_statement.xml",
        "views/outstanding_statement.xml",
        "views/aging_buckets.xml",
        "views/res_config_settings.xml",
        "wizard/statement_wizard.xml",
    ],
    'assets': {
        'web.assets_frontend': [
            '/partner_statement/static/src/scss/layout_statement.scss',
        ]
    },
    "installable": True,
    "application": False,
}
