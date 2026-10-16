#!/usr/bin/env bash
# Gestiona la VM de Life OS en Azure con el CLI `az` (requiere `az login`).
#
#   lifeos-vm.sh create            crea la VM en el primer par región:tamaño
#                                  disponible de LIFEOS_CANDIDATES
#   lifeos-vm.sh start             la prende; si la región no tiene capacidad
#                                  para el tamaño actual, prueba los de
#                                  LIFEOS_FALLBACK_SIZES
#   lifeos-vm.sh stop              la desasigna (deja de cobrarse el cómputo)
#   lifeos-vm.sh status            estado, región, tamaño e IP
#   lifeos-vm.sh tunnel [puerto]   túnel SSH a la API (localhost:8000 por defecto)
#   lifeos-vm.sh allow-ip          restringe SSH a tu IP pública actual
#   lifeos-vm.sh relocate REGION [TAMAÑO]
#                                  copia el disco a otra región y levanta ahí
#                                  una VM nueva con los mismos datos
#
# Ver docs/deployment.md para el contexto y el procedimiento completo.
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

RG=${LIFEOS_RG:-rg-lifeos}
VM=${LIFEOS_VM:-vm-lifeos}
RG_LOCATION=${LIFEOS_RG_LOCATION:-brazilsouth}
ADMIN_USER=${LIFEOS_ADMIN_USER:-azureuser}
SSH_KEY=${LIFEOS_SSH_KEY:-$HOME/.ssh/lifeos-azure}
SHUTDOWN_UTC=${LIFEOS_SHUTDOWN_UTC:-0400} # 01:00 en Argentina (UTC-3)
# Pares región:tamaño en orden de preferencia (precio). Las regiones son las que
# permite la política de Azure for Students; todos los tamaños son x64 porque
# la imagen es Ubuntu x64.
CANDIDATES=${LIFEOS_CANDIDATES:-"northcentralus:Standard_B2ats_v2 southafricanorth:Standard_B2ats_v2 newzealandnorth:Standard_B2ats_v2 southafricanorth:Standard_B2ts_v2 newzealandnorth:Standard_B2ts_v2 northcentralus:Standard_B2als_v2"}
FALLBACK_SIZES=${LIFEOS_FALLBACK_SIZES:-"Standard_B2ats_v2 Standard_B2ts_v2 Standard_B2als_v2 Standard_B2as_v2"}

log() { printf '==> %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

my_ip() { curl -fsS https://api.ipify.org; }
vm_field() { az vm show -g "$RG" -n "$VM" -d --query "$1" -o tsv; }
nsg_name() { az network nsg list -g "$RG" --query "[?contains(name,'$VM')].name | [0]" -o tsv; }

# Un tamaño está disponible si el catálogo de la suscripción no lo restringe
# en esa región. No garantiza capacidad, pero descarta lo que Azure ya sabe que
# va a rechazar (el caso de Brazil South en Azure for Students).
sku_available() {
  local region=$1 size=$2 sub
  sub=$(az account show --query id -o tsv)
  az rest --method get \
    --url "https://management.azure.com/subscriptions/$sub/providers/Microsoft.Compute/skus?api-version=2021-07-01&\$filter=location%20eq%20'$region'" \
    --query "value[?name=='$size' && resourceType=='virtualMachines'] | [0].restrictions[?type=='Location'] | length(@)" \
    -o tsv 2>/dev/null | grep -qx 0
}

allow_ssh() {
  local vm=$1 cidr=${2:-"$(my_ip)/32"} nsg
  nsg=$(az network nsg list -g "$RG" --query "[?contains(name,'$vm')].name | [0]" -o tsv)
  [ -n "$nsg" ] || die "no encontré el NSG de $vm"
  log "SSH permitido solo desde $cidr ($nsg)"
  az network nsg rule create -g "$RG" --nsg-name "$nsg" -n allow-ssh-home \
    --priority 1000 --direction Inbound --access Allow --protocol Tcp \
    --source-address-prefixes "$cidr" --destination-port-ranges 22 -o none
}

auto_shutdown() {
  local vm=$1 region=$2
  log "apagado automático diario a las $SHUTDOWN_UTC UTC"
  az vm auto-shutdown -g "$RG" -n "$vm" --time "$SHUTDOWN_UTC" --location "$region" -o none
}

cmd_create() {
  [ -f "$SSH_KEY.pub" ] || die "falta $SSH_KEY.pub (ssh-keygen -t ed25519 -f $SSH_KEY)"
  az group create -n "$RG" -l "$RG_LOCATION" -o none
  local c region size
  for c in $CANDIDATES; do
    region=${c%%:*} size=${c##*:}
    if ! sku_available "$region" "$size"; then
      log "$size no está habilitado en $region, sigo"
      continue
    fi
    log "creando $VM en $region ($size)"
    if az vm create -g "$RG" -n "$VM" -l "$region" --size "$size" \
        --image Ubuntu2404 --admin-username "$ADMIN_USER" \
        --authentication-type ssh --ssh-key-values "$SSH_KEY.pub" \
        --public-ip-sku Standard --nsg-rule NONE \
        --os-disk-size-gb 30 --storage-sku StandardSSD_LRS \
        --custom-data "$REPO_ROOT/deploy/vps/cloud-init.yaml" -o none; then
      allow_ssh "$VM"
      auto_shutdown "$VM" "$region"
      log "listo: $(vm_field publicIps). cloud-init tarda ~10 min en levantar la app"
      return
    fi
    log "falló en $region ($size), pruebo el siguiente candidato"
  done
  die "ningún candidato funcionó; revisá LIFEOS_CANDIDATES"
}

cmd_start() {
  local err current s
  log "prendiendo $VM"
  if err=$(az vm start -g "$RG" -n "$VM" -o none 2>&1); then
    log "prendida: $(vm_field publicIps)"
    return
  fi
  grep -qiE 'allocat|capacity|SkuNotAvailable' <<<"$err" || die "$err"
  current=$(vm_field hardwareProfile.vmSize)
  log "sin capacidad para $current en $(vm_field location); pruebo otros tamaños"
  for s in $FALLBACK_SIZES; do
    [ "$s" = "$current" ] && continue
    log "redimensionando a $s"
    az vm deallocate -g "$RG" -n "$VM" -o none
    if az vm resize -g "$RG" -n "$VM" --size "$s" -o none 2>/dev/null \
        && az vm start -g "$RG" -n "$VM" -o none 2>/dev/null; then
      log "prendida como $s: $(vm_field publicIps)"
      return
    fi
  done
  die "ningún tamaño consiguió capacidad. Esperá unos minutos o mudala: $0 relocate <región>"
}

cmd_relocate() {
  local region=${1:-} size=${2:-Standard_B2ats_v2}
  [ -n "$region" ] || die "uso: $0 relocate REGION [TAMAÑO]"
  sku_available "$region" "$size" || die "$size no está habilitado en $region"
  local src_region disk_id stamp snap_src snap_dst disk_dst new_vm pct
  src_region=$(vm_field location)
  disk_id=$(vm_field storageProfile.osDisk.managedDisk.id)
  stamp=$(date +%Y%m%d%H%M)
  snap_src="$VM-snap-$stamp"
  snap_dst="$VM-snap-$stamp-$region"
  disk_dst="$VM-osdisk-$region-$stamp"
  new_vm="$VM-$region"

  log "desasignando $VM para tomar un snapshot consistente"
  az vm deallocate -g "$RG" -n "$VM" -o none
  log "snapshot del disco en $src_region"
  az snapshot create -g "$RG" -n "$snap_src" -l "$src_region" --source "$disk_id" \
    --incremental true -o none
  log "copiando el snapshot a $region (puede tardar varios minutos)"
  az snapshot create -g "$RG" -n "$snap_dst" -l "$region" \
    --source "$(az snapshot show -g "$RG" -n "$snap_src" --query id -o tsv)" \
    --incremental true --copy-start true -o none
  until pct=$(az snapshot show -g "$RG" -n "$snap_dst" --query completionPercent -o tsv) \
      && [ "${pct%.*}" = 100 ]; do
    log "copia: ${pct:-0}%"
    sleep 30
  done
  log "creando disco y VM $new_vm en $region ($size)"
  az disk create -g "$RG" -n "$disk_dst" -l "$region" --source "$snap_dst" \
    --sku StandardSSD_LRS -o none
  az vm create -g "$RG" -n "$new_vm" -l "$region" --size "$size" \
    --attach-os-disk "$disk_dst" --os-type linux \
    --public-ip-sku Standard --nsg-rule NONE -o none
  allow_ssh "$new_vm"
  auto_shutdown "$new_vm" "$region"
  cat >&2 <<EOF
==> lista: $new_vm en $region, IP $(az vm show -g "$RG" -n "$new_vm" -d --query publicIps -o tsv)
    La VM original ($VM) quedó desasignada, con su disco intacto.
    Usá la nueva con LIFEOS_VM=$new_vm. Cuando verifiques que anda, borrá la
    vieja y los snapshots ($snap_src, $snap_dst) para no pagarlos.
EOF
}

cmd_status() {
  az vm show -g "$RG" -n "$VM" -d \
    --query "{estado:powerState, region:location, tamano:hardwareProfile.vmSize, ip:publicIps}" -o table
}

cmd_tunnel() {
  local port=${1:-8000}
  log "API en http://localhost:$port (Ctrl+C para cerrar)"
  exec ssh -i "$SSH_KEY" -N -L "$port:localhost:8000" "$ADMIN_USER@$(vm_field publicIps)"
}

case ${1:-} in
  create) cmd_create ;;
  start) cmd_start ;;
  stop) log "desasignando $VM"; az vm deallocate -g "$RG" -n "$VM" -o none ;;
  status) cmd_status ;;
  tunnel) shift; cmd_tunnel "$@" ;;
  allow-ip) allow_ssh "$VM" ;;
  relocate) shift; cmd_relocate "$@" ;;
  *) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
