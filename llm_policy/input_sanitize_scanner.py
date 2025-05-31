import ast, pathlib, re

# Functions we consider as “sanitizers”
SANITIZERS = {
    "html.escape", "re.escape", "bleach.clean", "sanitize_input",
    "strip_tags", "escape_html", "mark_safe", "escape",
}

API_RE = re.compile(r"\b(openai|anthropic|cohere|mistral)\b", re.I)

def _python_warnings(path: pathlib.Path):
    txt = path.read_text("utf-8", "ignore")
    tree = ast.parse(txt, filename=str(path))
    warns = []

    class Flow(ast.NodeVisitor):
        def __init__(self):
            self.tainted = set()

        # Any assignment from input()/request.json/etc. marks variable tainted
        def visit_Call(self, node):
            src = ast.unparse(node.func)
            if src in {"input", "request.get_json", "request.json"}:
                if isinstance(node.parent, ast.Assign):
                    for t in node.parent.targets:
                        if isinstance(t, ast.Name):
                            self.tainted.add(t.id)
            self.generic_visit(node)

        # Detect LLM calls with tainted args and no sanitizer in the call stack
        def visit_Call_final(self, node):
            if API_RE.search(ast.unparse(node.func)):
                for arg in node.args:
                    if isinstance(arg, ast.Name) and arg.id in self.tainted:
                        if not any(san in ast.unparse(node).lower() for san in SANITIZERS):
                            warns.append(f"{path}:{node.lineno} unsanitized input into LLM call")
            self.generic_visit(node)

    # parent links for easier context
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            c.parent = n
    Flow().visit(tree)
    return warns

def scan_input_sanitization(root: pathlib.Path, cfg):
    enabled_langs = set(cfg.get("input-sanitize", {}).get("languages", ["python"]))
    total = []

    if "python" in enabled_langs:
        for p in root.rglob("*.py"):
            try:
                total.extend(_python_warnings(p))
            except Exception:
                pass

    # JS/Go: simple regex search (optional to expand)
    if any(l in enabled_langs for l in ("javascript", "go")):
        TEXT_RE = re.compile(r"(prompt|message|input)\s*[:=].{0,80}\b(openai|anthropic)\b", re.I)
        for p in root.rglob("*.[jt]s") | root.rglob("*.go"):
            txt = p.read_text("utf-8", "ignore")
            if TEXT_RE.search(txt):
                total.append(f"{p}: possible unsanitized input")

    return {"warnings": total[:20], "total": len(total)}
