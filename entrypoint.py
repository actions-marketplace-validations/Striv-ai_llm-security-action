import os, sys, yaml, json, pathlib
from llm_policy.api_key_scanner import scan_api_keys
from llm_policy.rate_limit_scanner import scan_rate_limits
from llm_policy.telemetry import emit_metrics
from llm_policy.input_sanitize_scanner import scan_input_sanitization

ROOT = pathlib.Path(".")
CONFIG_FILE = os.getenv("INPUT_CONFIG", "llm-policy.yml")


def load_cfg():
    if pathlib.Path(CONFIG_FILE).exists():
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def set_github_outputs(results, failed):
    """Set GitHub Action outputs for use in workflows"""
    output_file = os.getenv('GITHUB_OUTPUT')
    if not output_file:
        return

    # Calculate overall status
    api_violations = results.get("api_key_security", {}).get("violations", 0)
    rate_warnings = results.get("rate_limit", {}).get("total", 0)
    sanitize_warnings = results.get("input_sanitize", {}).get("total", 0)

    if failed:
        status = "failed"
        badge_status = "❌ Failed"
    elif rate_warnings > 0 or sanitize_warnings > 0:
        status = "warning"
        badge_status = "⚠️ Warnings"
    else:
        status = "passed"
        badge_status = "✅ Secured"

    # Write outputs
    with open(output_file, 'a') as f:
        f.write(f"status={status}\n")
        f.write(f"api-key-violations={api_violations}\n")
        f.write(f"rate-limit-warnings={rate_warnings}\n")
        f.write(f"input-sanitize-warnings={sanitize_warnings}\n")
        f.write(f"badge-status={badge_status}\n")

    # Also set for GitHub Actions annotations
    print(f"::notice title=LLM Security Status::{badge_status}")


cfg = load_cfg()
policies = cfg.get("policies", {"api-key-security": True, "rate-limit": True})
failed = False
results = {}

# API Key Security Scanner
if policies.get("api-key-security"):
    res = scan_api_keys(ROOT, cfg)
    results["api_key_security"] = res
    failed |= res["violations"] > 0

    # Output annotations for violations
    if res["violations"] > 0:
        print(f"::error title=API Key Violations::Found {res['violations']} exposed API keys or tokens")
        for detail in res.get("details", [])[:5]:  # Show first 5
            print(f"::error file={detail.split(':')[0]}::{detail}")

# Input Sanitization Scanner
if policies.get("input-sanitize", True):
    res = scan_input_sanitization(ROOT, cfg)
    results["input_sanitize"] = res
    # warn-only → no change to `failed`

    # Output warnings as annotations
    if res.get("total", 0) > 0:
        print(f"::warning title=Input Sanitization::Found {res['total']} potential unsanitized inputs")
        for warning in res.get("warnings", [])[:5]:  # Show first 5
            if ":" in warning:
                parts = warning.split(":", 2)
                print(
                    f"::warning file={parts[0]},line={parts[1]}::{parts[2] if len(parts) > 2 else 'Unsanitized input'}")

# Rate Limit Scanner
if policies.get("rate-limit"):
    res = scan_rate_limits(ROOT, cfg)
    results["rate_limit"] = res
    # warn only; not changing `failed`

    # Output warnings as annotations
    if res.get("total", 0) > 0:
        print(f"::warning title=Rate Limiting::Found {res['total']} LLM calls without rate limiting")
        for warning in res.get("warnings", [])[:5]:  # Show first 5
            if ":" in warning:
                parts = warning.split(":", 2)
                print(
                    f"::warning file={parts[0]},line={parts[1]}::{parts[2] if len(parts) > 2 else 'Missing rate limit'}")

# Pretty print results
print("\n" + "=" * 50)
print("LLM POLICY SCAN RESULTS")
print("=" * 50)
print(json.dumps(results, indent=2))
print("=" * 50 + "\n")

# Emit telemetry
emit_metrics(results, cfg)

# Set GitHub Action outputs
set_github_outputs(results, failed)

# Final status
if failed:
    sys.exit("❌ Policy enforcement failed")
print("✅ All mandatory policies passed")