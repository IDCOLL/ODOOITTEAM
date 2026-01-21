# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

{
    'name': 'Claude AI Helpdesk Automation',
    'version': '1.0.1',
    'category': 'Helpdesk',
    'summary': 'Integrate Claude AI with Odoo Helpdesk for automated ticket analysis and GitHub PR creation',
    'description': """
        Claude AI Helpdesk Automation
        ==============================

        This module integrates Claude AI (Anthropic) with Odoo Helpdesk to:
        * Automatically analyze support tickets
        * Propose code solutions based on ticket descriptions
        * Create GitHub pull requests with fixes
        * Track analysis history and statistics
        * Support multiple clients with different GitHub repositories

        Features:
        ---------
        * Intelligent ticket analysis using Claude Sonnet 4.5
        * Automatic module detection from ticket description
        * GitHub integration for creating branches and pull requests
        * Prompt caching for cost optimization
        * Per-client configuration for GitHub repos and Odoo environments
        * Manual and automatic analysis modes
        * Comprehensive logging and error handling

        Installation:
        -------------
        For Odoo.sh: Add requirements.txt to repository root
        For Self-hosted: pip install anthropic requests

        See README.md for full installation instructions.
    """,
    'author': 'The IT Team',
    'website': 'https://theitteam.co.za',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'helpdesk',
        'mail',
    ],
    'external_dependencies': {
        'python': ['anthropic', 'requests'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/automation_rules.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/menuitem.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
