# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    claude_api_key = fields.Char(
        string='Claude API Key',
        config_parameter='claude_helpdesk_ai.api_key',
        help='Your Anthropic Claude API key. Get one at https://console.anthropic.com'
    )
    claude_model = fields.Char(
        string='Claude Model',
        config_parameter='claude_helpdesk_ai.model',
        default='claude-sonnet-4-20250514',
        help='The Claude model to use for analysis (e.g., claude-sonnet-4-20250514)'
    )
    claude_max_tokens = fields.Integer(
        string='Max Tokens',
        config_parameter='claude_helpdesk_ai.max_tokens',
        default=8192,
        help='Maximum tokens for Claude API responses'
    )
