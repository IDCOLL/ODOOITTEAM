# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

import json
import logging
import re
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    """Extend helpdesk.ticket to add Claude AI analysis capabilities."""

    _inherit = 'helpdesk.ticket'

    # Analysis Results
    x_claude_analysis = fields.Html(
        string='AI Analysis',
        readonly=True,
        help='Formatted analysis results from Claude AI'
    )
    x_claude_analysis_json = fields.Text(
        string='Full Response JSON',
        readonly=True,
        help='Complete JSON response from Claude API for debugging'
    )
    x_proposed_changes = fields.Text(
        string='Proposed Code Changes',
        readonly=True,
        help='JSON array of proposed file changes'
    )
    x_analysis_date = fields.Datetime(
        string='Analysis Date',
        readonly=True,
        help='When the ticket was analyzed by Claude AI'
    )
    x_estimated_hours = fields.Float(
        string='Estimated Hours',
        readonly=True,
        help='Estimated development hours from AI analysis'
    )

    # GitHub Integration
    x_github_branch = fields.Char(
        string='GitHub Branch',
        readonly=True,
        help='Name of the branch created for this fix'
    )
    x_github_pr_url = fields.Char(
        string='Pull Request URL',
        readonly=True,
        help='URL of the created pull request'
    )
    x_github_pr_number = fields.Integer(
        string='PR Number',
        readonly=True,
        help='GitHub pull request number'
    )

    # Technical Details
    x_affected_module = fields.Char(
        string='Affected Module',
        help='Odoo module name detected from ticket description'
    )
    x_error_logs = fields.Text(
        string='Error Logs',
        help='Paste error logs or stack traces here'
    )
    x_steps_to_reproduce = fields.Text(
        string='Steps to Reproduce',
        help='Detailed steps to reproduce the issue'
    )

    # Computed Fields
    x_ai_analyzed = fields.Boolean(
        string='AI Analyzed',
        compute='_compute_ai_status',
        store=True,
        help='Whether this ticket has been analyzed by Claude AI'
    )
    x_pr_created = fields.Boolean(
        string='PR Created',
        compute='_compute_ai_status',
        store=True,
        help='Whether a GitHub PR has been created'
    )

    @api.depends('x_claude_analysis', 'x_github_pr_url')
    def _compute_ai_status(self):
        """Compute AI analysis and PR creation status."""
        for ticket in self:
            ticket.x_ai_analyzed = bool(ticket.x_claude_analysis)
            ticket.x_pr_created = bool(ticket.x_github_pr_url)

    def action_analyze_with_claude(self):
        """Manual button action to trigger Claude AI analysis."""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Please assign a customer to this ticket first.'))

        return self._perform_claude_analysis()

    def _perform_claude_analysis(self):
        """Core method to perform Claude AI analysis."""
        self.ensure_one()

        _logger.info('Starting Claude AI analysis for ticket %s', self.id)

        # Validate configuration
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'claude_helpdesk_ai.api_key'
        )
        if not api_key:
            raise UserError(_(
                'Claude API key not configured. '
                'Please set system parameter: claude_helpdesk_ai.api_key'
            ))

        partner = self.partner_id
        if not partner:
            raise UserError(_('No customer assigned to this ticket.'))

        try:
            # Build cached context (universal + client-specific)
            cached_context = self._build_cached_prompt()

            # Call Claude API
            response_dict = self._call_claude_api(cached_context, api_key)

            # Process and store response
            self._process_claude_response(response_dict)

            # Create GitHub PR if enabled and changes proposed
            if (partner.x_auto_create_pr and
                response_dict.get('code_changes') and
                partner.x_github_repo and
                partner.x_github_token):
                self._create_github_solution(response_dict)

            _logger.info('Claude AI analysis completed for ticket %s', self.id)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Analysis Complete'),
                    'message': _('Claude AI has analyzed the ticket successfully.'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(
                'Claude AI analysis failed for ticket %s: %s',
                self.id, str(e), exc_info=True
            )
            raise UserError(_(
                'Analysis failed: %s\n\n'
                'Please check the logs for details.'
            ) % str(e))

    def _build_cached_prompt(self):
        """Build the cached context portion of the prompt."""
        # Get universal Odoo context
        universal_context = self._get_universal_context()

        # Get client-specific context
        client_context = self._get_client_context()

        # Combine with cache control markers
        cached_prompt = f"""You are an expert Odoo developer analyzing a support ticket.

{universal_context}

{client_context}

Your task is to analyze support tickets and provide detailed solutions with code changes.
"""
        return cached_prompt

    def _get_universal_context(self):
        """Return universal Odoo best practices and guidelines."""
        return """# ODOO DEVELOPMENT BEST PRACTICES

## Framework Guidelines
- Follow Odoo coding conventions and style guide
- Use proper model inheritance (_inherit for extending, _name for new models)
- Always use self.ensure_one() for singleton operations
- Use proper field types and attributes (string, help, required, readonly, etc.)
- Implement proper access rights and record rules
- Use computed fields with proper dependencies (@api.depends)
- Handle exceptions gracefully with try-except blocks
- Use _logger for logging important events and errors
- Validate user inputs with @api.constrains decorators
- Use proper ORM methods (create, write, unlink, search, browse)

## Security Best Practices
- Never use SQL injection vulnerable code
- Sanitize all user inputs
- Use proper access rights (ir.model.access.csv)
- Use groups parameter for sensitive fields
- Implement record rules for row-level security
- Use sudo() sparingly and only when necessary
- Validate file uploads and external data

## Performance Optimization
- Avoid N+1 queries (use prefetch, read_group)
- Use search_count() instead of len(search())
- Batch operations when possible
- Use proper indexes on database fields
- Avoid complex computed fields on tree views
- Use limit parameter for large datasets

## Code Quality
- Write clear, self-documenting code
- Use meaningful variable and method names
- Keep methods focused and under 50 lines
- Add docstrings for all methods
- Comment complex logic
- Follow DRY principle (Don't Repeat Yourself)
- Handle all edge cases
- Return proper values from methods

## Common Patterns
- Use @api.model for class methods
- Use @api.depends for computed fields
- Use @api.constrains for validations
- Use @api.onchange for UI updates
- Use context for passing parameters
- Use _rec_name for display names
- Use proper field naming (avoid 'x_' prefix for custom modules)
"""

    def _get_client_context(self):
        """Build client-specific context including GitHub code and ticket history."""
        partner = self.partner_id
        if not partner:
            return "No client information available."

        context_parts = [
            f"\n# CLIENT-SPECIFIC INFORMATION",
            f"\nClient: {partner.name}",
        ]

        # Add Odoo version info
        if partner.x_odoo_version:
            version_label = dict(partner._fields['x_odoo_version'].selection).get(
                partner.x_odoo_version, 'Unknown'
            )
            context_parts.append(f"Odoo Version: {version_label}")

        # Add custom modules
        if partner.x_custom_modules:
            context_parts.append(f"\nCustom Modules: {partner.x_custom_modules}")

        # Add configuration notes
        if partner.x_odoo_config_notes:
            context_parts.append(f"\nConfiguration Notes:\n{partner.x_odoo_config_notes}")

        # Fetch GitHub code if available
        if partner.x_github_repo and partner.x_github_token:
            github_code = self._fetch_client_github_code()
            if github_code:
                context_parts.append(f"\n# EXISTING CODE FROM GITHUB\n\n{github_code}")

        # Add ticket history
        ticket_history = self._get_client_ticket_history()
        if ticket_history:
            context_parts.append(f"\n# PAST RESOLVED TICKETS\n\n{ticket_history}")

        return '\n'.join(context_parts)

    def _fetch_client_github_code(self):
        """Fetch relevant code from client's GitHub repository."""
        partner = self.partner_id
        if not partner or not partner.x_github_repo or not partner.x_github_token:
            return ""

        try:
            from odoo.addons.claude_helpdesk_ai.lib.github_integration import GitHubIntegration

            github = GitHubIntegration(partner.x_github_repo, partner.x_github_token)

            # Detect affected module from ticket
            module_name = self._detect_affected_module()
            if not module_name:
                _logger.info('No module detected for ticket %s', self.id)
                return ""

            # Fetch module files
            module_files = github.get_odoo_module_files(
                module_name,
                partner.x_github_addons_path or 'addons'
            )

            if not module_files:
                _logger.warning(
                    'No files found for module %s in repo %s',
                    module_name, partner.x_github_repo
                )
                return ""

            # Build code context
            code_parts = [f"## Module: {module_name}\n"]

            for file_info in module_files[:20]:  # Limit to 20 files to avoid token limits
                file_path = file_info['path']
                content = file_info.get('content', '')

                if content:
                    code_parts.append(f"\n### File: {file_path}\n```python\n{content}\n```")

            return '\n'.join(code_parts)

        except Exception as e:
            _logger.error(
                'Failed to fetch GitHub code for ticket %s: %s',
                self.id, str(e), exc_info=True
            )
            return ""

    def _detect_affected_module(self):
        """Auto-detect affected module from ticket description or logs."""
        # First check if manually specified
        if self.x_affected_module:
            return self.x_affected_module.strip()

        # Search in description and error logs
        search_text = ' '.join(filter(None, [
            self.name or '',
            self.description or '',
            self.x_error_logs or '',
        ]))

        # Look for module patterns
        # Pattern 1: addons.module_name or odoo.addons.module_name
        pattern1 = r'(?:odoo\.)?addons\.([a-z_][a-z0-9_]*)'
        matches = re.findall(pattern1, search_text, re.IGNORECASE)
        if matches:
            module_name = matches[0]
            self.x_affected_module = module_name
            return module_name

        # Pattern 2: module names in custom modules list
        partner = self.partner_id
        if partner and partner.x_custom_modules:
            custom_modules = [m.strip() for m in partner.x_custom_modules.split(',')]
            for module in custom_modules:
                if module.lower() in search_text.lower():
                    self.x_affected_module = module
                    return module

        return None

    def _get_client_ticket_history(self):
        """Get history of past resolved tickets for this client."""
        partner = self.partner_id
        if not partner:
            return ""

        # Find resolved tickets with AI analysis
        # Use fold field for Odoo 19+ compatibility (is_close was renamed/removed)
        past_tickets = self.search([
            ('partner_id', '=', partner.id),
            ('x_ai_analyzed', '=', True),
            ('stage_id.fold', '=', True),
            ('id', '!=', self.id),
        ], limit=5, order='x_analysis_date desc')

        if not past_tickets:
            return ""

        history_parts = []
        for ticket in past_tickets:
            history_parts.append(f"""
## Ticket: {ticket.name}
Analysis Date: {ticket.x_analysis_date}

{ticket.x_claude_analysis or 'No analysis available'}
""")

        return '\n'.join(history_parts)

    def _call_claude_api(self, cached_context, api_key):
        """Call Claude API with prompt caching."""
        try:
            import anthropic
        except ImportError:
            raise UserError(_(
                'Python package "anthropic" is not installed. '
                'Please install it: pip install anthropic'
            ))

        # Build the ticket-specific prompt
        ticket_prompt = self._build_ticket_prompt()

        try:
            client = anthropic.Anthropic(api_key=api_key)

            # Create message with prompt caching
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.2,
                system=[
                    {
                        "type": "text",
                        "text": cached_context,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": ticket_prompt
                    }
                ]
            )

            # Extract response text
            response_text = message.content[0].text

            # Store raw response for debugging
            self.x_claude_analysis_json = json.dumps({
                'response': response_text,
                'usage': {
                    'input_tokens': message.usage.input_tokens,
                    'output_tokens': message.usage.output_tokens,
                    'cache_creation_tokens': getattr(message.usage, 'cache_creation_input_tokens', 0),
                    'cache_read_tokens': getattr(message.usage, 'cache_read_input_tokens', 0),
                }
            }, indent=2)

            # Parse JSON response
            response_dict = self._parse_claude_response(response_text)

            return response_dict

        except Exception as e:
            _logger.error('Claude API call failed: %s', str(e), exc_info=True)
            raise UserError(_(
                'Failed to call Claude API: %s\n\n'
                'Please check your API key and network connection.'
            ) % str(e))

    def _build_ticket_prompt(self):
        """Build the fresh (non-cached) ticket-specific prompt."""
        parts = [
            "# SUPPORT TICKET TO ANALYZE",
            f"\nTicket ID: {self.id}",
            f"Title: {self.name or 'No title'}",
            f"Customer: {self.partner_id.name if self.partner_id else 'Unknown'}",
        ]

        if self.description:
            parts.append(f"\nDescription:\n{self.description}")

        if self.x_error_logs:
            parts.append(f"\nError Logs:\n{self.x_error_logs}")

        if self.x_steps_to_reproduce:
            parts.append(f"\nSteps to Reproduce:\n{self.x_steps_to_reproduce}")

        if self.x_affected_module:
            parts.append(f"\nAffected Module: {self.x_affected_module}")

        parts.append("""

# YOUR TASK

Analyze this support ticket and provide a detailed solution. Return your response as valid JSON with this exact structure:

{
    "analysis": "Detailed root cause analysis of the issue",
    "solution_approach": "High-level description of the solution strategy",
    "code_changes": [
        {
            "file": "relative/path/to/file.py",
            "action": "modify",
            "content": "Complete file content after changes",
            "explanation": "Why this change is needed"
        }
    ],
    "testing_steps": "Step-by-step instructions for testing the fix",
    "estimated_hours": 2.5,
    "additional_notes": "Any warnings, considerations, or follow-up items"
}

IMPORTANT:
- Provide complete, production-ready code in the "content" field
- Include proper error handling and logging
- Follow Odoo best practices mentioned in the context
- If multiple files need changes, include all in the code_changes array
- Use "modify" action for existing files, "create" for new files
- Only propose changes that directly address the ticket issue
- Ensure all code is compatible with the client's Odoo version
""")

        return '\n'.join(parts)

    def _parse_claude_response(self, response_text):
        """Parse JSON from Claude response, handling markdown wrapping."""
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text.strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            _logger.error('Failed to parse Claude response as JSON: %s', str(e))
            _logger.debug('Response text: %s', response_text)
            raise UserError(_(
                'Failed to parse AI response. The response may not be valid JSON.\n\n'
                'Error: %s'
            ) % str(e))

    def _process_claude_response(self, response_dict):
        """Store Claude response results in ticket fields."""
        self.x_analysis_date = fields.Datetime.now()

        # Store proposed changes
        if response_dict.get('code_changes'):
            self.x_proposed_changes = json.dumps(
                response_dict['code_changes'],
                indent=2
            )

        # Store estimated hours
        if response_dict.get('estimated_hours'):
            self.x_estimated_hours = float(response_dict['estimated_hours'])

        # Format and store HTML analysis
        self.x_claude_analysis = self._format_analysis_html(response_dict)

    def _format_analysis_html(self, response_dict):
        """Format analysis results as HTML."""
        html_parts = [
            '<div style="font-family: Arial, sans-serif;">',
            '<h2>AI Analysis Results</h2>',
        ]

        if response_dict.get('analysis'):
            html_parts.append(
                f'<h3>Root Cause Analysis</h3>'
                f'<p>{self._escape_html(response_dict["analysis"])}</p>'
            )

        if response_dict.get('solution_approach'):
            html_parts.append(
                f'<h3>Solution Approach</h3>'
                f'<p>{self._escape_html(response_dict["solution_approach"])}</p>'
            )

        if response_dict.get('code_changes'):
            html_parts.append('<h3>Proposed Code Changes</h3>')
            for i, change in enumerate(response_dict['code_changes'], 1):
                html_parts.append(f"""
                    <div style="margin: 10px 0; padding: 10px; background: #f5f5f5; border-left: 3px solid #007bff;">
                        <strong>Change {i}: {self._escape_html(change.get('file', 'Unknown'))}</strong>
                        <br/>Action: {self._escape_html(change.get('action', 'modify'))}
                        <br/>Explanation: {self._escape_html(change.get('explanation', 'No explanation'))}
                    </div>
                """)

        if response_dict.get('testing_steps'):
            html_parts.append(
                f'<h3>Testing Steps</h3>'
                f'<pre>{self._escape_html(response_dict["testing_steps"])}</pre>'
            )

        if response_dict.get('estimated_hours'):
            html_parts.append(
                f'<p><strong>Estimated Hours:</strong> {response_dict["estimated_hours"]}</p>'
            )

        if response_dict.get('additional_notes'):
            html_parts.append(
                f'<h3>Additional Notes</h3>'
                f'<p>{self._escape_html(response_dict["additional_notes"])}</p>'
            )

        html_parts.append('</div>')

        return ''.join(html_parts)

    def _escape_html(self, text):
        """Escape HTML special characters and preserve newlines."""
        if not text:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace('\n', '<br/>')
        return text

    def _create_github_solution(self, response_dict):
        """Create GitHub branch and pull request with proposed solution."""
        self.ensure_one()

        partner = self.partner_id
        if not partner or not partner.x_github_repo or not partner.x_github_token:
            _logger.warning('Cannot create GitHub PR: missing configuration')
            return

        code_changes = response_dict.get('code_changes', [])
        if not code_changes:
            _logger.info('No code changes to commit for ticket %s', self.id)
            return

        try:
            from odoo.addons.claude_helpdesk_ai.lib.github_integration import GitHubIntegration

            github = GitHubIntegration(partner.x_github_repo, partner.x_github_token)

            # Create branch name
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            branch_prefix = partner.x_github_dev_branch_prefix or 'ai-fix/'
            branch_name = f"{branch_prefix}ticket-{self.id}-{timestamp}"

            # Create branch
            base_branch = partner.x_github_default_branch or 'main'
            github.create_branch(branch_name, from_branch=base_branch)
            self.x_github_branch = branch_name

            # Commit each file change
            for change in code_changes:
                file_path = change.get('file', '')
                content = change.get('content', '')
                action = change.get('action', 'modify')

                if not file_path or not content:
                    continue

                commit_message = f"[Ticket #{self.id}] {action.title()} {file_path}\n\n{change.get('explanation', '')}"

                github.create_or_update_file(
                    file_path=file_path,
                    content=content,
                    message=commit_message,
                    branch=branch_name
                )

            # Create pull request
            pr_title = f"Fix: {self.name} (Ticket #{self.id})"
            pr_body = self._format_pr_description(response_dict)

            pr_result = github.create_pull_request(
                title=pr_title,
                body=pr_body,
                head_branch=branch_name,
                base_branch=base_branch
            )

            if pr_result:
                self.x_github_pr_url = pr_result.get('html_url', '')
                self.x_github_pr_number = pr_result.get('number', 0)

                _logger.info(
                    'Created GitHub PR #%s for ticket %s',
                    self.x_github_pr_number, self.id
                )

        except Exception as e:
            _logger.error(
                'Failed to create GitHub solution for ticket %s: %s',
                self.id, str(e), exc_info=True
            )
            # Don't raise - just log the error

    def _format_pr_description(self, response_dict):
        """Format pull request body/description."""
        parts = [
            f"# Automated Fix for Ticket #{self.id}",
            f"\n**Ticket:** {self.name}",
            f"**Customer:** {self.partner_id.name if self.partner_id else 'Unknown'}",
            f"\n---\n",
        ]

        if response_dict.get('analysis'):
            parts.append(f"\n## Root Cause\n\n{response_dict['analysis']}")

        if response_dict.get('solution_approach'):
            parts.append(f"\n## Solution\n\n{response_dict['solution_approach']}")

        if response_dict.get('code_changes'):
            parts.append("\n## Changes Made\n")
            for change in response_dict['code_changes']:
                parts.append(
                    f"\n- **{change.get('action', 'modify').title()}** `{change.get('file', 'unknown')}`"
                    f"\n  {change.get('explanation', 'No explanation')}"
                )

        if response_dict.get('testing_steps'):
            parts.append(f"\n## Testing Steps\n\n{response_dict['testing_steps']}")

        if response_dict.get('additional_notes'):
            parts.append(f"\n## Additional Notes\n\n{response_dict['additional_notes']}")

        parts.append("\n---\n\n*This pull request was automatically generated by Claude AI Helpdesk Automation*")

        return '\n'.join(parts)

    def action_open_github_pr(self):
        """Open GitHub pull request in browser."""
        self.ensure_one()

        if not self.x_github_pr_url:
            raise UserError(_('No GitHub pull request URL available for this ticket.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.x_github_pr_url,
            'target': 'new',
        }
