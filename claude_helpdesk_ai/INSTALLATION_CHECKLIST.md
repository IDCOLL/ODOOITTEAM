# Installation Checklist for Claude AI Helpdesk Automation

Use this checklist to ensure proper installation and configuration.

## ☐ Pre-Installation

- [ ] Odoo version 14, 15, 16, 17, 18, or 19 is running
- [ ] Helpdesk module is installed and configured
- [ ] Determine deployment type: Odoo.sh or Self-Hosted
- [ ] You have an Anthropic API key (get from https://console.anthropic.com)
- [ ] You have GitHub Personal Access Token with repo permissions

---

## FOR ODOO.SH INSTALLATIONS

### ☐ Python Dependencies (Automatic)

- [ ] Ensure `requirements.txt` exists in repository root with:
  ```txt
  anthropic>=0.18.0
  requests>=2.31.0
  ```
- [ ] Push changes to Odoo.sh repository
- [ ] Wait for build to complete
- [ ] Dependencies installed automatically ✅

### ☐ Module Installation

- [ ] Module appears in Apps list (after git push)
- [ ] Update Apps List (Apps menu → Update Apps List)
- [ ] Search for "Claude AI Helpdesk Automation"
- [ ] Click Install button
- [ ] Installation completed without errors

---

## FOR SELF-HOSTED INSTALLATIONS

### ☐ Python Dependencies (Manual)

```bash
# Install required packages
pip install anthropic requests

# Verify installation
python -c "import anthropic; import requests; print('Dependencies OK')"
```

- [ ] `anthropic` package installed successfully
- [ ] `requests` package installed successfully

### ☐ Module Installation

- [ ] Copy `claude_helpdesk_ai` folder to Odoo addons directory
- [ ] Restart Odoo server
- [ ] Update Apps List (Apps menu → Update Apps List)
- [ ] Search for "Claude AI Helpdesk Automation"
- [ ] Click Install button
- [ ] Installation completed without errors

---

## BOTH DEPLOYMENT TYPES

## ☐ Global Configuration

### Claude API Key Setup

- [ ] Navigate to: Settings → Technical → System Parameters
- [ ] Create new parameter or edit existing:
  - **Key:** `claude_helpdesk_ai.api_key`
  - **Value:** Your Anthropic API key (starts with `sk-ant-`)
- [ ] Save parameter
- [ ] Verify key is correct (check for typos)

## ☐ Per-Client Configuration

For each client that will use AI analysis:

### Navigate to Configuration
- [ ] Go to: Helpdesk → Configuration → Claude AI Configuration
- [ ] Select customer/partner record
- [ ] Open "Claude AI & GitHub" tab

### GitHub Configuration
- [ ] Set **GitHub Repository URL**: `https://github.com/owner/repo`
- [ ] Set **GitHub Personal Access Token**: Your GitHub PAT
- [ ] Set **Default Branch**: e.g., `main`, `master`, `production`
- [ ] Set **Dev Branch Prefix**: e.g., `ai-fix/`, `feature/`
- [ ] Set **Addons Path in Repo**: e.g., `addons`, `custom_addons`
- [ ] Click **Test Connection** button
- [ ] Verify connection successful ✅

### Odoo Environment
- [ ] Select **Odoo Version** from dropdown
- [ ] Enter **Custom Modules** (comma-separated): e.g., `module1, module2`
- [ ] Add **Configuration Notes** (optional but recommended)

### AI Settings
- [ ] Enable **Enable Auto-Analysis** (if desired)
- [ ] Keep **Auto-Create Pull Requests** DISABLED (recommended)
- [ ] Save partner record

## ☐ Testing

### Test Manual Analysis

- [ ] Create test ticket
- [ ] Assign to configured customer
- [ ] Fill in ticket details:
  - [ ] Add description
  - [ ] Add error logs (optional)
  - [ ] Add steps to reproduce (optional)
- [ ] Click "Analyze with Claude AI" button
- [ ] Wait for analysis to complete
- [ ] Verify success notification appears
- [ ] Open "AI Analysis & Code" tab
- [ ] Verify analysis appears with:
  - [ ] Analysis date and time
  - [ ] Root cause analysis
  - [ ] Proposed solution
  - [ ] Code changes (if applicable)
  - [ ] Estimated hours

### Test GitHub Integration (Optional)

- [ ] After successful analysis with code changes
- [ ] Verify GitHub branch was created
- [ ] Click "Open Pull Request" button
- [ ] Verify PR opens in GitHub
- [ ] Review PR description and code changes
- [ ] Close/delete test PR

## ☐ Optional: Enable Auto-Analysis

**⚠️ Only enable after successful manual testing!**

- [ ] Go to: Settings → Technical → Automation → Automated Actions
- [ ] Search for: "Claude AI: Auto-Analyze New Tickets"
- [ ] Edit the record
- [ ] Check **Active** checkbox
- [ ] Save
- [ ] Create test ticket to verify auto-analysis works
- [ ] Verify ticket is analyzed automatically

## ☐ Documentation

- [ ] Read full README.md
- [ ] Bookmark Claude API console: https://console.anthropic.com
- [ ] Bookmark GitHub tokens page: https://github.com/settings/tokens
- [ ] Share configuration guide with team
- [ ] Document client-specific settings

## ☐ Monitoring

### First Week

- [ ] Monitor Odoo logs for errors
- [ ] Check Claude API usage in console
- [ ] Review actual costs vs estimates
- [ ] Gather user feedback
- [ ] Review PR quality

### Ongoing

- [ ] Monthly: Review API costs
- [ ] Monthly: Check GitHub token expiration
- [ ] Quarterly: Update custom module lists per client
- [ ] As needed: Rotate API keys and tokens

## 🎉 Installation Complete!

Once all items are checked, your Claude AI Helpdesk Automation module is ready for production use.

## 📞 Need Help?

- Read: `/claude_helpdesk_ai/README.md` (comprehensive documentation)
- Contact: The IT Team at https://theitteam.co.za
- Email: support@theitteam.co.za

---

**Pro Tips:**

1. Start with 1-2 test clients before rolling out to all clients
2. Keep "Auto-Create PR" disabled until you trust the AI output
3. Monitor costs closely in the first month to establish baseline
4. Create a Slack/Teams channel for AI-generated PR reviews
5. Document any common issues and solutions for your team
