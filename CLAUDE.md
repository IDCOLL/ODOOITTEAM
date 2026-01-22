# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Odoo ERP module repository** containing custom addons for Odoo 14-19. The primary module (`claude_helpdesk_ai`) integrates Claude AI with Odoo Helpdesk for automated ticket analysis and GitHub PR creation.

**Repository:** IDCOLL/ODOOITTEAM
**Branches:** `Prod` (production), `Staging_01092025` (current development)

## Modules

| Module | Purpose |
|--------|---------|
| `claude_helpdesk_ai` | AI-powered ticket analysis, code generation, GitHub PR creation |
| `contact_excel_export` | One-click contact export to Excel |
| `sale_custom_order_date` | Custom date field on sales orders |

## Development Commands

**No build system** - Odoo modules are installed via the Odoo UI.

### Dependencies
```bash
# Install Python dependencies (for local development)
pip install anthropic requests

# For Odoo.sh: requirements.txt in root is auto-detected
```

### Module Upgrade (after code changes)
```bash
# Via command line
./odoo-bin -d DATABASE -u module_name --stop-after-init

# Or via UI: Apps > Search module > Upgrade
```

### Debug Logging
```ini
# In odoo.conf
log_level = debug
```
Check logs for entries containing `claude_helpdesk_ai`.

## Architecture

### claude_helpdesk_ai Module

```
User clicks "Analyze with Claude AI" on helpdesk ticket
    ↓
helpdesk_ticket.action_analyze_with_claude()
    ↓
_perform_claude_analysis()
    ├── _build_cached_prompt()     # Universal guidelines + client context
    ├── _call_claude_api()         # API call with prompt caching
    ├── _process_claude_response() # Parse JSON, handle clarification requests
    └── _create_github_solution()  # Optional: create branch + PR
```

### Key Files

**Models (Business Logic):**
- `models/helpdesk_ticket.py` - Core analysis engine (~1,800 lines)
  - Extends `helpdesk.ticket` with AI analysis fields
  - Contains technology-specific guidelines (Odoo, Vue, React, Node, Python, Django, Flask)
  - Handles clarification workflow and feedback loop
- `models/res_partner.py` - Per-client GitHub/project configuration
- `models/res_config_settings.py` - Global Claude API settings

**Library:**
- `lib/github_integration.py` - GitHub API wrapper (repo access, file operations, PR creation)

**Views (UI):**
- `views/helpdesk_ticket_views.xml` - Ticket form buttons and tabs
- `views/res_partner_views.xml` - Client configuration tab

### Data Flow

1. **Ticket Analysis Request** → `action_analyze_with_claude()`
2. **Build Context** → Fetch code from GitHub, load client config, add tech guidelines
3. **Call Claude API** → With prompt caching (system context cached for 5 min)
4. **Process Response** → Either clarification request or solution with code changes
5. **Optional PR Creation** → Create branch, commit files, open PR

### Claude API Response Format

The AI returns JSON with this structure:
```json
{
    "needs_clarification": false,
    "analysis": "Root cause analysis...",
    "solution_approach": "Solution strategy...",
    "code_changes": [
        {"file": "path/to/file.py", "action": "modify", "content": "...", "explanation": "..."}
    ],
    "testing_steps": "How to test...",
    "estimated_hours": 2.5
}
```

Or for clarification:
```json
{
    "needs_clarification": true,
    "clarification_questions": "Questions for the user...",
    "partial_analysis": "What we understand so far..."
}
```

## Odoo-Specific Guidelines

### View Inheritance

Different Odoo models have different view structures. **Always verify xpath targets exist:**

**Views WITH `<header>` element:**
- sale.order, purchase.order, account.move, helpdesk.ticket, project.task, crm.lead

**Views WITHOUT `<header>` element:**
- res.partner, res.users, product.template - use `//div[hasclass('oe_button_box')]` or `//sheet` instead

### Common Patterns

```python
# Singleton operation
self.ensure_one()

# Computed field
x_field = fields.Boolean(compute='_compute_field', store=True)

@api.depends('other_field')
def _compute_field(self):
    for record in self:
        record.x_field = bool(record.other_field)

# Extend a model
class MyModel(models.Model):
    _inherit = 'existing.model'
```

### Field Naming
- Custom fields on existing models use `x_` prefix (e.g., `x_ai_analyzed`)
- New models in custom modules don't need prefix

## External Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| Claude API | AI analysis | Settings > Claude AI section (API key) |
| GitHub API | Code fetch, PR creation | Partner form > Claude AI & GitHub tab |

## Project Types Supported

The module detects project type from partner configuration:
- Odoo Module
- Vue.js Application
- React Application
- Node.js Backend
- Python/Django/Flask Application
- Full Stack (Multiple)

Each type loads technology-specific development guidelines into the AI prompt.
