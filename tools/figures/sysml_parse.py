#!/usr/bin/env python3
"""Read the parts of a SysML v2 textual model that figures need, so a figure never restates the model.

Supports the subset the Susanoo models use: `state def` blocks with `state <'ID'> name { doc /* ... */ }`
states and `transition tN first a accept Trigger then b;` transitions. Standard library only.
"""
from __future__ import annotations

import re
from pathlib import Path


class SysMLParseError(Exception):
    pass


def words(camel: str) -> str:
    """AuthorityApproves -> 'authority approves'; UAVClearOfDock -> 'UAV clear of dock'."""
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z]|\b|$)|[A-Z]?[a-z]+|\d+", camel)
    return " ".join(p if p.isupper() and len(p) > 1 else p.lower() for p in parts)


def _block(text: str, header: str) -> str:
    m = re.search(header, text)
    if not m:
        raise SysMLParseError(f"not found: {header}")
    i = text.index("{", m.end() - 1)
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    raise SysMLParseError(f"unbalanced braces after {header}")


def state_machine(path: Path, name: str) -> dict:
    """{'name', 'doc', 'initial', 'states': [{name, id, doc}], 'transitions': [(src, dst, trigger words)]}"""
    text = Path(path).read_text()
    body = _block(text, rf"state def\s+(?:<'[^']*'>\s+)?{re.escape(name)}\s*\{{")
    doc = re.search(r"^\s*doc\s*/\*\s*(.*?)\s*\*/", body, re.S | re.M)
    init = re.search(r"entry;\s*then\s+(\w+);", body)
    states = [{"id": sid or "", "name": sname, "doc": (sdoc or "").strip()}
              for sid, sname, sdoc in re.findall(
                  r"^\s*state\s+(?:<'([^']*)'>\s+)?(\w+)\s*(?:\{\s*doc\s*/\*\s*(.*?)\s*\*/\s*\}|;)", body, re.M)]
    trans = [(a, b, words(t) if t else "") for a, t, b in re.findall(
        r"transition\s+\w+\s+first\s+(\w+)(?:\s+accept\s+(\w+))?\s+then\s+(\w+)\s*;", body)]
    if not init or not states:
        raise SysMLParseError(f"{path}: state def {name} has no entry or states")
    names = {s["name"] for s in states}
    for a, b, _ in trans:
        if a not in names or b not in names:
            raise SysMLParseError(f"{path}: transition {a} -> {b} references an undeclared state")
    return {"name": name, "doc": doc.group(1) if doc else "", "initial": init.group(1), "states": states,
            "transitions": trans}


def definition(path: Path, name: str) -> dict:
    """{'kind': 'enum'|'attribute'|'item'|'part', 'members': [...]} for a definition in a .sysml file.

    Enum members are the literal names; other definitions list 'name : Type' for each attribute or ref feature."""
    text = Path(path).read_text()
    m = re.search(rf"\b(enum|attribute|item|part) def\s+(?:<'[^']*'>\s+)?{re.escape(name)}\s*\{{", text)
    if not m:
        raise SysMLParseError(f"{path}: no definition named {name}")
    body = _block(text, rf"\b{m.group(1)} def\s+(?:<'[^']*'>\s+)?{re.escape(name)}\s*\{{")
    body = re.sub(r"doc\s*/\*.*?\*/", "", body, flags=re.S)
    if m.group(1) == "enum":
        members = re.findall(r"^\s*enum\s+(\w+)\s*;", body, re.M)
    else:
        members = [f"{n} : {t.split('::')[-1]}{mult or ''}" for n, t, mult in re.findall(
            r"^\s*(?:ref\s+)?(?:attribute|item|part)\s+(\w+)\s*:\s*([\w:]+)(\[[^\]]*\])?\s*;", body, re.M)]
    return {"kind": m.group(1), "members": members}
