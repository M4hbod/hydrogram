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

from __future__ import annotations

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent

# The marker comes from the directory a test file lives in, not from a decorator
# on each test: a directory cannot be forgotten the way a decorator can, and it
# keeps "does this touch the network?" a structural property rather than a
# convention people have to remember.
LAYER_MARKERS = {
    "unit": "unit",
    "contract": "contract",
    "integration": "integration",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        relative = Path(str(item.fspath)).relative_to(TESTS_DIR)
        top = relative.parts[0] if len(relative.parts) > 1 else None
        marker = LAYER_MARKERS.get(top)
        if marker:
            item.add_marker(getattr(pytest.mark, marker))
