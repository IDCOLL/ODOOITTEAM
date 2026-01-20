# Claude AI Helpdesk Automation

**Transform your Odoo helpdesk with AI-powered ticket analysis and automated code fixes**

[![License: LGPL-3](https://img.shields.io/badge/license-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-14%20|%2015%20|%2016%20|%2017%20|%2018%20|%2019-purple.svg)](https://www.odoo.com)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Cost Optimization](#cost-optimization)
- [Technical Architecture](#technical-architecture)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## 🎯 Overview

This Odoo module integrates Anthropic's Claude AI (Sonnet 4.5) with Odoo Helpdesk to revolutionize your support workflow:

- **Analyze** support tickets automatically to identify root causes
- **Propose** complete code solutions based on your GitHub codebase
- **Create** GitHub pull requests with ready-to-review fixes
- **Track** analysis history and success metrics per client
- **Optimize** costs using Claude's prompt caching feature

Perfect for MSPs, software agencies, and in-house teams managing multiple Odoo instances.

---

## ✨ Features

### 🧠 Intelligent Ticket Analysis
- Analyzes ticket descriptions, error logs, and reproduction steps
- Identifies root causes using advanced reasoning
- Provides step-by-step solution approaches
- Estimates development hours for fixes

### 🔍 Smart Module Detection
- Automatically detects affected Odoo modules from ticket content
- Searches error logs for module patterns
- Cross-references with client's custom module list

### 💻 Code Generation
- Fetches existing code from GitHub repository
- Generates complete, production-ready code changes
- Follows Odoo best practices and coding conventions
- Provides file-by-file changes with explanations

### 🔗 GitHub Integration
- Tests repository connection before use
- Creates feature branches automatically
- Commits code changes with descriptive messages
- Opens pull requests with formatted descriptions

### 👥 Multi-Client Support
- Configure different GitHub repos per client
- Track Odoo version and custom modules per client
- Store client-specific configuration notes
- Separate analytics for each client

### 📊 Analytics & Tracking
- Count tickets analyzed per client
- Track pull requests created
- View analysis history
- Monitor success rates

### 💰 Cost Optimization
- Implements prompt caching (90% cost reduction)
- Caches universal Odoo best practices
- Caches client-specific code and configuration
- Only fresh ticket data sent with each request

---

## 📦 Requirements

### Odoo
- **Version:** 14.0, 15.0, 16.0, 17.0, 18.0, or 19.0
- **Modules:** `base`, `helpdesk`, `mail`

### Python
- **Version:** 3.7 or higher
- **Packages:**
  - `anthropic` (Claude API client)
  - `requests` (HTTP library)

### External Services
- **Claude API:** Anthropic API key with access to Claude Sonnet 4.5
  - Sign up at: https://console.anthropic.com
  - Model: `claude-sonnet-4-5-20250929`

- **GitHub:** Personal Access Token with repository permissions
  - Generate at: https://github.com/settings/tokens
  - Required scopes: `repo` (full repository access)

---

## 🚀 Installation

### Installation on Odoo.sh

If deploying on **Odoo.sh**, Python dependencies are installed automatically:

1. **Add requirements.txt to your repository root** (if not already present):

```txt
# requirements.txt
anthropic>=0.18.0
requests>=2.31.0
```

2. **Push to Odoo.sh repository**:
   - Odoo.sh automatically detects `requirements.txt`
   - Dependencies are installed during build
   - No manual installation needed

3. **Install the module**:
   - Go to Apps menu in Odoo.sh
   - Update Apps List
   - Search for "Claude AI Helpdesk Automation"
   - Click Install

4. **Configure API key** (see Configuration section below)

### Installation on Self-Hosted Odoo

#### Step 1: Install Python Dependencies

```bash
pip install anthropic requests
```

Or if using a virtual environment:

```bash
source /path/to/odoo/venv/bin/activate
pip install anthropic requests
```

#### Step 2: Install Odoo Module

1. Copy the `claude_helpdesk_ai` directory to your Odoo addons path:

```bash
cp -r claude_helpdesk_ai /path/to/odoo/addons/
```

2. Restart Odoo server:

```bash
sudo systemctl restart odoo
# OR
sudo service odoo restart
# OR manually restart if running in development mode
```

3. Update Apps List:
   - Login to Odoo as Administrator
   - Go to **Apps** menu
   - Click **Update Apps List**
   - Search for "Claude AI Helpdesk Automation"

4. Install the Module:
   - Click **Install** button
   - Wait for installation to complete

### Step 3: Configure Claude API Key

1. Go to **Settings → Technical → System Parameters**
2. Click **Create**
3. Set:
   - **Key:** `claude_helpdesk_ai.api_key`
   - **Value:** Your Anthropic API key (starts with `sk-ant-`)
4. Save

---

## ⚙️ Configuration

### Global Configuration

#### Claude API Key
Already configured in Step 3 of installation. You can update it anytime in System Parameters.

### Per-Client Configuration

Each client (partner/customer) needs individual configuration for GitHub integration.

#### Navigate to Configuration
1. Go to **Helpdesk → Configuration → Claude AI Configuration**
2. Select a customer/partner
3. Open the **Claude AI & GitHub** tab

#### GitHub Configuration Section

| Field | Description | Example |
|-------|-------------|---------|
| **GitHub Repository URL** | Full URL to client's GitHub repo | `https://github.com/mycompany/odoo-custom` |
| **GitHub Personal Access Token** | PAT with repo permissions (admin-only) | `ghp_xxxxxxxxxxxx` |
| **Default Branch** | Main branch for pull requests | `main` or `master` or `production` |
| **Dev Branch Prefix** | Prefix for auto-created branches | `ai-fix/` or `feature/` |
| **Addons Path in Repo** | Path to addons directory | `addons` or `custom_addons` or `src` |

After filling these fields, click **Test Connection** to verify GitHub access.

#### Odoo Environment Section

| Field | Description | Example |
|-------|-------------|---------|
| **Odoo Version** | Client's Odoo version | Select from 14-19 |
| **Custom Modules** | Comma-separated module names | `custom_sales, custom_inventory, custom_crm` |
| **Configuration Notes** | Additional environment details | Any architecture notes, customizations, etc. |

#### AI Settings Section

| Field | Description | Default | Recommendation |
|-------|-------------|---------|----------------|
| **Enable Auto-Analysis** | Analyze tickets on creation | ✅ Enabled | Enable for active clients |
| **Auto-Create Pull Requests** | Create PRs automatically | ❌ Disabled | Keep disabled, review first |

**⚠️ Warning:** Auto-create PR will commit code changes without human review. Use with extreme caution.

#### Statistics Section

- **Tickets Analyzed:** Total count of AI-analyzed tickets
- **PRs Created:** Total count of GitHub PRs created
- **View Analyzed Tickets:** Button to filter analyzed tickets
- **Refresh Statistics:** Button to update counts

---

## 📖 Usage

### Manual Ticket Analysis

This is the recommended workflow for most use cases.

#### Step-by-Step Process

1. **Create/Open Ticket**
   - Go to **Helpdesk → Tickets**
   - Create new ticket or open existing one
   - Assign customer (partner) with GitHub configuration

2. **Fill Technical Details**
   - Open **Technical Details** tab
   - Fill in:
     - **Affected Module** (optional, will auto-detect if empty)
     - **Error Logs** (paste stack traces, error messages)
     - **Steps to Reproduce** (detailed reproduction steps)

3. **Trigger Analysis**
   - Click **Analyze with Claude AI** button in header
   - Wait for analysis to complete (10-30 seconds)
   - Success notification will appear

4. **Review Results**
   - Open **AI Analysis & Code** tab
   - Review sections:
     - **Analysis Information:** Date, estimated hours, affected module
     - **GitHub Information:** Branch name, PR number/URL
     - **AI Analysis:** Formatted HTML analysis
     - **Proposed Code Changes:** JSON with all file changes
     - **Full API Response:** Raw JSON for debugging

5. **Open Pull Request (if created)**
   - If PR was auto-created, click **Open Pull Request** button
   - Review changes in GitHub
   - Request code review from team
   - Merge when approved

### Automatic Ticket Analysis

Enable this for high-volume clients or trusted environments.

#### Setup

1. Go to client's partner form
2. Open **Claude AI & GitHub** tab
3. Enable **Enable Auto-Analysis** checkbox
4. Optionally enable **Auto-Create Pull Requests** (not recommended)
5. Save

#### Activation

The automatic analysis rule is **disabled by default** for safety.

To activate:
1. Go to **Settings → Technical → Automation → Automated Actions**
2. Search for "Claude AI: Auto-Analyze New Tickets"
3. Edit the record
4. Check **Active** checkbox
5. Save

#### Behavior

Once activated, tickets will be analyzed automatically when:
- Ticket is created
- Customer has **Enable Auto-Analysis** enabled
- Customer has GitHub repository configured

Analysis happens asynchronously and won't block ticket creation if it fails.

### Search & Filter Tickets

Use these filters in the ticket list:

- **AI Analyzed:** Show only analyzed tickets
- **PR Created:** Show only tickets with GitHub PRs
- **Not Analyzed:** Show tickets pending analysis

---

## 💰 Cost Optimization

This module uses **prompt caching** to dramatically reduce Claude API costs.

### How Prompt Caching Works

Claude API caches parts of prompts that don't change between requests:

1. **Universal Context (Cached):**
   - Odoo development best practices
   - Security guidelines
   - Performance optimization tips
   - Common patterns and conventions
   - **Cache Duration:** 5 minutes
   - **Cost Reduction:** 90% for cached tokens

2. **Client-Specific Context (Cached):**
   - GitHub code for affected module
   - Client configuration and notes
   - Past resolved ticket history
   - **Cache Duration:** 5 minutes
   - **Cost Reduction:** 90% for cached tokens

3. **Fresh Ticket Data (Not Cached):**
   - Ticket title and description
   - Error logs and reproduction steps
   - Specific issue details
   - **Always Fresh:** Full cost

### Cost Breakdown Example

**First Request (Cold Cache):**
- Input tokens: ~15,000 (universal + client + ticket)
- Cache creation: ~12,000 tokens
- Output tokens: ~2,000
- **Cost:** ~$0.10

**Subsequent Requests (Warm Cache):**
- Input tokens: ~3,000 (only ticket data)
- Cache read: ~12,000 tokens (90% discount)
- Output tokens: ~2,000
- **Cost:** ~$0.01-0.02

### Estimated Monthly Costs

Assuming 100 tickets/month per client:

- **Without Caching:** ~$10.00/month
- **With Caching:** ~$1.50-2.00/month
- **Savings:** 80-85%

### Best Practices for Cost Optimization

1. **Batch Similar Tickets:** Analyze multiple tickets for same module within 5 minutes to maximize cache hits
2. **Keep Module Lists Updated:** More accurate module detection = better context = better results
3. **Provide Good Error Logs:** Better context leads to better solutions on first try
4. **Monitor Usage:** Check Claude console for actual usage and costs

---

## 🏗️ Technical Architecture

### Module Structure

```
claude_helpdesk_ai/
├── __init__.py                  # Module initialization
├── __manifest__.py              # Module manifest and dependencies
├── models/                      # Business logic models
│   ├── __init__.py
│   ├── res_partner.py          # Partner/client configuration
│   ├── helpdesk_ticket.py      # Ticket analysis logic
│   └── ir_config_parameter.py  # System parameters
├── lib/                         # External integrations
│   ├── __init__.py
│   └── github_integration.py   # GitHub API wrapper
├── views/                       # User interface
│   ├── res_partner_views.xml   # Partner form extension
│   ├── helpdesk_ticket_views.xml # Ticket form extension
│   └── menuitem.xml            # Menu items
├── data/                        # Initial data
│   ├── ir_config_parameter_data.xml # Default API key param
│   └── automation_rules.xml    # Automated actions
├── security/                    # Access control
│   └── ir.model.access.csv     # Model access rights
├── static/description/          # Module documentation
│   ├── icon.png                # Module icon
│   └── index.html              # Module description page
└── README.md                    # This file
```

### Data Flow

1. **User clicks "Analyze with Claude AI"**
2. **Ticket model validates configuration:**
   - Claude API key exists
   - Partner has GitHub configuration
3. **Build cached context:**
   - Universal Odoo best practices
   - Client-specific code from GitHub
   - Past ticket history
4. **Build fresh prompt:**
   - Ticket title, description
   - Error logs, reproduction steps
5. **Call Claude API with caching:**
   - Send cached context (marked with cache_control)
   - Send fresh ticket data
   - Receive JSON response
6. **Parse and store results:**
   - Extract analysis, code changes
   - Format as HTML for display
   - Store raw JSON for debugging
7. **Create GitHub solution (if enabled):**
   - Create feature branch
   - Commit code changes
   - Open pull request
8. **Display results to user**

### Claude API Integration

**Model:** `claude-sonnet-4-5-20250929`

**Parameters:**
- `max_tokens`: 8000
- `temperature`: 0.2 (deterministic)
- `system`: Cached context with `cache_control` markers

**Expected Response Format:**
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

### GitHub API Integration

**API Version:** GitHub REST API v3

**Endpoints Used:**
- `GET /repos/{owner}/{repo}` - Test connection
- `GET /repos/{owner}/{repo}/contents/{path}` - Get files
- `GET /repos/{owner}/{repo}/git/ref/heads/{branch}` - Get branch SHA
- `POST /repos/{owner}/{repo}/git/refs` - Create branch
- `PUT /repos/{owner}/{repo}/contents/{path}` - Create/update file
- `POST /repos/{owner}/{repo}/pulls` - Create pull request

**Authentication:** Bearer token (Personal Access Token)

---

## 🔒 Security

### API Key Protection

- **Claude API Key:**
  - Stored in `ir.config_parameter` (encrypted at database level)
  - Only accessible to system administrators
  - Never logged or exposed in UI

- **GitHub Tokens:**
  - Field restricted to `base.group_system` group
  - Password widget hides value in UI
  - Never included in API responses

### Data Privacy

- **No PII in Prompts:**
  - Customer names masked if sensitive
  - Only technical data sent to Claude
  - Error logs sanitized automatically

- **Audit Trail:**
  - All API calls logged with `_logger`
  - Timestamps tracked for all analyses
  - Full JSON responses stored for debugging

### Access Control

- **Helpdesk Users:**
  - Can analyze tickets
  - Can view results
  - Cannot modify configurations

- **Helpdesk Managers:**
  - All user permissions
  - Can configure per-client settings
  - Can view GitHub tokens (masked)

- **System Administrators:**
  - All manager permissions
  - Can configure Claude API key
  - Can view raw GitHub tokens

### Network Security

- **HTTPS Only:**
  - All GitHub API calls use HTTPS
  - All Claude API calls use HTTPS
  - Certificate validation enabled

- **Timeout Protection:**
  - API calls timeout after 30 seconds
  - Prevents hanging requests
  - Graceful error handling

---

## 🔧 Troubleshooting

### Common Issues

#### "Claude API key not configured"

**Cause:** System parameter missing or empty

**Solution:**
1. Go to Settings → Technical → System Parameters
2. Create/edit parameter with key `claude_helpdesk_ai.api_key`
3. Set value to your Anthropic API key (starts with `sk-ant-`)

#### "Connection failed" when testing GitHub

**Causes:**
- Invalid repository URL
- Invalid or expired token
- Token lacks required permissions

**Solutions:**
1. Verify repository URL format: `https://github.com/owner/repo`
2. Generate new token at https://github.com/settings/tokens
3. Ensure token has `repo` scope (full repository access)
4. Check token hasn't expired

#### "No module detected for ticket"

**Cause:** Module name not found in ticket content

**Solutions:**
1. Manually set **Affected Module** field in Technical Details tab
2. Include module name in ticket description (e.g., "Error in sale_order module")
3. Add module to **Custom Modules** list in partner configuration

#### "Failed to fetch GitHub code"

**Causes:**
- Module doesn't exist in repository
- Incorrect **Addons Path** setting
- Branch doesn't exist
- Token permissions insufficient

**Solutions:**
1. Verify module exists in GitHub at `{addons_path}/{module_name}`
2. Check **Addons Path in Repo** setting (e.g., `addons` vs `custom_addons`)
3. Ensure default branch name is correct
4. Verify token has read access to repository

#### "Failed to parse AI response"

**Cause:** Claude returned invalid JSON

**Solutions:**
1. Check **Full API Response** field in ticket for actual response
2. Verify Claude API key is valid and has credits
3. Check Odoo logs for detailed error message
4. Response may be truncated - check max_tokens setting

#### "Auto-analysis not triggering"

**Causes:**
- Automation rule is disabled
- Partner doesn't have auto-analysis enabled
- GitHub repo not configured

**Solutions:**
1. Activate automation: Settings → Technical → Automation → "Claude AI: Auto-Analyze New Tickets"
2. Enable **Enable Auto-Analysis** on partner
3. Configure GitHub repository URL on partner
4. Check Odoo logs for errors

### Debug Mode

Enable detailed logging:

```python
# In odoo.conf
log_level = debug
```

Then check logs at `/var/log/odoo/odoo-server.log` for:
- `Starting Claude AI analysis for ticket {id}`
- `GitHub connection test failed: {error}`
- `Claude API call failed: {error}`
- `Created GitHub PR #{number} for ticket {id}`

---

## 📞 Support

### Contact Information

- **Developer:** The IT Team
- **Website:** https://theitteam.co.za
- **Email:** support@theitteam.co.za

### Getting Help

1. **Documentation:** Read this README thoroughly
2. **Logs:** Check Odoo server logs for detailed errors
3. **GitHub Issues:** Report bugs or request features
4. **Direct Support:** Contact The IT Team for paid support

### Feature Requests

We welcome feature requests! Please include:
- Use case description
- Expected behavior
- Current workaround (if any)
- Priority level

### Bug Reports

When reporting bugs, include:
- Odoo version
- Module version
- Steps to reproduce
- Error message/logs
- Screenshots (if applicable)

---

## 📄 License

This module is licensed under the **LGPL-3** (GNU Lesser General Public License v3.0).

You are free to:
- Use commercially
- Modify
- Distribute
- Sublicense

Under the conditions:
- Disclose source
- License and copyright notice
- State changes
- Same license for modifications

See [LICENSE](LICENSE) file for full text.

---

## 🙏 Acknowledgments

- **Anthropic:** For Claude AI and excellent API
- **Odoo SA:** For the amazing Odoo framework
- **GitHub:** For Git hosting and API
- **The IT Team:** For development and support

---

## 🚀 Roadmap

Planned features for future versions:

- [ ] Support for other AI models (GPT-4, Gemini)
- [ ] GitLab and Bitbucket integration
- [ ] Automated testing of proposed changes
- [ ] Multi-language support
- [ ] Custom prompt templates
- [ ] Integration with CI/CD pipelines
- [ ] Team collaboration features
- [ ] Advanced analytics dashboard

---

**Made with ❤️ by The IT Team**

*Transforming support with AI, one ticket at a time.*
