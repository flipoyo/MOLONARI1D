#!/usr/bin/env python3
"""The MOLONARI1D front end of ComplexGitSync: one command per need, each mapped to the right `cgitsync` command.

    pixi run molo load .config/molonari.cgs           # recompose an Operating Space (cgitsync bootstrap)
    pixi run molo load .config/molonari.cgs --https   # same, without an SSH key
    pixi run molo update .config/molonari.cgs         # resynchronise the Operating Space of $CGSHOME (cgitsync pull)
    pixi run molo status                              # state of the Operating Space of $CGSHOME (cgitsync status)

`cgitsync` comes with the pixi environment of this repository (ComplexGitSync is a dependency of pixi.toml).
Any other option is passed to `cgitsync` as it is.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {"load": "bootstrap", "update": "pull", "status": "status"}


def cgs_path(name: str) -> str:
    """The .cgs as given, else in .config/ of this repository; absolute, since cgitsync may run elsewhere."""
    for path in (Path(name), ROOT / ".config" / name, ROOT / ".config" / f"{name}.cgs"):
        if path.is_file():
            return str(path.resolve())
    raise SystemExit(f"molo: no .cgs {name!r}; available: {', '.join(p.name for p in sorted((ROOT / '.config').glob('*.cgs')))}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="molo", description=__doc__.split("\n\n")[0])
    parser.add_argument("command", choices=COMMANDS, help="load (bootstrap), update (pull) or status")
    parser.add_argument("cgs", nargs="?", help="the .cgs of the Operating Space, e.g. .config/molonari.cgs or molonari")
    parser.add_argument("--https", action="store_true", help="clone over HTTPS instead of SSH")
    args, rest = parser.parse_known_args(argv)

    cgitsync = shutil.which("cgitsync")
    if cgitsync is None:
        raise SystemExit("molo: cgitsync not found; run it through pixi: pixi run molo ...")
    command = [cgitsync, COMMANDS[args.command]]
    if args.cgs:
        command.append(cgs_path(args.cgs))
    elif args.command == "load":
        parser.error("load needs a .cgs, e.g. pixi run molo load .config/molonari.cgs")
    if args.https:
        command += ["--force-protocol", "https"]
    command += rest
    print("molo:", " ".join(["cgitsync", *command[1:]]), flush=True)
    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
