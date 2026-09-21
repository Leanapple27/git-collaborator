from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from git_collab.semantic.ast_parser import parse_module, FunctionInfo, ClassInfo

@dataclass
class SymbolConflict:
    name: str
    kind: str
    ours_source: str
    theirs_source: str
    base_source: str

@dataclass
class FunctionMergeResult:
    merged_source: str
    auto_resolved: List[str]
    conflicts: List[SymbolConflict]

def merge_functions(base_src: str, ours_src: str, theirs_src: str) -> FunctionMergeResult:
    base_mod = parse_module(base_src)
    ours_mod = parse_module(ours_src)
    theirs_mod = parse_module(theirs_src)
    
    def get_symbols(mod) -> Dict[str, Dict[str, Any]]:
        syms = {}
        for c in mod.classes:
            syms[c.name] = {'kind': 'class', 'source': c.source}
        for f in mod.functions:
            syms[f.name] = {'kind': 'function', 'source': f.source}
        return syms

    base_syms = get_symbols(base_mod)
    ours_syms = get_symbols(ours_mod)
    theirs_syms = get_symbols(theirs_mod)
    
    all_names = set(base_syms.keys()) | set(ours_syms.keys()) | set(theirs_syms.keys())
    
    merged_symbols = {}
    conflicts = []
    auto_resolved = []
    
    for name in all_names:
        b = base_syms.get(name)
        o = ours_syms.get(name)
        t = theirs_syms.get(name)
        
        kind = o['kind'] if o else (t['kind'] if t else b['kind'])
        
        if b and not o and t and t['source'] != b['source']:
            conflicts.append(SymbolConflict(name, kind, "", t['source'], b['source']))
        elif b and not t and o and o['source'] != b['source']:
            conflicts.append(SymbolConflict(name, kind, o['source'], "", b['source']))
        elif o and t:
            if o['source'] == t['source']:
                merged_symbols[name] = o['source']
                if b and o['source'] != b['source']:
                    auto_resolved.append(name)
            else:
                if b:
                    if o['source'] != b['source'] and t['source'] == b['source']:
                        merged_symbols[name] = o['source']
                    elif t['source'] != b['source'] and o['source'] == b['source']:
                        merged_symbols[name] = t['source']
                    else:
                        conflicts.append(SymbolConflict(name, kind, o['source'], t['source'], b['source']))
                else:
                    conflicts.append(SymbolConflict(name, kind, o['source'], t['source'], ""))
        elif o:
            merged_symbols[name] = o['source']
        elif t:
            merged_symbols[name] = t['source']
            
    # Reconstruct preserving order mostly from ours and theirs
    order = []
    for sym in ours_mod.classes + ours_mod.functions:
        if sym.name in merged_symbols and sym.name not in order:
            order.append(sym.name)
    for sym in theirs_mod.classes + theirs_mod.functions:
        if sym.name in merged_symbols and sym.name not in order:
            order.append(sym.name)
            
    merged_source_lines = []
    for name in order:
        merged_source_lines.append(merged_symbols[name])
        
    return FunctionMergeResult(
        merged_source="\n\n".join(merged_source_lines),
        auto_resolved=auto_resolved,
        conflicts=conflicts
    )
