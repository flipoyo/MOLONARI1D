#!/usr/bin/env python3
"""Candidate Twin registry: offline only, no publication, secrets or network."""
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
    """The candidate cannot be exposed because its ontology is invalid."""


def _read_toml(path: Path) -> dict:
    with path.open("rb") as src:
        return tomllib.load(src)


def _identity(name: str) -> str:
    """Discovery key only: NEVER a MerkleRoot, PoE, or GLYPH public key."""
    return hashlib.sha256(name.encode("utf-8")).hexdigest()


def validate_records(records: list[dict]) -> None:
    if not records or records[0].get("name") != "MOLONARI":
        raise ContractError("MOLONARI must be first and root TWIN")
    by_name: dict[str, dict] = {}
    for record in records:
        name = record.get("name")
        kind = record.get("kind")
        parent = record.get("parent")
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ContractError("invalid TWIN NAME")
        if name in by_name:
            raise ContractError("duplicate TWIN NAME")
        if kind not in KINDS:
            raise ContractError("invalid TWIN kind")
        if not isinstance(parent, str):
            raise ContractError("invalid parent NAME")
        if name == "MOLONARI":
            if kind != "operating-space" or parent:
                raise ContractError("root TWIN must be an Operating Space")
        elif kind == "pole":
            if name not in EXPECTED_POLES or parent != "MOLONARI":
                raise ContractError("invalid pole definition")
        elif kind == "virtual-lab":
            if parent != "MOLO-TWIN":
                raise ContractError("Virtual Lab parent must be MOLO-TWIN")
        elif parent != "MOLO-TWIN" and (
            parent not in by_name or by_name[parent]["kind"] != "virtual-lab"
        ):
            raise ContractError("Sampling Point parent must be MOLO-TWIN or a Virtual Lab")
        if name != "MOLONARI" and parent not in by_name:
            raise ContractError("parent TWIN must precede child")
        by_name[name] = record
    if any(name not in by_name or by_name[name]["kind"] != "pole" for name in EXPECTED_POLES):
        raise ContractError("four canonical poles required")


def validate_cgs(config: dict) -> None:
    if config.get("project", {}).get("name") != "MOLONARI":
        raise ContractError("Operating Space must be named MOLONARI")
    repos = config.get("repos", [])
    ids = [r["repository"].split("/")[-1] for r in repos]
    if ids != ["MOLONARI1D", "MOLONARI-API", "MOLONARI-data",
               "MOLONARI-hardware", "MOLONARI-gate", "MOLONARI-computo", "atCGS"]:
        raise ContractError("expected six historical GitRepos plus atCGS")
    paths = [r["relative_path"] for r in repos]
    if paths != [".", "Molonaviz", "data", "hardware", "molonari.io", "pyheatmy", "atCGS"]:
        raise ContractError("legacy GitTree paths changed")
    branches = [r["default_branch"] for r in repos]
    if branches != ["CGS-ALPHA", *(["CGS-MOLO"] * 5), "CGS-ALPHA"]:
        raise ContractError("legacy branch or gate branch changed")
    if any(r.get("nested_config") != "disabled" for r in repos):
        raise ContractError("nested config must be disabled")
    if any(r.get("private") or r.get("writable") for r in repos):
        raise ContractError("phase-one bootstrap must be PUBLIC and read-only")


def load() -> tuple[dict, list[dict]]:
    spec = _read_toml(SPEC)
    config = _read_toml(CGS)
    if spec["operating_space"]["name"] != "MOLONARI":
        raise ContractError("Operating Space name mismatch")
    if spec["omniscience"]["publication"] != "NOT_PUBLISHED":
        raise ContractError("offline candidate must not claim publication")
    validate_cgs(config)
    records = list(spec["twins"])
    validate_records(records)
    return spec, records


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
            {
                "name": node["name"],
                "parent": node["parent"],
                "kind": node["kind"],
                "status": node["phase"],
                "name_sha256": _identity(node["name"]),
            }
            for node in records
        ],
    }


def add_examples(records: list[dict], examples: list[Path]) -> list[dict]:
    extended = [dict(row) for row in records]
    for path in examples:
        obj = _read_toml(path)
        if set(obj) != {"twin"}:
            raise ContractError("one [twin] per example")
        record = obj["twin"]
        if not set(record) <= {"name", "parent", "kind", "phase", "context"}:
            raise ContractError("private/unknown field in example")
        if record.get("phase") != "example":
            raise ContractError("only synthetic examples are allowed")
        extended.append({key: record[key] for key in ("name", "kind", "parent", "phase")})
    validate_records(extended)
    return extended


def write_candidate(result: dict, out: str | None) -> None:
    encoded = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if out:
        target = Path(out)
        if target.is_symlink():
            raise ContractError("refusing symlink output")
        target.write_text(encoded, encoding="utf-8")
        print(f"candidate only: {target}")
    else:
        print(encoded, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    candidate = sub.add_parser("candidate")
    candidate.add_argument("--out")
    instance = sub.add_parser("instantiate")
    instance.add_argument("examples", nargs="+", type=Path)
    instance.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        _, records = load()
        if args.command == "validate":
            print("OK: MOLONARI, 4 logical poles, 7 GitRepos, no publication")
        elif args.command == "candidate":
            write_candidate(public_candidate(records), args.out)
        else:
            write_candidate(public_candidate(add_examples(records, args.examples)), args.out)
        return 0
    except (ContractError, OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        print(f"CGS-ALPHA registry invalid: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
