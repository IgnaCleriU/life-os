#!/bin/sh
# Instala el chequeo diario de crédito en el VPS (idempotente). Se corre como
# root desde el bootstrap de cloud-init o a mano: sudo sh install.sh
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
install -D -m 0755 "$HERE/credit_check.py" /usr/local/lib/lifeos/credit_check.py
install -m 0644 "$HERE/lifeos-credit-check.service" "$HERE/lifeos-credit-check.timer" /etc/systemd/system/
[ -f /etc/lifeos/credit-check.env ] || install -D -m 0644 "$HERE/credit-check.env.example" /etc/lifeos/credit-check.env
systemctl daemon-reload
# Sin un perfil de facturación real (fuera de Azure, o antes de configurarlo)
# el timer fallaría todos los días: se deja instalado pero apagado.
if grep -q '<cuenta>' /etc/lifeos/credit-check.env; then
  echo "credit-check: completá /etc/lifeos/credit-check.env y corré" \
    "systemctl enable --now lifeos-credit-check.timer"
else
  systemctl enable --now lifeos-credit-check.timer
fi
