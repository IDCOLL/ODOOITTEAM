# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

from odoo import models


class IrConfigParameter(models.Model):
    """Extend ir.config_parameter for tracking Claude API configuration."""

    _inherit = 'ir.config_parameter'
