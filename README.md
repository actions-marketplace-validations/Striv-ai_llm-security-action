# LLM Policy Enforcer&nbsp;· GitHub Action ![version](https://img.shields.io/github/v/tag/<ORG>/llm-policy-action?label=version) ![tests](https://img.shields.io/github/actions/workflow/status/<ORG>/llm-policy-action/ci.yml?label=CI) ![license](https://img.shields.io/github/license/<ORG>/llm-policy-action) ![marketplace](https://img.shields.io/badge/GH_Marketplace-View-blue)

Secure your Gen-AI codebase in **one line**.  
This Action scans every push / pull request for:

| 🔐  **API-Key Security** | Detects leaked API keys & high-entropy tokens for common LLM / ML providers. _Fail_ the build on any hit. | 

| ⚡ **Rate-Limit Heuristic** | Warns when LLM calls appear in loops without back-off (`sleep`, retry, etc.). _Warn-only_ by default. |

No secrets required – uses the default `GITHUB_TOKEN`.

---

## Quick Start

```yaml
# .github/workflows/llm-policy.yml
name: LLM Policy Check
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: <ORG>/llm-policy-action@v1              # ← that’s it!
