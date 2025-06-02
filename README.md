# LLM Agent Trust Verification · GitHub Action ![version](https://img.shields.io/github/v/tag/Ballesty-Liam/llm-security-action?label=version) ![license](https://img.shields.io/github/license/Ballesty-Liam/llm-security-action) ![marketplace](https://img.shields.io/badge/GH_Marketplace-View-blue)

[![LLM Security](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml)

Secure your Gen-AI codebase in **one line**.  
Professional LLM security scanning for production AI applications:

| 🔐 **API Key Security** | Detects leaked API keys & high-entropy tokens for common LLM/ML providers. _Fails_ the build on any hit. |
|-------------------------|----------------------------------------------------------------------------------------------------------|
| ⚡ **Rate Limit Heuristic** | Warns when LLM calls appear in loops without back-off (`sleep`, retry, etc.). _Warn-only_ by default. |
| 🛡️ **Input Sanitization** | Identifies unsanitized user input flowing into LLM API calls. _Warn-only_ by default. |

No secrets required – uses the default `GITHUB_TOKEN`.

---

## Quick Start

```yaml
# .github/workflows/llm-security.yml
name: LLM Security Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Ballesty-Liam/llm-security-action@v1
```

That's it! The action will run on every push and PR, scanning your code for LLM security vulnerabilities.

---

## 🏆 Get the Security Badge

Show your commitment to LLM security with a GitHub-native status badge:

### One-Line Setup

```bash
curl -sSL https://raw.githubusercontent.com/Ballesty-Liam/llm-security-action/main/scripts/setup-badge.sh | bash
```

This will:
- ✅ Create the badge workflow (`.github/workflows/llm-security-badge.yml`)
- ✅ Add the badge to your README
- ✅ Create a default `llm-policy.yml` if needed

### Manual Badge Setup

Add to your README:
```markdown
[![LLM Security](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/Ballesty-Liam/llm-security-action/actions/workflows/llm-security-badge.yml)
```

---

## Features

### 🔍 What It Scans

**API Key Detection**
- Common LLM provider prefixes (OpenAI, Anthropic, Cohere, etc.)
- High-entropy strings that look like tokens
- Custom prefix patterns you define

**Rate Limiting**
- LLM API calls inside `for`/`while` loops
- Missing `sleep()` or backoff mechanisms
- Supports Python, JavaScript, TypeScript, and Go

**Input Sanitization**
- Direct user input → LLM API calls
- Missing HTML/SQL escape functions
- AST-based analysis for Python, regex for JS/Go

### ⚙️ Configuration

Create `llm-policy.yml` in your repo root:

```yaml
# Enable/disable policies
policies:
  api-key-security: true    # Fail on exposed keys
  rate-limit: true         # Warn on missing rate limits
  input-sanitize: true     # Warn on unsanitized input

# Add custom API key prefixes
custom-api-key-prefixes: 
  - "mycompany-"
  - "internal-key-"

# Exclude files/directories
exclude_globs:
  - "node_modules/*"
  - ".env.example"
  - "tests/fixtures/*"

# Rate limit settings
rate-limit:
  languages: ["python", "javascript", "go"]
  warn-only: true
  min-sleep-seconds: 1.0

# Input sanitization settings
input-sanitize:
  languages: ["python", "javascript", "go"]
  warn-only: true
```

### 📊 Action Outputs

Use scan results in your workflows:

```yaml
- uses: Ballesty-Liam/llm-security-action@v1
  id: security-scan
  
- name: Check results
  run: |
    echo "Status: ${{ steps.security-scan.outputs.status }}"
    echo "API Keys Found: ${{ steps.security-scan.outputs.api-key-violations }}"
    echo "Rate Limit Issues: ${{ steps.security-scan.outputs.rate-limit-warnings }}"
```

Available outputs:
- `status`: `passed`, `warning`, or `failed`
- `api-key-violations`: Number of exposed keys
- `rate-limit-warnings`: Number of rate limit issues  
- `input-sanitize-warnings`: Number of sanitization issues
- `badge-status`: Human-readable status with emoji

---

## Advanced Usage

### PR Comments on Failure

```yaml
- uses: Ballesty-Liam/llm-security-action@v1
  id: scan
  
- name: Comment PR
  if: failure() && github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: '❌ Security scan failed! Check logs for details.'
      })
```

---
## 🏢 Professional Security Analysis
- Production-grade scanning for commercial LLM applications
- Comprehensive vulnerability detection across multiple languages
- Professional reporting with actionable security findings
- Configurable policies for enterprise security requirements

**Need assistance with implementation?** Contact the maintainers for guidance.

---
## Why Use This?

**🚀 Beyond Basic Secret Scanning**
- Catches LLM-specific patterns GitHub's secret scanning misses
- Identifies architectural issues (rate limiting, input handling)
- Zero configuration required to start

**🎯 Built for AI/LLM Development**
- Understands common LLM SDK patterns
- Reduces false positives with smart exclusions
- Covers the OWASP Top 10 for LLMs

**📈 Network Effects**
- Display the security badge to build trust
- Join a growing community of secure LLM developers
- Encourage best practices across the ecosystem

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- 🐛 [Report bugs](https://github.com/Ballesty-Liam/llm-security-action/issues)
- 💡 [Request features](https://github.com/Ballesty-Liam/llm-security-action/issues)
- 📖 [Read docs](https://github.com/Ballesty-Liam/llm-security-action/wiki)

---
