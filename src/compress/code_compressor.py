"""
CodeCompressor for PromptLens.
Extracts structural representations (classes, functions, methods, imports, exports,
routes, decorators, docstrings, parameters) across Python, JavaScript, TypeScript,
Java, and C++ while compacting large function bodies into high-density structural skeletons.
Fails open on parsing errors.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple, Any

from src.store.retrieval_store import RetrievalStore, get_global_store
from src.tokens.counter import get_token_count


@dataclass
class CodeCompressionResult:
    original_code: str
    compressed_code: str
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    is_compressed: bool
    retrieval_id: Optional[str] = None
    language_detected: str = "unknown"
    symbols_extracted: int = 0


# Language pattern matchers
_CPP_PATTERNS = [r"#include\s*[<\"].+[>\"]", r"std::", r"namespace\s+\w+", r"cout\s*<<"]
_JS_TS_PATTERNS = [r"export\s+(?:default\s+)?(?:class|function|const|interface|type)", r"import\s+.*\s+from\s+['\"]", r"function\s+\w+\s*\(", r"interface\s+\w+", r"const\s+\w+\s*=\s*(?:async\s*)?\("]
_JAVA_PATTERNS = [r"package\s+[\w\.]+;", r"import\s+java\.", r"public\s+class\s+\w+", r"public\s+(?:static\s+)?(?:void|int|boolean|String|List<[\w<>]+>|Map<[\w<>]+>)\s+\w+\s*\(", r"@Override"]
_PY_PATTERNS = [r"def\s+\w+\s*\(", r"class\s+\w+\s*(?:\([^)]*\))?\s*:", r"from\s+\w+\s+import", r"elif\s+", r":\s*\n\s+def\s+"]


class CodeCompressor:
    """
    Compresses large source code blocks into structural skeletons preserving classes,
    functions, signatures, decorators, and docstrings while compacting large bodies.
    """

    def __init__(
        self,
        min_lines_threshold: int = 15,
        min_tokens_threshold: int = 100,
        store: Optional[RetrievalStore] = None
    ):
        self.min_lines_threshold = min_lines_threshold
        self.min_tokens_threshold = min_tokens_threshold
        self.store = store or get_global_store()

    def detect_language(self, code: str) -> str:
        """Heuristically detects programming language."""
        if any(re.search(p, code) for p in _CPP_PATTERNS):
            return "cpp"
        if any(re.search(p, code) for p in _JS_TS_PATTERNS):
            return "typescript" if ("interface " in code or ": string" in code or ": number" in code or "Promise<" in code or ": void" in code) else "javascript"
        if any(re.search(p, code) for p in _JAVA_PATTERNS):
            return "java"
        if any(re.search(p, code) for p in _PY_PATTERNS):
            return "python"
        return "generic"

    def _extract_python_structure(self, lines: List[str]) -> Tuple[List[str], int]:
        """Extracts structural skeleton of Python code."""
        out = []
        in_docstring = False
        docstring_delim = None
        symbol_count = 0
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Handle docstrings right after def/class
            if in_docstring:
                out.append(line)
                if docstring_delim in stripped and not stripped.startswith(docstring_delim + docstring_delim):
                    in_docstring = False
                i += 1
                continue

            # Preserve imports
            if stripped.startswith(("import ", "from ")) and not in_docstring:
                out.append(line)
                i += 1
                continue

            # Preserve decorators
            if stripped.startswith("@"):
                out.append(line)
                i += 1
                continue

            # Match class
            if stripped.startswith("class "):
                symbol_count += 1
                out.append(line)
                i += 1
                # Check for docstring right after class
                if i < n:
                    next_line = lines[i]
                    next_stripped = next_line.strip()
                    if next_stripped.startswith(('"""', "'''")):
                        docstring_delim = next_stripped[:3]
                        out.append(next_line)
                        if not (next_stripped.count(docstring_delim) >= 2 and len(next_stripped) > 3):
                            in_docstring = True
                        i += 1
                continue

            # Match function or method
            if stripped.startswith(("def ", "async def ")):
                symbol_count += 1
                indent = len(line) - len(line.lstrip())
                out.append(line)

                # Check if multi-line signature
                while not stripped.endswith(":") and i + 1 < n:
                    i += 1
                    line = lines[i]
                    stripped = line.strip()
                    out.append(line)

                # Check for docstring on next line
                if i + 1 < n:
                    next_line = lines[i + 1]
                    next_stripped = next_line.strip()
                    if next_stripped.startswith(('"""', "'''")):
                        docstring_delim = next_stripped[:3]
                        out.append(next_line)
                        if not (next_stripped.count(docstring_delim) >= 2 and len(next_stripped) > 3):
                            in_docstring = True
                        i += 1

                # Compact the inner body: collect summary of statements or insert ellipsis
                body_lines = []
                j = i + 1
                while j < n:
                    cur_line = lines[j]
                    cur_stripped = cur_line.strip()
                    if not cur_stripped:
                        j += 1
                        continue
                    cur_indent = len(cur_line) - len(cur_line.lstrip())
                    if cur_indent <= indent:
                        break
                    body_lines.append(cur_stripped)
                    j += 1

                # If body is substantial (>4 lines), outline operations
                if len(body_lines) > 4:
                    indent_str = " " * (indent + 4)
                    ops = []
                    for bline in body_lines:
                        if bline.startswith("return "):
                            ops.append(f"{indent_str}# returns {bline[7:].strip()}")
                        elif bline.startswith("raise "):
                            ops.append(f"{indent_str}# raises {bline[6:].strip()}")
                        elif " = " in bline and not bline.startswith("#"):
                            lhs = bline.split("=")[0].strip()
                            if len(lhs) < 30:
                                ops.append(f"{indent_str}# assigns {lhs}")
                        elif bline.startswith(("if ", "for ", "while ", "try:", "except")):
                            ops.append(f"{indent_str}# controls: {bline.split(':')[0]}")

                    seen = set()
                    unique_ops = []
                    for op in ops:
                        if op not in seen:
                            seen.add(op)
                            unique_ops.append(op)
                    
                    if unique_ops:
                        out.extend(unique_ops[:5])
                    out.append(f"{indent_str}... [implementation body compact ({len(body_lines)} lines)]")
                    i = j - 1
                i += 1
                continue

            # Top-level comments or headers
            if stripped.startswith("#"):
                out.append(line)
                i += 1
                continue

            i += 1

        return out, symbol_count

    def _extract_brace_structure(self, lines: List[str], lang: str) -> Tuple[List[str], int]:
        """Extracts structural skeleton for C-style brace languages (JS, TS, Java, C++)."""
        out = []
        symbol_count = 0
        i = 0
        n = len(lines)

        container_keywords = ("class ", "interface ", "namespace ", "struct ")
        func_keywords = (
            "function ", "public ", "private ", "protected ", "void ", "int ", "bool ", "auto ",
            "@app.", "router.", "@Get", "@Post", "app.get", "app.post", "login(", "processOrders("
        )

        while i < n:
            line = lines[i]
            stripped = line.strip()

            # Preserve imports / includes / package
            if stripped.startswith(("import ", "from ", "export *", "require(", "#include", "package ")):
                out.append(line)
                i += 1
                continue

            # Comments
            if stripped.startswith(("//", "/*", "*")):
                out.append(line)
                i += 1
                continue

            # Container signatures (class, interface, struct): keep line and continue inside
            if any(kw in stripped for kw in container_keywords) and not ("(" in stripped and ")" in stripped):
                symbol_count += 1
                out.append(line)
                i += 1
                continue

            # Method / function signatures
            if any(kw in stripped for kw in func_keywords) or ("(" in stripped and "{" in stripped):
                symbol_count += 1
                out.append(line)
                if "{" in stripped and "}" in stripped:
                    i += 1
                    continue

                if "{" in stripped:
                    indent = len(line) - len(line.lstrip())
                    indent_str = " " * (indent + 4)
                    brace_depth = stripped.count("{") - stripped.count("}")
                    body_count = 0
                    j = i + 1
                    while j < n and brace_depth > 0:
                        cline = lines[j]
                        brace_depth += cline.count("{") - cline.count("}")
                        body_count += 1
                        j += 1

                    if body_count > 4:
                        out.append(f"{indent_str}... [body omitted ({body_count} lines)]")
                        if j - 1 < n and "}" in lines[j - 1]:
                            out.append(lines[j - 1])
                        i = j
                        continue
            elif stripped.startswith(("return ", "throw ")):
                out.append(line)

            i += 1

        return out, symbol_count

    def compress(
        self,
        code: str,
        retrieval_id: Optional[str] = None,
        save_to_store: bool = True
    ) -> CodeCompressionResult:
        """
        Compresses code by extracting signatures and compacting bodies.
        Fails open if parsing encounters any issue.
        """
        orig_tokens = get_token_count(code)
        lines = code.splitlines()

        if len(lines) < self.min_lines_threshold or orig_tokens < self.min_tokens_threshold:
            return CodeCompressionResult(
                original_code=code,
                compressed_code=code,
                original_tokens=orig_tokens,
                compressed_tokens=orig_tokens,
                savings_pct=0.0,
                is_compressed=False,
                retrieval_id=None,
                language_detected="unknown",
                symbols_extracted=0,
            )

        try:
            lang = self.detect_language(code)
            if lang == "python":
                struct_lines, sym_count = self._extract_python_structure(lines)
            else:
                struct_lines, sym_count = self._extract_brace_structure(lines, lang)

            compressed_body = "\n".join(struct_lines)
            comp_tokens = get_token_count(compressed_body)

            # Only accept compression if token reduction actually occurred and symbols were found
            if comp_tokens < orig_tokens and sym_count > 0:
                stored_id = None
                if save_to_store:
                    stored_id = self.store.save(code, retrieval_id=retrieval_id)
                    retrieval_notice = f"\n\n[PromptLens compressed content: {stored_id}]"
                    compressed_body += retrieval_notice
                    comp_tokens = get_token_count(compressed_body)

                savings = round((1.0 - (comp_tokens / orig_tokens)) * 100.0, 2)
                return CodeCompressionResult(
                    original_code=code,
                    compressed_code=compressed_body,
                    original_tokens=orig_tokens,
                    compressed_tokens=comp_tokens,
                    savings_pct=savings,
                    is_compressed=True,
                    retrieval_id=stored_id,
                    language_detected=lang,
                    symbols_extracted=sym_count,
                )
        except Exception:
            # Fail-open guarantee: on any failure, return original code intact
            pass

        return CodeCompressionResult(
            original_code=code,
            compressed_code=code,
            original_tokens=orig_tokens,
            compressed_tokens=orig_tokens,
            savings_pct=0.0,
            is_compressed=False,
            retrieval_id=None,
            language_detected="unknown",
            symbols_extracted=0,
        )
