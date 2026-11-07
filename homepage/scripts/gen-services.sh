#!/bin/bash
# Tao homepage/config/services.yaml tu cac file link private tren may.
# Doc link tu ~/private-link.txt, ~/rsshub-link.txt, ... nen token khong
# can go tay, khong can gui qua chat, khong co trong repo.
# Chay tren may: bash ~/homepage/scripts/gen-services.sh
# Sau do chay lai: docker compose -f ~/homepage/docker-compose.yml up -d
set -u
OUT="$HOME/homepage/config/services.yaml"
link() {
  local f="$1"
  if [ -f "$HOME/$f" ]; then
    tr -d ' \n\r' < "$HOME/$f"
  else
    echo "#"
  fi
}
FRESHRSS="$(link private-link.txt)"
RSSHub="$(link rsshub-link.txt)"
WEBAPP="$(link webapp-link.txt)"
VAULT="$(link vaultwarden-link.txt)"
TRILIUM="$(link trilium-link.txt)"
LINKDING="$(link linkding-link.txt)"
FILEBROWSER="$(link filebrowser-link.txt)"
KUMA="$(link uptime-kuma-link.txt)"
PORTAINER="$(link portainer-link.txt)"
# Changedetection khong co file link rieng tren may, giu "#" de bo sung sau.
cat > "$OUT" <<YAML
- Tin tuc:
    - FreshRSS:
        icon: freshrss
        href: "$FRESHRSS"
        description: Doc tin RSS, 11 feed VN va quoc te
    - WebApp tin:
        icon: mdi-newspaper-variant-outline
        href: "$WEBAPP"
        description: Ban tin da loc theo quoc gia va chu de
    - RSSHub:
        icon: mdi-rss
        href: "$RSSHub"
        description: Tao feed RSS cho trang khong co RSS
- Cong viec:
    - Vaultwarden:
        icon: bitwarden
        href: "$VAULT"
        description: Quan ly mat khau, bat 2FA sau khi tao tai khoan
    - Trilium:
        icon: trilium
        href: "$TRILIUM"
        description: Ghi chu
    - Linkding:
        icon: mdi-bookmark-multiple-outline
        href: "$LINKDING"
        description: Luu link doc sau
    - FileBrowser:
        icon: mdi-folder-outline
        href: "$FILEBROWSER"
        description: Quan ly file tren may, doi mat khau mac dinh ngay
- He thong:
    - Uptime Kuma:
        icon: uptime-kuma
        href: "$KUMA"
        description: Giam sat suc khoe cac dich vu
    - Changedetection:
        icon: changedetection
        href: "#"
        description: Theo doi thay doi trang web
    - Portainer:
        icon: portainer
        href: "$PORTAINER"
        description: Quan ly container Docker, chi dung private
YAML
echo "Da ghi $OUT"
grep -c 'href: "#"' "$OUT" || true
echo "So link con thieu (href #): xem dong tren, 1 la Changedetection chua co file link."
