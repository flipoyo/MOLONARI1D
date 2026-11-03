# TUTORIAL — MOLONARI as a TWIN, Virtual Lab and Sampling Point

## Phase 1 (non-destructive)

1. Checkout `flipoyo/MOLONARI1D:CGS-ALPHA`, based on CGS-MOLO.
2. Inspect `MOLONARI.cgs` — the six legacy GitRepos are on CGS-MOLO.
3. Run `python3 cgs-alpha/twin_registry.py validate`.
4. Run `python3 cgs-alpha/twin_registry.py candidate --out /tmp/molonari.json`.
5. Run `python3 cgs-alpha/twin_registry.py instantiate cgs-alpha/examples/virtual-lab.toml cgs-alpha/examples/sampling-point.toml --out /tmp/molonari-lab.json`.
6. Run `python3 -m unittest discover -s cgs-alpha/tests -v`.
7. In a **separate** `atCGS/CGS-ALPHA` clone, run `pixi install`, then
   `pixi run cgitsync validate /absolute/path/to/MOLONARI.cgs`.
8. For a true Operating Space, explicitly authorize a disposable
   `pixi run cgitsync bootstrap /absolute/path/to/MOLONARI.cgs`.
   Save the resulting actual CGSHOME and .gts separately; no push or release.

## Identity and TWIN activation (target functionality)

The atCGS identity layer allows an OPX to enroll a user and grant a role on
each GitRepo. A session proves possession, opens the sealed GLYPH and loads
repo-specific SSH credentials into an isolated ssh-agent, then delegates to
cgitsync. Currently `Session.cgs()` imposes `main` and baseline paths,
so it cannot yet generate an accurate multi-role MOLONARI Twin configuration.

The desired interface is:

```text
@cgs OPX: register OperatingSpace MOLONARI
@cgs OPX: register TWIN MOLO-HRDW/MOLO-DATA/MOLO-CMPT/MOLO-TWIN
@cgs DEV/USR: activate MOLONARI with grants per GitRepo, preserving .cgs
@cgs DEV: create TWIN virtual-lab NAME under MOLO-TWIN
@cgs DEV: create TWIN sampling-point NAME under MOLO-TWIN or a Virtual Lab
@cgs PUB: read only verified and authorized public references
```

These are **target contracts, not existing CLI verbs**. Current tested
offline actions are `validate`, `candidate` and `instantiate` in
`cgs-alpha/twin_registry.py`.

## Phase 2: new repository convergence

Introduce the four GitRepos only after verifying that the original
6-GitRepo GitTree can be fully reconstructed from a .gts. Preserve every
source GitRepo and immutable commit in a migration manifest. The new graph
must maintain all TWIN names/parent links; migration changes storage paths,
not ontological identity.
