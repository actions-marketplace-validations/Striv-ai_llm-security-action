import hashlib, json, os, uuid, urllib.request

ENDPOINT = "https://llm-policy-telemetry.example.com"   # placeholder

def emit_metrics(results, cfg):
    if os.getenv("LLM_POLICY_TELEMETRY", "on") == "off":
        return
    repo = os.getenv("GITHUB_REPOSITORY", "")
    payload = {
        "repo_id": hashlib.sha256(repo.encode()).hexdigest()[:12],
        "run_id": os.getenv("GITHUB_RUN_ID"),
        "violations": results,
        "uuid": str(uuid.uuid4())[:8],
    }
    try:
        req = urllib.request.Request(
            ENDPOINT,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            timeout=2,
        )
        urllib.request.urlopen(req)
    except Exception:
        pass  # silent fail
