import ast, pathlib, re

# Refined to match actual method calls like openai.ChatCompletion.create
API_CALL_RE = re.compile(r"\b(openai|anthropic|cohere|mistral)\s*\.\s*\w+", re.I)
SLEEP_FUNCS = {"sleep", "asyncio.sleep"}
SUPPORTED = {"python": [".py"], "javascript": [".js", ".ts"], "go": [".go"]}

def _python_check(path, min_sleep):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        try:
            tree = ast.parse(f.read(), filename=str(path))
        except Exception as e:
            return [f"{path}: failed to parse AST"]
    warnings = []

    class Finder(ast.NodeVisitor):
        def visit_For(self, node):
            self._scan_body(node)
        def visit_While(self, node):
            self._scan_body(node)
        def _scan_body(self, node):
            calls = [n for n in ast.walk(node) if isinstance(n, ast.Call)]
            found_api_call = False
            found_sleep_call = False

            for c in calls:
                if isinstance(c.func, ast.Attribute):
                    if API_CALL_RE.search(ast.unparse(c.func)):
                        found_api_call = True

                if ast.unparse(c.func).split(".")[-1] in SLEEP_FUNCS:
                    found_sleep_call = True
                    if (len(c.args) > 0 and isinstance(c.args[0], ast.Constant) and
                        float(c.args[0].value) < min_sleep):
                        warnings.append(f"{path}:{c.lineno} sleep too short for rate-limit")

            if found_api_call and not found_sleep_call:
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
                    else:
                        txt = path.read_text("utf-8", "ignore")
                        if API_CALL_RE.search(txt) and "sleep" not in txt:
                            warns.append(f"{path}: possible missing rate-limit")
                except Exception:
                    pass
    return {"warnings": warns[:20], "total": len(warns)}