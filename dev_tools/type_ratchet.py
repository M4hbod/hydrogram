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

"""A ratchet for `ty`, the same shape as the coverage one in .coveragerc.

The tree does not type-check clean and will not for a long time: most of the
findings are `resolve_peer` returning a union of input peers where a raw
constructor asks for one specific kind, which is correct at runtime and wrong
in the annotations. Failing CI on all of them would mean turning the checker
off within a week.

So this gates the *count* instead. New code may not add findings, and every
module that reaches zero is added to CLEAN below, where it is then held at zero.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent

# The whole package: the count may not grow.
BASELINE = 0  # replaced below, on first run, by --update

# Modules that check clean today and must stay that way. Moving one here is how
# the ratchet tightens; nothing is ever moved out.
CLEAN = ("pyrogram/enums",)

BASELINE_FILE = REPO / "dev_tools" / "type_baseline.txt"


def diagnostics(*targets: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "ty", "check", *targets],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=False,
    )
    found = re.search(r"Found (\d+) diagnostic", result.stdout + result.stderr)

    return int(found.group(1)) if found else 0


def main() -> int:
    total = diagnostics("pyrogram")

    if "--update" in sys.argv:
        BASELINE_FILE.write_text(f"{total}\n")
        print(f"baseline set to {total}")
        return 0

    baseline = int(BASELINE_FILE.read_text().strip())
    status = 0

    if total > baseline:
        print(f"ty findings grew: {baseline} -> {total}. Fix them, or explain why in the PR.")
        status = 1
    else:
        if total < baseline:
            print(f"ty findings fell: {baseline} -> {total}. Lower the baseline:")
            print("    uv run python dev_tools/type_ratchet.py --update")
        print(f"ty: {total} findings against a baseline of {baseline}")

    for module in CLEAN:
        found = diagnostics(module)

        if found:
            print(f"{module} is meant to be clean but has {found} findings")
            status = 1

    return status


if __name__ == "__main__":
    raise SystemExit(main())
