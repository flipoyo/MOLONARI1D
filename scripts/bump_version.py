#!/usr/bin/env python3
"""Bump the SemVer version of this repository and sync it into every file that mirrors it.

    pixi run bump-version minor             # 0.12.1 -> 0.13.0
    pixi run bump-version patch --dry-run   # print the plan, write nothing
    pixi run bump-version major --stage rc  # 0.12.1 -> 1.0.0-rc
    pixi run bump-version --check           # every mirror holds the version of pixi.toml (for CI)

The same file is in MOLONARI-computo and MOLONARI1D, after the bump-version of ComplexGitSync.
`pixi.toml` `[workspace] version` is the reference. The mirrors are found, not listed: a "v<version>" in a level-1 heading of `README.md`, the `[project] version` of
`pyproject.toml` if there is one, and `__version__` in the `__init__.py` of each package named by
`[tool.setuptools] packages`. Every file is read and rewritten in memory first; a field found other than exactly
once stops the bump with nothing on disk changed. The level is the caller's judgement against the public interface
of the repository; nothing here computes it.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

# scripts/bump_version.py -> the root of the repository
ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<stage>[0-9A-Za-z.-]+))?")
VERSION_LINE = r'^version = "{v}"'
ANY = r"[0-9][0-9A-Za-z.+-]*"  # a version, up to the first character that cannot be in one
README_HEADER = r"^# .*\bv{v}(?![0-9A-Za-z.+-])"  # "v1.2.3" in a level-1 heading of README.md


@dataclass(frozen=True)
class Target:
    path: str
    pattern: str  # must contain {v}: the version, escaped
    section: str | None = None  # TOML table the line must be in, e.g. "workspace"

    def _span(self, text: str) -> tuple[int, int]:
        """The part of the text the pattern is looked for in: one TOML table, or the whole file."""
        if self.section is None:
            return 0, len(text)
        head = re.search(rf"^\[{re.escape(self.section)}\]\s*$", text, re.M)
        if not head:
            raise SystemExit(f"bump-version: {self.path}: no [{self.section}] table; nothing written")
        nxt = re.compile(r"^\[", re.M).search(text, head.end())
        return head.end(), nxt.start() if nxt else len(text)

    def find(self, text: str, version: str = ANY) -> list[str]:
        start, end = self._span(text)
        pattern = self.pattern.format(v=f"({version})" if version == ANY else re.escape(version))
        return re.findall(pattern, text[start:end], re.M)

    def rewrite(self, text: str, old: str, new: str) -> str:
        start, end = self._span(text)
        regex = re.compile(self.pattern.format(v=re.escape(old)), re.M)
        found = regex.findall(text[start:end])
        if len(found) != 1:
            raise SystemExit(f"bump-version: {self.path}: expected one match of {self.pattern!r}, found {len(found)}; nothing written")
        part = regex.sub(lambda m: m.group(0).replace(old, new), text[start:end])
        return text[:start] + part + text[end:]


REFERENCE = Target("pixi.toml", VERSION_LINE, "workspace")


def targets(root: Path = ROOT) -> list[Target]:
    """The reference, then every mirror this repository has."""
    found = [REFERENCE]
    readme = root / "README.md"
    if readme.is_file() and Target("README.md", README_HEADER).find(readme.read_text(encoding="utf-8")):
        found.append(Target("README.md", README_HEADER))
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        found.append(Target("pyproject.toml", VERSION_LINE, "project"))
        packages = re.search(r"^\[tool\.setuptools\][^\[]*?^packages\s*=\s*\[([^\]]*)\]", text, re.M | re.S)
        for name in re.findall(r'"([^"]+)"', packages.group(1)) if packages else []:
            init = f"{name.replace('.', '/')}/__init__.py"
            if (root / init).is_file():
                found.append(Target(init, r'^__version__ = "{v}"'))
    return found


def current(root: Path = ROOT) -> str:
    path = root / REFERENCE.path
    if not path.is_file():
        raise SystemExit("bump-version: no pixi.toml at the root of the repository")
    found = REFERENCE.find(path.read_text(encoding="utf-8"))
    if len(found) != 1:
        raise SystemExit('bump-version: pixi.toml needs exactly one version = "..." in [workspace]')
    return found[0]


def next_version(old: str, level: str, stage: str | None = None) -> str:
    parts = SEMVER.fullmatch(old)
    if not parts:
        raise SystemExit(f"bump-version: {old!r} is not SemVer")
    major, minor, patch = (int(parts[k]) for k in ("major", "minor", "patch"))
    if level == "major":
        major, minor, patch = major + 1, 0, 0
    elif level == "minor":
        minor, patch = minor + 1, 0
    elif level == "patch":
        patch += 1
    else:
        raise SystemExit(f"bump-version: level is major, minor or patch, not {level!r}")
    label = parts["stage"] if stage is None else stage
    if label and not re.fullmatch(r"[0-9A-Za-z.-]+", label):
        raise SystemExit(f"bump-version: {label!r} is not a SemVer pre-release label")
    return f"{major}.{minor}.{patch}" + (f"-{label}" if label else "")


def plan(old: str, new: str, root: Path = ROOT) -> dict[Path, str]:
    """Every rewritten file's new text, all computed before any is written."""
    texts: dict[Path, str] = {}
    for target in targets(root):
        path = root / target.path
        texts[path] = target.rewrite(texts.get(path, path.read_text(encoding="utf-8")), old, new)
    return texts


def check(root: Path = ROOT) -> int:
    version = current(root)
    if not SEMVER.fullmatch(version):
        print(f"bump-version: {version!r} in pixi.toml is not SemVer")
        return 1
    wrong = []
    for target in targets(root)[1:]:
        found = target.find((root / target.path).read_text(encoding="utf-8"))
        if found != [version]:
            wrong.append(f"  {target.path}: {', '.join(found) or 'no version'}")
    if wrong:
        print(f"bump-version: the mirrors do not hold {version}, the version of pixi.toml:")
        print("\n".join(wrong))
        return 1
    print(f"{version}: " + ", ".join(t.path for t in targets(root)))
    return 0


def write(texts: dict[Path, str]) -> None:
    drafts = []
    for path, text in texts.items():
        draft = path.with_name(f".{path.name}.bump")
        draft.write_text(text, encoding="utf-8")
        drafts.append((draft, path))
    for draft, path in drafts:
        os.replace(draft, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("level", nargs="?", choices=("major", "minor", "patch"))
    parser.add_argument("--stage", help="pre-release label (default: keep the current one); '' drops it")
    parser.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    parser.add_argument("--check", action="store_true", help="check that every mirror holds the version of pixi.toml")
    args = parser.parse_args(argv)
    if args.check:
        return check()
    if args.level is None:
        parser.error("a level (major, minor or patch) or --check is needed")
    if check() != 0:
        raise SystemExit("bump-version: fix the mirrors before bumping; nothing written")
    old = current()
    new = next_version(old, args.level, args.stage)
    texts = plan(old, new)
    print(f"{old} -> {new}")
    for path in texts:
        print(f"  {path.relative_to(ROOT)}")
    if args.dry_run:
        print("dry run: nothing written")
        return 0
    write(texts)
    print(f"written; commit subject: {ROOT.name}-{new} …")
    return 0


if __name__ == "__main__":
    sys.exit(main())
