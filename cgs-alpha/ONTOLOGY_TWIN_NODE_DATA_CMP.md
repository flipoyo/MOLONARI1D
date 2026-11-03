# MOLONARI — Operating Space domain ontology (CGS-ALPHA)

**Canonical pilot strategy for the MOLONARI1D Operating Space.**
This document instantiates the generic atCGS domain contract `{TWIN, NODE, DATA, CMP}` defined on `flipoyo/atCGS:CGS-ALPHA` in `spec/OPERATING_SPACE_TWIN_NODE_DATA_CMP.md`.

```text
OperatingSpace = {TWIN, NODE, DATA, CMP}
```

| Primitive | Meaning for MOLONARI | Important distinction |
| --- | --- | --- |
| TWIN | Persistently identified Operating Space: MOLONARI, Virtual Lab, Sampling Point, or logical pole | TWIN is not a GitRepo and is not necessarily a physical device |
| NODE | Physical object, typed `HARDWARE` (sensor/device) or `RIVERBED` (natural riverbed) | A physical object is distinct from the PRIME G graph-level NODE |
| DATA | Temperature, pressure, inferred fluxes, quality controls and associated provenance | Measurements and derived results have separate, versionable provenance |
| CMP | Processing / scientific calculation, initially `pyheatmy` | Computation version and inputs are referenced; computation is not physical NODE |

## One root Twin, multiple nested Twins

```text
TWIN MOLONARI  (Operating Space root)
├── MOLO-HRDW  [logical pole; future GitRepo target]
├── MOLO-DATA  [logical pole; future GitRepo target]
├── MOLO-CMPT  [logical pole; future GitRepo target]
└── MOLO-TWIN  [logical pole; future GitRepo target]
    └── Virtual Lab [persistent TWIN]
        └── Sampling Point [persistent TWIN]
            ├── NODE HARDWARE
            ├── NODE RIVERBED
            ├── DATA observations and model results
            └── CMP pyheatmy
```

A Sampling Point may also descend directly from MOLO-TWIN. The four poles and the root are already represented as *logical* TWIN entries in `cgs-alpha/twins.toml`; they are **not yet four consolidated repositories**.

## Physical identity and time-varying relations

- `TWIN Sampling Point` is a persistent logical/scientific identity for the measurement site.
- `NODE RIVERBED` is a persistent physical referent, with location data PRIVATE by default.
- `NODE HARDWARE` names a particular physical instrument, independent of where it is deployed.
- `installed_at(HARDWARE, Sampling Point, [from,to))` is time-bounded and can change.
- `observes(HARDWARE, RIVERBED, [from,to))` is independently time-bounded.
- `DATA` references the sampling window, source NODE, units, provenance and immutable measurement state.
- `CMP` references the scientific processing configuration (e.g. pyheatmy), source DATA State and derived DATA State.

**Acceptance invariant:** replacing/moving a hardware NODE changes only its relations and associated datasets, never the identity of the Sampling Point or Riverbed. Prior relations must remain queryable by State/time.

## PoC first; four-GitRepo convergence second

Phase 1 retains `MOLONARI.cgs`: MOLONARI1D plus `MOLONARI-API`, `MOLONARI-data`, `MOLONARI-hardware`, `MOLONARI-gate`, `MOLONARI-computo` on their existing `CGS-MOLO` branches, alongside `atCGS/CGS-ALPHA` (seven repositories in one Operating Space). No renaming, forced migration, or loss of history.

Phase 2 will converge the logical poles into the future `MOLO-HRDW`, `MOLO-DATA`, `MOLO-CMPT`, `MOLO-TWIN` repository topology only after independent validation of GitTree history, individual repository rights and real `.gts` State restores.

## Omniscience contract

atCGS must first register the **TWIN MOLONARI**, then its four poles and each instantiated Virtual Lab/Sampling Point, with typed references to physical NODE, DATA and CMP. A registration candidate may be produced locally, but must **never be reported as existing in `.omniscience`** without authenticated OPX registration and independently verified GitTree State. Public projections disclose only specifically allowed attributes; confidential sampling positions, raw sensor data, credentials, journals and private compute assets remain PRIVATE.

No new cryptographic commitment is implemented here: ComplexGitSync owns `.gts`, integrity, memory and Merkle provenance. The domain `NODE` field is not the `NODE` field of infrastructure `PRIME G = {NAME, NODE, EDGE, OP*}`, and the ontology is **not** executable `.cgs` grammar.

## Minimal reproducible acceptance scenario

1. Instantiate a synthetic Virtual Lab and a Sampling Point as different TWIN identities; keep both stable across States.
2. Attach `RIVERBED-001` plus `SENSOR-001`; add temperature/pressure DATA and a versioned pyheatmy CMP reference.
3. Close the original sensor link and attach `SENSOR-002` with a new interval; the Sampling Point and RIVERBED identifiers must remain identical.
4. Validate timestamps, parent links, source/derived-data provenance, and deny unauthorized public projection of physical coordinates.
5. Materialize, record and **independently verify** a CGS-ALPHA `.gts` State before authenticating and publishing any TWIN reference to real `.omniscience`.

The first four steps are a **design/test contract**. No real atCGS registry publication, git state restore, scientific acquisition or live sampling site is claimed.
