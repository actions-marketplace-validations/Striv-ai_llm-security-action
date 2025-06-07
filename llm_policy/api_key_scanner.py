import re, pathlib, fnmatch

# default prefixes file
DEFAULT_PREFIXES = pathlib.Path("verified_prefixes.txt")


def load_prefixes(extra):
    prefixes = set()
    if DEFAULT_PREFIXES.exists():
        prefixes |= {l.strip() for l in DEFAULT_PREFIXES.read_text().splitlines() if l.strip()}
    prefixes |= set(extra or [])
    return prefixes


# Patterns that are definitely NOT API keys
NOT_KEYS = [
    # File paths and URLs
    r"\.txt$", r"\.py$", r"\.js$", r"\.md$", r"\.yml$", r"\.yaml$", r"\.conf$",
    r"^/", r"^\./", r"^https?://", r"^[a-zA-Z]+://",
    r"/", r"\\",  # Contains path separators

    # Common false positive patterns
    r"^share/", r"^pip-", r"^node_modules/", r"^dist/", r"^build/",
    r"-wheels/", r"-citadel/", r"-directory",

    # Package names, versions, hashes
    r"^[a-z0-9]+-[0-9]+\.[0-9]+",  # package-1.2.3
    r"^sha[0-9]+:",  # sha256:abc123

    # Model names (additional patterns)
    r"^(gpt|claude|llama|mistral|gemini|palm|cohere)-",

    # Configuration values
    r"_backups=[0-9]+$",  # stderr_logfile_backups=5
    r"_maxbytes=[0-9]+[KMG]?B?$",  # stdout_capture_maxbytes=50MB
    r"^[a-z_]+=[0-9]+[a-zA-Z]*$",  # any_config_key=123value
]

NOT_KEYS_RE = re.compile("|".join(NOT_KEYS), re.IGNORECASE)

# Common configuration file patterns
CONFIG_PATTERNS = [
    r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=",  # key = value
    r"^\s*[a-zA-Z_][a-zA-Z0-9_]*:",  # key: value (YAML)
    r"^\s*\[[^\]]+\]",  # [section]
]
CONFIG_RE = re.compile("|".join(CONFIG_PATTERNS))


def is_config_line(line):
    """Check if this line looks like a configuration setting"""
    return bool(CONFIG_RE.match(line))


def is_likely_api_key(text, after_prefix=False, full_line=None):
    """
    Determine if a string is likely an API key based on its characteristics.

    Args:
        text: The string to check
        after_prefix: True if this is the part after a known prefix
        full_line: The complete line for context
    """
    # Definitely not a key if it matches exclusion patterns
    if NOT_KEYS_RE.search(text):
        return False

    # Check if this is part of a configuration line
    if full_line and is_config_line(full_line):
        # Only flag if it really looks like a key (very long, high entropy)
        if len(text) < 30:
            return False

    # If it's after a known prefix, be more lenient
    if after_prefix:
        # Must have reasonable length
        if len(text) < 20:
            return False
        # Must have mix of letters/numbers or high entropy
        if not re.search(r'[0-9]', text) or not re.search(r'[a-zA-Z]', text):
            return False
        return True

    # For standalone strings, be very strict
    # Must be very long and look like a token
    if len(text) < 40:
        return False

    # Must have good character distribution (not just letters or numbers)
    has_upper = bool(re.search(r'[A-Z]', text))
    has_lower = bool(re.search(r'[a-z]', text))
    has_digit = bool(re.search(r'[0-9]', text))

    # Need at least 2 of 3 character types
    char_types = sum([has_upper, has_lower, has_digit])
    if char_types < 2:
        return False

    # Check entropy (simple approximation)
    unique_chars = len(set(text))
    if unique_chars < len(text) * 0.5:  # Low entropy
        return False

    return True


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

        # Skip .gitignore and common config files entirely
        if path.name in [".gitignore", "supervisord.conf", "supervisor.conf"]:
            continue

        # Skip common configuration file extensions
        if path.suffix in [".conf", ".ini", ".cfg", ".config", ".toml"]:
            # Only scan if explicitly not excluded
            if any(fnmatch.fnmatch(str(path), "*.conf") for pat in exclude_globs):
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

            # Skip lines that are obviously not containing keys
            if line_stripped.startswith('.') or line_stripped.endswith('/'):
                continue

            # Check for API key prefixes
            prefix_match = prefix_re.search(line)
            if prefix_match:
                # Extract the full potential key (prefix + following characters)
                start_pos = prefix_match.start()
                # Only capture alphanumeric and common key chars, stop at spaces/quotes
                potential_key = re.match(r'[A-Za-z0-9+/=_-]+', line[start_pos:])

                if potential_key:
                    full_key = potential_key.group()
                    after_prefix = full_key[len(prefix_match.group()):]

                    if is_likely_api_key(after_prefix, after_prefix=True, full_line=line_stripped):
                        viol.append(f"{path}:{i}: {line_stripped[:120]}")

            # For standalone high entropy detection, be VERY conservative
            else:
                # Skip configuration lines unless they have extremely suspicious patterns
                if is_config_line(line):
                    continue

                # Look for token-like patterns (must have specific characteristics)
                token_pattern = re.compile(r'\b[A-Za-z0-9_-]{40,}\b')
                for match in token_pattern.finditer(line):
                    candidate = match.group()
                    if is_likely_api_key(candidate, after_prefix=False, full_line=line_stripped):
                        # Extra check: not in a URL or file path context
                        surrounding = line[max(0, match.start() - 10):match.end() + 10]
                        if not any(sep in surrounding for sep in ['/', '\\', '://', 'http', '.com', '.org']):
                            viol.append(f"{path}:{i}: {line_stripped[:120]}")
                            break

    return {"violations": len(viol), "details": viol[:20]}  # cap output