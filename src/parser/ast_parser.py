import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SymbolKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    ROUTE = "route"
    INTERFACE = "interface"
    SCHEMA = "schema"
    MODULE_VARIABLE = "variable"
    IMPORT = "import"


@dataclass
class CodeSymbol:
    name: str
    kind: SymbolKind
    signature: str
    start_line: int
    end_line: int
    full_code: str
    skeleton_code: str
    docstring: Optional[str] = None
    parent_class: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)  # Symbols referenced or called
    filepath: Optional[str] = None
    full_tokens: int = 0
    skeleton_tokens: int = 0


@dataclass
class ParsedCodeFile:
    filepath: str
    language: str
    symbols: list[CodeSymbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    raw_code: str = ""
    full_skeleton: str = ""


class ASTParser:
    """
    Multi-language AST and structural parser for Python, JS/TS, Go, Java, Rust.
    Parses code into hierarchical CodeSymbols with full source vs compact skeletons.
    """

    def parse(self, code: str, language: str = "python", filepath: Optional[str] = None) -> ParsedCodeFile:
        lang = language.lower() if language else "python"
        filepath = filepath or f"snippet.{lang}"

        if lang in ("python", "py"):
            return self._parse_python(code, filepath)
        elif lang in ("javascript", "typescript", "js", "ts", "jsx", "tsx"):
            return self._parse_javascript(code, filepath, lang)
        else:
            return self._parse_generic(code, filepath, lang)

    def _parse_python(self, code: str, filepath: str) -> ParsedCodeFile:
        symbols: list[CodeSymbol] = []
        imports: list[str] = []
        lines = code.splitlines()

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fallback to generic structural parsing if syntax is incomplete
            return self._parse_generic(code, filepath, "python")

        # 1. Collect Imports & module-level dependencies
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"{mod}.{alias.name}" if mod else alias.name)

        # Helper to get source segment
        def get_source(node: ast.AST) -> str:
            start = getattr(node, 'lineno', 1) - 1
            end = getattr(node, 'end_lineno', len(lines))
            return "\n".join(lines[start:end])

        # Helper to extract function calls / dependencies in a subtree
        def extract_calls(node: ast.AST) -> list[str]:
            calls = []
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        calls.append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        calls.append(child.func.attr)
            return list(dict.fromkeys(calls))

        # 2. Extract Top-level and Class functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig_prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
                args_str = self._format_py_args(node.args)
                ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
                sig = f"{sig_prefix}{node.name}({args_str}){ret_str}"
                
                doc = ast.get_docstring(node)
                doc_str = f'\n    """{doc}"""' if doc else ""
                skeleton = f"{sig}:{doc_str}\n    ..."
                full = get_source(node)
                calls = extract_calls(node)

                # Check if route decorator (e.g. @app.get('/users'))
                is_route = any(
                    isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ('get', 'post', 'put', 'delete', 'patch')
                    for dec in node.decorator_list
                )

                symbols.append(CodeSymbol(
                    name=node.name,
                    kind=SymbolKind.ROUTE if is_route else SymbolKind.FUNCTION,
                    signature=sig,
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    full_code=full,
                    skeleton_code=skeleton,
                    docstring=doc,
                    dependencies=calls,
                    filepath=filepath,
                ))

            elif isinstance(node, ast.ClassDef):
                bases_str = f"({', '.join(ast.unparse(b) for b in node.bases)})" if node.bases else ""
                class_sig = f"class {node.name}{bases_str}"
                class_doc = ast.get_docstring(node)
                
                method_skeletons = []
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_prefix = "async def " if isinstance(sub, ast.AsyncFunctionDef) else "def "
                        m_args = self._format_py_args(sub.args)
                        m_ret = f" -> {ast.unparse(sub.returns)}" if sub.returns else ""
                        m_sig = f"{m_prefix}{sub.name}({m_args}){m_ret}"
                        m_doc = ast.get_docstring(sub)
                        m_skel = f"    {m_sig}:\n        ..."
                        method_skeletons.append(m_skel)

                        symbols.append(CodeSymbol(
                            name=f"{node.name}.{sub.name}",
                            kind=SymbolKind.METHOD,
                            signature=m_sig,
                            start_line=sub.lineno,
                            end_line=getattr(sub, 'end_lineno', sub.lineno),
                            full_code=get_source(sub),
                            skeleton_code=m_skel,
                            docstring=m_doc,
                            parent_class=node.name,
                            dependencies=extract_calls(sub),
                            filepath=filepath,
                        ))

                class_skel_lines = [f"{class_sig}:"]
                if class_doc:
                    class_skel_lines.append(f'    """{class_doc}"""')
                if method_skeletons:
                    class_skel_lines.extend(method_skeletons)
                else:
                    class_skel_lines.append("    ...")

                symbols.append(CodeSymbol(
                    name=node.name,
                    kind=SymbolKind.CLASS,
                    signature=class_sig,
                    start_line=node.lineno,
                    end_line=getattr(node, 'end_lineno', node.lineno),
                    full_code=get_source(node),
                    skeleton_code="\n".join(class_skel_lines),
                    docstring=class_doc,
                    dependencies=extract_calls(node),
                    filepath=filepath,
                ))

        # Build full file skeleton
        full_skel_parts = []
        if imports:
            full_skel_parts.append("\n".join(f"import {imp}" for imp in imports[:8]))
        for sym in symbols:
            if not sym.parent_class:  # Only top-level symbols in file skeleton
                full_skel_parts.append(sym.skeleton_code)

        return ParsedCodeFile(
            filepath=filepath,
            language="python",
            symbols=symbols,
            imports=imports,
            raw_code=code,
            full_skeleton="\n\n".join(full_skel_parts) if full_skel_parts else code,
        )

    def _format_py_args(self, args: ast.arguments) -> str:
        res = []
        for arg in args.posonlyargs + args.args:
            ann = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
            res.append(f"{arg.arg}{ann}")
        if args.vararg:
            res.append(f"*{args.vararg.arg}")
        for arg in args.kwonlyargs:
            ann = f": {ast.unparse(arg.annotation)}" if arg.annotation else ""
            res.append(f"{arg.arg}{ann}")
        if args.kwarg:
            res.append(f"**{args.kwarg.arg}")
        return ", ".join(res)

    def _parse_javascript(self, code: str, filepath: str, lang: str) -> ParsedCodeFile:
        symbols: list[CodeSymbol] = []
        imports: list[str] = []
        lines = code.splitlines()

        # 1. Extract imports / requires
        import_pattern = re.compile(r'^\s*(?:import\s+(?:.*?\s+from\s+)?[\'"]([^\'"]+)[\'"]|const\s+.*?\s*=\s*require\([\'"]([^\'"]+)[\'"]\))', re.MULTILINE)
        for m in import_pattern.finditer(code):
            imp = m.group(1) or m.group(2)
            if imp:
                imports.append(imp)

        # 2. Extract Routes (e.g. router.get('/users', ...), app.post('/login', ...))
        route_pattern = re.compile(r'^\s*(?:app|router|server)\.(get|post|put|delete|patch|use)\s*\(\s*([\'"][^\'"]+[\'"])', re.MULTILINE)
        for m in route_pattern.finditer(code):
            method = m.group(1).upper()
            path = m.group(2).strip("'\"")
            line_no = code[:m.start()].count("\n") + 1
            sig = f"{method} {path}"
            symbols.append(CodeSymbol(
                name=f"{method} {path}",
                kind=SymbolKind.ROUTE,
                signature=sig,
                start_line=line_no,
                end_line=line_no,
                full_code=m.group(0),
                skeleton_code=sig,
                filepath=filepath,
            ))

        # 3. Extract Classes & Methods
        class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?\s*\{', re.MULTILINE)
        for m in class_pattern.finditer(code):
            cls_name = m.group(1)
            line_no = code[:m.start()].count("\n") + 1
            sig = f"class {cls_name}" + (f" extends {m.group(2)}" if m.group(2) else "")
            
            # Find class block boundaries using curly brace matching
            body, end_line = self._extract_brace_block(lines, line_no - 1)
            
            # Extract methods inside class
            method_pattern = re.compile(r'^\s*(?:async\s+)?([A-Za-z0-9_$]+)\s*\(([^)]*)\)\s*\{', re.MULTILINE)
            methods_found = []
            for meth in method_pattern.finditer(body):
                m_name = meth.group(1)
                if m_name in ("if", "for", "while", "switch", "catch"):
                    continue
                m_sig = f"{m_name}({meth.group(2)})"
                methods_found.append(f"  ├── {m_sig}")
                
                m_line = line_no + body[:meth.start()].count("\n")
                symbols.append(CodeSymbol(
                    name=f"{cls_name}.{m_name}",
                    kind=SymbolKind.METHOD,
                    signature=m_sig,
                    start_line=m_line,
                    end_line=m_line + 5,
                    full_code=meth.group(0),
                    skeleton_code=f"  {m_sig} {{ ... }}",
                    parent_class=cls_name,
                    filepath=filepath,
                ))

            skel = f"{sig} {{\n" + "\n".join(methods_found) + "\n}" if methods_found else f"{sig} {{ ... }}"
            symbols.append(CodeSymbol(
                name=cls_name,
                kind=SymbolKind.CLASS,
                signature=sig,
                start_line=line_no,
                end_line=end_line,
                full_code=body,
                skeleton_code=skel,
                filepath=filepath,
            ))

        # 4. Extract Top-level Functions & Arrow Functions
        fn_pattern = re.compile(r'^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)', re.MULTILINE)
        for m in fn_pattern.finditer(code):
            fn_name = m.group(1)
            line_no = code[:m.start()].count("\n") + 1
            sig = f"function {fn_name}({m.group(2)})"
            body, end_line = self._extract_brace_block(lines, line_no - 1)
            
            symbols.append(CodeSymbol(
                name=fn_name,
                kind=SymbolKind.FUNCTION,
                signature=sig,
                start_line=line_no,
                end_line=end_line,
                full_code=body if body else m.group(0),
                skeleton_code=f"{sig} {{ ... }}",
                filepath=filepath,
            ))

        # 5. Extract Arrow Functions: const myFn = async (a, b) => { ... }
        arrow_pattern = re.compile(r'^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', re.MULTILINE)
        for m in arrow_pattern.finditer(code):
            fn_name = m.group(1)
            line_no = code[:m.start()].count("\n") + 1
            sig = f"const {fn_name} = ({m.group(2)}) =>"
            body, end_line = self._extract_brace_block(lines, line_no - 1)
            
            symbols.append(CodeSymbol(
                name=fn_name,
                kind=SymbolKind.FUNCTION,
                signature=sig,
                start_line=line_no,
                end_line=end_line,
                full_code=body if body else m.group(0),
                skeleton_code=f"{sig} {{ ... }}",
                filepath=filepath,
            ))

        # Build full skeleton
        full_skel_parts = []
        if imports:
            full_skel_parts.append("\n".join(f"import '{imp}';" for imp in imports[:8]))
        for sym in symbols:
            if not sym.parent_class:
                full_skel_parts.append(sym.skeleton_code)

        return ParsedCodeFile(
            filepath=filepath,
            language=lang,
            symbols=symbols,
            imports=imports,
            raw_code=code,
            full_skeleton="\n\n".join(full_skel_parts) if full_skel_parts else code,
        )

    def _parse_generic(self, code: str, filepath: str, lang: str) -> ParsedCodeFile:
        symbols: list[CodeSymbol] = []
        lines = code.splitlines()

        # Generic pattern for functions / methods across Go, Rust, Java, C++
        generic_fn = re.compile(r'^\s*(?:pub\s+|public\s+|private\s+|protected\s+|func\s+|fn\s+|def\s+)([A-Za-z0-9_$]+)\s*\(([^)]*)\)', re.MULTILINE)
        for m in generic_fn.finditer(code):
            name = m.group(1)
            line_no = code[:m.start()].count("\n") + 1
            sig = m.group(0).strip()
            symbols.append(CodeSymbol(
                name=name,
                kind=SymbolKind.FUNCTION,
                signature=sig,
                start_line=line_no,
                end_line=min(len(lines), line_no + 10),
                full_code=sig,
                skeleton_code=f"{sig} {{ ... }}",
                filepath=filepath,
            ))

        return ParsedCodeFile(
            filepath=filepath,
            language=lang,
            symbols=symbols,
            imports=[],
            raw_code=code,
            full_skeleton="\n".join(s.skeleton_code for s in symbols) if symbols else code,
        )

    def _extract_brace_block(self, lines: list[str], start_idx: int) -> tuple[str, int]:
        depth = 0
        block_lines = []
        found_open = False

        for idx in range(start_idx, len(lines)):
            line = lines[idx]
            block_lines.append(line)
            for char in line:
                if char == '{':
                    depth += 1
                    found_open = True
                elif char == '}':
                    depth -= 1
                    if found_open and depth <= 0:
                        return "\n".join(block_lines), idx + 1

        return "\n".join(block_lines), len(lines)
