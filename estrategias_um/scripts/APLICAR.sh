#!/bin/bash
# Aplica el parche MC-fix con parada/arranque LIMPIOS por API (nunca kill).
# Uso: bash /tmp/um_mcpatch/APLICAR.sh
set -e
API="http://localhost:5050/call"
PROJ="Ultra_Matrix"
CFX="/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/project.cfx"

echo "== estado antes:"
curl -s --max-time 15 "$API?cmd=-project%20action=status%20name=$PROJ" | head -c 300; echo
echo "== stop (ordenado por API):"
curl -s --max-time 15 "$API?cmd=-project%20action=stop%20name=$PROJ" | head -c 200; echo
for i in $(seq 1 24); do
  S=$(curl -s --max-time 15 "$API?cmd=-project%20action=status%20name=$PROJ" || true)
  echo "$S" | grep -qiE 'running|started' || { echo "proyecto parado (intento $i)"; break; }
  sleep 5
done
echo "== parche:"
python3 /tmp/um_mcpatch/patcher.py "$CFX" --apply
echo "== start:"
curl -s --max-time 15 "$API?cmd=-project%20action=start%20name=$PROJ" | head -c 200; echo
sleep 25
echo "== estado tras:"
curl -s --max-time 15 "$API?cmd=-project%20action=status%20name=$PROJ" | head -c 400; echo
