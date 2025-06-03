import re, pathlib, fnmatch

# default prefixes file
DEFAULT_PREFIXES = pathlib.Path("verified_prefixes.txt")
MODEL_EXCLUDE_FILE = pathlib.Path("model_names_exclude.txt")

# Common model name patterns that should NOT be flagged
MODEL_PATTERNS = [
    r"gpt-[0-9]+(\.[0-9]+)?(-[a-z]+)*",  # gpt-4, gpt-3.5-turbo
    r"claude-[0-9]+(-[a-z]+)*",  # claude-3-opus, claude-2
    r"mistral-[a-z]+(-[0-9]+(\.[0-9]+)?)?(-[a-z0-9]+)*",  # mistral-medium-2505
    r"llama-[0-9]+(\.[0-9]+)?(-[0-9]+b)?(-[a-z]+)*",  # llama-3.3-70b-instruct
    r"gemini-[0-9]+(\.[0-9]+)?(-[a-z]+)*",  # gemini-1.5-pro
    r"anthropic/[a-z-]+",  # anthropic/claude-3
    r"openai/[a-z0-9-]+",  # openai/gpt-4
    r"meta-llama/[a-z0-9-]+",  # meta-llama/llama-3
    r"cohere-[a-z]+",  # cohere-command
    r"text-[a-z]+-[0-9]+",  # text-davinci-003
    r"code-[a-z]+-[0-9]+",  # code-davinci-002
]

MODEL_RE = re.compile("|".join(MODEL_PATTERNS), re.IGNORECASE)


def load_prefixes(extra):
    prefixes = set()
    if DEFAULT_PREFIXES.exists():
        prefixes |= {l.strip() for l in DEFAULT_PREFIXES.read_text().splitlines() if l.strip()}
    prefixes |= set(extra or [])
    return prefixes


# High entropy pattern - but must be AFTER a prefix, not including it
HIGH_ENTROPY = re.compile(r"[A-Za-z0-9+/=_-]{32,}")


def is_likely_model_name(text):
    """Check if the text looks like a model name rather than an API key"""
    # If it matches known model patterns, it's not an API key
    if MODEL_RE.match(text):
        return True

    # Additional heuristics for model names
    # Model names often have version numbers and descriptive words
    if re.match(r"^[a-z]+-[0-9]+(\.[0-9]+)?(-[a-z]+)*$", text.lower()):
        return True

    return False


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
            # Skip comments and empty lines
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('//'):
                continue

            # Check for API key prefixes
            prefix_match = prefix_re.search(line)
            if prefix_match:
                # Extract the full potential key (prefix + following characters)
                start_pos = prefix_match.start()
                potential_key = re.match(r'[A-Za-z0-9+/=_-]+', line[start_pos:])

                if potential_key:
                    full_key = potential_key.group()

                    # Skip if it looks like a model name
                    if is_likely_model_name(full_key):
                        continue

                    # Check if there's high entropy AFTER the prefix
                    after_prefix = full_key[len(prefix_match.group()):]
                    if len(after_prefix) >= 20:  # Reasonable minimum for API keys
                        viol.append(f"{path}:{i}: {line_stripped[:120]}")

            # Also check for standalone high entropy strings (but not model names)
            elif HIGH_ENTROPY.search(line):
                # Extract all high entropy strings
                for match in HIGH_ENTROPY.finditer(line):
                    candidate = match.group()
                    # Skip if it looks like a model name or base64 data
                    if not is_likely_model_name(candidate) and not candidate.endswith('='):
                        # Only flag if it's really suspicious (very long)
                        if len(candidate) >= 40:
                            viol.append(f"{path}:{i}: {line_stripped[:120]}")
                            break

    return {"violations": len(viol), "details": viol[:20]}  # cap output