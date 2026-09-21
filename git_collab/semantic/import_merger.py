from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional
from git_collab.semantic.ast_parser import parse_module, ImportInfo

KNOWN_STDLIB = {
    'os', 'sys', 'pathlib', 'collections', 'typing', 'json', 're', 
    'datetime', 'time', 'math', 'itertools', 'functools', 'logging',
    'subprocess', 'ast', 'dataclasses', 'argparse'
}

@dataclass
class MergeResult:
    merged_imports: List[ImportInfo]
    had_conflicts: bool
    conflict_details: List[str]

def _normalize_import(imp: ImportInfo) -> str:
    """Create a canonical string key for comparison."""
    if imp.is_from_import:
        mod = imp.module or ""
        names = ",".join(sorted(imp.names))
        return f"from {mod} import {names}"
    else:
        name = imp.names[0]
        alias = f" as {imp.alias}" if imp.alias else ""
        return f"import {name}{alias}"

def format_imports(imports: List[ImportInfo]) -> str:
    """Convert import list back to Python source code."""
    res = []
    for imp in imports:
        if imp.is_from_import:
            mod = imp.module or ""
            names = ", ".join(imp.names)
            res.append(f"from {mod} import {names}")
        else:
            name = imp.names[0]
            if imp.alias:
                res.append(f"import {name} as {imp.alias}")
            else:
                res.append(f"import {name}")
    return "\n".join(res)

def _get_import_dict(src: str) -> Dict[str, ImportInfo]:
    parsed = parse_module(src)
    return {_normalize_import(imp): imp for imp in parsed.imports}

def merge_imports(base_src: str, ours_src: str, theirs_src: str) -> MergeResult:
    base_imports = _get_import_dict(base_src)
    ours_imports = _get_import_dict(ours_src)
    theirs_imports = _get_import_dict(theirs_src)
    
    base_keys = set(base_imports.keys())
    ours_keys = set(ours_imports.keys())
    theirs_keys = set(theirs_imports.keys())
    
    ours_added = ours_keys - base_keys
    theirs_added = theirs_keys - base_keys
    ours_removed = base_keys - ours_keys
    theirs_removed = base_keys - theirs_keys
    
    merged_keys = (base_keys | ours_added | theirs_added) - (ours_removed | theirs_removed)
    
    merged_imports = []
    conflict_details = []
    had_conflicts = False
    
    for key in merged_keys:
        if key in ours_added and key in theirs_added:
            merged_imports.append(ours_imports[key])
        elif key in ours_imports:
            merged_imports.append(ours_imports[key])
        elif key in theirs_imports:
            merged_imports.append(theirs_imports[key])
        else:
            if key in base_imports:
                merged_imports.append(base_imports[key])
            
    # Sort: stdlib first, then third-party/local
    def sort_key(imp: ImportInfo) -> int:
        mod = imp.module if imp.is_from_import else imp.names[0]
        if mod and mod.split('.')[0] in KNOWN_STDLIB:
            return 0
        elif mod and not mod.startswith('.'):
            return 1
        return 2
        
    merged_imports.sort(key=lambda i: (sort_key(i), _normalize_import(i)))
    
    return MergeResult(
        merged_imports=merged_imports,
        had_conflicts=had_conflicts,
        conflict_details=conflict_details
    )
