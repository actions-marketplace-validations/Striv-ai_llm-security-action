#!/bin/bash
# Quick setup script for LLM Security Badge
# Usage: bash scripts/setup-badge.sh

set -e

echo "🚀 Setting up LLM Security Badge..."

# Detect repository info from git remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE_URL" ]; then
    echo "Error: Not a git repository or no origin remote found"
    exit 1
fi

# Extract owner and repo name from various Git URL formats
if [[ $REMOTE_URL =~ github.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    REPO_OWNER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]}"
else
    echo "Error: Could not parse GitHub repository information"
    echo "Remote URL: $REMOTE_URL"
    exit 1
fi

echo "Repository: $REPO_OWNER/$REPO_NAME"

# Create workflow directory
mkdir -p .github/workflows

# Create workflow file directly (instead of downloading)
WORKFLOW_FILE=".github/workflows/llm-security-badge.yml"
echo "Creating workflow template..."

cat > "$WORKFLOW_FILE" << 'EOF'
name: LLM Security  # This text appears on the badge

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 0'  # Weekly verification to keep badge current
  workflow_dispatch:  # Allow manual runs

jobs:
  verify:
    name: Verify
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - uses: Ballesty-Liam/llm-security-action@v1
        id: scan
        with:
          config: llm-policy.yml

      # Optional: Post comment on PR with details (only on failure)
      - name: Comment PR
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            const output = `### ❌ LLM Security Check Failed

            The LLM Policy Enforcer detected security violations in this PR.

            Please check the [workflow logs](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}) for details.

            Common issues:
            - Exposed API keys or tokens
            - Missing rate limiting in LLM API loops
            - Unsanitized user input to LLM calls`;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })
EOF

# Create default config if it doesn't exist
if [ ! -f "llm-policy.yml" ]; then
    echo "Creating default llm-policy.yml..."
    cat > llm-policy.yml << 'EOF'
# LLM Policy Configuration
policies:
  api-key-security: true
  rate-limit: true
  input-sanitize: true

# Customize API key prefixes for your organization
custom-api-key-prefixes: []

# Files to exclude from scanning
exclude_globs:
  - ".git/*"
  - "__pycache__/*"
  - "*.pyc"
  - "node_modules/*"
  - ".env.example"

rate-limit:
  warn-only: true

input-sanitize:
  warn-only: true
EOF
fi

# Add badge to README
BADGE_MD="[![LLM Security](https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/llm-security-badge.yml/badge.svg)](https://github.com/${REPO_OWNER}/${REPO_NAME}/actions/workflows/llm-security-badge.yml)"

if [ -f README.md ]; then
    # Check if badge already exists
    if grep -q "llm-security-badge.yml/badge.svg" README.md; then
        echo "Badge already exists in README.md"
    else
        echo "Adding badge to README.md..."

        # Create temp file
        TEMP_FILE=$(mktemp)

        # Try to insert after the first heading, or at the top if no heading
        if grep -q "^# " README.md; then
            # Insert after first h1 heading
            awk -v badge="$BADGE_MD" '
                /^# / && !done {print; print ""; print badge; print ""; done=1; next}
                {print}
            ' README.md > "$TEMP_FILE"
        else
            # Insert at top
            echo "$BADGE_MD" > "$TEMP_FILE"
            echo "" >> "$TEMP_FILE"
            cat README.md >> "$TEMP_FILE"
        fi

        mv "$TEMP_FILE" README.md
        echo "Badge added to README.md"
    fi
else
    echo "No README.md found - creating one with badge..."
    cat > README.md << EOF
# $REPO_NAME

$BADGE_MD

Add your project description here.
EOF
fi

# Summary
echo ""
echo "Setup complete! Next steps:"
echo "   1. Review the changes:"
echo "      git status"
echo "   2. Commit the changes:"
echo "      git add .github/workflows/llm-security-badge.yml llm-policy.yml README.md"
echo "      git commit -m 'Add LLM Security badge'"
echo "   3. Push to GitHub:"
echo "      git push"
echo ""
echo "Your security badge will appear after the first workflow run!"