#  Pyrogram - Telegram MTProto API Client Library for Python
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

import ast
import pathlib
import re
import shutil
from pathlib import Path

import pyrogram
import pyrogram.enums
from pyrogram import types

DOCS_HOME_PATH = Path(__file__).parent.resolve()
REPO_HOME_PATH = DOCS_HOME_PATH.parent.parent

DOCS_DEST_PATH = REPO_HOME_PATH / "docs" / "source" / "telegram"
API_DOCS_DEST_PATH = REPO_HOME_PATH / "docs" / "source" / "api"

FUNCTIONS_PATH = REPO_HOME_PATH / "pyrogram" / "raw" / "functions"
TYPES_PATH = REPO_HOME_PATH / "pyrogram" / "raw" / "types"
BASE_PATH = REPO_HOME_PATH / "pyrogram" / "raw" / "base"

FUNCTIONS_BASE = "functions"
TYPES_BASE = "types"
BASE_BASE = "base"


def snake(s: str):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def generate(source_path: Path, base_name: str):
    all_entities: dict[str, list[str]] = {}

    def build(path: Path, level=0):
        last = path.name

        for i in path.iterdir():
            if not i.name.startswith("__"):
                item_path = path / i
                if item_path.is_dir():
                    build(item_path, level=level + 1)
                elif item_path.is_file():
                    with item_path.open(encoding="utf-8") as f:
                        p = ast.parse(f.read())

                    for node in ast.walk(p):
                        if isinstance(node, ast.ClassDef):
                            name = node.name
                            break
                    else:
                        continue

                    full_path = Path(last, snake(name).replace("_", "-") + ".rst")

                    if level:
                        full_path = Path(base_name, full_path)

                    namespace = "" if last in {"base", "types", "functions"} else last

                    full_name = f"{f'{namespace}.' if namespace else ''}{name}"

                    (DOCS_DEST_PATH / full_path).parent.mkdir(parents=True, exist_ok=True)

                    with (DOCS_DEST_PATH / full_path).open("w", encoding="utf-8") as f:
                        f.write(
                            page_template.format(
                                title=full_name,
                                title_markup="=" * len(full_name),
                                full_class_path="pyrogram.raw.{}".format(
                                    ".".join(full_path.parts[:-1]) + "." + name
                                ),
                            )
                        )

                    if last not in all_entities:
                        all_entities[last] = []

                    all_entities[last].append(name)

    build(source_path)

    for k, v in sorted(all_entities.items()):
        v = sorted(v)
        entities = []

        entities = [f"{i} <{snake(i).replace('_', '-')}>" for i in v]

        if k != base_name:
            inner_path = Path(base_name, k, "index.rst")
            module = f"pyrogram.raw.{base_name}.{k}"
        else:
            for i in sorted(all_entities, reverse=True):
                if i != base_name:
                    entities.insert(0, f"{i}/index")

            inner_path = Path(base_name, "index.rst")
            module = f"pyrogram.raw.{base_name}"

        with (DOCS_DEST_PATH / inner_path).open("w", encoding="utf-8") as f:
            if k == base_name:
                f.write(":tocdepth: 1\n\n")
                k = f"Raw {k}"

            f.write(
                toctree.format(
                    title=k.title(),
                    title_markup="=" * len(k),
                    module=module,
                    entities="\n    ".join(entities),
                )
            )

            f.write("\n")


# The section headings, in the order they appear on each page. Everything else
# is read off the package: a hand-written list of 445 methods and 502 types
# drifts the moment one is added, and it did -- these pages were 71 methods and
# 128 types behind before this became derived.
METHOD_SECTIONS = {
    "utilities": "Utilities",
    "messages": "Messages",
    "chats": "Chats",
    "users": "Users",
    "contacts": "Contacts",
    "invite_links": "Invite Links",
    "folders": "Folders",
    "stories": "Stories",
    "premium": "Premium",
    "payments": "Payments & Gifts",
    "business": "Business",
    "bots": "Bots",
    "account": "Account",
    "password": "Password",
    "phone": "Phone & Video Chats",
    "auth": "Authorization",
    "advanced": "Advanced",
    "decorators": "Decorators",
    "pyromod": "Listeners",
}

# Public methods defined on Client itself rather than in a method group, and
# which section they belong in. Everything else on the class -- fetch_peers,
# handle_updates, load_session, get_session and the guess_* helpers -- is
# machinery a caller has no reason to reach for.
CLIENT_METHODS = {
    "set_parse_mode": "utilities",
}

TYPE_SECTIONS = {
    "user_and_chats": "Users & Chats",
    "messages_and_media": "Messages & Media",
    "bots_and_keyboards": "Bots & Keyboards",
    "inline_mode": "Inline Mode",
    "input_media": "Input Media",
    "input_message_content": "Input Message Content",
    "authorization": "Authorization",
    "pyromod": "Listeners",
}

# The types whose bound methods get a page of their own.
BOUND_METHOD_TYPES = (
    "Message",
    "Chat",
    "User",
    "Story",
    "CallbackQuery",
    "InlineQuery",
    "ChatJoinRequest",
    "PreCheckoutQuery",
    "ShippingQuery",
)


def section(title: str, entries: list[str], *, hidden_toctree: bool = True) -> str:
    """One autosummary block, with the toctree that makes the pages reachable."""
    if not entries:
        return ""

    body = "\n    ".join(entries)
    out = f"{title}\n{'-' * len(title)}\n\n.. autosummary::\n    :nosignatures:\n\n    {body}\n"

    if hidden_toctree:
        out += f"\n.. toctree::\n    :hidden:\n\n    {body}\n"

    return out + "\n"


def client_methods_by_group() -> dict[str, list[str]]:
    """Public Client methods, grouped by the package directory they live in."""
    on_client = {
        name
        for name in dir(pyrogram.Client)
        if not name.startswith("_") and callable(getattr(pyrogram.Client, name, None))
    }

    groups: dict[str, list[str]] = {}
    methods_root = pathlib.Path(pyrogram.__file__).parent / "methods"

    for group in METHOD_SECTIONS:
        directory = methods_root / group

        if not directory.is_dir():
            continue

        names = set()

        for path in directory.glob("*.py"):
            if path.name == "__init__.py":
                continue

            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if (
                            isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                            and item.name in on_client
                        ):
                            names.add(item.name)

                        # `get_received_gifts = get_chat_gifts` and friends: a
                        # second public name for the same method, which still
                        # deserves a page of its own.
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if (
                                    isinstance(target, ast.Name)
                                    and not target.id.startswith("_")
                                    and target.id in on_client
                                ):
                                    names.add(target.id)

        groups[group] = sorted(names)

    for name, group in CLIENT_METHODS.items():
        if name in on_client:
            groups.setdefault(group, []).append(name)
            groups[group] = sorted(groups[group])

    return groups


def types_by_group() -> dict[str, list[str]]:
    """Public types, grouped by the package directory they live in."""
    exported = set(types.__all__)
    groups: dict[str, list[str]] = {}
    types_root = pathlib.Path(pyrogram.__file__).parent / "types"

    for group in TYPE_SECTIONS:
        directory = types_root / group

        if not directory.is_dir():
            continue

        names = set()

        for path in directory.glob("*.py"):
            for node in ast.parse(path.read_text(encoding="utf-8")).body:
                if isinstance(node, ast.ClassDef) and node.name in exported:
                    names.add(node.name)

        groups[group] = sorted(names)

    return groups


def bound_methods_by_type() -> dict[str, list[str]]:
    found = {}

    for name in BOUND_METHOD_TYPES:
        cls = getattr(types, name, None)

        if cls is None:
            continue

        # `answer_photo is reply_photo` and twenty more like it: one function
        # under two names. Documenting both makes Sphinx warn about a duplicate
        # object and gives the reader two pages that are the same page, so the
        # first name wins and the alias is mentioned on it instead.
        seen: dict[int, str] = {}
        methods = []

        for attribute in sorted(vars(cls)):
            if attribute.startswith("_"):
                continue

            value = vars(cls)[attribute]

            if not callable(value):
                continue

            # The function knows its own name, and that is the one it was
            # defined under: `Message.answer_photo.__name__` is "reply_photo".
            defined_as = getattr(value, "__name__", attribute)
            canonical = defined_as if hasattr(cls, defined_as) else attribute
            seen.setdefault(id(value), canonical)

            if canonical == attribute:
                methods.append(attribute)

        found[name] = methods

    return found


def pyrogram_api():
    # Enums

    root = API_DOCS_DEST_PATH / "enums"
    (root / "cleanup.html").read_text() if (root / "cleanup.html").exists() else None

    names = sorted(pyrogram.enums.__all__)

    for name in names:
        page = root / f"{name}.rst"
        page.write_text(
            f"{name}\n{'=' * len(name)}\n\n"
            f".. autoclass:: pyrogram.enums.{name}()\n    :members:\n\n"
            ".. raw:: html\n    :file: ./cleanup.html\n"
        )

    index = root / "index.rst"
    head = index.read_text()
    head = head[: head.index(".. currentmodule:: pyrogram.enums")]
    listing = "\n    ".join(names)
    index.write_text(
        f"{head}.. currentmodule:: pyrogram.enums\n\n"
        f".. autosummary::\n    :nosignatures:\n\n    {listing}\n\n"
        f".. toctree::\n    :hidden:\n\n    {listing}\n"
    )

    # Methods

    root = API_DOCS_DEST_PATH / "methods"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "methods.rst").open() as f:
        template = f.read()

    sections = []

    for group, methods in client_methods_by_group().items():
        sections.append(section(METHOD_SECTIONS[group], [f"{m} <{m}>" for m in methods]))

        for method in methods:
            with (root / f"{method}.rst").open("w") as f2:
                title = f"{method}()"

                f2.write(title + "\n" + "=" * len(title) + "\n\n")
                f2.write(f".. automethod:: pyrogram.Client.{method}()")

    for func in ("idle", "compose"):
        with (root / f"{func}.rst").open("w") as f2:
            title = f"{func}()"

            f2.write(title + "\n" + "=" * len(title) + "\n\n")
            f2.write(f".. autofunction:: pyrogram.{func}()")

    with (root / "index.rst").open("w") as f:
        f.write(template.format(sections="".join(sections)))

    # Types

    root = API_DOCS_DEST_PATH / "types"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "types.rst").open() as f:
        template = f.read()

    sections = []

    for group, names in types_by_group().items():
        sections.append(section(TYPE_SECTIONS[group], names))

        for name in names:
            with (root / f"{name}.rst").open("w") as f2:
                f2.write(f"{name}\n" + "=" * len(name) + "\n\n")
                f2.write(f".. autoclass:: pyrogram.types.{name}()\n    :members:")

    with (root / "index.rst").open("w") as f:
        f.write(template.format(sections="".join(sections)))

    # Bound methods

    root = API_DOCS_DEST_PATH / "bound-methods"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "bound-methods.rst").open() as f:
        template = f.read()

    sections = []

    for name, methods in bound_methods_by_type().items():
        qualified = [f"{name}.{method}" for method in methods]
        heading = f"{name}\n{'-' * len(name)}\n\n"
        hlist = "\n    ".join(f"- :meth:`~{q}`" for q in qualified)
        toctree = "\n    ".join(f"{q.split('.')[1]} <{q}>" for q in qualified)
        sections.append(
            f"{heading}.. hlist::\n    :columns: 3\n\n    {hlist}\n\n"
            f".. toctree::\n    :hidden:\n\n    {toctree}\n\n"
        )

        for q in qualified:
            with (root / f"{q}.rst").open("w") as f2:
                title = f"{q}()"

                f2.write(title + "\n" + "=" * len(title) + "\n\n")
                # The type's own page documents these members already, via
                # `autoclass :members:`. Without :no-index: Sphinx warns about
                # every one of them and picks a winner for cross-references at
                # random; the type page is the canonical home, this is the
                # shortcut listing.
                f2.write(f".. automethod:: pyrogram.types.{q}()\n    :no-index:")

    with (root / "index.rst").open("w") as f:
        f.write(template.format(sections="".join(sections)))


def start():
    global page_template, toctree

    shutil.rmtree(DOCS_DEST_PATH, ignore_errors=True)

    with (DOCS_HOME_PATH / "template" / "page.txt").open(encoding="utf-8") as f:
        page_template = f.read()

    with (DOCS_HOME_PATH / "template" / "toctree.txt").open(encoding="utf-8") as f:
        toctree = f.read()

    generate(TYPES_PATH, TYPES_BASE)
    generate(FUNCTIONS_PATH, FUNCTIONS_BASE)
    generate(BASE_PATH, BASE_BASE)
    pyrogram_api()


if __name__ == "__main__":
    start()
