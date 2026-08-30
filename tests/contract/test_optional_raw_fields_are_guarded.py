#  Pyrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
#  This file is part of Pyrogram.
#
#  Pyrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Pyrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

"""A parser must only read raw fields its input actually has.

Two checks, both against the generated schema, both for defects that raise
inside a parser rather than at import time.

An optional ``Vector`` field arrives as ``None``, not ``[]``. Kurigram's parsers
are written as though it were ``[]``, so ported code iterates it bare and raises
``TypeError: 'NoneType' object is not iterable`` the first time the server omits
it. Inside a parser that exception is caught and logged by ``handler_worker``,
so the symptom is an update type that silently never fires -- never a crash.

This walks every function in the hand-written package that annotates a parameter
as a ``raw.*`` type, resolves attribute chains against the generated schema, and
fails on any iteration of an optional field that is not guarded by ``or []``, a
ternary, an enclosing ``if``, a ``getattr`` default, or an early return.

It found ``Thumbnail._parse`` iterating ``Document.thumbs`` (every document
without a thumbnail) and ``ChatPreview._parse`` iterating
``ChatInvite.participants`` (every invite without a member preview).

The second check is for reading a field no constructor the annotated input can
hold declares at all, narrowing through ``isinstance`` on both arms. That is the
shape of ``CallbackQuery._parse`` reading ``game_short_name`` off a business
callback query, which killed every business button press. A wrong annotation
hides this check as effectively as a wrong read causes the crash, so both count
as findings.
"""

from __future__ import annotations

import ast
import inspect
import pathlib
import re
import types as pytypes
import typing

from pyrogram import raw

PACKAGE = pathlib.Path(__file__).resolve().parents[2] / "pyrogram"

#: Generated trees. They are written by the compiler, not ported by hand.
SKIP = ("raw", "errors")

#: ``raw.types.messages.ChatFull`` is a different class from ``raw.types.ChatFull``,
#: so the namespace has to come along with the name.
RAW_RE = re.compile(r"raw\.(?:types|base)\.((?:\w+\.)?\w+)")

#: Builtins that iterate their first argument.
ITERATING_BUILTINS = frozenset({
    "len",
    "enumerate",
    "list",
    "tuple",
    "set",
    "frozenset",
    "sorted",
    "reversed",
    "any",
    "all",
    "sum",
    "max",
    "min",
    "zip",
    "map",
    "filter",
})


#: A parameter annotated as a container of raw objects is not itself one.
#: ``users: dict[int, raw.types.User]`` is the common shape, and reading it as a
#: ``User`` turns every ``users.get(...)`` into a finding.
CONTAINER_RE = re.compile(r"\b(?:dict|list|set|tuple|Dict|List|Set|Tuple|Mapping|Sequence)\s*\[")


def raw_names(annotation: object) -> set[str]:
    """Every ``raw.types.X`` / ``raw.base.X`` name mentioned in an annotation."""
    return set(RAW_RE.findall(str(annotation)))


def parameter_holders(annotation: ast.AST) -> set[type]:
    """The raw constructors a parameter can hold, or nothing for a container."""
    text = ast.unparse(annotation)
    if CONTAINER_RE.search(text):
        return set()
    return resolve(raw_names(text))


def walk(root: object, dotted: str) -> object:
    """``walk(raw.types, "messages.ChatFull")`` -> the class, or ``None``."""
    node = root
    for part in dotted.split("."):
        node = getattr(node, part, None)
        if node is None:
            return None
    return node


def resolve(names: set[str], _seen: frozenset[str] = frozenset()) -> set[type]:
    """Turn raw names into the concrete ``raw.types`` classes they can be.

    ``raw.base.X`` is a ``Union`` of constructors, so a base name fans out to
    every constructor that can arrive in that slot.
    """
    out: set[type] = set()
    for name in names:
        if name in _seen:
            continue
        seen = _seen | {name}

        concrete = walk(raw.types, name)
        if isinstance(concrete, type):
            out.add(concrete)
            continue

        base = walk(raw.base, name)
        if base is None or isinstance(base, pytypes.ModuleType):
            continue

        args = typing.get_args(base)
        if args:
            for arg in args:
                out |= resolve(raw_names(arg), seen)
        else:
            out |= resolve(raw_names(base) - {name}, seen)
    return out


_FIELDS: dict[type, dict[str, tuple[bool, set[str]]]] = {}


def fields_of(cls: type) -> dict[str, tuple[bool, set[str]]]:
    """``field -> (optional, raw names of what it holds)`` for one constructor."""
    cached = _FIELDS.get(cls)
    if cached is not None:
        return cached

    info: dict[str, tuple[bool, set[str]]] = {}
    try:
        signature = inspect.signature(cls.__init__)
    except (TypeError, ValueError):
        _FIELDS[cls] = info
        return info

    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        optional = parameter.default is not inspect.Parameter.empty
        info[parameter.name] = (optional, raw_names(parameter.annotation))

    _FIELDS[cls] = info
    return info


def lookup(holders: set[type], field: str) -> tuple[bool | None, set[type]]:
    """Is ``field`` optional across every constructor that declares it?

    ``None`` means no holder declares it at all, which is a chain this check
    cannot follow rather than a finding.
    """
    seen = False
    optional = False
    nxt: set[type] = set()

    for holder in holders:
        declared = fields_of(holder)
        if field not in declared:
            continue
        seen = True
        is_optional, names = declared[field]
        optional = optional or is_optional
        nxt |= resolve(names)

    return (optional if seen else None), nxt


def terminates(body: list[ast.stmt]) -> bool:
    """Does this block always leave the enclosing one?"""
    return bool(body) and isinstance(body[-1], (ast.Return, ast.Raise, ast.Continue))


def names_in(node: ast.AST) -> set[str]:
    """Every name a test mentions, with ``getattr(x, "y", ...)`` read as ``x.y``.

    Half the guards in the tree are spelled as ``getattr``, and a guard the
    scanner cannot read is a false finding.
    """
    out: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, (ast.Attribute, ast.Name)):
            out.add(ast.unparse(sub))
        elif (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Name)
            and sub.func.id == "getattr"
            and len(sub.args) >= 2
            and isinstance(sub.args[1], ast.Constant)
            and isinstance(sub.args[1].value, str)
        ):
            out.add(f"{ast.unparse(sub.args[0])}.{sub.args[1].value}")
    return out


def negated_names(test: ast.AST) -> set[str]:
    """Names an early return proves truthy for the code that follows it.

    Only ``not x`` and ``x is None`` count. ``if x: return`` proves the opposite
    and must not be read as a guard.
    """
    out: set[str] = set()
    for node in ast.walk(test):
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            out |= names_in(node.operand)
        elif isinstance(node, ast.Compare) and len(node.ops) == 1:
            op = node.ops[0]
            comparator = node.comparators[0]
            is_none = isinstance(comparator, ast.Constant) and comparator.value is None
            if is_none and isinstance(op, (ast.Is, ast.Eq)):
                out |= names_in(node.left)
    return out


def isinstance_narrow(test: ast.AST) -> dict[str, set[type]]:
    """``isinstance(x, raw.types.A)`` -> ``{"x": {A}}``, tuples included."""
    out: dict[str, set[type]] = {}
    for node in ast.walk(test):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "isinstance"
            and len(node.args) == 2
            and isinstance(node.args[0], ast.Name)
        ):
            continue
        narrowed = resolve(raw_names(ast.unparse(node.args[1])))
        if narrowed:
            out.setdefault(node.args[0].id, set()).update(narrowed)
    return out


class Scan(ast.NodeVisitor):
    """Resolve raw attribute chains inside one function and flag bare iteration."""

    def __init__(self, env: dict[str, set[type]]) -> None:
        self.env = dict(env)
        # local name -> (chain text, is it an unguarded optional field)
        self.aliases: dict[str, tuple[str, bool]] = {}
        self.guards: list[set[str]] = []
        self.hits: list[tuple[int, str]] = []
        # reads of a field no constructor in the narrowed union declares
        self.missing: list[tuple[int, str]] = []

    # -- resolution ----------------------------------------------------------

    def chain(self, node: ast.AST) -> tuple[set[type], bool | None, str | None]:
        if isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id], False, node.id
            return set(), None, None

        if isinstance(node, ast.Attribute):
            holders, _, text = self.chain(node.value)
            if not holders:
                return set(), None, None
            optional, nxt = lookup(holders, node.attr)
            if optional is None:
                return set(), None, None
            return nxt, optional, f"{text}.{node.attr}"

        return set(), None, None

    # -- guards --------------------------------------------------------------

    def guarded(self, text: str) -> bool:
        return any(text in scope for scope in self.guards)

    def body(self, statements: list[ast.stmt]) -> None:
        """Visit a block, honouring early returns as guards for what follows."""
        pushed = 0
        restore: list[tuple[str, set[type] | None]] = []

        for statement in statements:
            self.visit(statement)
            if not (
                isinstance(statement, ast.If)
                and not statement.orelse
                and terminates(statement.body)
            ):
                continue

            proven = negated_names(statement.test)
            if proven:
                self.guards.append(proven)
                pushed += 1

            # `if not isinstance(x, A): return` proves x is an A afterwards,
            # and `if isinstance(x, A): return` proves it is not.
            negated = any(
                isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not)
                for n in ast.walk(statement.test)
            )
            for name, narrowed in isinstance_narrow(statement.test).items():
                before = self.env.get(name)
                restore.append((name, before))
                if negated:
                    self.env[name] = narrowed
                else:
                    self.env[name] = (before - narrowed) if before else set()

        for name, previous in reversed(restore):
            if previous is None:
                self.env.pop(name, None)
            else:
                self.env[name] = previous
        for _ in range(pushed):
            self.guards.pop()

    def branch(self, test: ast.AST, then: object, otherwise: object, block: bool) -> None:
        """Visit both arms of an if, narrowing each by the isinstance test."""
        self.visit(test)
        narrowed = isinstance_narrow(test)
        previous = {name: self.env.get(name) for name in narrowed}

        self.env.update(narrowed)
        self.guards.append(names_in(test))
        self.body(then) if block else self.visit(then)
        self.guards.pop()

        # The else arm proves the opposite, which is what makes an
        # `if isinstance(x, A): ... else: x.b` read correctly.
        for name, narrowed_to in narrowed.items():
            before = previous[name]
            self.env[name] = (before - narrowed_to) if before else set()

        self.body(otherwise) if block else self.visit(otherwise)

        for name, before in previous.items():
            if before is None:
                self.env.pop(name, None)
            else:
                self.env[name] = before

    def visit_If(self, node: ast.If) -> None:
        self.branch(node.test, node.body, node.orelse, block=True)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.branch(node.test, node.body, node.orelse, block=False)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)

        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return

        name = node.targets[0].id
        value = node.value
        safe = False

        if isinstance(value, ast.BoolOp) and isinstance(value.op, ast.Or):
            value, safe = value.values[0], True
        if isinstance(value, ast.IfExp):
            safe = True

        resolved, optional, text = self.chain(value)
        if text is None:
            self.env.pop(name, None)
            self.aliases.pop(name, None)
            return

        self.env[name] = resolved
        self.aliases[name] = (text, bool(optional) and not safe)

    # -- findings ------------------------------------------------------------

    def flag(self, node: ast.AST) -> None:
        if isinstance(node, (ast.BoolOp, ast.IfExp)):
            return

        if isinstance(node, ast.Name):
            alias = self.aliases.get(node.id)
            if alias is None:
                return
            text, optional = alias
            if optional and not self.guarded(node.id) and not self.guarded(text):
                self.hits.append((node.lineno, text))
            return

        if isinstance(node, ast.Attribute):
            _, optional, text = self.chain(node)
            if optional and text and not self.guarded(text):
                self.hits.append((node.lineno, text))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        self.generic_visit(node)

        if not isinstance(node.value, ast.Name):
            return
        holders = self.env.get(node.value.id)
        if not holders:
            return

        text = f"{node.value.id}.{node.attr}"
        if self.guarded(text):
            return
        if all(node.attr not in fields_of(h) and not hasattr(h, node.attr) for h in holders):
            self.missing.append((node.lineno, text))

    def visit_For(self, node: ast.For) -> None:
        self.flag(node.iter)
        self.visit(node.iter)
        self.visit(node.target)
        self.body(node.body)
        self.body(node.orelse)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        self.flag(node.iter)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Name) and func.id in ITERATING_BUILTINS and node.args:
            self.flag(node.args[0])
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred) -> None:
        self.flag(node.value)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.flag(node.value)
        self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> None:
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                if value and isinstance(value[0], ast.stmt):
                    self.body(value)
                    continue
                for item in value:
                    if isinstance(item, ast.AST):
                        self.visit(item)
            elif isinstance(value, ast.AST):
                self.visit(value)


def scan_package() -> tuple[list[str], list[str], int]:
    """``(bare iterations, reads of absent fields, functions analysed)``."""
    findings: list[str] = []
    missing: list[str] = []
    analysed = 0

    for path in sorted(PACKAGE.rglob("*.py")):
        if any(part in SKIP for part in path.relative_to(PACKAGE).parts):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            arguments = function.args.args + function.args.kwonlyargs
            env = {}
            for argument in arguments:
                if argument.annotation is None:
                    continue
                resolved = parameter_holders(argument.annotation)
                if resolved:
                    env[argument.arg] = resolved

            if not env:
                continue

            analysed += 1
            scan = Scan(env)
            scan.body(function.body)

            for lineno, text in scan.hits:
                findings.append(
                    f"{path.name}:{lineno}: {function.name}() iterates `{text}`, "
                    f"which the schema marks optional"
                )
            for lineno, text in scan.missing:
                missing.append(
                    f"{path.name}:{lineno}: {function.name}() reads `{text}`, "
                    f"which no constructor it can hold declares"
                )

    return findings, missing, analysed


#: Functions analysed when this check was written. A resolver that stopped
#: resolving would pass vacuously, so the floor matters as much as the finding.
ANALYSED_FLOOR = 200


def test_no_parser_iterates_an_optional_raw_field_bare():
    findings, _, analysed = scan_package()
    assert not findings, (
        "These iterate a raw field that arrives as None when the server omits it. "
        "Guard with `or []`.\n  " + "\n  ".join(findings)
    )
    assert analysed >= ANALYSED_FLOOR, (
        f"only {analysed} functions resolved a raw parameter, was {ANALYSED_FLOOR}+. "
        "The check is passing because it stopped looking, not because the tree is clean."
    )


def test_no_parser_reads_a_field_its_input_cannot_have():
    """``CallbackQuery._parse`` read ``game_short_name`` off a business query.

    Business callback queries do not carry that field, so every one of them
    raised ``AttributeError`` inside the parser. Either the annotation is wrong
    or the read is; both are worth failing on.
    """
    _, missing, _ = scan_package()
    assert not missing, (
        "These read a field the annotated input does not declare. Fix the "
        "annotation if it is wrong, or use getattr if the field is conditional."
        "\n  " + "\n  ".join(missing)
    )


def test_the_scanner_still_resolves_chains():
    """A resolver that silently stops resolving would pass the check vacuously."""
    holders = resolve({"Document"})
    assert holders, "raw.types.Document did not resolve"

    optional, _ = lookup(holders, "thumbs")
    assert optional is True, "Document.thumbs should read as optional"

    optional, _ = lookup(holders, "id")
    assert optional is False, "Document.id should read as required"

    assert lookup(holders, "not_a_field") == (None, set())


def test_the_scanner_flags_a_known_bad_shape():
    """The guard forms in the tree must not be the only thing it recognises."""
    source = (
        "def _parse(client, media: raw.types.Document):\n    return [t for t in media.thumbs]\n"
    )
    function = ast.parse(source).body[0]
    scan = Scan({"media": resolve({"Document"})})
    scan.body(function.body)
    assert scan.hits, "an unguarded iteration of Document.thumbs was not flagged"

    guarded = (
        "def _parse(client, media: raw.types.Document):\n"
        "    return [t for t in media.thumbs or []]\n"
    )
    function = ast.parse(guarded).body[0]
    scan = Scan({"media": resolve({"Document"})})
    scan.body(function.body)
    assert not scan.hits, "`or []` should not be flagged"


def test_the_scanner_flags_the_callback_query_shape():
    """The bug this second check exists for, reduced to its shape."""
    holders = resolve({"UpdateBusinessBotCallbackQuery"})
    assert holders, "raw.types.UpdateBusinessBotCallbackQuery did not resolve"

    source = "def _parse(client, q):\n    return q.game_short_name\n"
    function = ast.parse(source).body[0]
    scan = Scan({"q": holders})
    scan.body(function.body)
    assert scan.missing, "a read of a field the update does not carry was not flagged"

    fine = "def _parse(client, q):\n    return q.chat_instance\n"
    function = ast.parse(fine).body[0]
    scan = Scan({"q": holders})
    scan.body(function.body)
    assert not scan.missing, "a field the update does carry was flagged"


def test_isinstance_narrows_both_arms():
    """`else: x.b` after `if isinstance(x, A)` must read as the other branch."""
    source = (
        "def _parse(msg_id):\n"
        "    if isinstance(msg_id, raw.types.InputBotInlineMessageID):\n"
        "        return msg_id.id\n"
        "    return msg_id.owner_id\n"
    )
    function = ast.parse(source).body[0]
    union = resolve({"InputBotInlineMessageID"}) | resolve({"InputBotInlineMessageID64"})
    scan = Scan({"msg_id": union})
    scan.body(function.body)
    assert not scan.missing, (
        "owner_id lives on InputBotInlineMessageID64, which the else arm narrows to"
    )
