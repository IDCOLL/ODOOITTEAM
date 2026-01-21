# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

import logging
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    """Extend res.partner to add GitHub and Odoo configuration for Claude AI integration."""

    _inherit = 'res.partner'

    # Project Type Configuration
    x_project_type = fields.Selection(
        selection=[
            ('odoo', 'Odoo Module'),
            ('vue', 'Vue.js Application'),
            ('react', 'React Application'),
            ('node', 'Node.js Backend'),
            ('python', 'Python Application'),
            ('django', 'Django Application'),
            ('flask', 'Flask Application'),
            ('fullstack', 'Full Stack (Multiple)'),
            ('other', 'Other'),
        ],
        string='Project Type',
        default='odoo',
        help='Type of project/application for this client'
    )

    # GitHub Configuration
    x_github_repo = fields.Char(
        string='GitHub Repository URL',
        help='Full GitHub repository URL (e.g., https://github.com/owner/repo)'
    )
    x_github_token = fields.Char(
        string='GitHub Personal Access Token',
        groups='base.group_system',
        help='GitHub PAT with repo permissions. Visible only to system administrators.'
    )
    x_github_default_branch = fields.Char(
        string='Default Branch',
        default='main',
        help='Main branch to create pull requests against (e.g., main, master, production)'
    )
    x_github_dev_branch_prefix = fields.Char(
        string='Dev Branch Prefix',
        default='ai-fix/',
        help='Prefix for auto-created branches (e.g., ai-fix/, feature/, bugfix/)'
    )
    x_github_addons_path = fields.Char(
        string='Addons Path in Repo',
        default='addons',
        help='Path to addons directory in GitHub repo (e.g., addons, custom_addons, src)'
    )
    x_github_source_path = fields.Char(
        string='Source Code Path',
        default='src',
        help='Path to source code directory for non-Odoo projects (e.g., src, app, lib)'
    )

    # Odoo Environment Configuration (visible when project_type is odoo)
    x_odoo_version = fields.Selection(
        selection=[
            ('14', 'Odoo 14.0'),
            ('15', 'Odoo 15.0'),
            ('16', 'Odoo 16.0'),
            ('17', 'Odoo 17.0'),
            ('18', 'Odoo 18.0'),
            ('19', 'Odoo 19.0'),
        ],
        string='Odoo Version',
        help='Odoo version running for this client'
    )
    x_custom_modules = fields.Text(
        string='Custom Modules',
        help='Comma-separated list of custom module names installed for this client'
    )
    x_odoo_config_notes = fields.Text(
        string='Configuration Notes',
        help='Additional notes about client Odoo environment, customizations, or architecture'
    )

    # Custom App Configuration (visible when project_type is not odoo)
    x_app_framework_version = fields.Char(
        string='Framework Version',
        help='Version of the main framework (e.g., Vue 3.4, React 18, Node 20)'
    )
    x_app_tech_stack = fields.Text(
        string='Technology Stack',
        help='Describe the tech stack: frameworks, libraries, databases, etc.\nExample: Vue 3 + Pinia + Vue Router, Node.js + Express, PostgreSQL, Redis'
    )
    x_app_architecture_notes = fields.Text(
        string='Architecture Notes',
        help='Describe the application architecture, folder structure, key patterns used.\nExample: Component-based SPA, REST API backend, JWT authentication'
    )
    x_app_build_commands = fields.Text(
        string='Build/Run Commands',
        help='Common commands for building and running the app.\nExample:\nnpm install\nnpm run dev\nnpm run build'
    )
    x_app_test_commands = fields.Text(
        string='Test Commands',
        help='Commands for running tests.\nExample:\nnpm run test\nnpm run test:e2e'
    )
    x_app_key_files = fields.Text(
        string='Key Files/Directories',
        help='Important files and directories to focus on.\nExample:\nsrc/components/ - Vue components\nsrc/stores/ - Pinia stores\nsrc/api/ - API client'
    )

    # AI Settings
    x_enable_auto_analysis = fields.Boolean(
        string='Enable Auto-Analysis',
        default=True,
        help='Automatically analyze new tickets with Claude AI when created'
    )
    x_auto_create_pr = fields.Boolean(
        string='Auto-Create Pull Requests',
        default=False,
        help='Automatically create GitHub PRs when analysis proposes code changes (use with caution)'
    )

    # Statistics
    x_total_tickets_analyzed = fields.Integer(
        string='Tickets Analyzed',
        compute='_compute_ticket_stats',
        help='Total number of tickets analyzed by Claude AI for this client'
    )
    x_total_prs_created = fields.Integer(
        string='PRs Created',
        compute='_compute_ticket_stats',
        help='Total number of GitHub pull requests created'
    )

    @api.depends('name')
    def _compute_ticket_stats(self):
        """Compute statistics about tickets analyzed and PRs created."""
        for partner in self:
            tickets = self.env['helpdesk.ticket'].search([
                ('partner_id', '=', partner.id)
            ])
            partner.x_total_tickets_analyzed = len(tickets.filtered('x_ai_analyzed'))
            partner.x_total_prs_created = len(tickets.filtered('x_pr_created'))

    @api.constrains('x_github_repo')
    def _check_github_repo_url(self):
        """Validate GitHub repository URL format."""
        for partner in self:
            if partner.x_github_repo:
                # Accept both https://github.com/owner/repo and github.com/owner/repo
                pattern = r'^(https?://)?github\.com/[\w\-]+/[\w\-\.]+/?$'
                if not re.match(pattern, partner.x_github_repo.strip()):
                    raise ValidationError(_(
                        'Invalid GitHub repository URL. '
                        'Expected format: https://github.com/owner/repo'
                    ))

    def action_test_github_connection(self):
        """Test GitHub connection and display result to user."""
        self.ensure_one()

        if not self.x_github_repo:
            raise UserError(_('Please configure GitHub Repository URL first.'))

        if not self.x_github_token:
            raise UserError(_('Please configure GitHub Personal Access Token first.'))

        try:
            from odoo.addons.claude_helpdesk_ai.lib.github_integration import GitHubIntegration

            github = GitHubIntegration(self.x_github_repo, self.x_github_token)
            status = github.test_connection()

            if status['success']:
                message = _(
                    'Connection successful!\n\n'
                    'Repository: %(repo)s\n'
                    'Default Branch: %(branch)s\n'
                    'Permissions: %(perms)s'
                ) % {
                    'repo': status.get('repo_name', 'Unknown'),
                    'branch': status.get('default_branch', 'Unknown'),
                    'perms': ', '.join(status.get('permissions', []))
                }

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('GitHub Connection Test'),
                        'message': message,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_(
                    'Connection failed: %s'
                ) % status.get('error', 'Unknown error'))

        except Exception as e:
            _logger.error('GitHub connection test failed: %s', str(e), exc_info=True)
            raise UserError(_(
                'Connection test failed: %s\n\n'
                'Please check your GitHub URL and token.'
            ) % str(e))

    def action_view_analyzed_tickets(self):
        """Open tree view of all analyzed tickets for this partner."""
        self.ensure_one()

        return {
            'name': _('Analyzed Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('x_ai_analyzed', '=', True)
            ],
            'context': {'default_partner_id': self.id},
        }

    def action_refresh_cache(self):
        """Force refresh of computed fields and cache."""
        self.ensure_one()
        self._compute_ticket_stats()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Cache Refreshed'),
                'message': _('Statistics have been updated.'),
                'type': 'success',
                'sticky': False,
            }
        }
