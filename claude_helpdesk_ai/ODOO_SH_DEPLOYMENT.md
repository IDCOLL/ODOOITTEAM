# Odoo.sh Deployment Guide

Quick reference for deploying Claude AI Helpdesk Automation on Odoo.sh.

## 📋 Prerequisites

- [ ] Odoo.sh project with Helpdesk module installed
- [ ] Git repository connected to Odoo.sh
- [ ] Anthropic API key (from https://console.anthropic.com)
- [ ] GitHub Personal Access Token (from https://github.com/settings/tokens)

---

## 🚀 Deployment Steps

### 1. Add Python Dependencies

Odoo.sh automatically installs Python packages listed in `requirements.txt` at the repository root.

**Option A: Use the provided requirements.txt**

Copy the requirements file from the module to your repository root:

```bash
cp claude_helpdesk_ai/requirements.txt ./requirements.txt
```

**Option B: Add to existing requirements.txt**

If you already have a `requirements.txt` file, add these lines:

```txt
anthropic>=0.18.0
requests>=2.31.0
```

### 2. Commit and Push to Odoo.sh

```bash
git add requirements.txt
git add claude_helpdesk_ai/
git commit -m "Add Claude AI Helpdesk Automation module"
git push odoo-sh main
```

Replace `odoo-sh` and `main` with your remote name and branch.

### 3. Wait for Build

- Odoo.sh will detect the changes
- Build process starts automatically
- Python dependencies are installed during build
- Wait for build to complete (usually 5-10 minutes)
- Check build logs for any errors

### 4. Install the Module

1. Login to your Odoo.sh instance
2. Go to **Apps** menu
3. Click **Update Apps List**
4. Search for "Claude AI Helpdesk Automation"
5. Click **Install**
6. Wait for installation to complete

### 5. Configure Claude API Key

**Important:** Use Odoo.sh environment variables for security!

#### Method 1: Using Environment Variables (Recommended)

1. In Odoo.sh dashboard, go to your project
2. Navigate to **Settings → Environment Variables**
3. Add variable:
   - **Name:** `CLAUDE_API_KEY`
   - **Value:** Your Anthropic API key (starts with `sk-ant-`)
4. Restart the instance

Then, set the system parameter to read from the environment variable:

1. In Odoo, go to **Settings → Technical → System Parameters**
2. Find or create parameter: `claude_helpdesk_ai.api_key`
3. Set value to: `${CLAUDE_API_KEY}` (will be replaced at runtime)

#### Method 2: Direct System Parameter (Less Secure)

1. Go to **Settings → Technical → System Parameters**
2. Create parameter:
   - **Key:** `claude_helpdesk_ai.api_key`
   - **Value:** Your Anthropic API key
3. Save

### 6. Configure Clients

For each client that will use AI analysis:

1. Go to **Helpdesk → Configuration → Claude AI Configuration**
2. Select customer/partner
3. Open **Claude AI & GitHub** tab
4. Configure:
   - GitHub Repository URL
   - GitHub Personal Access Token
   - Default Branch
   - Addons Path
   - Odoo Version
   - Custom Modules
5. Click **Test Connection** to verify
6. Enable **Enable Auto-Analysis** if desired
7. Save

---

## 🔧 Troubleshooting on Odoo.sh

### Dependencies Not Installed

**Symptom:** Error "No module named 'anthropic'" when analyzing tickets

**Solution:**
1. Check `requirements.txt` is in repository root (not in subdirectory)
2. Verify file is committed and pushed
3. Check Odoo.sh build logs for dependency installation errors
4. Try rebuilding the instance
5. Ensure requirements.txt uses Unix line endings (LF, not CRLF)

### Build Fails

**Check:**
- Build logs in Odoo.sh dashboard
- requirements.txt syntax (no typos)
- Python package versions are compatible

**Fix:**
```txt
# Use specific versions if latest causes issues
anthropic==0.18.1
requests==2.31.0
```

### Module Not Appearing

**Solution:**
1. Verify module is in the correct addons path
2. Check module folder name matches expected structure
3. Restart the Odoo.sh instance
4. Update Apps List again
5. Check for errors in server logs

### API Key Not Working

**Check:**
1. System parameter key is exactly: `claude_helpdesk_ai.api_key`
2. API key is valid (test at https://console.anthropic.com)
3. API key has sufficient credits
4. No extra spaces or quotes in the value

### GitHub Connection Fails

**Common Issues:**
- Token expired (GitHub tokens can have expiration dates)
- Token lacks `repo` permissions
- Repository URL format incorrect
- Repository is private but token lacks access

**Fix:**
1. Generate new token at https://github.com/settings/tokens
2. Select `repo` scope (full repository access)
3. Copy token immediately (shown only once)
4. Update in partner configuration

---

## 📊 Monitoring on Odoo.sh

### Check Build Logs

1. Odoo.sh Dashboard → Your Project
2. Builds tab
3. Select latest build
4. View logs for dependency installation

### Check Runtime Logs

1. Odoo.sh Dashboard → Your Project
2. Logs tab
3. Filter by:
   - `claude_helpdesk_ai` (module logs)
   - `anthropic` (API calls)
   - `ERROR` (errors only)

### Monitor API Usage

1. Visit https://console.anthropic.com
2. Go to Usage & Billing
3. Monitor:
   - API calls per day
   - Token usage
   - Costs
   - Cache hit rate

---

## 🔒 Security Best Practices on Odoo.sh

### API Keys

- ✅ **DO:** Use environment variables for API keys
- ✅ **DO:** Rotate keys regularly (every 90 days)
- ✅ **DO:** Monitor usage for anomalies
- ❌ **DON'T:** Commit API keys to git
- ❌ **DON'T:** Share keys between environments

### GitHub Tokens

- ✅ **DO:** Use separate tokens per environment (staging/production)
- ✅ **DO:** Set token expiration dates
- ✅ **DO:** Use minimal required scopes
- ❌ **DON'T:** Use personal tokens for production
- ❌ **DON'T:** Give tokens admin access unless necessary

### Database Backups

Odoo.sh handles backups automatically, but verify:
- Backups include system parameters
- Regular backup schedule is enabled
- You can restore if needed

---

## 🚦 Deployment Checklist

- [ ] requirements.txt in repository root
- [ ] Module committed to repository
- [ ] Pushed to Odoo.sh
- [ ] Build completed successfully
- [ ] Dependencies visible in build logs
- [ ] Module installed in Odoo
- [ ] Claude API key configured (preferably via environment variable)
- [ ] At least one client configured for testing
- [ ] Test ticket analyzed successfully
- [ ] GitHub connection tested
- [ ] Team trained on usage
- [ ] Documentation shared with team
- [ ] Monitoring set up for API usage
- [ ] Backup/restore tested

---

## 📞 Support

If you encounter issues specific to Odoo.sh deployment:

1. **Check Odoo.sh Documentation:** https://www.odoo.sh/documentation
2. **Odoo.sh Support:** support@odoo.com
3. **Module Support:** The IT Team at https://theitteam.co.za

---

## 🔄 Updates and Maintenance

### Updating the Module

1. Make changes to module code
2. Commit and push to repository
3. Odoo.sh rebuilds automatically
4. Restart instance if needed
5. Test changes in staging first

### Updating Dependencies

Edit requirements.txt:

```txt
# Update to newer versions
anthropic>=0.19.0  # Changed from 0.18.0
requests>=2.31.0
```

Commit, push, and rebuild.

### Version Control

Use git tags for releases:

```bash
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

---

**Happy deploying! 🎉**
