import re, pathlib, fnmatch

# default prefixes file
DEFAULT_PREFIXES = pathlib.Path("verified_prefixes.txt")

def load_prefixes(extra):
    prefixes = set()
    if DEFAULT_PREFIXES.exists():
        prefixes |= {l.strip() for l in DEFAULT_PREFIXES.read_text().splitlines() if l.strip()}
    prefixes |= set(extra or [])
    return prefixes

HIGH_ENTROPY = re.compile(r"[A-Za-z0-9+/=_-]{32,}")

def scan_api_keys(root: pathlib.Path, cfg):
    prefixes = load_prefixes(cfg.get("custom-api-key-prefixes"))
    prefix_re = re.compile(r"|".join(re.escape(p) for p in prefixes), re.IGNORECASE)
    default_ex = [".git/*", "__pycache__/*", "*.pyc", "verified_prefixes.txt"]
    exclude_globs = cfg.get("exclude_globs", default_ex)
    viol = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(fnmatch.fnmatch(str(path), pat) for pat in exclude_globs):
            continue
        text = ""
        try:
            text = path.read_text("utf-8", "ignore")
        except Exception:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if prefix_re.search(line) or HIGH_ENTROPY.search(line):
                viol.append(f"{path}:{i}: {line.strip()[:120]}")
    return {"violations": len(viol), "details": viol[:20]}  # cap output
