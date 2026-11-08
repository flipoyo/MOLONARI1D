#!/usr/bin/env bash
# Expérience SIMU : le twin direct de Point034 est calculé dans cet espace, exporté dans le dépôt SIMU, puis comparé au bit
# près aux exports des autres machines (`molonari-twin reproduce --export`, puis `reproduce --compare`).
#
#     pixi run -e simu simu-direct
#
# À lancer depuis la racine d'un espace monté par `cgitsync bootstrap simu-direct.cgs`, sur un Mac M1 (Darwin arm64).
# Un espace ne sert qu'à un calcul : `lab build` laisse `data/processed_data/` non suivi, et les résultats existent ensuite.
# Le twin n'est pas tagué et `run` est lancé sans `--strict` : `strict_problems` refuse toute pré-version
# (E_STRICT_PRERELEASE). Le script fait lui-même les contrôles qui comptent : dépôts propres, mêmes commits que les
# machines déjà présentes, twin jamais calculé dans cet espace.
# Variables : MACHINE (nom du dossier d'export, `hostname -s` par défaut), SIMU_PUSH (1 par défaut, 0 pour ne pas pousser),
# CGITSYNC_HOME (dossier de ComplexGitSync), TWIN_CLI et PYTHON (pour essayer un autre code que celui du venv).
# Codes de sortie : 0 identique ou aucune autre machine, 1 au moins une machine DIFFÉRENTE, 2 refus avant le calcul.

set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$PWD"
CGITSYNC_HOME="${CGITSYNC_HOME:-$HOME/tools/ComplexGitSync}"
SIMU_PUSH="${SIMU_PUSH:-1}"
MACHINE="${MACHINE:-$(hostname -s)}"
BACKEND="$ROOT/Molonaviz/molonari_desk"
LAB="MOLONARI-TWIN/virtual_lab/lab_point034/description"
TWIN="MOLONARI-TWIN/Point034/twins/twin_direct"
FORWARD="SIMU/forward/Point034"
OUT="$FORWARD/$MACHINE"
# Nom affiché -> dossier du dépôt, pour les quatre dépôts dont les commits doivent être les mêmes sur toutes les machines.
REPOS=("MOLONARI1D:." "Molonaviz:Molonaviz" "data:data" "MOLONARI-TWIN:MOLONARI-TWIN")

START=$SECONDS
STEP=""
SUMMARY=""

on_exit() {
    local code=$?
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

refuse() {
    echo "REFUS : $*" >&2
    STEP=""
    exit 2
}

step "Contrôles : machine, noms, dépôts"
if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
    refuse "cette expérience se joue sur un Mac M1 (Darwin arm64), pas sur $(uname -s) $(uname -m) : jaxlib 0.11.2 n'a pas de paquet pour Mac Intel."
fi
if ! [[ "$MACHINE" =~ ^[A-Za-z0-9._-]+$ ]]; then
    refuse "MACHINE='$MACHINE' ne suit pas ^[A-Za-z0-9._-]+\$."
fi
if [ -e "$OUT" ]; then
    refuse "export déjà présent : $OUT (un espace ne sert qu'à un calcul ; choisir un autre MACHINE)."
fi
DIRTY=""
for dir in . Molonaviz data MOLONARI-TWIN SIMU; do
    if [ ! -d "$dir/.git" ] && ! git -C "$dir" rev-parse --git-dir > /dev/null 2>&1; then
        refuse "le dépôt $dir est absent : espace non monté par cgitsync bootstrap simu-direct.cgs ?"
    fi
    if [ -n "$(git -C "$dir" status --porcelain)" ]; then
        DIRTY+="  $dir"$'\n'"$(git -C "$dir" status --porcelain | head -5 | sed 's/^/      /')"$'\n'
    fi
done
if [ -n "$DIRTY" ]; then
    refuse "dépôts non propres :"$'\n'"$DIRTY"
fi

step "SIMU : pull --ff-only"
git -C SIMU pull --ff-only

step "Installation du backend (uv sync --frozen)"
(cd "$BACKEND" && uv sync --frozen --package molonari-twin --no-default-groups)
TWIN_CLI="${TWIN_CLI:-$BACKEND/.venv/bin/molonari-twin}"
PYTHON="${PYTHON:-$BACKEND/.venv/bin/python}"
"$TWIN_CLI" --help > /dev/null

step "Commits identiques à ceux des machines déjà présentes"
# SIMU n'entre pas dans la comparaison : son commit avance à chaque export.
mkdir -p "$FORWARD"
SIMU_COMMIT="$(git -C SIMU rev-parse HEAD)"
for entry in "${REPOS[@]}"; do
    name="${entry%%:*}"
    dir="${entry#*:}"
    echo "$name : $(git -C "$dir" rev-parse HEAD) ($(git -C "$dir" rev-parse --abbrev-ref HEAD))"
done
for other in "$FORWARD"/*/; do
    [ -d "$other" ] || continue
    other_name="$(basename "$other")"
    [ -f "$other/commits.json" ] || refuse "la machine $other_name n'a pas de commits.json dans $other."
    for entry in "${REPOS[@]}"; do
        name="${entry%%:*}"
        dir="${entry#*:}"
        mine="$(git -C "$dir" rev-parse HEAD)"
        theirs="$("$PYTHON" -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))[sys.argv[2]]["commit"])' "$other/commits.json" "$name")"
        if [ "$mine" != "$theirs" ]; then
            refuse "commits différents : la machine $other_name a $name à $theirs, cet espace à $mine."
        fi
    done
done

step "Virtual lab : lab build"
"$TWIN_CLI" lab build "$LAB" --point Point034

step "Le twin direct n'a jamais été calculé ici"
if [ -d "$TWIN/results" ] && [ -n "$(ls -A "$TWIN/results")" ]; then
    refuse "l'espace n'est pas neuf : $TWIN/results contient déjà des résultats (le calcul doit avoir lieu ici)."
fi

step "Twin direct : run"
"$TWIN_CLI" run "$TWIN"

step "Export de la reproduction"
"$TWIN_CLI" reproduce "$TWIN" --export "$OUT"
"$PYTHON" - "$OUT/commits.json" "$MACHINE" "$(uname -a)" "$SIMU_COMMIT" "${REPOS[@]}" <<'PYEOF'
import json
import subprocess
import sys

target, machine, uname, simu_commit, *repos = sys.argv[1:]


def git(directory, *args):
    return subprocess.run(["git", "-C", directory, *args], check=True, capture_output=True, text=True).stdout.strip()


data = {"machine": machine, "uname": uname, "simu_commit": simu_commit}
for entry in repos:
    name, directory = entry.split(":", 1)
    data[name] = {"commit": git(directory, "rev-parse", "HEAD"), "branch": git(directory, "rev-parse", "--abbrev-ref", "HEAD")}
with open(target, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2, sort_keys=True)
    handle.write("\n")
PYEOF
CGITSYNC="$CGITSYNC_HOME/.pixi/envs/default/bin/cgitsync"
if [ -x "$CGITSYNC" ]; then
    "$CGITSYNC" env show > "$OUT/environment.txt" 2>&1 || echo "cgitsync env show a échoué (code $?)" >> "$OUT/environment.txt"
else
    echo "cgitsync absent" > "$OUT/environment.txt"
fi

step "Comparaison aux autres machines"
REPORT="$OUT/compte_rendu.txt"
: > "$REPORT"
FINAL=0
COMPARED=0
for other in "$FORWARD"/*/; do
    [ -d "$other" ] || continue
    name="$(basename "$other")"
    [ "$name" != "$MACHINE" ] || continue
    COMPARED=$((COMPARED + 1))
    rc=0
    "$TWIN_CLI" reproduce --compare "$other" "$OUT" --json > "$OUT/compare_$name.json" || rc=$?
    if [ "$rc" -eq 0 ]; then
        echo "$name : identique" >> "$REPORT"
    elif [ "$rc" -eq 1 ]; then
        echo "$name : DIFFÉRENT" >> "$REPORT"
        FINAL=1
    else
        echo "reproduce --compare $name a échoué avec le code $rc (voir $OUT/compare_$name.json)." >&2
        STEP=""
        exit "$rc"
    fi
done
if [ "$COMPARED" -eq 0 ]; then
    echo "aucune autre machine : rien à comparer pour l'instant." > "$REPORT"
fi

step "SIMU : commit et push"
git -C SIMU add "forward/Point034/$MACHINE"
git -C SIMU commit -m "simu: export de $MACHINE"
if [ "$SIMU_PUSH" = "1" ]; then
    echo "Push vers : $(git -C SIMU remote get-url origin)"
    git -C SIMU push
else
    echo "SIMU_PUSH=$SIMU_PUSH : pas de push."
fi

finish_step
STEP=""
echo
echo "=== Compte rendu ($OUT/compte_rendu.txt)"
cat "$REPORT"
echo
echo "=== Terminé en $((SECONDS - START)) s"
printf '%s' "$SUMMARY"
exit "$FINAL"
