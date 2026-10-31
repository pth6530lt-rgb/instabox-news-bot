#!/bin/bash
# Kiểm tra sức khỏe container và backup nhẹ cho máy InstaBox agent-brower.
# Cách dùng:
#   bash health-backup.sh            # chỉ kiểm tra và backup nhẹ, không xóa gì
#   bash health-backup.sh --prune    # thêm bước dọn image Docker cũ nếu ổ đĩa dưới 3GB trống
# Script này KHÔNG gửi Telegram, KHÔNG tự restart container, KHÔNG xóa dữ liệu.
# Nó chỉ ghi log và tạo file backup tar, để bạn xem và quyết định tiếp.
set -u
LOG="$HOME/health-check.log"
BACKUP="$HOME/backup-$(date +%F).tar.gz"
{
  echo "=== $(date '+%d/%m/%Y %H:%M') ==="
  echo "--- Disk ---"
  df -h /data/home 2>/dev/null || df -h
  echo "--- Containers (docker ps) ---"
  docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' 2>&1
  echo "--- Expected services ---"
  for name in freshrss rsshub news-webapp changedetection vaultwarden filebrowser linkding portainer trilium; do
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$name"; then
      echo "OK $name đang chạy"
    else
      echo "CẢNH BÁO $name không thấy trong docker ps, kiểm tra bằng docker compose ps trong thư mục của nó"
    fi
  done
} | tee -a "$LOG"
echo "Đã ghi log vào $LOG"
# Backup nhẹ: chỉ lấy file cấu hình, feed, digest, compose, không lấy toàn bộ vault hay database lớn.
# Nếu bạn muốn backup Vaultwarden đầy đủ, hãy xuất vault từ giao diện Vaultwarden và lưu riêng, an toàn hơn.
tar -czf "$BACKUP" \
  --ignore-failed-read \
  -C "$HOME" \
  news/feeds.json news/docker-compose.news.yml news/webapp/digest.json news/bot.py \
  changedetection/docker-compose.yml vaultwarden/docker-compose.yml filebrowser/docker-compose.yml \
  linkding/docker-compose.yml portainer/docker-compose.yml trilium/docker-compose.yml \
  2>/dev/null || true
ls -lh "$BACKUP" "$LOG"
if [ "${1:-}" = "--prune" ]; then
  FREE_GB=$(df -BG /data/home 2>/dev/null | awk 'NR==2 {gsub("G","",$4); print $4}')
  echo "Ổ đĩa trống: ${FREE_GB:-không xác định}GB"
  if [ -n "$FREE_GB" ] && [ "$FREE_GB" -lt 3 ]; then
    echo "Dưới 3GB trống, đang dọn image Docker cũ..."
    docker image prune -a -f
    df -h
  else
    echo "Còn đủ ổ đĩa, không dọn image."
  fi
fi
