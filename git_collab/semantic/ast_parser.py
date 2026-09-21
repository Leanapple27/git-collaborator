from __future__ import annotations
import ast
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: Optional[str]
    names: List[str]
    alias: Optional[str]
    is_from_import: bool
    line_number: int

@dataclass
class FunctionInfo:
    """Information about a function definition."""
    name: str
    args: List[str]
    start_line: int
    end_line: int
    source: str
    decorators: List[str]

@dataclass
class ClassInfo:
    """Information about a class definition."""
    name: str
    start_line: int
    end_line: int
    source: str
    methods: List[str]

@dataclass
class ModuleSymbols:
    """Symbols extracted from a Python module."""
    imports: List[ImportInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    source: str = ""

def parse_module(source: str) -> ModuleSymbols:
    """
    Parse source code and return extracted symbols.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ModuleSymbols(source=source)
        
    lines = source.split('\n')
    symbols = ModuleSymbols(source=source)
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                symbols.imports.append(
                    ImportInfo(
                        module=None,
                        names=[alias.name],
                        alias=alias.asname,
                        is_from_import=False,
                        line_number=node.lineno
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            names = [alias.name for alias in node.names]
            symbols.imports.append(
                ImportInfo(
                    module=node.module,
                    names=names,
                    alias=None,
                    is_from_import=True,
                    line_number=node.lineno
                )
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = getattr(node, 'lineno', 1)
            end = getattr(node, 'end_lineno', start)
            
            # Line-based extraction
            func_source = '\n'.join(lines[start - 1 : end])
            args = [arg.arg for arg in node.args.args]
            
            decs = []
            for dec in node.decorator_list:
                if hasattr(ast, 'unparse'):
                    decs.append(ast.unparse(dec))
                else:
                    decs.append("decorator")
            
            symbols.functions.append(
                FunctionInfo(
                    name=node.name,
                    args=args,
                    start_line=start,
                    end_line=end,
                    source=func_source,
                    decorators=decs
                )
            )
        elif isinstance(node, ast.ClassDef):
            start = getattr(node, 'lineno', 1)
            end = getattr(node, 'end_lineno', start)
            
            class_source = '\n'.join(lines[start - 1 : end])
            
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            
            symbols.classes.append(
                ClassInfo(
                    name=node.name,
                    start_line=start,
                    end_line=end,
                    source=class_source,
                    methods=methods
                )
            )
            
    return symbols
