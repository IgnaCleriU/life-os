#!/bin/sh
# Tests de lifeos-metrics.sh sin tocar el sistema: /proc, `df` y
# `docker stats` se reemplazan por fixtures. Uso: sh test-lifeos-metrics.sh
set -eu

HERE=$(cd "$(dirname "$0")" && pwd)
SCRIPT="$HERE/lifeos-metrics.sh"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

FAILS=0
fail() { echo "FAIL: $*"; FAILS=$((FAILS + 1)); }
assert_eq() { [ "$1" = "$2" ] || fail "$3: esperaba '$2', obtuve '$1'"; }

mkdir -p "$WORK/proc" "$WORK/out"
echo "cpu  100 0 100 800 0 0 0 0 0 0" > "$WORK/proc/stat"
echo "0.09 0.10 0.09 1/200 1234" > "$WORK/proc/loadavg"
cat > "$WORK/proc/meminfo" <<'EOF'
MemTotal:         908400 kB
MemFree:           20000 kB
MemAvailable:     460800 kB
SwapTotal:       2097148 kB
SwapFree:        2064380 kB
EOF
cat > "$WORK/df.txt" <<'EOF'
Filesystem     1024-blocks    Used Available Capacity Mounted on
/dev/root         30298176 5242880  25038912      18% /
EOF
cat > "$WORK/stats.txt" <<'EOF'
life-os-backend-java-1;0.15%;122.2MiB / 887.1MiB
life-os-caddy-1;0.00%;16.79MiB / 887.1MiB
big;1.00%;1.5GiB / 2GiB
tiny;0.00%;512KiB / 887.1MiB
EOF

run() {
  LIFEOS_METRICS_DIR="$WORK/out" \
  LIFEOS_METRICS_PROC="$WORK/proc" \
  LIFEOS_METRICS_INTERVAL=0 \
  LIFEOS_METRICS_DF_CMD="cat $WORK/df.txt" \
  LIFEOS_METRICS_STATS_CMD="${STATS_CMD:-cat $WORK/stats.txt}" \
  sh "$SCRIPT"
}

DAY=$(date +%F)
HOST="$WORK/out/host-$DAY.csv"
CONT="$WORK/out/containers-$DAY.csv"

# --- Una muestra: encabezado y fila del host ---
run || fail "la primera corrida terminó con error"
assert_eq "$(head -n1 "$HOST" 2>/dev/null)" \
  "timestamp,cpu_pct,load1,mem_total_mb,mem_available_mb,swap_used_mb,disk_used_pct" \
  "encabezado del host"
ROW=$(sed -n 2p "$HOST" 2>/dev/null)
assert_eq "$(echo "$ROW" | cut -d, -f2-)" "0.0,0.09,887,450,32,18" "fila del host"
echo "$ROW" | cut -d, -f1 | grep -Eq '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:]{8}[+-][0-9]{4}$' \
  || fail "timestamp ISO 8601: '$(echo "$ROW" | cut -d, -f1)'"

# --- Contenedores: unidades convertidas a MiB ---
assert_eq "$(head -n1 "$CONT" 2>/dev/null)" "timestamp,container,cpu_pct,mem_mib" \
  "encabezado de contenedores"
assert_eq "$(sed -n '2,$p' "$CONT" 2>/dev/null | cut -d, -f2- | tr '\n' ' ')" \
  "life-os-backend-java-1,0.15,122.2 life-os-caddy-1,0.00,16.8 big,1.00,1536.0 tiny,0.00,0.5 " \
  "filas de contenedores"

# --- Segunda muestra: agrega filas, no repite el encabezado ---
run || fail "la segunda corrida terminó con error"
assert_eq "$(grep -c '^timestamp' "$HOST" 2>/dev/null)" "1" "encabezados del host tras dos corridas"
assert_eq "$(wc -l < "$HOST" 2>/dev/null | tr -d ' ')" "3" "líneas del host tras dos corridas"
assert_eq "$(wc -l < "$CONT" 2>/dev/null | tr -d ' ')" "9" "líneas de contenedores tras dos corridas"

# --- Sin Docker, el host se sigue registrando ---
rm -f "$WORK/out"/*.csv
STATS_CMD=false run || fail "terminó con error cuando docker stats falla"
assert_eq "$(wc -l < "$HOST" 2>/dev/null | tr -d ' ')" "2" "fila del host sin docker"

# --- Retención: borra solo CSV propios más viejos que el límite ---
touch -d '40 days ago' "$WORK/out/host-2020-01-01.csv" "$WORK/out/containers-2020-01-01.csv" "$WORK/out/notas.txt"
touch -d '5 days ago' "$WORK/out/host-2020-02-01.csv"
run
[ ! -e "$WORK/out/host-2020-01-01.csv" ] || fail "no borró host viejo"
[ ! -e "$WORK/out/containers-2020-01-01.csv" ] || fail "no borró contenedores viejo"
[ -e "$WORK/out/host-2020-02-01.csv" ] || fail "borró un CSV reciente"
[ -e "$WORK/out/notas.txt" ] || fail "borró un archivo ajeno"

if [ "$FAILS" -eq 0 ]; then echo "OK"; else echo "$FAILS fallas"; exit 1; fi
