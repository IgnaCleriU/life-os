#!/bin/sh
# Instala el colector de métricas (lifeos-metrics.sh) y su timer de systemd.
# Copia el script en vez de enlazarlo: corre como root y el repo es del
# usuario, que no debe poder cambiar lo que root ejecuta. Idempotente; volver
# a correrlo después de un `git pull` actualiza la copia. Requiere root.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
install -D -m 0755 "$HERE/lifeos-metrics.sh" /usr/local/lib/lifeos/lifeos-metrics.sh
install -m 0644 "$HERE/lifeos-metrics.service" "$HERE/lifeos-metrics.timer" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now lifeos-metrics.timer
