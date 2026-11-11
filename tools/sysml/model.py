"""Read the Susanoo SysML v2 model (models/sysml/model) into Python objects. Standard library only.

This is not a SysML v2 implementation. It reads the subset of the textual notation that the model files use
and refuses anything else with the file and line it stopped at, so a new construct is either added here on
purpose or not used. Conformance to SysML v2 is checked separately by the OMG pilot implementation
(tools/sysml/pilot/validate.sh). Approach ported from LionDriver's sysml_lite.py (MIT, same maintainer).

Subset: package, private import, enum def, metadata def, connection def, part def, action def, requirement def;
part / action / requirement usages with a short name <'ID'>, a name, an optional type and a body; doc comments;
metadata annotations @Name { attr = value; } with enum, string and tuple values; perform; connection ... connect
a to b; satisfy X by chain.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "models" / "sysml" / "model"
MODEL_FILES = ["SusanooLibrary.sysml", "Functions.sysml", "Architecture.sysml", "Requirements.sysml", "Satisfaction.sysml"]
CONTEXT = ("SusanooArchitecture", "context")   # package, root part usage
SYSTEM_ID = "SUS-I1"


class ModelError(Exception):
    pass


# ---------------------------------------------------------------- tokens

TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<line>//[^\n]*)
  | (?P<block>/\*.*?\*/)
  | (?P<str>"(?:[^"\\]|\\.)*")
  | (?P<num>[0-9]+(?:\.[0-9]+)?)
  | (?P<qname>'(?:[^'\\]|\\.)*')
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<sym>::|\.\.|[{};:=(),<>\[\].*@])
""", re.S | re.X)


@dataclass
class Tok:
    kind: str
    text: str
    line: int


def tokenize(text: str, fname: str) -> list[Tok]:
    out, pos, line = [], 0, 1
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise ModelError(f"{fname}:{line}: unexpected character {text[pos]!r}")
        kind, s = m.lastgroup, m.group()
        if kind not in ("ws", "line"):
            out.append(Tok(kind, s, line))
        line += s.count("\n")
        pos = m.end()
    out.append(Tok("eof", "", line))
    return out


def doc_text(block: str) -> str:
    body = block[2:-2]
    lines = [re.sub(r"^\s*\*\s?", "", ln).rstrip() for ln in body.splitlines()]
    return " ".join(" ".join(lines).split())


def unquote(s: str) -> str:
    return s[1:-1].replace("\\'", "'").replace('\\"', '"')


# ---------------------------------------------------------------- declarations

@dataclass
class Decl:
    kind: str                     # package, enum_def, metadata_def, connection_def, part_def, action_def,
                                  # requirement_def, part, action, requirement, connection, perform, satisfy, import
    name: str | None
    file: str
    line: int
    short: str | None = None
    type: str | None = None
    doc: str = ""
    meta: dict = field(default_factory=dict)          # metadata name -> {attr: value}
    members: list = field(default_factory=list)
    ends: tuple = ()                                  # connection: (chain, chain)
    target: str | None = None                         # perform / satisfy target; import namespace
    by: str | None = None                             # satisfy ... by chain
    values: list = field(default_factory=list)        # enum literals, metadata attribute names


DEFS = {"enum": "enum_def", "metadata": "metadata_def", "connection": "connection_def", "part": "part_def",
        "action": "action_def", "requirement": "requirement_def"}


class Parser:
    def __init__(self, toks: list[Tok], fname: str):
        self.t, self.i, self.f = toks, 0, fname

    def peek(self, k=0) -> Tok:
        j, seen = self.i, 0
        while True:
            if self.t[j].kind != "block":
                if seen == k:
                    return self.t[j]
                seen += 1
            j += 1

    def next(self) -> Tok:
        while self.t[self.i].kind == "block":
            self.i += 1
        tok = self.t[self.i]
        self.i += 1
        return tok

    def error(self, tok: Tok, msg: str) -> ModelError:
        return ModelError(f"{self.f}:{tok.line}: {msg} (at {tok.text!r})")

    def expect(self, text: str) -> Tok:
        tok = self.next()
        if tok.text != text:
            raise self.error(tok, f"expected {text!r}")
        return tok

    def accept(self, text: str) -> bool:
        if self.peek().text == text:
            self.next()
            return True
        return False

    def ident(self) -> str:
        tok = self.next()
        if tok.kind == "name":
            return tok.text
        if tok.kind == "qname":
            return unquote(tok.text)
        raise self.error(tok, "expected a name")

    def qualified(self) -> str:
        """a::b::c or a.b.c (feature chain), with the separators kept and quoted names unquoted."""
        s = self.ident()
        while self.peek().text in ("::", "."):
            sep = self.next().text
            if self.peek().text == "*":
                self.next()
                return s + sep + "*"
            s += sep + self.ident()
        return s

    def value(self):
        tok = self.peek()
        if tok.text == "(":
            self.next()
            vals = []
            while not self.accept(")"):
                vals.append(self.value())
                self.accept(",")
            return vals
        if tok.kind == "str":
            self.next()
            return unquote(tok.text)
        if tok.kind == "num":
            self.next()
            return float(tok.text) if "." in tok.text else int(tok.text)
        if tok.kind in ("name", "qname"):
            q = self.qualified()
            return q.split("::")[-1] if "::" in q else q
        raise self.error(tok, "expected a value")

    def multiplicity(self) -> None:
        if self.accept("["):
            while not self.accept("]"):
                self.next()

    # -------------------------------------------------------------- statements

    def parse_file(self) -> list[Decl]:
        out = []
        while self.peek().kind != "eof":
            out.append(self.statement())
        return out

    def metadata(self, d: Decl) -> None:
        name = self.qualified()
        attrs = {}
        if self.accept("{"):
            while not self.accept("}"):
                key = self.ident()
                self.expect("=")
                attrs[key] = self.value()
                self.expect(";")
        else:
            self.expect(";")
        if name in d.meta:
            raise self.error(self.peek(), f"metadata {name} given twice")
        d.meta[name] = attrs

    def body(self, d: Decl) -> None:
        if self.accept(";"):
            return
        self.expect("{")
        while not self.accept("}"):
            tok = self.peek()
            if tok.text == "doc":
                self.next()
                d.doc = self.take_doc_after()
            elif tok.text == "@":
                self.next()
                self.metadata(d)
            else:
                d.members.append(self.statement(owner=d))

    def take_doc_after(self) -> str:
        if self.t[self.i].kind != "block":
            raise self.error(self.t[self.i], "doc must be followed by a /* comment */")
        block = self.t[self.i]
        self.i += 1
        return doc_text(block.text)

    def head(self, kind: str, tok: Tok) -> Decl:
        d = Decl(kind, None, self.f, tok.line)
        if self.accept("<"):
            d.short = self.ident()
            self.expect(">")
        if self.peek().kind in ("name", "qname") and self.peek().text not in ("connect",):
            d.name = self.ident()
        self.multiplicity()
        if self.accept(":"):
            d.type = self.qualified()
            self.multiplicity()
        return d

    def statement(self, owner: Decl | None = None) -> Decl:
        tok = self.next()
        w = tok.text
        if w == "package":
            d = Decl("package", self.ident(), self.f, tok.line)
            self.body(d)
            return d
        if w in ("private", "public"):
            self.expect("import")
            d = Decl("import", None, self.f, tok.line, target=self.qualified())
            self.expect(";")
            return d
        if w == "perform":
            d = Decl("perform", None, self.f, tok.line, target=self.qualified())
            self.expect(";")
            return d
        if w == "satisfy":
            target = self.qualified()
            self.expect("by")
            d = Decl("satisfy", None, self.f, tok.line, target=target, by=self.qualified())
            self.expect(";")
            return d
        if w == "end":
            self.expect("part")
            d = Decl("end", self.ident(), self.f, tok.line)
            self.expect(";")
            return d
        if w == "attribute":
            name = self.ident()
            self.expect(":")
            typ = self.qualified()
            self.multiplicity()
            self.expect(";")
            return Decl("attribute", name, self.f, tok.line, type=typ)
        if w == "enum" and self.peek().text != "def":
            d = Decl("literal", self.ident(), self.f, tok.line)
            self.expect(";")
            return d
        if w in DEFS and self.peek().text == "def":
            self.next()
            d = Decl(DEFS[w], self.ident(), self.f, tok.line)
            self.body(d)
            return d
        if w in ("part", "action", "requirement"):
            d = self.head(w, tok)
            self.body(d)
            return d
        if w == "connection":
            d = self.head("connection", tok)
            self.expect("connect")
            a = self.qualified()
            self.expect("to")
            b = self.qualified()
            d.ends = (a, b)
            self.body(d)
            return d
        raise self.error(tok, "construct not supported by tools/sysml/model.py")


def parse_text(text: str, fname: str = "<text>") -> list[Decl]:
    return Parser(tokenize(text, fname), fname).parse_file()


# ---------------------------------------------------------------- model

@dataclass
class Element:
    id: str                       # short name, e.g. SUS-M1-PIL
    name: str                     # SysML name, e.g. pilotStation
    path: str                     # chain from context, e.g. system.walker.pilotStation
    parent: str | None            # parent element short name (None for context children)
    type: str | None
    doc: str
    meta: dict
    performs: list
    external: bool
    file: str
    line: int


@dataclass
class Connection:
    id: str
    name: str
    ends: tuple                   # (from element id, to element id)
    doc: str
    meta: dict
    file: str
    line: int


@dataclass
class Function:
    id: str
    name: str
    doc: str


@dataclass
class Requirement:
    id: str
    name: str
    doc: str
    meta: dict


@dataclass
class Model:
    elements: dict = field(default_factory=dict)      # id -> Element (system elements and externals)
    connections: dict = field(default_factory=dict)   # id -> Connection
    functions: dict = field(default_factory=dict)     # id -> Function
    requirements: dict = field(default_factory=dict)  # id -> Requirement
    satisfies: list = field(default_factory=list)     # (requirement id, element id, file, line)
    defs: dict = field(default_factory=dict)          # def name -> Decl
    files: list = field(default_factory=list)

    def by_path(self) -> dict:
        return {e.path: e for e in self.elements.values()}


def load(files: list[Path] | None = None) -> Model:
    files = files or [MODEL_DIR / f for f in MODEL_FILES]
    packages: dict[str, Decl] = {}
    for p in files:
        for d in parse_text(p.read_text(encoding="utf-8"), p.name):
            if d.kind != "package":
                raise ModelError(f"{p.name}:{d.line}: top-level declarations must be packages")
            packages[d.name] = d
    m = Model(files=[p.name for p in files])

    def walk_defs(decl: Decl):
        for x in decl.members:
            if x.kind.endswith("_def"):
                m.defs[x.name] = x
            if x.kind == "package":
                walk_defs(x)
    for pkg in packages.values():
        walk_defs(pkg)

    # functions and requirements: top-level usages in any package
    for pkg in packages.values():
        for x in pkg.members:
            if x.kind == "action":
                if not x.short:
                    raise ModelError(f"{x.file}:{x.line}: action usage needs a short name <'F-nn'>")
                m.functions[x.short] = Function(x.short, x.name, x.doc or _def_doc(m, x.type))
            elif x.kind == "requirement":
                if not x.short:
                    raise ModelError(f"{x.file}:{x.line}: requirement usage needs a short name <'SYS-nnn'>")
                m.requirements[x.short] = Requirement(x.short, x.name, x.doc, x.meta)
    fn_by_name = {f.name: f.id for f in m.functions.values()}

    pkg_name, root_name = CONTEXT
    if pkg_name not in packages:
        raise ModelError(f"package {pkg_name} not found")
    root = next((x for x in packages[pkg_name].members if x.kind == "part" and x.name == root_name), None)
    if root is None:
        raise ModelError(f"{pkg_name}::{root_name} not found")

    def instantiate(decl: Decl, path: str, parent: str | None, external: bool):
        if not decl.short:
            raise ModelError(f"{decl.file}:{decl.line}: part usage {decl.name} needs a short name <'ID'>")
        if decl.short in m.elements:
            raise ModelError(f"{decl.file}:{decl.line}: duplicate element id {decl.short}")
        performs = []
        for x in decl.members:
            if x.kind == "perform":
                fname = x.target.split("::")[-1]
                if fname not in fn_by_name:
                    raise ModelError(f"{x.file}:{x.line}: perform {x.target}: no such function")
                performs.append(fn_by_name[fname])
        m.elements[decl.short] = Element(decl.short, decl.name, path, parent, decl.type, decl.doc or _def_doc(m, decl.type),
                                         decl.meta, performs, external, decl.file, decl.line)
        for x in decl.members:
            if x.kind == "part":
                instantiate(x, f"{path}.{x.name}", decl.short, external)
            elif x.kind not in ("perform",):
                raise ModelError(f"{x.file}:{x.line}: {x.kind} not allowed inside part {decl.name}")

    for x in root.members:
        if x.kind == "part":
            instantiate(x, x.name, None, external=(x.short != SYSTEM_ID))
    paths = m.by_path()
    for x in root.members:
        if x.kind == "connection":
            if not x.short:
                raise ModelError(f"{x.file}:{x.line}: connection needs a short name <'IF-nnn'>")
            ends = []
            for chain in x.ends:
                if chain not in paths:
                    raise ModelError(f"{x.file}:{x.line}: connection end {chain} is not a part of the context")
                ends.append(paths[chain].id)
            if x.short in m.connections:
                raise ModelError(f"{x.file}:{x.line}: duplicate connection id {x.short}")
            m.connections[x.short] = Connection(x.short, x.name, tuple(ends), x.doc, x.meta, x.file, x.line)
        elif x.kind != "part":
            raise ModelError(f"{x.file}:{x.line}: {x.kind} not allowed in the context")

    for pkg in packages.values():
        for x in pkg.members:
            if x.kind == "satisfy":
                req = x.target.split("::")[-1]
                if req not in m.requirements:
                    by_name = {r.name: r.id for r in m.requirements.values()}
                    req = by_name.get(req, req)
                if req not in m.requirements:
                    raise ModelError(f"{x.file}:{x.line}: satisfy {x.target}: no such requirement")
                chain = x.by.removeprefix(f"{root_name}.")
                if chain not in paths:
                    raise ModelError(f"{x.file}:{x.line}: satisfy ... by {x.by}: not a part of the context")
                m.satisfies.append((req, paths[chain].id, x.file, x.line))
    return m


def _def_doc(m: Model, typ: str | None) -> str:
    if not typ:
        return ""
    d = m.defs.get(typ.split("::")[-1])
    return d.doc if d else ""
