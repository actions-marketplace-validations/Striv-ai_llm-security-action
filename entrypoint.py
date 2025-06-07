#!/usr/bin/env python3
import sys, json, pathlib, os
from llm_policy import api_key_scanner, rate_limiter, input_sanitizer

CONFIG_FILE = "llm-policy.yml"


def load_config():
    if pathlib.Path(CONFIG_FILE).exists():
        import yaml
        return yaml.safe_load(pathlib.Path(CONFIG_FILE).read_text())
    return {"policies": {"api-key-security": True, "rate-limit": True, "input-sanitize": True}}


def set_github_output(name, value):
    """Set output for GitHub Actions"""
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
            f.write(f"{name}={value}\n")


def main():
    print("Starting LLM Policy Scanner...")
    cfg = load_config()
    repo_root = pathlib.Path(".")

    results = {}
    violations = 0
    warnings = 0
    has_error = False  # Now only for actual errors, not security issues

    # Run enabled scanners
    if cfg["policies"].get("api-key-security", True):
        print("\n🔍 Scanning for API Keys...")
        try:
            res = api_key_scanner.scan_api_keys(repo_root, cfg)
            results["api_key_security"] = res
            if res["violations"] > 0:
                # API keys are now warnings, not errors
                warnings += res["violations"]
                for detail in res["details"]:
                    # Use warning annotation instead of error
                    print(
                        f"::warning file={detail.split(':')[0]},line={detail.split(':')[1]}::Potential API key found: {detail}")
        except Exception as e:
            print(f"Error in API key scanner: {e}")
            has_error = True

    if cfg["policies"].get("rate-limit", True):
        print("\n⏱️  Checking Rate Limits...")
        try:
            res = rate_limiter.scan_rate_limits(repo_root, cfg)
            results["rate_limit"] = res
            if res["warnings"] > 0:
                warnings += res["warnings"]
                for detail in res["details"]:
                    print(f"::warning file={detail.split(':')[0]},line={detail.split(':')[1]}::{detail}")
        except Exception as e:
            print(f"Error in rate limit scanner: {e}")
            has_error = True

    if cfg["policies"].get("input-sanitize", True):
        print("\n🛡️  Checking Input Sanitization...")
        try:
            res = input_sanitizer.scan_input_sanitization(repo_root, cfg)
            results["input_sanitize"] = res
            if res["warnings"] > 0:
                warnings += res["warnings"]
                for detail in res["details"]:
                    print(f"::warning file={detail.split(':')[0]},line={detail.split(':')[1]}::{detail}")
        except Exception as e:
            print(f"Error in input sanitizer: {e}")
            has_error = True

    # Summary
    print("\n" + "=" * 50)
    print("LLM POLICY SCAN RESULTS")
    print("=" * 50)
    print(json.dumps(results, indent=2))
    print("=" * 50)

    # Determine status - only fail on actual errors, not security findings
    if has_error:
        status = "failed"
        badge_status = "❌ Error"
        print("\nNotice: ❌ Scan encountered errors")
    elif warnings > 0:
        status = "warning"
        badge_status = "⚠️ Warnings"
        print(f"\nNotice: ⚠️ Found {warnings} warnings")
    else:
        status = "passed"
        badge_status = "✅ Secured"
        print("\nNotice: ✅ All checks passed!")

    # Set GitHub outputs
    set_github_output("status", status)
    set_github_output("api-key-violations", results.get("api_key_security", {}).get("violations", 0))
    set_github_output("rate-limit-warnings", results.get("rate_limit", {}).get("warnings", 0))
    set_github_output("input-sanitize-warnings", results.get("input_sanitize", {}).get("warnings", 0))
    set_github_output("badge-status", badge_status)

    # Exit based on errors only, not security findings
    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()