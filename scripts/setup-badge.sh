#!/bin/bash
# Quick setup script for LLM Security Badge

REPO_OWNER=$(git remote get-url origin | sed -n 's/.*github.com[:/]\([^/]*\).*/\1/p')
REPO_NAME=$(git remote get-url origin | sed -n 's/.*github.com[:/][^/]*\/\([^.]*\).*/\1/p')

# Create workflow directory
mkdir -p .github/workflows

# Download workflow template
curl -s https://raw.githubusercontent.com/Ballesty-Liam/llm-policy-action/main/templates/llm-security-badge.yml \
  -o .github/workflows/llm-security-badge.yml

# Add badge to README
if [ -f README.md ]; then
    BADGE="[![LLM Security](https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/llm-security-badge.yml)"

    # Insert after first heading or at top
    if grep -q "^#" README.md; then
        sed -i "/^#/a\\\\n${BADGE}\\n" README.md
    else
        echo -e "${BADGE}\\n\\n$(cat README.md)" > README.md
    fi

    echo "✅ Badge added to README.md"
else
    echo "❌ No README.md found"
fi

echo "✅ Workflow created at .github/workflows/llm-security-badge.yml"
echo "📝 Please commit these changes and push to activate your security badge"