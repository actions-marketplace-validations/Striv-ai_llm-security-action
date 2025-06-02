import fnmatch, pathlib, re

# ------------ Default Provider Prefixes ------------
DEFAULT_PREFIXES = {
    "sk-",          # OpenAI
    "sk-ant-",      # Anthropic
    "hf_",          # HF
    "AKIA",         # AWS key id
    "azure_openai_",  # Azure env var
    "cohere-",
    "mistral-",
    "claude-",
    "gpt-4",        # model IDs can leak
    "llama-3",
    "phi-2",
}

# Provider prefixes compiled with a word-boundary/look-behind
PREFIX_RE = re.compile(
    r"(?<![A-Za-z0-9_\-])(" + "|".join(re.escape(p) for p in DEFAULT_PREFIXES) + r")",
    re.IGNORECASE,
)

# Files to skip entirely
IGNORE_FILES = {
    ".gitattributes", ".gitignore",
    "requirements.txt", "poetry.lock", "package.json",
}

# Wildcard path skips
DEFAULT_GLOBS = [
    "**/.git/*", "**/__pycache__/*", "**/*.pyc", "**/*.class",
    "**/*.png", "**/*.jpg", "**/*.md", "**/*.rst",
    "**/llm_policy/**", "**/.github/**", "**/scripts/**",
]

def is_comment_or_pattern(line: str) -> bool:
    stripped = line.strip()
    # Comments or ignore wildcards
    return (
        stripped.startswith("#")
        or stripped.startswith("*")
        or stripped.startswith("!")
        or stripped == ""
    )

def scan_api_keys(root: pathlib.Path, cfg):
    # Allow users to add extra prefixes
    custom = set(cfg.get("custom-api-key-prefixes", []))
    regex = re.compile(
        r"(?<![A-Za-z0-9_\-])(" + "|".join(
            re.escape(p) for p in sorted(DEFAULT_PREFIXES | custom, key=len, reverse=True)
        ) + r")",
        re.IGNORECASE,
    )

    exclude_globs = DEFAULT_GLOBS + cfg.get("exclude_globs", [])
    violations = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        rel = path.as_posix()
        if any(fnmatch.fnmatch(rel, pat) for pat in exclude_globs):
            continue
        if path.name in IGNORE_FILES:
            continue

        try:
            for lineno, line in enumerate(path.read_text("utf-8", "ignore").splitlines(), 1):
                if is_comment_or_pattern(line):
                    continue
                if regex.search(line):
                    violations.append(f"{rel}:{lineno}: {line.strip()[:120]}")
                    if len(violations) >= 20:  # cap output
                        break
        except Exception:
            continue

    return {"violations": len(violations), "details": violations}
