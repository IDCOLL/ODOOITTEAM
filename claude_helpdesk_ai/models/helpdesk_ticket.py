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

    # Feedback Fields
    x_feedback_text = fields.Text(
        string='Feedback',
        help='Provide feedback if the AI solution did not work as expected'
    )
    x_feedback_status = fields.Selection([
        ('pending', 'Pending Review'),
        ('working', 'Fix Working'),
        ('not_working', 'Fix Not Working'),
        ('partial', 'Partially Working'),
    ], string='Fix Status', default=False,
        help='Status of the AI-proposed fix after testing'
    )
    x_feedback_date = fields.Datetime(
        string='Feedback Date',
        readonly=True,
        help='When feedback was last submitted'
    )
    x_reanalysis_count = fields.Integer(
        string='Re-analysis Count',
        default=0,
        readonly=True,
        help='Number of times this ticket has been re-analyzed based on feedback'
    )
    x_feedback_history = fields.Text(
        string='Feedback History',
        readonly=True,
        help='JSON array of all feedback submissions and re-analyses'
    )

    # Clarification Request Fields
    x_needs_clarification = fields.Boolean(
        string='Needs Clarification',
        default=False,
        help='Whether Claude AI needs more information before proceeding'
    )
    x_clarification_questions = fields.Text(
        string='Clarification Questions',
        readonly=True,
        help='Questions from Claude AI that need to be answered'
    )
    x_clarification_response = fields.Text(
        string='Clarification Response',
        help='Your answers to the clarification questions'
    )
    x_clarification_history = fields.Text(
        string='Clarification History',
        readonly=True,
        help='JSON array of all clarification Q&A exchanges'
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
    x_has_feedback = fields.Boolean(
        string='Has Feedback',
        compute='_compute_ai_status',
        store=True,
        help='Whether feedback has been submitted for this ticket'
    )

    @api.depends('x_claude_analysis', 'x_github_pr_url', 'x_feedback_status')
    def _compute_ai_status(self):
        """Compute AI analysis, PR creation, and feedback status."""
        for ticket in self:
            ticket.x_ai_analyzed = bool(ticket.x_claude_analysis)
            ticket.x_pr_created = bool(ticket.x_github_pr_url)
            ticket.x_has_feedback = bool(ticket.x_feedback_status)

    def action_analyze_with_claude(self):
        """Manual button action to trigger Claude AI analysis."""
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_('Please assign a customer to this ticket first.'))

        return self._perform_claude_analysis()

    def action_submit_clarification(self):
        """Submit clarification response and re-run analysis."""
        self.ensure_one()

        if not self.x_needs_clarification:
            raise UserError(_('No clarification is currently requested for this ticket.'))

        if not self.x_clarification_response:
            raise UserError(_(
                'Please provide your response to the clarification questions.'
            ))

        if not self.partner_id:
            raise UserError(_('Please assign a customer to this ticket first.'))

        # Record the clarification exchange in history
        self._record_clarification_history()

        # Clear the clarification state
        self.x_needs_clarification = False
        self.x_clarification_response = False

        # Re-run analysis with the new information
        return self._perform_claude_analysis()

    def _record_clarification_history(self):
        """Record the current clarification Q&A exchange in history."""
        history = []
        if self.x_clarification_history:
            try:
                history = json.loads(self.x_clarification_history)
            except (json.JSONDecodeError, TypeError):
                history = []

        # Add current exchange to history
        history.append({
            'date': fields.Datetime.now().isoformat(),
            'questions': self.x_clarification_questions or '',
            'response': self.x_clarification_response or '',
        })

        self.x_clarification_history = json.dumps(history, indent=2)

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

            # Check if clarification was requested
            if response_dict.get('needs_clarification'):
                _logger.info('Claude AI requested clarification for ticket %s', self.id)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Clarification Needed'),
                        'message': _('Claude AI needs more information. Please answer the questions and submit your response.'),
                        'type': 'warning',
                        'sticky': True,
                    }
                }

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
        partner = self.partner_id
        project_type = partner.x_project_type if partner else 'odoo'

        # Get universal context based on project type
        universal_context = self._get_universal_context()

        # Get client-specific context
        client_context = self._get_client_context()

        # Build role description based on project type
        role_descriptions = {
            'odoo': 'an expert Odoo developer',
            'vue': 'an expert Vue.js developer',
            'react': 'an expert React developer',
            'node': 'an expert Node.js backend developer',
            'python': 'an expert Python developer',
            'django': 'an expert Django developer',
            'flask': 'an expert Flask developer',
            'fullstack': 'an expert full-stack developer',
            'other': 'an expert software developer',
        }
        role = role_descriptions.get(project_type, 'an expert software developer')

        # Combine with cache control markers
        cached_prompt = f"""You are {role} analyzing a support ticket.

{universal_context}

{client_context}

Your task is to analyze support tickets and provide detailed solutions with code changes.
"""
        return cached_prompt

    def _get_universal_context(self):
        """Return universal best practices based on project type."""
        partner = self.partner_id
        project_type = partner.x_project_type if partner else 'odoo'

        # Return technology-specific guidelines
        if project_type == 'odoo':
            return self._get_odoo_guidelines()
        elif project_type == 'vue':
            return self._get_vue_guidelines()
        elif project_type == 'react':
            return self._get_react_guidelines()
        elif project_type == 'node':
            return self._get_node_guidelines()
        elif project_type in ('python', 'django', 'flask'):
            return self._get_python_guidelines(project_type)
        elif project_type == 'fullstack':
            return self._get_fullstack_guidelines()
        else:
            return self._get_general_guidelines()

    def _get_odoo_guidelines(self):
        """Return Odoo-specific development guidelines."""
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

## Module Structure Requirements
- static/description/index.html MUST be an HTML fragment, NOT a complete HTML document
- NEVER include <!DOCTYPE>, <html>, <head>, <meta>, or <body> tags in index.html
- Use Odoo's CSS classes: oe_container, oe_row, oe_spaced, oe_span6, oe_span12
- Use <section class="oe_container"> as the root elements
- Use <br/> for self-closing tags (XHTML style)
- Avoid special characters like & (use 'and' instead) or encode them properly

## View Inheritance - CRITICAL Knowledge
Different Odoo models have different view structures. Know which elements exist before using xpath:

### Views WITH <header> element (have status bar/workflow buttons):
- sale.order, purchase.order, account.move (invoices)
- helpdesk.ticket, project.task, crm.lead
- stock.picking, mrp.production
- hr.expense, hr.leave

### Views WITHOUT <header> element:
- res.partner (contacts) - use //div[hasclass('oe_button_box')] or //sheet instead
- res.users - use //sheet
- product.template, product.product - use //div[hasclass('oe_button_box')]
- res.company - no header

### Safe xpath targets that exist in most form views:
- //sheet - the main content area
- //div[hasclass('oe_button_box')] - smart buttons area (top right)
- //notebook - tab container (if present)
- //group - field groupings
- //field[@name='specific_field'] - target specific existing fields

### ALWAYS verify before using xpath:
1. Check the code context provided to see the actual view structure
2. If unsure, ask for clarification about available elements
3. Never assume a view has elements just because other views do
"""

    def _get_vue_guidelines(self):
        """Return Vue.js-specific development guidelines."""
        return """# VUE.JS DEVELOPMENT BEST PRACTICES

## Component Guidelines
- Use Composition API with <script setup> for Vue 3 projects
- Keep components small and focused (single responsibility)
- Use props for parent-to-child communication
- Use emits for child-to-parent communication
- Use provide/inject sparingly for deep prop drilling
- Prefer computed properties over methods for derived state
- Use v-model for two-way binding on form inputs

## State Management
- Use Pinia for global state management (Vue 3)
- Keep store modules focused and well-organized
- Use getters for derived state
- Use actions for async operations
- Avoid mutating state directly outside of actions/mutations

## Reactivity Best Practices
- Use ref() for primitive values, reactive() for objects
- Use computed() for derived reactive values
- Use watch() and watchEffect() appropriately
- Avoid destructuring reactive objects (loses reactivity)
- Use toRefs() when destructuring is needed

## Performance Optimization
- Use v-show vs v-if appropriately (v-show for frequent toggles)
- Use key attribute properly in v-for loops
- Lazy load routes and components
- Use shallowRef/shallowReactive when deep reactivity not needed
- Memoize expensive computations

## Code Organization
- Follow consistent file naming (PascalCase for components)
- Organize by feature/module, not by type
- Use index.ts/js for clean imports
- Keep composables in dedicated folders
- Separate concerns: components, composables, stores, utils

## TypeScript Integration
- Define proper interfaces for props and emits
- Use defineProps<T>() and defineEmits<T>() with types
- Type your store state and actions
- Avoid using 'any' type

## Testing
- Write unit tests for composables and utilities
- Write component tests for complex interactions
- Use data-testid attributes for test selectors
- Mock external dependencies properly
"""

    def _get_react_guidelines(self):
        """Return React-specific development guidelines."""
        return """# REACT DEVELOPMENT BEST PRACTICES

## Component Guidelines
- Use functional components with hooks
- Keep components small and focused
- Use props for component configuration
- Lift state up when needed for sharing
- Use composition over inheritance
- Implement proper error boundaries

## Hooks Best Practices
- Follow rules of hooks (top level, React functions only)
- Use useState for local component state
- Use useEffect for side effects with proper dependencies
- Use useCallback for memoized callbacks
- Use useMemo for expensive computations
- Create custom hooks for reusable logic

## State Management
- Use React Context for simple global state
- Consider Redux Toolkit or Zustand for complex state
- Keep state as local as possible
- Normalize complex nested state
- Use selectors for derived state

## Performance Optimization
- Use React.memo for expensive pure components
- Implement proper key props in lists
- Use code splitting with React.lazy
- Avoid inline function definitions in render
- Use virtualization for long lists

## Code Organization
- Follow consistent file naming conventions
- Organize by feature/module
- Separate presentational and container components
- Keep hooks in dedicated files
- Use barrel exports (index.ts)

## TypeScript Integration
- Define interfaces for props and state
- Use generic types for reusable components
- Type your hooks properly
- Avoid 'any' type usage

## Testing
- Write unit tests for utilities and hooks
- Use React Testing Library for component tests
- Test user interactions, not implementation
- Mock external dependencies properly
"""

    def _get_node_guidelines(self):
        """Return Node.js-specific development guidelines."""
        return """# NODE.JS BACKEND BEST PRACTICES

## Architecture Guidelines
- Follow layered architecture (routes, controllers, services, repositories)
- Use dependency injection for better testability
- Implement proper error handling middleware
- Use environment variables for configuration
- Follow 12-factor app principles

## API Design
- Follow RESTful conventions
- Use proper HTTP methods and status codes
- Implement consistent error responses
- Version your APIs
- Document with OpenAPI/Swagger

## Security Best Practices
- Validate and sanitize all inputs
- Use parameterized queries (prevent SQL injection)
- Implement proper authentication (JWT, sessions)
- Use HTTPS in production
- Set security headers (helmet)
- Implement rate limiting
- Handle CORS properly

## Error Handling
- Use async/await with try-catch
- Create custom error classes
- Implement global error handling middleware
- Log errors with context
- Never expose internal errors to clients

## Database Best Practices
- Use an ORM or query builder (Prisma, Knex, Sequelize)
- Implement proper migrations
- Use transactions for multi-step operations
- Index frequently queried columns
- Implement connection pooling

## Performance
- Use async operations properly
- Implement caching (Redis)
- Use streaming for large data
- Profile and optimize bottlenecks
- Use clustering for CPU-intensive tasks

## Code Quality
- Use TypeScript for type safety
- Follow consistent code style (ESLint, Prettier)
- Write meaningful tests
- Document complex logic
- Keep functions small and focused
"""

    def _get_python_guidelines(self, project_type):
        """Return Python/Django/Flask-specific guidelines."""
        base = """# PYTHON DEVELOPMENT BEST PRACTICES

## Code Quality
- Follow PEP 8 style guide
- Use type hints for function signatures
- Write docstrings for modules, classes, and functions
- Keep functions focused and under 50 lines
- Use meaningful variable and function names
- Follow DRY principle

## Error Handling
- Use specific exception types
- Implement proper try-except blocks
- Log errors with context
- Create custom exceptions when needed
- Never catch bare exceptions

## Security
- Validate and sanitize all inputs
- Use parameterized queries
- Never store passwords in plain text
- Use environment variables for secrets
- Implement proper authentication
"""

        if project_type == 'django':
            base += """
## DJANGO-SPECIFIC GUIDELINES

## Model Best Practices
- Use appropriate field types
- Add indexes for frequently queried fields
- Use select_related and prefetch_related
- Implement __str__ methods
- Use model managers for complex queries

## View Best Practices
- Use class-based views when appropriate
- Implement proper permission classes
- Use serializers for validation (DRF)
- Keep views thin, logic in services

## Security
- Use Django's built-in protections (CSRF, XSS)
- Implement proper authentication
- Use permission classes
- Validate file uploads

## Testing
- Use Django's test client
- Write model, view, and integration tests
- Use factories for test data
- Test permissions and edge cases
"""
        elif project_type == 'flask':
            base += """
## FLASK-SPECIFIC GUIDELINES

## Application Structure
- Use application factory pattern
- Organize with blueprints
- Use Flask extensions appropriately
- Implement proper configuration management

## Request Handling
- Use request context properly
- Implement input validation
- Return consistent response formats
- Use proper HTTP status codes

## Database
- Use Flask-SQLAlchemy or similar ORM
- Implement database migrations (Flask-Migrate)
- Use connection pooling
- Handle sessions properly

## Security
- Use Flask-Login for authentication
- Implement CSRF protection
- Validate all inputs
- Set secure cookie flags
"""

        return base

    def _get_fullstack_guidelines(self):
        """Return guidelines for full-stack applications."""
        return """# FULL-STACK DEVELOPMENT BEST PRACTICES

## Architecture
- Separate frontend and backend clearly
- Use API contracts (OpenAPI/GraphQL schema)
- Implement proper authentication flow
- Handle errors consistently across stack

## Frontend Guidelines
- Use modern framework best practices
- Implement proper state management
- Handle loading and error states
- Optimize for performance

## Backend Guidelines
- Follow RESTful or GraphQL conventions
- Implement proper validation
- Use appropriate HTTP status codes
- Document your APIs

## Security
- Implement proper authentication (JWT, sessions)
- Validate inputs on both frontend and backend
- Use HTTPS in production
- Handle CORS properly
- Protect against common vulnerabilities (XSS, CSRF, SQL injection)

## Database
- Use appropriate database for your needs
- Implement proper migrations
- Optimize queries
- Use transactions where needed

## Testing
- Write unit tests for both frontend and backend
- Implement integration tests
- Use E2E tests for critical flows
- Mock external dependencies

## Deployment
- Use environment variables for configuration
- Implement CI/CD pipelines
- Use containerization when appropriate
- Monitor application health
"""

    def _get_general_guidelines(self):
        """Return general software development guidelines."""
        return """# SOFTWARE DEVELOPMENT BEST PRACTICES

## Code Quality
- Write clean, readable code
- Follow consistent naming conventions
- Keep functions/methods small and focused
- Use meaningful names for variables and functions
- Comment complex logic
- Follow DRY principle

## Error Handling
- Handle errors gracefully
- Log errors with context
- Provide meaningful error messages
- Never expose internal errors to users

## Security
- Validate all inputs
- Use parameterized queries for databases
- Implement proper authentication
- Follow principle of least privilege
- Keep dependencies updated

## Testing
- Write unit tests for critical logic
- Implement integration tests
- Test edge cases
- Mock external dependencies

## Documentation
- Document APIs and interfaces
- Keep README updated
- Document complex algorithms
- Use inline comments sparingly but effectively
"""

    def _get_client_context(self):
        """Build client-specific context including GitHub code and ticket history."""
        partner = self.partner_id
        if not partner:
            return "No client information available."

        project_type = partner.x_project_type or 'odoo'

        context_parts = [
            f"\n# CLIENT-SPECIFIC INFORMATION",
            f"\nClient: {partner.name}",
            f"Project Type: {dict(partner._fields['x_project_type'].selection).get(project_type, 'Unknown')}",
        ]

        # Add project-type specific information
        if project_type == 'odoo':
            # Odoo-specific context
            if partner.x_odoo_version:
                version_label = dict(partner._fields['x_odoo_version'].selection).get(
                    partner.x_odoo_version, 'Unknown'
                )
                context_parts.append(f"Odoo Version: {version_label}")

            if partner.x_custom_modules:
                context_parts.append(f"\nCustom Modules: {partner.x_custom_modules}")

            if partner.x_odoo_config_notes:
                context_parts.append(f"\nConfiguration Notes:\n{partner.x_odoo_config_notes}")
        else:
            # Custom app context
            if partner.x_app_framework_version:
                context_parts.append(f"Framework Version: {partner.x_app_framework_version}")

            if partner.x_app_tech_stack:
                context_parts.append(f"\n## Technology Stack:\n{partner.x_app_tech_stack}")

            if partner.x_app_architecture_notes:
                context_parts.append(f"\n## Architecture Notes:\n{partner.x_app_architecture_notes}")

            if partner.x_app_build_commands:
                context_parts.append(f"\n## Build/Run Commands:\n```\n{partner.x_app_build_commands}\n```")

            if partner.x_app_test_commands:
                context_parts.append(f"\n## Test Commands:\n```\n{partner.x_app_test_commands}\n```")

            if partner.x_app_key_files:
                context_parts.append(f"\n## Key Files/Directories:\n{partner.x_app_key_files}")

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

        project_type = partner.x_project_type or 'odoo'

        try:
            from odoo.addons.claude_helpdesk_ai.lib.github_integration import GitHubIntegration

            github = GitHubIntegration(partner.x_github_repo, partner.x_github_token)

            if project_type == 'odoo':
                return self._fetch_odoo_module_code(github)
            else:
                return self._fetch_custom_app_code(github)

        except Exception as e:
            _logger.error(
                'Failed to fetch GitHub code for ticket %s: %s',
                self.id, str(e), exc_info=True
            )
            return ""

    def _fetch_odoo_module_code(self, github):
        """Fetch Odoo module code from GitHub."""
        partner = self.partner_id

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

    def _fetch_custom_app_code(self, github):
        """Fetch custom app code from GitHub based on key files or source path."""
        partner = self.partner_id
        project_type = partner.x_project_type or 'other'

        # Determine file extensions based on project type
        file_extensions = self._get_file_extensions_for_project(project_type)

        # Get source path
        source_path = partner.x_github_source_path or 'src'

        # Try to fetch files from the source directory
        try:
            app_files = github.get_app_files(
                source_path,
                file_extensions,
                max_files=25
            )

            if not app_files:
                # Try root directory if source path doesn't work
                app_files = github.get_app_files(
                    '',
                    file_extensions,
                    max_files=25
                )

            if not app_files:
                _logger.warning(
                    'No files found in repo %s for project type %s',
                    partner.x_github_repo, project_type
                )
                return ""

            # Build code context
            code_parts = [f"## Application Source Code\n"]

            for file_info in app_files:
                file_path = file_info['path']
                content = file_info.get('content', '')

                if content:
                    # Determine language for syntax highlighting
                    lang = self._get_language_for_file(file_path)
                    code_parts.append(f"\n### File: {file_path}\n```{lang}\n{content}\n```")

            return '\n'.join(code_parts)

        except Exception as e:
            _logger.error('Failed to fetch custom app code: %s', str(e))
            return ""

    def _get_file_extensions_for_project(self, project_type):
        """Return relevant file extensions for each project type."""
        extensions_map = {
            'vue': ['.vue', '.ts', '.js', '.json'],
            'react': ['.tsx', '.jsx', '.ts', '.js', '.json'],
            'node': ['.ts', '.js', '.json'],
            'python': ['.py', '.json', '.yaml', '.yml'],
            'django': ['.py', '.html', '.json', '.yaml'],
            'flask': ['.py', '.html', '.json', '.yaml'],
            'fullstack': ['.vue', '.tsx', '.jsx', '.ts', '.js', '.py', '.json'],
            'other': ['.py', '.js', '.ts', '.json', '.yaml'],
        }
        return extensions_map.get(project_type, extensions_map['other'])

    def _get_language_for_file(self, file_path):
        """Determine programming language from file extension."""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.vue': 'vue',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sql': 'sql',
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return 'text'

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

        # Include any previous clarification Q&A
        if self.x_clarification_history:
            try:
                history = json.loads(self.x_clarification_history)
                if history:
                    parts.append("\n# PREVIOUS CLARIFICATION EXCHANGES:")
                    for i, exchange in enumerate(history, 1):
                        parts.append(f"\n## Clarification {i}:")
                        parts.append(f"Questions Asked:\n{exchange.get('questions', '')}")
                        parts.append(f"Answers Provided:\n{exchange.get('response', '')}")
            except (json.JSONDecodeError, TypeError):
                pass

        parts.append("""

# YOUR TASK

Analyze this support ticket. You have TWO options:

## OPTION 1: Request Clarification (if needed)
If the ticket lacks essential information to provide a proper solution, you can ask for clarification.
Return JSON with this structure:

{
    "needs_clarification": true,
    "clarification_questions": "Your questions here. Be specific about what information you need:\\n1. Question 1\\n2. Question 2\\n3. Question 3",
    "partial_analysis": "What you understand so far and why you need more information"
}

Use this option when:
- The problem description is vague or unclear
- You need specific error messages, logs, or stack traces
- You need to know which specific feature/module/component is affected
- The expected vs actual behavior is not clearly described
- You need environment details (versions, configurations)
- Steps to reproduce are missing or incomplete

## OPTION 2: Provide Solution (if you have enough information)
If you have sufficient information, provide a complete solution.
Return JSON with this structure:

{
    "needs_clarification": false,
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

IMPORTANT GUIDELINES:
- Always include "needs_clarification" field (true or false)
- If requesting clarification, ask specific, actionable questions
- If providing solution, include complete, production-ready code
- Include proper error handling and logging in code
- Follow best practices mentioned in the context
- If multiple files need changes, include all in the code_changes array
- Use "modify" action for existing files, "create" for new files
- Only propose changes that directly address the ticket issue

## CRITICAL: VALIDATION REQUIREMENTS

Before proposing any code changes, you MUST verify that referenced elements exist:

### For Odoo XML Views:
1. **XPath expressions**: Only use xpath expressions that target elements that ACTUALLY EXIST in the parent view:
   - `//header` - ONLY exists in views with status bar (sale.order, helpdesk.ticket, etc.) - NOT in res.partner form
   - `//div[hasclass('oe_button_box')]` - exists in most form views with smart buttons
   - `//sheet` - exists in most form views
   - `//notebook` - only if the parent view has a notebook element
   - `//field[@name='field_name']` - only if that field exists in the parent view

2. **Common mistakes to AVOID**:
   - Do NOT use `//header` on res.partner form view (it doesn't have one)
   - Do NOT reference fields that don't exist on the model
   - Do NOT use xpath on elements that are not in the inherited view

3. **When unsure about view structure**: Request clarification asking for the current view XML structure

### For Odoo Python Models:
1. **Field references**: Only reference fields that exist on the model or its parent models
2. **Method calls**: Verify methods exist before calling them (e.g., ensure_one(), search(), etc.)
3. **Inheritance**: When using _inherit, verify the parent model exists and has the expected fields

### For Any Framework:
1. **Imports**: Only import modules/components that exist in the project
2. **API calls**: Verify endpoint paths and method signatures match the existing codebase
3. **File paths**: Use paths that match the project's actual directory structure

### If you cannot verify an element exists:
- Ask for clarification about the current structure
- Request the user to provide the existing file/view content
- Do NOT assume or guess about structure

REMEMBER: It's better to ask for clarification than to propose changes that will fail because they reference non-existent elements.
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

        # Check if Claude is requesting clarification
        if response_dict.get('needs_clarification'):
            self.x_needs_clarification = True
            self.x_clarification_questions = response_dict.get('clarification_questions', '')

            # Store partial analysis if provided
            partial = response_dict.get('partial_analysis', '')
            if partial:
                self.x_claude_analysis = self._format_clarification_html(response_dict)

            # Don't set code changes or estimated hours for clarification requests
            return

        # Claude provided a solution - clear any previous clarification state
        self.x_needs_clarification = False
        self.x_clarification_questions = False

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

    def _format_clarification_html(self, response_dict):
        """Format clarification request as HTML."""
        html_parts = [
            '<div style="font-family: Arial, sans-serif;">',
            '<h2 style="color: #856404;">Clarification Needed</h2>',
            '<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin-bottom: 15px;">',
            '<p><strong>Claude AI needs more information before proceeding.</strong></p>',
            '</div>',
        ]

        if response_dict.get('partial_analysis'):
            html_parts.append(
                f'<h3>Initial Assessment</h3>'
                f'<p>{self._escape_html(response_dict["partial_analysis"])}</p>'
            )

        if response_dict.get('clarification_questions'):
            html_parts.append(
                f'<h3>Questions</h3>'
                f'<div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">'
                f'<p>{self._escape_html(response_dict["clarification_questions"])}</p>'
                f'</div>'
            )

        html_parts.append(
            '<p style="margin-top: 15px;"><em>Please answer the questions above in the "Clarification Response" field below, then click "Submit Clarification".</em></p>'
        )
        html_parts.append('</div>')

        return ''.join(html_parts)

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

    def action_create_github_pr(self):
        """Manually create GitHub PR from analyzed ticket."""
        self.ensure_one()

        if not self.x_ai_analyzed:
            raise UserError(_('Please analyze the ticket with Claude AI first.'))

        if self.x_github_pr_url:
            raise UserError(_('A pull request already exists for this ticket.'))

        if not self.x_proposed_changes:
            raise UserError(_('No code changes were proposed in the analysis.'))

        partner = self.partner_id
        if not partner:
            raise UserError(_('No customer assigned to this ticket.'))

        if not partner.x_github_repo or not partner.x_github_token:
            raise UserError(_('GitHub repository and token must be configured for the customer.'))

        # Parse the proposed changes
        try:
            response_dict = {'code_changes': json.loads(self.x_proposed_changes)}
        except (json.JSONDecodeError, TypeError):
            raise UserError(_('Could not parse proposed code changes. Please re-analyze the ticket.'))

        if not response_dict.get('code_changes'):
            raise UserError(_('No valid code changes found in the analysis.'))

        # Add analysis info to response dict for PR description
        if self.x_claude_analysis_json:
            try:
                full_response = json.loads(self.x_claude_analysis_json)
                response_dict.update({
                    'analysis': full_response.get('analysis', ''),
                    'solution_approach': full_response.get('solution_approach', ''),
                    'testing_steps': full_response.get('testing_steps', ''),
                    'additional_notes': full_response.get('additional_notes', ''),
                })
            except (json.JSONDecodeError, TypeError):
                pass

        # Create the GitHub solution
        self._create_github_solution(response_dict)

        if self.x_github_pr_url:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Pull request created successfully!'),
                    'type': 'success',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_url',
                        'url': self.x_github_pr_url,
                        'target': 'new',
                    }
                }
            }
        else:
            raise UserError(_('Failed to create pull request. Check the logs for details.'))

    def action_submit_feedback(self):
        """Submit feedback about the AI fix and optionally re-analyze."""
        self.ensure_one()

        if not self.x_ai_analyzed:
            raise UserError(_('No AI analysis exists for this ticket yet.'))

        if not self.x_feedback_status:
            raise UserError(_('Please select a fix status before submitting feedback.'))

        # Record feedback in history
        self._record_feedback_history()

        # Update feedback date
        self.x_feedback_date = fields.Datetime.now()

        # If fix is not working or partial, offer to re-analyze
        if self.x_feedback_status in ('not_working', 'partial'):
            if not self.x_feedback_text:
                raise UserError(_(
                    'Please provide feedback details explaining what went wrong '
                    'so Claude can provide an improved solution.'
                ))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Feedback Recorded'),
                    'message': _('Your feedback has been saved. Click "Re-analyze with Feedback" to get an improved solution.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Fix is working - just confirm
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Feedback Recorded'),
                'message': _('Thank you for confirming the fix is working!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reanalyze_with_feedback(self):
        """Re-analyze ticket with Claude, including previous feedback."""
        self.ensure_one()

        if not self.x_ai_analyzed:
            raise UserError(_('Please analyze the ticket first before requesting a re-analysis.'))

        if not self.x_feedback_text:
            raise UserError(_(
                'Please provide feedback explaining what went wrong with the previous solution.'
            ))

        if not self.partner_id:
            raise UserError(_('Please assign a customer to this ticket first.'))

        _logger.info('Starting Claude AI re-analysis with feedback for ticket %s', self.id)

        # Validate configuration
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'claude_helpdesk_ai.api_key'
        )
        if not api_key:
            raise UserError(_(
                'Claude API key not configured. '
                'Please set system parameter: claude_helpdesk_ai.api_key'
            ))

        try:
            # Build cached context (universal + client-specific)
            cached_context = self._build_cached_prompt()

            # Call Claude API with feedback context
            response_dict = self._call_claude_api_with_feedback(cached_context, api_key)

            # Process and store response
            self._process_claude_response(response_dict)

            # Increment re-analysis count
            self.x_reanalysis_count += 1

            # Clear feedback text for next iteration (status remains)
            self.x_feedback_text = False

            # Reset GitHub PR fields for new solution
            self.x_github_branch = False
            self.x_github_pr_url = False
            self.x_github_pr_number = False

            _logger.info('Claude AI re-analysis completed for ticket %s', self.id)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Re-analysis Complete'),
                    'message': _('Claude AI has provided an updated solution based on your feedback.'),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(
                'Claude AI re-analysis failed for ticket %s: %s',
                self.id, str(e), exc_info=True
            )
            raise UserError(_(
                'Re-analysis failed: %s\n\n'
                'Please check the logs for details.'
            ) % str(e))

    def _call_claude_api_with_feedback(self, cached_context, api_key):
        """Call Claude API with feedback context for re-analysis."""
        try:
            import anthropic
        except ImportError:
            raise UserError(_(
                'Python package "anthropic" is not installed. '
                'Please install it: pip install anthropic'
            ))

        # Build the ticket prompt with feedback
        ticket_prompt = self._build_ticket_prompt_with_feedback()

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
                },
                'is_reanalysis': True,
                'reanalysis_count': self.x_reanalysis_count + 1,
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

    def _build_ticket_prompt_with_feedback(self):
        """Build ticket prompt including previous analysis and feedback."""
        parts = [
            "# SUPPORT TICKET RE-ANALYSIS REQUEST",
            f"\nTicket ID: {self.id}",
            f"Title: {self.name or 'No title'}",
            f"Customer: {self.partner_id.name if self.partner_id else 'Unknown'}",
            f"\nThis ticket has been analyzed {self.x_reanalysis_count + 1} time(s) previously.",
        ]

        if self.description:
            parts.append(f"\n## Original Description:\n{self.description}")

        if self.x_error_logs:
            parts.append(f"\n## Error Logs:\n{self.x_error_logs}")

        if self.x_steps_to_reproduce:
            parts.append(f"\n## Steps to Reproduce:\n{self.x_steps_to_reproduce}")

        if self.x_affected_module:
            parts.append(f"\n## Affected Module: {self.x_affected_module}")

        # Add previous analysis
        parts.append("\n## PREVIOUS AI ANALYSIS (DID NOT WORK):")
        if self.x_claude_analysis_json:
            try:
                prev_response = json.loads(self.x_claude_analysis_json)
                prev_analysis = prev_response.get('response', '')
                if prev_analysis:
                    # Truncate if too long
                    if len(prev_analysis) > 4000:
                        prev_analysis = prev_analysis[:4000] + "\n... (truncated)"
                    parts.append(prev_analysis)
            except (json.JSONDecodeError, TypeError):
                parts.append(str(self.x_claude_analysis or 'Previous analysis not available'))

        # Add user feedback
        parts.append(f"\n## USER FEEDBACK ON PREVIOUS SOLUTION:")
        parts.append(f"Status: {dict(self._fields['x_feedback_status'].selection).get(self.x_feedback_status, 'Unknown')}")
        parts.append(f"\nFeedback Details:\n{self.x_feedback_text}")

        # Add feedback history if available
        if self.x_feedback_history:
            try:
                history = json.loads(self.x_feedback_history)
                if len(history) > 1:  # More than just current feedback
                    parts.append("\n## FEEDBACK HISTORY (Previous iterations):")
                    for i, entry in enumerate(history[:-1], 1):  # Exclude current
                        parts.append(f"\nIteration {i}:")
                        parts.append(f"- Status: {entry.get('status', 'Unknown')}")
                        parts.append(f"- Feedback: {entry.get('feedback', 'No feedback')}")
            except (json.JSONDecodeError, TypeError):
                pass

        parts.append("""

# YOUR TASK

The previous solution did NOT work. Based on the user's feedback, provide a REVISED solution.

IMPORTANT:
- Carefully analyze what went wrong with the previous solution
- Address the specific issues mentioned in the user feedback
- Provide a different approach if the previous one was fundamentally flawed
- Do not repeat the same mistakes

Return your response as valid JSON with this exact structure:

{
    "analysis": "Analysis of what went wrong and the revised root cause",
    "solution_approach": "New/revised solution strategy addressing the feedback",
    "code_changes": [
        {
            "file": "relative/path/to/file.py",
            "action": "modify",
            "content": "Complete file content after changes",
            "explanation": "Why this change fixes the issue (addressing feedback)"
        }
    ],
    "testing_steps": "Step-by-step instructions for testing the revised fix",
    "estimated_hours": 2.5,
    "additional_notes": "What was wrong before and how this solution differs",
    "feedback_addressed": "Specific explanation of how each feedback point was addressed"
}
""")

        return '\n'.join(parts)

    def _record_feedback_history(self):
        """Record current feedback in the history."""
        history = []
        if self.x_feedback_history:
            try:
                history = json.loads(self.x_feedback_history)
            except (json.JSONDecodeError, TypeError):
                history = []

        # Add current feedback to history
        history.append({
            'date': fields.Datetime.now().isoformat(),
            'status': self.x_feedback_status,
            'feedback': self.x_feedback_text or '',
            'reanalysis_count': self.x_reanalysis_count,
        })

        self.x_feedback_history = json.dumps(history, indent=2)

    def action_mark_fix_working(self):
        """Quick action to mark fix as working."""
        self.ensure_one()
        self.x_feedback_status = 'working'
        self.x_feedback_date = fields.Datetime.now()
        self._record_feedback_history()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Fix marked as working. Thank you for your feedback!'),
                'type': 'success',
                'sticky': False,
            }
        }
