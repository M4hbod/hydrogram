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

"""``parse_messages`` may only be handed something that has ``messages``.

``parse_messages`` reads ``.users``, ``.chats`` and ``.messages`` off its
argument. Most of the send and edit family return ``Updates``, which has none of
them, so passing the result raises ``AttributeError: 'Updates' object has no
attribute 'messages'`` on the first real call.

It hid for so long because of the shortcut: a *user* sending to their own
private chat gets ``UpdateShortSentMessage`` back, which the methods do handle,
so the broken branch is only reached by bots and in groups. Fifteen methods were
in that state, ``send_rich_message`` among them, each raising on every call.

This resolves each ``parse_messages`` argument back to the RPC that produced it
and checks the return type the schema declares for that RPC.
"""

from __future__ import annotations

import ast
import pathlib
import re

METHODS = pathlib.Path(__file__).resolve().parents[2] / "pyrogram" / "methods"
SCHEMA = (
    pathlib.Path(__file__).resolve().parents[2] / "compiler" / "api" / "source" / "main_api.tl"
)

DEFINITION = re.compile(r"^([a-zA-Z][\w.]*)#[0-9a-f]+\s*(.*?)=\s*([\w.<>]+);\s*$")

#: Return types that carry no ``messages`` vector of their own.
WITHOUT_MESSAGES = frozenset({"Updates"})


def schema_returns() -> dict[str, str]:
    """``messages.sendMessage`` -> ``Updates``, for every function in the schema."""
    out: dict[str, str] = {}
    for line in SCHEMA.read_text(encoding="utf-8").splitlines():
        found = DEFINITION.match(line)
        if found:
            out[found.group(1)] = found.group(3)
    return out


RETURNS = schema_returns()


def tl_name(node: ast.AST) -> str | None:
    """``raw.functions.messages.SendMessage(...)`` -> ``messages.sendMessage``."""
    if not isinstance(node, ast.Call):
        return None
    text = ast.unparse(node.func)
    if not text.startswith("raw.functions."):
        return None
    parts = text[len("raw.functions.") :].split(".")
    parts[-1] = parts[-1][0].lower() + parts[-1][1:]
    return ".".join(parts)


class Scan(ast.NodeVisitor):
    """Track which local names hold the result of which RPC."""

    def __init__(self) -> None:
        self.origin: dict[str, str] = {}
        self.hits: list[tuple[int, str, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)

        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            return

        name = node.targets[0].id
        value = node.value
        while isinstance(value, ast.Await):
            value = value.value

        if isinstance(value, ast.Call) and ast.unparse(value.func).endswith("invoke"):
            for argument in value.args:
                returned = RETURNS.get(tl_name(argument) or "")
                if returned:
                    self.origin[name] = returned
                    return

        self.origin.pop(name, None)

    def visit_Call(self, node: ast.Call) -> None:
        self.generic_visit(node)

        if not ast.unparse(node.func).endswith("parse_messages"):
            return

        arguments = list(node.args)
        arguments += [kw.value for kw in node.keywords if kw.arg == "messages"]

        for argument in arguments:
            base = argument
            suffix = ""
            if isinstance(argument, ast.Attribute):
                base, suffix = argument.value, f".{argument.attr}"
            if not isinstance(base, ast.Name):
                continue

            returned = self.origin.get(base.id)
            if not returned:
                continue

            # `r.updates` off a PaymentResult is itself an Updates, not a vector.
            if returned in WITHOUT_MESSAGES or suffix == ".updates":
                self.hits.append((node.lineno, f"{base.id}{suffix}", returned))


def findings() -> tuple[list[str], int]:
    """``(findings, number of parse_messages arguments actually resolved)``."""
    out: list[str] = []
    resolved = 0

    for path in sorted(METHODS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            scan = Scan()
            for statement in function.body:
                scan.visit(statement)

            resolved += len(scan.origin)
            for lineno, expression, returned in scan.hits:
                out.append(
                    f"{path.name}:{lineno}: {function.name}() passes `{expression}` to "
                    f"parse_messages, but the RPC returns {returned}, which has no `messages`"
                )

    return out, resolved


#: RPC results resolved when this check was written. A resolver that stopped
#: resolving would pass vacuously.
RESOLVED_FLOOR = 150


def test_parse_messages_is_never_handed_an_updates():
    found, resolved = findings()

    assert not found, (
        "These raise AttributeError on every call. Use "
        "utils.parse_messages_from_updates instead.\n  " + "\n  ".join(found)
    )
    assert resolved >= RESOLVED_FLOOR, (
        f"only {resolved} RPC results resolved, was {RESOLVED_FLOOR}+. The check is passing "
        "because it stopped looking, not because the tree is clean."
    )


def test_the_schema_returns_are_actually_read():
    assert RETURNS.get("messages.sendMessage") == "Updates"
    assert RETURNS.get("ephemeral.sendMessage") == "Updates"
    assert RETURNS.get("messages.getHistory") == "messages.Messages"
    assert RETURNS.get("payments.sendStarsForm") == "payments.PaymentResult"


def test_the_scanner_flags_the_shape_it_exists_for():
    source = (
        "async def send(self):\n"
        "    r = await self.invoke(raw.functions.messages.SendMessage(peer=1))\n"
        "    return await utils.parse_messages(client=self, messages=r)\n"
    )
    function = ast.parse(source).body[0]
    scan = Scan()
    for statement in function.body:
        scan.visit(statement)
    assert scan.hits, "the original send_rich_message shape was not flagged"

    fine = (
        "async def history(self):\n"
        "    r = await self.invoke(raw.functions.messages.GetHistory(peer=1))\n"
        "    return await utils.parse_messages(client=self, messages=r)\n"
    )
    function = ast.parse(fine).body[0]
    scan = Scan()
    for statement in function.body:
        scan.visit(statement)
    assert not scan.hits, "an RPC that really returns messages.Messages was flagged"
