#!/usr/bin/env bash
# Chaîne complète sur Point034 : bootstrap, lab build, run, report, requêtes au niveau user, puis le travail d'un dev.
#
#     scripts/demo_lundi.sh <dossier vide>
#
# Un dossier qui contient déjà l'espace de travail MOLONARI1D est repris : bootstrap et installation sont sautés, et les
# twins déjà calculés ne sont pas recalculés. S'arrête à la première étape en échec, avec un code de sortie non nul.
# Variables : CGITSYNC_HOME (dossier de ComplexGitSync), PORT (port du serveur local), TWIN_CLI et PYTHON (pour essayer un
# autre code que celui de l'espace de travail : le script lance alors cette commande au lieu de celle du venv).

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage : $0 <dossier vide>" >&2
    exit 2
fi

MANIFEST="$(cd "$(dirname "$0")/.." && pwd)/install-orx.cgs"
CGITSYNC_HOME="${CGITSYNC_HOME:-$HOME/tools/ComplexGitSync}"
PORT="${PORT:-8765}"
mkdir -p "$1"
TARGET="$(cd "$1" && pwd)"
WORKSPACE="$TARGET/MOLONARI1D"
BACKEND="$WORKSPACE/Molonaviz/molonaviz2"
POINT="MOLONARI-TWIN/Point034"
TWINS="$POINT/twins"
REPORTS="$POINT/public_reports"
LAB="MOLONARI-TWIN/virtual_lab/lab_point034/description"  # lab.yaml est dans le sous-dépôt description du lab
BASE="http://127.0.0.1:$PORT/v1"

if [ ! -d "$WORKSPACE" ] && [ -n "$(ls -A "$TARGET")" ]; then
    echo "Le dossier $TARGET n'est pas vide et ne contient pas MOLONARI1D." >&2
    exit 2
fi

START=$SECONDS
STEP=""
SUMMARY=""
SERVER=""

on_exit() {
    local code=$?
    if [ -n "$SERVER" ]; then
        kill "$SERVER" 2>/dev/null || true
    fi
    if [ "$code" -ne 0 ] && [ -n "$STEP" ]; then
        echo "ÉCHEC à l'étape : $STEP (code $code)" >&2
    fi
}
trap on_exit EXIT

step() {
    finish_step
    STEP="$1"
    STEP_START=$SECONDS
    echo
    echo "=== $STEP"
}

finish_step() {
    if [ -n "$STEP" ]; then
        SUMMARY+=$(printf '  %4d s  %s' "$((SECONDS - STEP_START))" "$STEP")$'\n'
    fi
}

step "Installation par cgitsync et uv"
if [ -d "$WORKSPACE" ]; then
    echo "Espace de travail existant : $WORKSPACE"
else
    (cd "$CGITSYNC_HOME" && .pixi/envs/default/bin/cgitsync bootstrap "$MANIFEST" --cgs-path "$TARGET")
    (cd "$BACKEND" && uv sync --package molonari-twin --extra server --no-default-groups)
fi
TWIN_CLI="${TWIN_CLI:-$BACKEND/.venv/bin/molonari-twin}"
PYTHON="${PYTHON:-$BACKEND/.venv/bin/python}"
cd "$WORKSPACE"
"$TWIN_CLI" --help > /dev/null

step "Virtual lab : lab build"
"$TWIN_CLI" lab build "$LAB" --point Point034
"$PYTHON" - <<'EOF'
import json

manifest = json.load(open("data/processed_data/Point034/manifest.json", encoding="utf-8"))
assert manifest["lab"] == "lab_point034" and manifest["point"] == "Point034", manifest
assert manifest["rows"] > 0 and len(manifest["cleaned_sha256"]) == 64, manifest
print(f"Manifeste : lab {manifest['lab']}, code {manifest['code_version']}, {manifest['rows']} lignes")
EOF

step "Twin direct"
"$TWIN_CLI" validate "$TWINS/twin_direct"
"$TWIN_CLI" run "$TWINS/twin_direct"

step "Twin MCMC"
"$TWIN_CLI" validate "$TWINS/twin_mcmc"
"$TWIN_CLI" run "$TWINS/twin_mcmc"

step "Rapport public"
"$TWIN_CLI" report "$TWINS/twin_mcmc" --output "$REPORTS"
test -f "$TWINS/twin_direct/generation.yaml"  # écrit par report : les couches et les bornes de generate
for twin in twin_direct twin_mcmc; do
    test -f "$TWINS/$twin/registry.csv" && test -n "$(ls "$TWINS/$twin/results")"  # résultats et registre par twin
done
"$PYTHON" - "$REPORTS" "$TARGET" "$HOME" <<'EOF'
import json
import pathlib
import sys

reports, target, home = sys.argv[1:]
folder = pathlib.Path(reports)
index = json.loads((folder / "report.json").read_text(encoding="utf-8"))
assert index["point"] == "Point034", index["point"]  # un rapport public appartient à un point réel
files = [path for path in folder.rglob("*") if path.is_file() and path.suffix != ".npz"]
for forbidden in ('"seed"', "orx", target, home):
    found = [path.name for path in files if forbidden.encode() in path.read_bytes()]
    assert not found, (forbidden, found)
flux = json.loads((folder / "inversion-water_flux.json").read_text(encoding="utf-8"))["data"]["mean"]
print(f"Point {index['point']} : {len(index['entries'])} entrées, ni graine ni chemin dans {len(files)} fichiers")
print(f"Flux d'eau moyen, inversion : {flux['value']:.2e} m/s, intervalle {flux['interval']}")
EOF

step "Lecture du rapport et état généré (user)"
"$TWIN_CLI" reports list MOLONARI-TWIN
"$TWIN_CLI" reports show "$POINT"
"$TWIN_CLI" reports chains "$POINT"
STATE="$TARGET/state"
rm -rf "$STATE"
"$TWIN_CLI" generate "$POINT" --output "$STATE"
"$TWIN_CLI" ask "$STATE" water_flux --level user
if "$TWIN_CLI" ask "$STATE" residuals --level user --json > /dev/null; then
    echo "residuals aurait dû être refusée au niveau user sur un état généré" >&2
    exit 1
fi
echo "Question réservée au dev refusée sur l'état généré : residuals"

step "Requêtes au niveau user"
ASKED="$TARGET/ask.json"
SERVED="$TARGET/serve.json"
"$TWIN_CLI" questions "$TWINS/twin_mcmc"
"$TWIN_CLI" ask "$TWINS/twin_mcmc" water_flux --params '{"level":0.9}' --json > "$ASKED"
"$TWIN_CLI" ask "$TWINS/twin_mcmc" heat_budget
"$TWIN_CLI" ask "$TWINS/twin_mcmc" temperature --params '{"z":0.2}' --json > /dev/null
if "$TWIN_CLI" ask "$TWINS/twin_mcmc" residuals --json > /dev/null; then
    echo "residuals aurait dû être refusée au niveau user" >&2
    exit 1
fi
echo "Question réservée à l'admin refusée par ask : residuals"

if curl -s "$BASE/info" > /dev/null; then
    echo "Le port $PORT est déjà occupé : un autre serveur répondrait à la place de celui-ci (PORT=... pour en changer)." >&2
    exit 1
fi
"$TWIN_CLI" serve --local --level user --port "$PORT" --twins-folder "$TWINS" --tasks-db "$TARGET/tasks.sqlite" > "$TARGET/serve.log" 2>&1 &
SERVER=$!
for _ in $(seq 1 60); do
    curl -sf "$BASE/info" > /dev/null && break
    kill -0 "$SERVER" 2> /dev/null || { cat "$TARGET/serve.log" >&2; exit 1; }
    sleep 1
done
curl -sf -X POST -H 'content-type: application/json' -d '{"level":0.9}' "$BASE/twins/twin_mcmc/questions/water_flux" > "$SERVED"
"$PYTHON" - "$ASKED" "$SERVED" <<'EOF'
import json
import sys

asked, served = (json.load(open(path, encoding="utf-8")) for path in sys.argv[1:])
assert asked == served, "ask et curl ne donnent pas le même JSON"
print("ask --json et curl sur /v1 donnent le même JSON")
EOF
for request in "questions/residuals" "run"; do
    code=$(curl -s -o /dev/null -w '%{http_code}' -X POST -H 'content-type: application/json' -d '{}' "$BASE/twins/twin_mcmc/$request")
    if [ "$code" != "403" ]; then
        echo "$request : 403 attendu, $code reçu" >&2
        exit 1
    fi
    echo "Refusé par le serveur (403) : $request"
done

step "Travail d'un dev : twin de σ dans son operating space"
# Le dev lance son twin avec sa propre graine, hors du dossier du point, et reçoit un rapport local de ce twin. Il lui faut
# le dépôt de données (MOLONARI_DATA), puisque son space n'est pas dans l'espace de travail.
SPACE="$TARGET/operating-space"
SIGMA="0.08"
DEVSEED="7"
rm -rf "$SPACE"
BEFORE=$(cd "$REPORTS" && find . -type f | sort | xargs shasum | shasum)
MOLONARI_DATA="$WORKSPACE/data" "$TWIN_CLI" run "$TWINS/twin_mcmc" --sigma-temperature "$SIGMA" --space "$SPACE" --seed "$DEVSEED"
DEVTWIN="$SPACE/twin_mcmc_sigmaT$SIGMA"
MOLONARI_DATA="$WORKSPACE/data" "$TWIN_CLI" report "$DEVTWIN" --forward "$TWINS/twin_direct" --output "$SPACE/rapport_local"
AFTER=$(cd "$REPORTS" && find . -type f | sort | xargs shasum | shasum)
"$PYTHON" - "$POINT/orx/twin_mcmc.yaml" "$DEVTWIN" "$SPACE/rapport_local" "$DEVSEED" "$BEFORE" "$AFTER" <<'EOF'
import json
import pathlib
import sys

import yaml

reference, devtwin, local, devseed, before, after = sys.argv[1:]
assert before == after, "le rapport local a modifié public_reports/"
refseed = yaml.safe_load(open(reference, encoding="utf-8"))["mcmc"]["seed"]
dev = yaml.safe_load((pathlib.Path(devtwin) / "orx.yaml").read_text(encoding="utf-8"))["mcmc"]["seed"]
assert dev == int(devseed) != refseed, (dev, refseed)  # la graine du dev, jamais la graine de référence
assert json.loads((pathlib.Path(local) / "report.json").read_text(encoding="utf-8")).get("local") is True
print(f"Twin du dev : graine {dev} (celle de référence n'est pas copiée), rapport local marqué local, public_reports/ inchangé")
EOF

finish_step
STEP=""
echo
echo "=== Chaîne réussie en $((SECONDS - START)) s"
printf '%s' "$SUMMARY"
echo "Espace de travail : $WORKSPACE"
echo "Rapport public : $WORKSPACE/$REPORTS"
