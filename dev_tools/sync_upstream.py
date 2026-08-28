#!/usr/bin/env python3
# Pyrogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2023-present Pyrogram <https://pyrogram.org>
#
# This file is part of Pyrogram.
#
# Pyrogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pyrogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Pyrogram.  If not, see <http://www.gnu.org/licenses/>.

"""Replay upstream Hydrogram commits onto this fork with the namespace rename applied.

This fork renamed the package ``hydrogram`` -> ``pyrogram`` in 868507da so that
``py-tgcalls``, ``pykeyboard`` and friends import it by the name they expect. Upstream
(hydrogram/hydrogram) still uses the old name, so ``git merge upstream/dev`` conflicts on
essentially every file and is useless.

Instead, take each upstream commit as a patch, rewrite the patch text through the same rename,
and apply it. Upstream is slow (single-digit commits per quarter), so the volume is tiny and a
conflict is a thing to look at by hand, not to automate around.

Usage::

    make sync-upstream-check    # report unsynced commits, apply nothing
    make sync-upstream          # replay them
    dev_tools/sync_upstream.py --dry-run       # show the rewritten patches
    dev_tools/sync_upstream.py --limit 1       # replay a single commit

State lives in ``dev_tools/.upstream-sync``: the last upstream SHA whose content is present here.
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
import tempfile
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("sync-upstream")

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "dev_tools" / ".upstream-sync"

UPSTREAM_REMOTE = "upstream"
UPSTREAM_BRANCH = "dev"

# 868507da was a straight case-preserving substitution; every URL, module path, package name
# and Telegram handle followed from these three. Order matters only in that the all-caps form
# must not be shadowed by the lowercase one, so they are applied as a single regex pass.
RENAMES: dict[str, str] = {
    "hydrogram": "pyrogram",
    "Hydrogram": "Pyrogram",
    "HYDROGRAM": "PYROGRAM",
}
RENAME_RE = re.compile("|".join(re.escape(k) for k in RENAMES))

# `f81a62a4` raised __version__ to 2.0.106 because py-tgcalls declares
# `pyrogram>=1.2.20; extra == "pyrogram"` and Hydrogram's own 0.2.0 failed that floor. An
# upstream commit that bumps its own version would drag us back under the floor.
# Patch surgery does not work here: rewriting the version change into a context line makes the
# hunk fail to apply, because upstream's context ("0.2.1.dev") is not what our file says. So the
# patch is applied untouched and the version is put back afterwards.
VERSION_FILE = "pyrogram/__init__.py"
VERSION_ASSIGN_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
VERSION_CHANGE_RE = re.compile(r'^[-+]__version__\s*=\s*["\']')

# pyrogram/emoji.py has no upstream counterpart (5a878348 + a2784cb9); upstream cannot
# meaningfully delete a file it has never had, but a rewritten path could collide.
PROTECTED_PATHS = ("pyrogram/emoji.py",)


class SyncError(RuntimeError):
    """Raised when the sync cannot proceed safely and a human must look."""


def git(*args: str, check: bool = True, capture: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=capture,
    )
    if check and result.returncode != 0:
        raise SyncError(
            f"git {' '.join(args)} failed ({result.returncode}):\n{result.stderr or result.stdout}"
        )
    return (result.stdout or "").strip()


def apply_renames(text: str) -> str:
    return RENAME_RE.sub(lambda m: RENAMES[m.group(0)], text)


def read_last_synced() -> str:
    if not STATE_FILE.is_file():
        raise SyncError(
            f"{STATE_FILE.relative_to(REPO_ROOT)} is missing. Seed it with the upstream SHA whose "
            f"content is already present here, e.g. `git rev-parse {UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}`."
        )
    for line in STATE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    raise SyncError(f"{STATE_FILE.relative_to(REPO_ROOT)} contains no SHA")


def write_last_synced(sha: str) -> None:
    STATE_FILE.write_text(
        "# Last upstream (hydrogram/hydrogram) commit whose content is present in this fork.\n"
        "# Managed by dev_tools/sync_upstream.py -- see docs/dev/UPGRADE-PLAN.md, stage 0.\n"
        f"{sha}\n",
        encoding="utf-8",
    )


def ensure_clean_worktree() -> None:
    if git("status", "--porcelain"):
        raise SyncError("working tree is dirty; commit or stash before syncing")


def fetch_upstream() -> None:
    remotes = git("remote").splitlines()
    if UPSTREAM_REMOTE not in remotes:
        raise SyncError(
            f"no '{UPSTREAM_REMOTE}' remote. Add it with:\n"
            f"  git remote add {UPSTREAM_REMOTE} https://github.com/hydrogram/hydrogram"
        )
    logger.info("Fetching %s...", UPSTREAM_REMOTE)
    git("fetch", UPSTREAM_REMOTE, capture=False)


def unsynced_commits(last_synced: str, upstream_ref: str) -> list[tuple[str, str]]:
    """Oldest first, so they replay in the order upstream made them."""
    rng = f"{last_synced}..{upstream_ref}"
    out = git("log", "--reverse", "--format=%H%x1f%s", rng)
    if not out:
        return []
    commits = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\x1f")
        commits.append((sha, subject))
    return commits


def read_version() -> str | None:
    """Current ``__version__`` from the working tree, or None if it cannot be found."""
    path = REPO_ROOT / VERSION_FILE
    if not path.is_file():
        return None
    match = VERSION_ASSIGN_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def restore_version(pinned: str) -> bool:
    """Put ``pinned`` back if the patch we just applied changed it. True if we had to."""
    path = REPO_ROOT / VERSION_FILE
    text = path.read_text(encoding="utf-8")
    match = VERSION_ASSIGN_RE.search(text)
    if match is None or match.group(1) == pinned:
        return False
    path.write_text(text[: match.start(1)] + pinned + text[match.end(1) :], encoding="utf-8")
    return True


def split_file_diffs(patch: str) -> tuple[str, list[str]]:
    """Split a format-patch into (preamble, [one chunk per changed file])."""
    marker = "\ndiff --git "
    head, sep, rest = patch.partition(marker)
    if not sep:
        return patch, []
    chunks = [marker.lstrip("\n") + c for c in rest.split(marker)]
    return head + "\n", chunks


def drop_version_only_diff(patch: str) -> tuple[str, bool]:
    """Remove the ``pyrogram/__init__.py`` chunk when its only change is ``__version__``.

    Dropping a whole file chunk is safe; editing hunks is not, because the hunk header line
    counts and the surrounding context both have to stay truthful. If the chunk changes anything
    besides the version line it is kept, and any conflict is left for a human.
    """
    preamble, chunks = split_file_diffs(patch)
    if not chunks:
        return patch, False

    kept: list[str] = []
    dropped = False
    for chunk in chunks:
        if not chunk.startswith(f"diff --git a/{VERSION_FILE} "):
            kept.append(chunk)
            continue
        changed = [
            line
            for line in chunk.splitlines()
            if (line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
        ]
        if changed and all(VERSION_CHANGE_RE.match(line) for line in changed):
            dropped = True
            continue
        kept.append(chunk)
    return preamble + "".join(kept), dropped


def check_protected(patch: str) -> None:
    for path in PROTECTED_PATHS:
        if re.search(
            rf"^deleted file mode .*\n(?:.*\n)*?^--- a/{re.escape(path)}$", patch, re.MULTILINE
        ):
            raise SyncError(f"patch deletes protected file {path}; resolve by hand")


def rewrite_patch(patch: str) -> tuple[str, bool]:
    renamed = apply_renames(patch)
    check_protected(renamed)
    return drop_version_only_diff(renamed)


def replay(sha: str, subject: str, *, dry_run: bool) -> None:
    patch = git("format-patch", "-1", "--stdout", sha)
    rewritten, version_diff_dropped = rewrite_patch(patch)

    if version_diff_dropped:
        logger.warning(
            "  %s only bumped __version__ in %s; that chunk was dropped to keep the "
            "2.0.106 floor py-tgcalls needs",
            sha[:8],
            VERSION_FILE,
        )

    if dry_run:
        print(f"----- {sha[:8]} {subject}")
        print(rewritten)
        return

    pinned_version = read_version()

    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False, encoding="utf-8") as fh:
        fh.write(rewritten)
        patch_path = Path(fh.name)

    # `git am` runs with hooks skipped: a mid-replay hook failure would leave the sync half
    # applied, which is worse than a lint error found afterwards. Run the suite when it finishes.
    result = subprocess.run(
        ["git", "am", "--3way", "--keep-non-patch", "--no-verify", str(patch_path)],
        cwd=REPO_ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        git("am", "--abort", check=False)
        # Deliberately leave the patch on disk so it can be applied by hand.
        raise SyncError(
            f"could not apply {sha[:8]} ({subject}).\n"
            f"{result.stdout}{result.stderr}\n"
            f"The rewritten patch is at {patch_path}. Apply it by hand, commit, then record "
            f"the SHA:\n  echo {sha} > {STATE_FILE.relative_to(REPO_ROOT)}"
        )
    patch_path.unlink(missing_ok=True)

    if pinned_version is not None and restore_version(pinned_version):
        logger.warning(
            "  %s bumped __version__; restored the %s pin (py-tgcalls needs >=1.2.20)",
            sha[:8],
            pinned_version,
        )
        git("add", VERSION_FILE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report unsynced commits and exit 1 if there are any; apply nothing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the rewritten patches instead of applying them",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="replay at most N commits (0 = all)",
    )
    parser.add_argument(
        "--no-fetch",
        action="store_true",
        help="skip `git fetch upstream` (useful in tests and offline runs)",
    )
    parser.add_argument(
        "--upstream-ref",
        default=f"{UPSTREAM_REMOTE}/{UPSTREAM_BRANCH}",
        metavar="REF",
        help="ref to replay from (default: %(default)s); overriding it is how this tool is tested",
    )
    args = parser.parse_args()

    try:
        last_synced = read_last_synced()
        if not args.no_fetch:
            fetch_upstream()

        commits = unsynced_commits(last_synced, args.upstream_ref)
        if not commits:
            logger.info("Up to date with %s (%s).", args.upstream_ref, last_synced[:8])
            return 0

        logger.info("%d unsynced upstream commit(s):", len(commits))
        for sha, subject in commits:
            logger.info("  %s %s", sha[:8], subject)

        if args.check:
            return 1

        if args.limit:
            commits = commits[: args.limit]

        if not args.dry_run:
            ensure_clean_worktree()

        for sha, subject in commits:
            logger.info("Replaying %s %s", sha[:8], subject)
            replay(sha, subject, dry_run=args.dry_run)
            if not args.dry_run:
                write_last_synced(sha)
                git("add", str(STATE_FILE.relative_to(REPO_ROOT)))
                git("commit", "--amend", "--no-edit", "--no-verify")

        if args.dry_run:
            logger.info("Dry run: nothing applied.")
        else:
            logger.info("Done. Run the test suite before pushing.")
    except SyncError as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
