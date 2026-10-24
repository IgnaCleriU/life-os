#!/bin/sh
# Toma una muestra de recursos del VPS y la agrega a CSV diarios en
# LIFEOS_METRICS_DIR (un archivo por día y por tipo):
#
#   host-AAAA-MM-DD.csv        CPU, carga, RAM, swap y disco del host
#   containers-AAAA-MM-DD.csv  CPU y RAM de cada contenedor
#
# Lo corre cada minuto lifeos-metrics.timer. Borra los CSV propios con más de
# LIFEOS_METRICS_RETENTION_DAYS días. Las demás variables existen para los
# tests (test-lifeos-metrics.sh), que reemplazan /proc, df y docker.
set -eu

DIR=${LIFEOS_METRICS_DIR:-/var/log/lifeos-metrics}
PROC=${LIFEOS_METRICS_PROC:-/proc}
INTERVAL=${LIFEOS_METRICS_INTERVAL:-1}
RETENTION_DAYS=${LIFEOS_METRICS_RETENTION_DAYS:-30}
DF_CMD=${LIFEOS_METRICS_DF_CMD:-df -P /}
STATS_CMD=${LIFEOS_METRICS_STATS_CMD:-"docker stats --no-stream --format {{.Name}};{{.CPUPerc}};{{.MemUsage}}"}

mkdir -p "$DIR"
NOW=$(date +%Y-%m-%dT%H:%M:%S%z)
DAY=$(date +%F)

# Escribe el encabezado solo si el archivo del día está vacío o no existe.
append() {
  file=$1 header=$2
  [ -s "$file" ] || echo "$header" > "$file"
  cat >> "$file"
}

# CPU usada entre dos lecturas de /proc/stat (idle incluye iowait).
cpu_sample() { awk '/^cpu /{ print $2+$3+$4+$5+$6+$7+$8+$9, $5+$6 }' "$PROC/stat"; }
set -- $(cpu_sample)
sleep "$INTERVAL"
set -- "$@" $(cpu_sample)
CPU=$(awk -v t1="$1" -v i1="$2" -v t2="$3" -v i2="$4" 'BEGIN {
  dt = t2 - t1; printf "%.1f", (dt > 0 ? 100 * (dt - (i2 - i1)) / dt : 0) }')

LOAD=$(cut -d' ' -f1 "$PROC/loadavg")
MEM=$(awk '/^(MemTotal|MemAvailable|SwapTotal|SwapFree):/ { v[$1] = $2 }
  END { printf "%d,%d,%d", v["MemTotal:"] / 1024, v["MemAvailable:"] / 1024,
        (v["SwapTotal:"] - v["SwapFree:"]) / 1024 }' "$PROC/meminfo")
DISK=$($DF_CMD | awk 'NR == 2 { sub(/%/, "", $5); print $5 }')

echo "$NOW,$CPU,$LOAD,$MEM,$DISK" | append "$DIR/host-$DAY.csv" \
  "timestamp,cpu_pct,load1,mem_total_mb,mem_available_mb,swap_used_mb,disk_used_pct"

# Sin Docker (o con el daemon caído) se registra igual el host.
STATS=$($STATS_CMD 2>/dev/null) || STATS=""
if [ -n "$STATS" ]; then
  echo "$STATS" | awk -F';' -v now="$NOW" '{
    cpu = $2; sub(/%/, "", cpu)
    split($3, used, " / "); mem = used[1]
    n = mem + 0; unit = mem; sub(/^[0-9.]+/, "", unit)
    if (unit == "B") n /= 1048576
    else if (unit == "KiB" || unit == "kB") n /= 1024
    else if (unit == "GiB" || unit == "GB") n *= 1024
    printf "%s,%s,%s,%.1f\n", now, $1, cpu, n
  }' | append "$DIR/containers-$DAY.csv" "timestamp,container,cpu_pct,mem_mib"
fi

find "$DIR" -maxdepth 1 -type f \( -name 'host-*.csv' -o -name 'containers-*.csv' \) \
  -mtime +"$RETENTION_DAYS" -delete
