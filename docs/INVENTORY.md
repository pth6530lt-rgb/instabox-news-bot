# Kiểm kê vận hành máy agent-brower (cập nhật 31/10/2026)

Máy: InstaBox free, 4 vCPU, 8GB RAM, 20GB /data, auto-pause 30 phút idle, tối đa 8 giờ chạy liên tục.
Nguyên tắc: mọi cổng đều private, link có token giữ kín như mật khẩu, không publish public.

| Dịch vụ | Cổng host | Thư mục trên máy | Link private lưu trong máy |
|---|---|---|---|
| FreshRSS | 8080 | ~/news | ~/private-link.txt |
| RSSHub | 1200 | ~/news | ~/rsshub-link.txt |
| WebApp | 8000 | ~/news/webapp | ~/webapp-link.txt |
| Changedetection | 5000 | ~/changedetection | xem tab Ports, xoay token nếu link lỗi |
| Vaultwarden | 8082 | ~/vaultwarden | ~/vaultwarden-link.txt |
| FileBrowser | 8083 | ~/filebrowser | ~/filebrowser-link.txt |
| Trilium | 8084 | ~/trilium | ~/trilium-link.txt |
| Linkding | 8085 | ~/linkding | ~/linkding-link.txt |
| Portainer | 9000 | ~/portainer | ~/portainer-link.txt |
| Uptime Kuma | 3001 | ~/uptime-kuma | ~/uptime-kuma-link.txt |
| Trang tổng Homepage | 3002 | ~/homepage | ~/homepage-link.txt |

Tổng cộng 11 dịch vụ, 11 cổng private, trong giới hạn 16 cổng của InstaBox.

## Việc chỉ người dùng mới làm được
- Đặt mật khẩu cho Changedetection, Portainer, Trilium, Linkding, FreshRSS.
- Tạo tài khoản Vaultwarden đầu tiên, bật 2FA, đổi mật khẩu mặc định của FileBrowser ngay sau lần đăng nhập đầu.
- Tạo bot Telegram bằng BotFather, tạo ~/news/.env, tạo API key InstaBox và GitHub Secrets để bật daily.
- Sửa feed CafeF trong FreshRSS sang link Google News site:cafef.vn.

## Vận hành định kỳ
- Chạy `bash ~/scripts/health-backup.sh` mỗi tuần, xem ~/health-check.log, giữ file backup-YYYY-MM-DD.tar.gz.
- Kiểm tra `df -h`: ổ /data còn trống nhiều, ổ hệ thống / còn 6.5GB lúc kiểm tra 31/10/2026, nếu dưới 3GB thì dọn image Docker cũ.
- Trước thay đổi lớn, tạo snapshot InstaBox và xuất OPML từ FreshRSS.
- Không dùng ping liên tục để giữ máy free thức cả ngày; daily chạy bằng GitHub Actions wake máy đúng giờ.
