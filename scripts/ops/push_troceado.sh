#!/bin/bash
# Push troceado v2. Fixes sobre v1: (a) exit code REAL de cada push (sin pipe en el if),
# (b) lotes de 80MB, (c) tmp-sync remota se conserva hasta VERIFICAR main en origin,
# (d) verificacion final con ls-remote. Reanudable: si origin ya tiene tmp-sync, parte de ella.
set -u
REPO="/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
WT="/tmp/wt-tmpsync"
LOTE_MAX=$((40*1024*1024))
cd "$REPO" || exit 1
git fetch -q origin

BASE="origin/main"
if git ls-remote --exit-code origin refs/heads/tmp-sync >/dev/null 2>&1; then
  git fetch -q origin tmp-sync:refs/remotes/origin/tmp-sync
  BASE="origin/tmp-sync"
fi
echo "Base de tmp-sync: $BASE"

# Blobs >8MB del rango pendiente que la base aun no contiene
git rev-list "$BASE"..main --objects \
  | git cat-file --batch-check='%(objecttype) %(objectsize) %(objectname) %(rest)' \
  | awk '$1=="blob" && $2>8388608 {print $2" "$3" "$4}' | sort -rn > /tmp/blobs_grandes2.txt
echo "Blobs pendientes: $(wc -l < /tmp/blobs_grandes2.txt) ($(awk '{s+=$1} END {printf "%.0f MB", s/1048576}' /tmp/blobs_grandes2.txt))"

git worktree remove --force "$WT" 2>/dev/null
git branch -D tmp-sync 2>/dev/null
git worktree add -b tmp-sync "$WT" "$BASE" >/dev/null 2>&1 || exit 1
cd "$WT" || exit 1

lote=0; acum=0
push_lote() {
  lote=$((lote+1))
  git commit -qm "tmp-sync v2 lote $lote" 2>/dev/null || return 0
  for intento in 1 2 3; do
    if git push -q origin tmp-sync >/dev/null 2>>/tmp/push_lotes.err; then
      echo "LOTE $lote OK ($((acum/1048576)) MB, intento $intento)"; return 0
    fi
    echo "LOTE $lote FALLO intento $intento"; sleep 45
  done
  return 1
}
while read -r size sha path; do
  mkdir -p "$(dirname "$path")"
  git -C "$REPO" cat-file blob "$sha" > "$path" || continue
  git add -f "$path"; acum=$((acum+size))
  if [ "$acum" -ge "$LOTE_MAX" ]; then push_lote || { echo "ABORTADO en lote $lote"; exit 1; }; acum=0; fi
done < /tmp/blobs_grandes2.txt
[ "$acum" -gt 0 ] && { push_lote || { echo "ABORTADO en lote final"; exit 1; }; }

cd "$REPO"
echo "--- push final de main ---"
for intento in 1 2 3; do
  if git push origin main 2>>/tmp/push_lotes.err; then echo "MAIN PUSH OK (intento $intento)"; break; fi
  echo "main fallo intento $intento"; sleep 20
done

REMOTO=$(git ls-remote origin refs/heads/main | awk '{print $1}')
LOCAL=$(git rev-parse main)
echo "origin/main=$REMOTO local=$LOCAL"
if [ "$REMOTO" = "$LOCAL" ]; then
  echo "VERIFICADO: origin == local. Limpiando tmp-sync."
  git push -q origin --delete tmp-sync 2>/dev/null
  git worktree remove --force "$WT" 2>/dev/null
  git branch -D tmp-sync 2>/dev/null
  git fetch -q origin && git status -sb | head -1
else
  echo "NO VERIFICADO: tmp-sync se CONSERVA en origin para reanudar sin perder lo subido."
fi
