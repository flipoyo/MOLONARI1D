# MOLONARI — CGS-ALPHA Operating Space POC

**Phase 1: CGS-MOLO GitRepos preserved; atCGS integrated as a seventh GitRepo.**

The branch `MOLONARI1D/CGS-ALPHA` forks `CGS-MOLO` without modifying
`CGS-MOLO` or creating the four future GitRepos. `MOLONARI.cgs` defines
one Operating Space, `MOLONARI`, rooted at `flipoyo/MOLONARI1D`.
Its six historical repositories retain the existing paths and CGS-MOLO branch;
`flipoyo/atCGS/CGS-ALPHA` is mounted at `atCGS/`.

## Domain-level Operating Space strategy

Canonical MOLONARI domain model: [`{TWIN, NODE, DATA, CMP}`](ONTOLOGY_TWIN_NODE_DATA_CMP.md), with an [illustrative physical-node/data/computation fixture](examples/domain-sampling-point.toml). **NODE denotes a physical object (`HARDWARE` or `RIVERBED`), not a GitRepo nor the infrastructure graph NODE.** Virtual Labs, Sampling Points and the four poles are TWINs. This is separate from `PRIME G`, changes no `.cgs` grammar, and does not publish into `.omniscience`.

## The two graphs are different

**Actual GitTree**: MOLONARI1D (root), Molonaviz, data, hardware, molonari.io,
pyheatmy and atCGS — seven existing GitRepos, only one Operating Space.

**Logical Twin tree** (not yet separate GitRepos):

```text
MOLONARI  (Operating Space and root TWIN)
├── MOLO-HRDW  (MOLONARI-hardware)
├── MOLO-DATA  (MOLONARI-data)
├── MOLO-CMPT  (MOLONARI-computo/pyheatmy)
└── MOLO-TWIN  (MOLONARI1D + MOLONARI-API + MOLONARI-gate + atCGS)
    └── Virtual Lab <NAME>            # instantiated on request
        └── Sampling Point <NAME>     # instantiated on request
```

A Sampling Point may also be a direct child of MOLO-TWIN.
Four poles here are typed TWIN identities, **not four new Git repositories**.
A second migration phase may consolidate into MOLO-HRDW, MOLO-DATA, MOLO-CMPT,
MOLO-TWIN after an explicit history-preserving GitRepo migration.

## atCGS and registered TWINs

`atCGS/CGS-ALPHA` version `1.7.1-alpha` pins
`ComplexGitSync/CGS-ALPHA` at `8.7.1` (MemorySetupBranch).
The engine-owned `.cgitsync/.memory` mount is declared at OPX and DEV;
its branch is derived by ComplexGitSync rather than fixed to `main`.
This is distinct from the `.omniscience` publication boundary.
For precise current commits, consult `cgs-alpha/refs.lock.toml` and
`cgs-alpha/LATEST_CGS_ALPHA.md`.
atCGS owns identities, grants, GLYPH-sealed SSH keys, OPX/DEV/USR/PUB routing
and public projection. ComplexGitSync owns GitTree, .gts, memory and Integrity.

The local `cgs-alpha/twins.toml` defines the root, poles, and parent links.
`twin_registry.py` can validate this topology and export a **candidate**
namespace for eventual Omniscience registration. For every TWIN it emits
NAME, kind, parent and SHA-256(NAME), with `evidence=unverified`,
`publication=NOT_PUBLISHED`, `gts_verified=false`. A NAME hash is a lookup
key only, not a MerkleRoot, cryptographic PoE, or public GLYPH. No actual
Codeberg `.omniscience` write, GLYPH release or register merge is performed.

The authentic Omniscience publication process must:
1. authenticate an authorized OPX session;
2. resolve a real GitTree State with a verified .gts and its provenance;
3. atomically register MOLONARI and its typed parent/child TWIN references;
4. publish an allowlisted projection with independently verifiable proof;
5. keep `.cgitsync/.memory/.register`, SSH keys, user names and confidential
   sampling-site locations PRIVATE.

## Known integration gap

Current `atcgs.session.Session.cgs()` still generates `relative_path` from
each GitRepo basename and `default_branch=main`. It also limits each session
to grants of one role, even though a Twin may require mixed GitRepo grants.
**Do not use its generated configuration to bootstrap MOLONARI yet.**
For phase 1, use the committed `MOLONARI.cgs`, which preserves the repository
paths and branch assignments, and run the public CGS read-only workflow.

## Offline reproducibility

Run from this repository's root, with Python 3.11+:

```sh
python3 cgs-alpha/twin_registry.py validate
python3 cgs-alpha/twin_registry.py candidate --out /tmp/molonari-index.json
python3 cgs-alpha/twin_registry.py instantiate cgs-alpha/examples/virtual-lab.toml cgs-alpha/examples/sampling-point.toml --out /tmp/molonari-examples.json
python3 -m unittest discover -s cgs-alpha/tests -v
```

To validate the real CGS grammar, use a separate local clone of atCGS/CGS-ALPHA:

```sh
pixi install
pixi run cgitsync validate /absolute/path/to/MOLONARI.cgs
pixi run cgitsync view-tree /absolute/path/to/MOLONARI.cgs
# ONLY from a disposable workspace after inspecting remotes:
pixi run cgitsync bootstrap /absolute/path/to/MOLONARI.cgs
```

The bootstrap requires network access; no live BOOT, authentic .gts,
remote publish or write operation has been run by this POC.

## Gate for phase 2

- [x] CGS-ALPHA branch from CGS-MOLO; keep original intact.
- [x] Six MOLONARI historical repositories and CGS-MOLO branches conserved.
- [x] atCGS linked at CGS-ALPHA; candidate MOLONARI root + four poles.
- [x] Synthetic Virtual Lab and Sampling Point references.
- [ ] Validate with actual ComplexGitSync 8.7.1 CgsDocument inside Pixi.
- [ ] BOOT real 7-GitRepo State to READY, .gts saved and independently restored.
- [ ] atCGS role-filtered TWIN.cgs retains topological paths, branch and mixed grants.
- [ ] Authenticate and publish verified TWIN references into real .omniscience.
- [ ] Only then plan migration to four new GitRepos.

See `cgs-alpha/TUTORIAL.md` and the source-head inventory in
`cgs-alpha/refs.lock.toml` (baseline refs; not a .gts).
