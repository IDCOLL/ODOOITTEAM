# Claude AI Helpdesk Automation

**Transform your Odoo helpdesk with AI-powered ticket analysis and automated code fixes**

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-14%20|%2015%20|%2016%20|%2017%20|%2018%20|%2019-purple.svg)](https://www.odoo.com)

---

## Overview

This Odoo module integrates Anthropic's Claude AI with Odoo Helpdesk to revolutionize your support workflow:

- **Analyze** support tickets automatically to identify root causes
- **Propose** complete code solutions based on your GitHub codebase
- **Create** GitHub pull requests with ready-to-review fixes
- **Track** analysis history and success metrics per client
- **Optimize** costs using Claude's prompt caching feature

Perfect for MSPs, software agencies, and in-house teams managing multiple Odoo instances.

---

## Features

### Intelligent Ticket Analysis
- Analyzes ticket descriptions, error logs, and reproduction steps
- Identifies root causes using advanced reasoning
- Provides step-by-step solution approaches
- Estimates development hours for fixes

### Smart Module Detection
- Automatically detects affected Odoo modules from ticket content
- Searches error logs for module patterns
- Cross-references with client's custom module list

### Code Generation
- Fetches existing code from GitHub repository
- Generates complete, production-ready code changes
- Follows Odoo best practices and coding conventions
- Provides file-by-file changes with explanations

### GitHub Integration
- Tests repository connection before use
- Creates feature branches automatically
- Commits code changes with descriptive messages
- Opens pull requests with formatted descriptions

### Multi-Client Support
- Configure different GitHub repos per client
- Track Odoo version and custom modules per client
- Store client-specific configuration notes
- Separate analytics for each client

### Cost Optimization
- Implements prompt caching (90% cost reduction on cached tokens)
- Caches universal Odoo best practices
- Caches client-specific code and configuration
- Only fresh ticket data sent with each request

---

## Requirements

### Odoo
- **Version:** 14.0, 15.0, 16.0, 17.0, 18.0, or 19.0
- **Modules:** `base`, `helpdesk`, `mail`

### Python Dependencies
- `anthropic` (Claude API client)
- `requests` (HTTP library)

### External Services
- **Claude API:** Anthropic API key
  - Sign up at: https://console.anthropic.com
  - Default model: `claude-sonnet-4-20250514`

- **GitHub:** Personal Access Token with repository permissions
  - Generate at: https://github.com/settings/tokens
  - Required scopes: `repo` (full repository access)

---

## Installation

### Odoo.sh Deployment

1. **Add Python dependencies**

   Create or update `requirements.txt` in your repository root:

   ```txt
   anthropic>=0.18.0
   requests>=2.31.0
   ```

2. **Add the module to your repository**

   ```bash
   git add requirements.txt
   git add claude_helpdesk_ai/
   git commit -m "Add Claude AI Helpdesk Automation module"
   git push
   ```

3. **Wait for build**
   - Odoo.sh automatically detects the changes
   - Build process starts automatically
   - Python dependencies are installed during build
   - Check build logs in the Odoo.sh dashboard for any errors

4. **Install the module**
   - Login to your Odoo.sh instance
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "Claude AI Helpdesk Automation"
   - Click **Install**

5. **Configure** (see Configuration section below)

### Self-Hosted Deployment

1. **Install Python dependencies**

   ```bash
   pip install anthropic requests
   ```

   Or with a virtual environment:

   ```bash
   source /path/to/odoo/venv/bin/activate
   pip install anthropic requests
   ```

2. **Install the module**

   Copy `claude_helpdesk_ai` to your Odoo addons path:

   ```bash
   cp -r claude_helpdesk_ai /path/to/odoo/addons/
   ```

3. **Restart Odoo**

   ```bash
   sudo systemctl restart odoo
   ```

4. **Install from Odoo**
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "Claude AI Helpdesk Automation"
   - Click **Install**

5. **Configure** (see Configuration section below)

---

## Configuration

### Step 1: Configure Claude API Key

The API key is configured through Odoo's Settings page:

1. Go to **Settings** (main Odoo settings)
2. Scroll down to find the **Claude AI** section
3. Enter your Claude API key (starts with `sk-ant-`)
4. Optionally adjust the model and max tokens settings
5. Click **Save**

**Note:** The Claude AI settings section is only visible to users in the System Administrator group.

**Available Settings:**

| Setting | Default | Description |
|---------|---------|-------------|
| Claude API Key | (required) | Your Anthropic API key |
| Claude Model | `claude-sonnet-4-20250514` | The Claude model to use |
| Max Tokens | 8192 | Maximum response tokens |

### Step 2: Configure Clients (Per-Customer GitHub Setup)

Each client/customer needs individual configuration for GitHub integration.

1. Go to **Helpdesk > Configuration > Claude AI Configuration**
2. Select a customer/partner
3. Open the **Claude AI & GitHub** tab

**GitHub Configuration:**

| Field | Description | Example |
|-------|-------------|---------|
| GitHub Repository URL | Full URL to client's repo | `https://github.com/company/odoo-custom` |
| GitHub Personal Access Token | PAT with repo permissions | `ghp_xxxxxxxxxxxx` |
| Default Branch | Main branch for PRs | `main` or `master` |
| Dev Branch Prefix | Prefix for auto-created branches | `ai-fix/` |
| Addons Path in Repo | Path to addons directory | `addons` or `custom_addons` |

After filling these fields, click **Test Connection** to verify GitHub access.

**Odoo Environment:**

| Field | Description | Example |
|-------|-------------|---------|
| Odoo Version | Client's Odoo version | Select 14-19 |
| Custom Modules | Comma-separated module names | `custom_sales, custom_crm` |
| Configuration Notes | Additional environment details | Architecture notes, etc. |

**AI Settings:**

| Field | Default | Description |
|-------|---------|-------------|
| Enable Auto-Analysis | Disabled | Analyze tickets on creation |
| Auto-Create Pull Requests | Disabled | Create PRs automatically |

**Warning:** Auto-create PR will commit code changes without human review. Use with caution.

---

## Usage

### Manual Ticket Analysis (Recommended)

1. **Create or open a ticket**
   - Go to **Helpdesk > Tickets**
   - Ensure the customer has GitHub configuration

2. **Fill technical details**
   - Open the **Technical Details** tab
   - Add error logs, steps to reproduce
   - Optionally specify the affected module

3. **Trigger analysis**
   - Click **Analyze with Claude AI** button
   - Wait for analysis (10-30 seconds)

4. **Review results**
   - Open the **AI Analysis & Code** tab
   - Review: Analysis, estimated hours, proposed code changes
   - If a PR was created, click **Open Pull Request** to review in GitHub

### Automatic Analysis (Optional)

For high-volume environments:

1. Enable **Enable Auto-Analysis** on the customer's partner record
2. Activate the automation rule:
   - Go to **Settings > Technical > Automation > Automated Actions**
   - Find "Claude AI: Auto-Analyze New Tickets"
   - Enable the rule

Tickets will be analyzed automatically when created for customers with auto-analysis enabled.

### Filtering Tickets

Use these filters in the ticket list:
- **AI Analyzed:** Show analyzed tickets
- **PR Created:** Show tickets with GitHub PRs
- **Not Analyzed:** Show pending tickets

---

## Cost Optimization

The module uses prompt caching to reduce Claude API costs by up to 90%.

### How It Works

1. **Cached Context (90% cost reduction):**
   - Odoo development best practices
   - Client-specific code from GitHub
   - Configuration and past ticket context
   - Cache duration: 5 minutes

2. **Fresh Data (Full cost):**
   - Current ticket details
   - Error logs and reproduction steps

### Estimated Costs

| Scenario | Cost per Ticket |
|----------|-----------------|
| First request (cold cache) | ~$0.10 |
| Subsequent requests (warm cache) | ~$0.01-0.02 |

**Tip:** Analyze multiple tickets for the same module within 5 minutes to maximize cache hits.

---

## Troubleshooting

### "Claude API key not configured"

1. Go to **Settings** (main Odoo settings)
2. Scroll to the **Claude AI** section
3. Enter your API key and save

### "Connection failed" when testing GitHub

- Verify repository URL format: `https://github.com/owner/repo`
- Generate a new token at https://github.com/settings/tokens
- Ensure token has `repo` scope
- Check token hasn't expired

### "No module detected for ticket"

- Manually set **Affected Module** in the Technical Details tab
- Include module name in ticket description
- Add module to client's **Custom Modules** list

### "Failed to fetch GitHub code"

- Verify module exists at `{addons_path}/{module_name}` in the repo
- Check **Addons Path in Repo** setting
- Ensure default branch name is correct

### Dependencies not installed (Odoo.sh)

- Ensure `requirements.txt` is in the repository root (not a subdirectory)
- Check the file uses Unix line endings (LF, not CRLF)
- Review Odoo.sh build logs for errors

### Module not appearing

- Verify module is in a recognized addons path
- Restart the Odoo instance
- Click **Update Apps List** in the Apps menu
- Check server logs for errors

### Debug logging

Enable detailed logging in `odoo.conf`:

```ini
log_level = debug
```

Then check logs for entries containing `claude_helpdesk_ai`.

---

## Security

### API Key Protection

- Claude API key is stored in `ir.config_parameter` (database-level security)
- Only accessible to system administrators
- Displayed with password widget (masked in UI)

### GitHub Token Protection

- Token field restricted to system administrators
- Password widget hides value in UI
- Never included in API responses or logs

### Access Control

| Role | Permissions |
|------|-------------|
| Helpdesk User | Analyze tickets, view results |
| Helpdesk Manager | Configure per-client settings |
| System Administrator | Configure API key, view all settings |

### Best Practices

- Rotate API keys regularly
- Use separate GitHub tokens per environment (staging/production)
- Set token expiration dates
- Use minimal required scopes for tokens
- Monitor API usage for anomalies

---

## Technical Details

### Module Structure

```
claude_helpdesk_ai/
├── __manifest__.py              # Module manifest (v1.0.2)
├── models/
│   ├── res_partner.py           # Client GitHub configuration
│   ├── helpdesk_ticket.py       # Ticket analysis logic
│   ├── res_config_settings.py   # Global settings
│   └── ir_config_parameter.py   # System parameters
├── lib/
│   └── github_integration.py    # GitHub API wrapper
├── views/
│   ├── res_config_settings_views.xml  # Settings UI
│   ├── res_partner_views.xml    # Partner form extension
│   ├── helpdesk_ticket_views.xml # Ticket form extension
│   └── menuitem.xml             # Menu items
├── data/
│   └── automation_rules.xml     # Auto-analysis rules
├── security/
│   └── ir.model.access.csv      # Access rights
└── static/description/
    └── icon.png                 # Module icon
```

### API Response Format

Claude returns analysis in this JSON structure:

```json
{
    "analysis": "Root cause analysis...",
    "solution_approach": "High-level solution...",
    "code_changes": [
        {
            "file": "path/to/file.py",
            "action": "modify",
            "content": "Complete file content...",
            "explanation": "Why this change..."
        }
    ],
    "testing_steps": "How to test...",
    "estimated_hours": 2.5,
    "additional_notes": "Warnings and considerations..."
}
```

---

## Support

- **Developer:** The IT Team
- **Website:** https://theitteam.co.za
- **Email:** support@theitteam.co.za

### Resources

1. Check this README for common issues
2. Review Odoo server logs for detailed errors
3. Contact The IT Team for support

---

## License

This module is licensed under **LGPL-3** (GNU Lesser General Public License v3.0).

---

**Made with care by The IT Team**

*Transforming support with AI, one ticket at a time.*
