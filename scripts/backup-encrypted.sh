#!/bin/bash
# Backup ma hoa cho may InstaBox agent-brower.
# Chi ma hoa file backup nhe do health-backup.sh tao, KHONG tai len dau,
# KHONG gui Telegram, KHONG restart container, KHONG xoa du lieu.
#
# Truoc khi chay lan dau, BAN phai tu tao file mat khau tren may:
#   echo -n 'mat-khau-ban-chon' > ~/scripts/backup-passphrase.txt
#   chmod 600 ~/scripts/backup-passphrase.txt
# Mat khau nay KHONG co trong repo, KHONG gui qua chat, KHONG duoc quen:
# quen mat khau thi file .enc khong giai ma duoc nua.
# Neu muon doi mat khau, sua file tren may roi chay lai script.
set -u
PASSFILE="$HOME/scripts/backup-passphrase.txt"
TODAY="$(date +%F)"
BACKUP="$HOME/backup-$TODAY.tar.gz"
ENC="$HOME/backup-$TODAY.tar.gz.enc"

if [ ! -f "$PASSFILE" ]; then
  echo "CHUA CO MAT KHAU: tao file $PASSFILE truoc, xem huong dan trong docs/BACKUP-RESTORE.md."
  echo "Script dung lai, khong lam gi them."
  exit 1
fi

if [ ! -f "$BACKUP" ]; then
  echo "Chua co $BACKUP, chay health-backup.sh truoc..."
  bash "$HOME/scripts/health-backup.sh"
fi
if [ ! -f "$BACKUP" ]; then
  echo "Khong tao duoc file backup, dung lai."
  exit 1
fi

echo "Dang ma hoa $BACKUP -> $ENC (AES-256, PBKDF2)..."
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in "$BACKUP" -out "$ENC" \
  -pass "file:$PASSFILE"
echo "Ma hoa xong:"
ls -lh "$BACKUP" "$ENC"
sha256sum "$BACKUP" "$ENC" | tee "$HOME/backup-$TODAY.sha256"

# Kiem chung khoi phuc: giai ma vao /tmp (RAM, mat khi may pause/tat),
# so sanh hash voi ban goc, liet ke noi dung, roi xoa ban giai ma.
echo "Kiem chung: giai ma vao /tmp/restore-test va so sanh hash..."
mkdir -p /tmp/restore-test
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in "$ENC" -out /tmp/restore-test/backup-decrypted.tar.gz \
  -pass "file:$PASSFILE"
if ! sha256sum -c "$HOME/backup-$TODAY.sha256" --quiet 2>/dev/null; then
  echo "Loi: file hash khong khop, dung lai de kiem tra."
  exit 1
fi
echo "OK: hash cua file goc va file ma hoa deu khop voi file .sha256."
# So sanh truc tiep hash cua ban giai ma voi ban goc.
ORIG_HASH="$(sha256sum "$BACKUP" | awk '{print $1}')"
DEC_HASH="$(sha256sum /tmp/restore-test/backup-decrypted.tar.gz | awk '{print $1}')"
if [ "$ORIG_HASH" = "$DEC_HASH" ]; then
  echo "OK: ban giai ma trung hash voi ban goc."
else
  echo "LOI: ban giai ma khac hash voi ban goc, dung lai."
  exit 1
fi
echo "Noi dung file backup (kiem chung, khong ghi de du lieu that):"
tar -tzf /tmp/restore-test/backup-decrypted.tar.gz
rm -f /tmp/restore-test/backup-decrypted.tar.gz
echo "Da xoa ban giai ma tam trong /tmp."
echo "Xong. File ma hoa de tai xuong hoac gui di offsite: $ENC"
echo "Nho giu file mat khau $PASSFILE va file hash $HOME/backup-$TODAY.sha256 cung voi file .enc."
