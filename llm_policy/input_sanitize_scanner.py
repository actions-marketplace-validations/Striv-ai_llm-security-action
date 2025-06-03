import ast
import pathlib
import re
import itertools
from typing import Set, List, Dict

# ----------------------- Configuration -----------------------
SANITIZERS = {
    "html.escape", "re.escape", "bleach.clean", "sanitize_input",
    "strip_tags", "escape_html", "mark_safe", "escape"
}

# Add known LLM API identifiers (customizable)
LLM_APIS = re.compile(r"\b(openai|anthropic|cohere|mistral|llama|langchain|huggingface|transformers)\b", re.I)

# Strings to check for prompt injection red flags
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore (previous|all) instructions"),
    re.compile(r"(?i)you are now"),
    re.compile(r"(?i)as an ai")
]

# ----------------------- AST Scanner -----------------------
def _python_warnings(path: pathlib.Path):
    txt = path.read_text("utf-8", "ignore")
    tree = ast.parse(txt, filename=str(path))
    warns = []

    class Flow(ast.NodeVisitor):
        def __init__(self):
            self.tainted: Set[str] = set()
            self.sanitized: Set[str] = set()

        def visit_Assign(self, node):
            value = node.value
            targets = node.targets
            # Track tainted assignments
            if isinstance(value, ast.Call):
                func_name = ast.unparse(value.func)
                if func_name in {"input", "request.get_json", "request.json"}:
                    for t in targets:
                        if isinstance(t, ast.Name):
                            self.tainted.add(t.id)
                elif any(s in func_name for s in SANITIZERS):
                    for t in targets:
                        if isinstance(t, ast.Name):
                            self.sanitized.add(t.id)
                elif any(isinstance(arg, ast.Name) and arg.id in self.tainted for arg in value.args):
                    for t in targets:
                        if isinstance(t, ast.Name):
                            self.tainted.add(t.id)  # Propagate taint
            elif isinstance(value, ast.Name) and value.id in self.tainted:
                for t in targets:
                    if isinstance(t, ast.Name):
                        self.tainted.add(t.id)  # Propagate taint
            self.generic_visit(node)

        def visit_Call(self, node):
            func_name = ast.unparse(node.func)

            if LLM_APIS.search(func_name):
                # Scan arguments for tainted usage
                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        varname = arg.id
                        if varname in self.tainted and varname not in self.sanitized:
                            warns.append(f"{path}:{node.lineno} UNSAFE: unsanitized input into LLM call: '{func_name}'")
                    elif isinstance(arg, ast.JoinedStr):
                        for val in arg.values:
                            if isinstance(val, ast.FormattedValue) and isinstance(val.value, ast.Name):
                                varname = val.value.id
                                if varname in self.tainted and varname not in self.sanitized:
                                    warns.append(f"{path}:{node.lineno} UNSAFE: tainted f-string in LLM call")

            # Detect suspicious string content (e.g., prompt injections)
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    # Skip if this is part of PROMPT_INJECTION_PATTERNS declaration
                    parent = getattr(arg, 'parent', None)
                    grandparent = getattr(parent, 'parent', None)
                    if isinstance(parent, ast.List) and isinstance(grandparent, ast.Assign):
                        if any(isinstance(t, ast.Name) and t.id == "PROMPT_INJECTION_PATTERNS" for t in grandparent.targets):
                            continue  # skip pattern list definitions
                    for patt in PROMPT_INJECTION_PATTERNS:
                        if patt.search(arg.value):
                            warns.append(f"{path}:{node.lineno} SUSPICIOUS: possible prompt injection pattern")

            self.generic_visit(node)

    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            c.parent = n

    Flow().visit(tree)
    return warns

# ----------------------- Main Entry Scanner -----------------------
def scan_input_sanitization(root: pathlib.Path, cfg: Dict):
    enabled_langs = set(cfg.get("input-sanitize", {}).get("languages", ["python"]))
    total: List[str] = []

    # Python (AST-based)
    if "python" in enabled_langs:
        for p in root.rglob("*.py"):
            try:
                total.extend(_python_warnings(p))
            except Exception as e:
                total.append(f"{p}: ERROR scanning file - {e}")

    # JS/TS/Go (heuristic based)
    if enabled_langs.intersection({"javascript", "go"}):
        text_re = re.compile(r"(prompt|message|input)\s*[:=].{0,100}\b(openai|anthropic|llama)\b", re.I)
        for p in itertools.chain(root.rglob("*.js"), root.rglob("*.ts"), root.rglob("*.go")):
            try:
                txt = p.read_text("utf-8", "ignore")
                if text_re.search(txt):
                    total.append(f"{p}: heuristic match for unsanitized input into LLM API")
            except Exception as e:
                total.append(f"{p}: ERROR reading file - {e}")

    return {
        "warnings": total[:100],  # truncate output to first 100
        "total": len(total)
    }
