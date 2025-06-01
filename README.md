# Updated README.md Content (add after Quick Start section)

## 🏆 Security Badge

Show your commitment to LLM security with a GitHub-native status badge:

[![LLM Security](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml)

### One-Line Setup

```bash
curl -sSL https://raw.githubusercontent.com/Ballesty-Liam/llm-policy-action/main/scripts/setup-badge.sh | bash
```

This will:
- ✅ Create the badge workflow (`.github/workflows/llm-security-badge.yml`)
- ✅ Add the badge to your README
- ✅ Create a default `llm-policy.yml` if needed

### Manual Setup

1. Create `.github/workflows/llm-security-badge.yml`:

```yaml
name: LLM Security
on: [push, pull_request]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Ballesty-Liam/llm-policy-action@v1
```

2. Add the badge to your README:

```markdown
[![LLM Security](https://github.com/USERNAME/REPO/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/llm-security-badge.yml)
```

### Badge States

- 🟢 **Passing** - All security checks passed
- 🔴 **Failing** - Security violations detected
- ⚪ **No Status** - Workflow not yet run

### Why Use the Badge?

- **Build Trust** - Show users you take LLM security seriously
- **Prevent Issues** - Catch security problems before production
- **Join the Community** - Be part of the secure LLM development movement

---

## Configuration

The action uses `llm-policy.yml` for configuration:

```yaml
# llm-policy.yml
policies:
  api-key-security: true     # Fail on exposed keys
  rate-limit: true          # Warn on missing rate limits
  input-sanitize: true      # Warn on unsanitized input

# Add your organization's API key prefixes
custom-api-key-prefixes: 
  - "org-"
  - "internal-"

# Speed up scans by excluding files
exclude_globs:
  - "node_modules/*"
  - ".env.example"
  - "tests/fixtures/*"
```

---

## Network Effects & Social Proof

When you display the LLM Security badge, you're:
1. **Setting an Example** - Encouraging others to adopt security best practices
2. **Building Trust** - Users can verify your security stance at a glance  
3. **Raising Standards** - Contributing to a more secure LLM ecosystem
