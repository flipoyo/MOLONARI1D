#!/usr/bin/env python3
"""Read-only MOLONARI TWIN graph candidate. Not a real Omniscience record or PoE."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "cgs-alpha" / "twins.toml"
CGS = ROOT / "MOLONARI.cgs"
EXPECTED_POLES = ("MOLO-HRDW", "MOLO-DATA", "MOLO-CMPT", "MOLO-TWIN")
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,63}\Z")
KINDS = {"operating-space", "pole", "virtual-lab", "sampling-point"}


class ContractError(ValueError):
    pass


def _read_toml(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate_cgs(config: dict) -> None:
    if config.get("project", {}).get("name") != "MOLONARI":
        raise ContractError("wrong Operating Space name")
    repos = config.get("repos", [])
    names = [r["repository"].rsplit("/", 1)[-1] for r in repos]
    if names != ["MOLONARI1D", "MOLONARI-API", "MOLONARI-data",
                 "MOLONARI-hardware", "MOLONARI-gate", "MOLONARI-computo", "atCGS"]:
        raise ContractError("seven GitRepos expected in historical order")
    paths = [r.get("relative_path") for r in repos]
    if paths != [".", "Molonaviz", "data", "hardware",
                 "molonari.io", "pyheatmy", "atCGS"]:
        raise ContractError("historical GitTree layout modified")
    branches = [r.get("default_branch") for r in repos]
    if branches != ["CGS-ALPHA", *(["CGS-MOLO"] * 5), "CGS-ALPHA"]:
        raise ContractError("historical branch changed")
    if any(r.get("private") or r.get("writable") or
           r.get("nested_config") != "disabled" for r in repos):
        raise ContractError("phase 1 must be a public leaf-only topology")


def validate_records(records: list[dict]) -> None:
    if not records or records[0].get("name") != "MOLONARI":
        raise ContractError("MOLONARI must be root")
    known = {}
    for row in records:
        name, kind, parent = row.get("name"), row.get("kind"), row.get("parent")
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in known:
            raise ContractError("invalid or duplicate Twin name")
        if kind not in KINDS or not isinstance(parent, str):
            raise ContractError("invalid Twin type or parent")
        if name == "MOLONARI":
            if kind != "operating-space" or parent != "":
                raise ContractError("invalid root")
        elif kind == "pole":
            if name not in EXPECTED_POLES or parent != "MOLONARI":
                raise ContractError("invalid pole")
        elif kind == "virtual-lab":
            if parent != "MOLO-TWIN":
                raise ContractError("Virtual Lab must descend from MOLO-TWIN")
        elif parent != "MOLO-TWIN" and (parent not in known or
                                        known[parent]["kind"] != "virtual-lab"):
            raise ContractError("Sampling Point must descend from MOLO-TWIN or a Virtual Lab")
        if name != "MOLONARI" and parent not in known:
            raise ContractError("parent must precede child")
        known[name] = row
    if not all(name in known and known[name]["kind"] == "pole" for name in EXPECTED_POLES):
        raise ContractError("four poles required")


def load() -> tuple[dict, list[dict]]:
    specification, config = _read_toml(SPEC), _read_toml(CGS)
    if specification["operating_space"]["name"] != "MOLONARI":
        raise ContractError("name mismatch")
    if specification["omniscience"]["publication"] != "NOT_PUBLISHED":
        raise ContractError("cannot claim publication")
    records = specification["twins"]
    validate_cgs(config)
    validate_records(records)
    return specification, records


def public_candidate(records: list[dict]) -> dict:
    validate_records(records)
    return {
        "namespace": "MOLONARI",
        "operating_space": "MOLONARI",
        "schema": "atCGS/twin-namespace/candidate/v0",
        "publication": "NOT_PUBLISHED",
        "evidence": "unverified",
        "gts_verified": False,
        "glyph_available": False,
        "twins": [
            {"name": row["name"], "kind": row["kind"], "parent": row["parent"],
             "name_sha256": hashlib.sha256(row["name"].encode()).hexdigest(),
             "status": row["phase"]}
            for row in records
        ],
    }


def add_examples(records: list[dict], files: list[Path]) -> list[dict]:
    out = [dict(row) for row in records]
    for path in files:
        data = _read_toml(path)
        if set(data) != {"twin"}:
            raise ContractError("only [twin] expected")
        twin = data["twin"]
        if not set(twin) <= {"name", "kind", "parent", "phase", "context"}:
            raise ContractError("unexpected or private twin fields")
        if twin.get("phase") != "example":
            raise ContractError("POC only accepts synthetic examples")
        out.append({key: twin[key] for key in ("name", "kind", "parent", "phase")})
    validate_records(out)
    return out


def write_candidate(doc: dict, filename: str | None) -> None:
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if filename:
        p = Path(filename)
        if p.is_symlink():
            raise ContractError("symlink output refused")
        p.write_text(text, encoding="utf-8")
        print(f"candidate only: {p}")
    else:
        print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="command", required=True)
    actions.add_parser("validate")
    candidate = actions.add_parser("candidate")
    candidate.add_argument("--out")
    instantiate = actions.add_parser("instantiate")
    instantiate.add_argument("examples", nargs="+", type=Path)
    instantiate.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        _, records = load()
        if args.command == "validate":
            print("OK: MOLONARI, four logical poles, seven GitRepos, NOT_PUBLISHED")
        elif args.command == "candidate":
            write_candidate(public_candidate(records), args.out)
        else:
            write_candidate(public_candidate(add_examples(records, args.examples)), args.out)
        return 0
    except (ContractError, OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        print(f"CGS-ALPHA invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
