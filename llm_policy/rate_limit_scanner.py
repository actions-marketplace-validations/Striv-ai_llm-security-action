import ast, pathlib, re

API_CALL_RE = re.compile(r"\b(openai|anthropic|cohere|mistral)\b", re.I)
SLEEP_FUNCS = {"sleep", "asyncio.sleep"}
SUPPORTED = {"python": [".py"], "javascript": [".js", ".ts"], "go": [".go"]}

def _python_check(path, min_sleep):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        tree = ast.parse(f.read(), filename=str(path))
    warnings = []
    class Finder(ast.NodeVisitor):
        def visit_For(self, node):
            self._scan_body(node)
        def visit_While(self, node):
            self._scan_body(node)
        def _scan_body(self, node):
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            if any(API_CALL_RE.search(ast.unparse(c.func)) for c in calls):
                if not any(ast.unparse(c.func).split(".")[-1] in SLEEP_FUNCS for c in calls):
                    warnings.append(f"{path}:{node.lineno} missing rate-limit")
    Finder().visit(tree)
    return warnings

def scan_rate_limits(root: pathlib.Path, cfg):
    langs = set(cfg.get("rate-limit", {}).get("languages", SUPPORTED.keys()))
    min_sleep = cfg.get("rate-limit", {}).get("min-sleep-seconds", 1.0)
    warns = []
    for lang, exts in SUPPORTED.items():
        if lang not in langs:
            continue
        for path in root.rglob("*"):
            if path.suffix in exts:
                try:
                    if lang == "python":
                        warns += _python_check(path, min_sleep)
                    # JS/Go stubs: regex fall-back (simpler)
                    else:
                        txt = path.read_text("utf-8", "ignore")
                        if API_CALL_RE.search(txt) and "sleep" not in txt:
                            warns.append(f"{path}: possible missing rate-limit")
                except Exception:
                    pass
    return {"warnings": warns[:20], "total": len(warns)}
