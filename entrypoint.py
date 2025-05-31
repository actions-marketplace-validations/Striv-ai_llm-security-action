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

cfg = load_cfg()
policies = cfg.get("policies", {"api-key-security": True, "rate-limit": True})
failed = False
results = {}

if policies.get("api-key-security"):
    res = scan_api_keys(ROOT, cfg)
    results["api_key_security"] = res
    failed |= res["violations"] > 0


if policies.get("input-sanitize", True):
    res = scan_input_sanitization(ROOT, cfg)
    results["input_sanitize"] = res
    # warn-only → no change to `failed`


if policies.get("rate-limit"):
    res = scan_rate_limits(ROOT, cfg)
    results["rate_limit"] = res
    # warn only; not changing `failed`

print(json.dumps(results, indent=2))

emit_metrics(results, cfg)          # anonymized/opt-out

if failed:
    sys.exit("❌ Policy enforcement failed")
print("✅ All mandatory policies passed")
