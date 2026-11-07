# Backup, snapshot và khôi phục — máy agent-brower

Cập nhật 07/11/2026. Nguyên tắc: backup trong máy chưa phải offsite,
snapshot InstaBox cũng nằm trong hệ thống InstaBox, nên cả hai đều chưa
phải bản sao ngoài thật sự. Muốn offsite thật, phải tải file mã hóa ra
khỏi máy, xem mục 4.

## 1. File backup nhẹ hiện có làm được gì, không làm được gì

`~/scripts/health-backup.sh` tạo `~/backup-YYYY-MM-DD.tar.gz` chỉ chứa
file cấu hình, feed và digest: `news/feeds.json`, `news/docker-compose.news.yml`,
`news/webapp/digest.json`, `news/bot.py` và các compose của Changedetection,
Vaultwarden, FileBrowser, Linkding, Portainer, Trilium. Nó KHÔNG chứa:

- Dữ liệu FreshRSS (bài đã đọc, tài khoản), dữ liệu Trilium, Linkding,
  Changedetection, Vaultwarden, Portainer — các dữ liệu này nằm trong
  volume Docker trên máy, chỉ snapshot máy mới giữ nguyên vẹn.
- File `~/news/.env` (chứa Telegram token) — cố tình không backup vào
  file tar, vì token phải giữ riêng.
- Vault trong Vaultwarden — muốn backup đầy đủ, xuất vault từ giao
  diện Vaultwarden và lưu riêng, an toàn hơn.

Vì vậy file backup nhẹ chỉ đủ để dựng lại cấu hình và feed, còn dữ
liệu ứng dụng phải khôi phục bằng snapshot máy, hoặc bằng xuất dữ
liệu riêng của từng app (OPML của FreshRSS, xuất vault của Vaultwarden).

## 2. Backup mã hóa (script mới)

Script `scripts/backup-encrypted.sh` chỉ mã hóa file backup nhẹ,
không tải lên đâu, không gửi Telegram, không restart container.

### Lần đầu, bạn tự tạo mật khẩu trên máy

```bash
echo -n 'mat-khau-ban-chon' > ~/scripts/backup-passphrase.txt
chmod 600 ~/scripts/backup-passphrase.txt
```

Mật khẩu này không có trong repo, không gửi qua chat, và nếu quên
thì file `.enc` không giải mã được nữa. Muốn đổi mật khẩu, sửa file
trên máy rồi chạy lại script.

### Chạy và kiểm chứng

```bash
bash ~/scripts/health-backup.sh
bash ~/scripts/backup-encrypted.sh
```

Script sẽ mã hóa bằng AES-256, ghi file `~/backup-YYYY-MM-DD.tar.gz.enc`
và file hash `~/backup-YYYY-MM-DD.sha256`, rồi tự kiểm chứng bằng cách
giải mã vào `/tmp/restore-test`, so sánh hash với bản gốc, liệt kê
nội dung file backup, rồi xóa bản giải mã tạm trong `/tmp`. Nếu hash
không khớp, script dừng lại và báo lỗi, không làm gì thêm.

### Giải mã tay khi cần

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in backup-YYYY-MM-DD.tar.gz.enc \
  -out backup-YYYY-MM-DD.tar.gz \
  -pass file:~/scripts/backup-passphrase.txt
tar -tzf backup-YYYY-MM-DD.tar.gz
```

## 3. Snapshot máy và diễn tập khôi phục

### Tạo snapshot (làm trên dashboard InstaBox)

1. Mở dashboard, vào máy `agent-brower`, mục Snapshots.
2. Tạo snapshot mới, đặt tên có ngày, ví dụ `pro-v1-2026-11-07`.
3. Đợi snapshot xong rồi ghi tên và ngày vào đây, đừng xóa snapshot
   cũ khi chưa chắc snapshot mới đã tốt.
4. Gói free cho tối đa 5 snapshot, nên giữ lại 2 snapshot gần nhất
   và xóa snapshot quá cũ khi sắp hết chỗ.

### Diễn tập khôi phục kiểm chứng (không ghi đè dữ liệu thật)

Diễn tập này chỉ kiểm chứng file backup đọc được, không khôi phục
thật lên máy đang chạy:

1. Chạy `bash ~/scripts/health-backup.sh` để có backup mới nhất.
2. Chạy `bash ~/scripts/backup-encrypted.sh` để kiểm chứng giải mã
   và hash, như mục 2.
3. Giải nén bản kiểm chứng vào thư mục tạm `/tmp/restore-test` và
   kiểm tra có đủ `feeds.json`, `bot.py`, các compose hay không.
4. Ghi lại kết quả diễn tập: ngày, tên file backup, hash khớp hay
   không, có thiếu file nào không.

Khôi phục thật chỉ làm khi máy hỏng hoặc dữ liệu mất, và phải làm
theo thứ tự: khôi phục snapshot máy trước (giữ nguyên volume và
dữ liệu app), nếu không có snapshot thì dựng lại từng app bằng
compose trong repo, rồi nhập OPML vào FreshRSS và nhập vault vào
Vaultwarden từ bản xuất riêng của bạn.

## 4. Offsite — cần bạn chọn nơi lưu

| Hướng | Cách làm | Cần bạn làm |
|---|---|---|
| Tải về máy tính của bạn | Mở FileBrowser bằng link private, tải file `.enc` và file `.sha256` về, giữ cùng file mật khẩu ở nơi riêng | Tải tay sau mỗi lần backup |
| Rclone lên Google Drive / Dropbox | Cài rclone trên máy, bạn tự đăng nhập và cấp quyền cho rclone, script chỉ chạy lệnh copy file `.enc` lên đó | Đăng nhập và cấp quyền cho rclone, mình không tự lấy tài khoản của bạn |
| Chỉ dùng snapshot InstaBox | Không có bản offsite thật, chỉ có điểm khôi phục trong hệ thống InstaBox | Không cần làm gì thêm, nhưng chấp nhận rủi ro nếu InstaBox gặp sự cố |

Khi bạn chọn một hướng, mình sẽ viết thêm bước đó vào script và
hướng dẫn, còn hiện tại script chỉ tạo và kiểm chứng file mã hóa
trong máy.
