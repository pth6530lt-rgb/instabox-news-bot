# HƯỚNG DẪN TOÀN BỘ HỆ THỐNG — Máy InstaBox agent-brower

Tài liệu học tập, viết ngày 07/11/2026, cập nhật tới trạng thái hệ thống
lúc đó. Đọc từ đầu tới cuối một lần để hiểu bức tranh chung, sau đó dùng
mục lục để tra cứu từng phần khi cần làm việc cụ thể. File này không chứa
mật khẩu, token hay link private nào — những thứ đó chỉ nằm trên máy,
trong các file `*-link.txt` và `~/news/.env`.

## Mục lục

1. Bức tranh chung: hệ thống này là gì
2. Máy ảo InstaBox và giới hạn gói free
3. Bảng kiểm kê: 13 dịch vụ, cổng, thư mục, giới hạn
4. Repo GitHub: cấu trúc và vai trò từng file
5. Cách một app được tạo ra: mẫu chuẩn 7 bước
6. Từng dịch vụ: làm gì, code nào, bước đầu tiên nào
7. Hệ tin tức và bot Telegram: bot.py, feeds.json, WebApp, daily
8. Mạng và cổng private: token hoạt động ra sao, xoay token khi nào
9. Giám sát và thông báo: Uptime Kuma, Ntfy, check-updates
10. Log rotation và giới hạn tài nguyên
11. Backup, snapshot và khôi phục
12. Bảo mật: những quy tắc không bao giờ phá vỡ
13. Vận hành định kỳ: lịch tuần, lịch tháng
14. Xử lý sự cố: bảng tra nhanh
15. Tối ưu hoá tiếp theo: thứ tự đề xuất
16. Nhật ký cập nhật 07/11/2026: 3 đợt update 11 app

---

## 1. Bức tranh chung: hệ thống này là gì

Hệ thống là một máy Linux nhỏ tự quản, chạy 13 dịch vụ bằng Docker,
phục vụ 3 nhu cầu: đọc tin, quản lý công việc và tài liệu, giám sát
chính hệ thống đó.

Luồng dữ liệu chính, đọc từ trái sang phải, một hàng duy nhất:

Nguồn tin (VnExpress, CafeF, Bloomberg, Fed, Google News)
  → RSSHub / feed RSS trực tiếp
  → FreshRSS (đọc, lưu, cập nhật mỗi 15 phút)
  → bot.py (lọc, gom nhóm, viết digest.json)
  → WebApp (trang tin đã lọc) và Telegram (tin nhắn daily, khi có bot)

Các dịch vụ còn lại không nằm trong luồng tin, chúng là công cụ độc lập
chạy cùng máy: Vaultwarden giữ mật khẩu, Trilium giữ ghi chú, Linkding
giữ link đọc sau, FileBrowser giữ file, Portainer quản lý Docker,
Changedetection theo dõi trang web, Uptime Kuma giám sát dịch vụ,
Ntfy gửi thông báo, Homepage gom link, IT-Tools làm công cụ web.

Nguyên tắc thiết kế xuyên suốt:

- Nhẹ trước, nặng sau: app nào cũng dưới 1GB RAM, trừ FreshRSS và
  Trilium được 1GB, còn lại 256–512MB.
- Dữ liệu nhỏ: ổ đĩa chỉ 20GB, nên không lưu phim, ảnh lớn, không chạy
  mô hình AI local, không chạy Elasticsearch.
- Private trước: mọi cổng đều publish dạng private có token, không có
  cổng public nào.
- Không tự động thay đổi production: script chỉ kiểm tra và báo cáo,
  việc update, restart hay xoá do con người quyết định.
- Mọi thay đổi đều có bản sao trong repo GitHub, để máy hỏng vẫn dựng
  lại được từ code.

## 2. Máy ảo InstaBox và giới hạn gói free

- Nhà cung cấp: instabox.sh, máy Firecracker microVM, hệ điều hành
  Debian, tên máy `agent-brower`, tạo ngày 28/10/2026.
- Cấu hình: 4 vCPU, 8GB RAM, ổ đĩa bền 20GB gắn tại `/data`, thư mục
  home là `/data/home`, thư mục `/tmp` là RAM tmpfs, mất khi máy tắt.
- Gói free, đã xác nhận lại ngày 07/11/2026: chỉ 1 máy, tối đa 5
  snapshot, tối đa 16 cổng publish, tự pause sau 30 phút không dùng,
  chạy liên tục tối đa 8 giờ rồi phải nghỉ 5–20 phút.
- Hệ quả thực tế: máy không chạy 24/7 được. Muốn tin tức cập nhật
  mỗi ngày thì dùng GitHub Actions đánh thức máy đúng giờ, chạy bot,
  rồi để máy pause lại. Muốn cảnh báo gần như ngay lập tức thì phải
  lên gói trả phí hoặc chuyển riêng bot sang VPS luôn chạy.
- Truy cập: vào trang instabox.sh, đăng nhập bằng Google với tài khoản
  `pth6530lt@gmail.com`, vào workspace Personal, mở máy, dùng terminal
  trong dashboard. Bảng Filesystem trong dashboard chỉ đọc, nên muốn
  tạo file trên máy thì dùng terminal hoặc tải file từ GitHub raw.
- Docker trên máy: Docker 29.8.2, dùng lệnh `docker compose` và
  `docker ps`. Lệnh `instabox-port` dùng để publish cổng từ terminal.

## 3. Bảng kiểm kê: 13 dịch vụ, cổng, thư mục, giới hạn

Tổng cộng 13 dịch vụ, 13 cổng private, trong giới hạn 16 cổng.

| Dịch vụ | Cổng host | Thư mục trên máy | File link private | RAM | Vai trò |
|---|---|---|---|---|---|
| FreshRSS | 8080 | ~/news | ~/private-link.txt | 1GB | Đọc tin RSS |
| RSSHub | 1200 | ~/news | ~/rsshub-link.txt | 512MB | Tạo feed RSS |
| WebApp tin | 8000 | ~/news/webapp | ~/webapp-link.txt | 256MB | Trang tin đã lọc |
| Changedetection | 5000 | ~/changedetection | chưa có file link riêng | 512MB | Theo dõi trang web |
| Vaultwarden | 8082 | ~/vaultwarden | ~/vaultwarden-link.txt | 512MB | Quản lý mật khẩu |
| FileBrowser | 8083 | ~/filebrowser | ~/filebrowser-link.txt | 512MB | Quản lý file |
| Trilium | 8084 | ~/trilium | ~/trilium-link.txt | 1GB | Ghi chú |
| Linkding | 8085 | ~/linkding | ~/linkding-link.txt | 512MB | Lưu link đọc sau |
| Portainer | 9000 | ~/portainer | ~/portainer-link.txt | 512MB | Quản lý Docker |
| Uptime Kuma | 3001 | ~/uptime-kuma | ~/uptime-kuma-link.txt | 512MB | Giám sát dịch vụ |
| Trang tổng Homepage | 3002 | ~/homepage | ~/homepage-link.txt | 256MB | Gom link các dịch vụ |
| Ntfy | 3003 | ~/ntfy | ~/ntfy-link.txt | 256MB | Gửi thông báo |
| IT-Tools | 3004 | ~/it-tools | ~/it-tools-link.txt | 256MB | Công cụ web nhẹ |

Ngoài 13 container trên còn có bot Telegram, nhưng bot không chạy nền
mặc định, chỉ chạy tay hoặc chạy theo lịch daily, nên không tính vào
bảng trên. File kiểm kê chính thức nằm trong repo tại
`docs/INVENTORY.md`, cập nhật mỗi khi thêm hoặc đổi dịch vụ.

## 4. Repo GitHub: cấu trúc và vai trò từng file

Repo public: `github.com/pth6530lt-rgb/instabox-news-bot`, nhánh `main`,
tài khoản `pth6530lt-rgb`. Repo public nên tuyệt đối không có token,
API key, mật khẩu hay file `.env` trong repo.

```
instabox-news-bot/
├── README.md                    # Gioi thieu ngan, cach dung repo
├── bot.py                       # Bot Telegram + tao digest tin
├── feeds.json                   # Danh sach feed, co country va topic
├── docker-compose.news.yml      # Stack tin tuc: freshrss, rsshub, webapp, bot
├── webapp/index.html            # Giao dien WebApp tin da loc
├── .github/workflows/daily.yml  # GitHub Actions: danh thuc may, chay bot daily luc 07:00
├── changedetection/docker-compose.yml
├── vaultwarden/docker-compose.yml
├── filebrowser/docker-compose.yml
├── linkding/docker-compose.yml
├── portainer/docker-compose.yml
├── trilium/docker-compose.yml
├── uptime-kuma/docker-compose.yml
├── homepage/
│   ├── docker-compose.yml
│   ├── config/services.yaml     # Danh sach dich vu tren Trang tong (link tam #)
│   ├── config/settings.yaml     # Tieu de, ngon ngu, kieu hien thi
│   └── scripts/gen-services.sh  # Dien link private that vao services.yaml
├── ntfy/
│   ├── docker-compose.yml
│   └── config/server.yml
├── it-tools/docker-compose.yml
├── scripts/
│   ├── health-backup.sh         # Kiem tra container + backup nhe
│   ├── check-updates.py         # Kiem tra ban moi cua image, chi doc
│   └── backup-encrypted.sh      # Ma hoa file backup, kem kiem chung giai ma
├── docs/
│   ├── INVENTORY.md             # Bang kiem ke dich vu
│   ├── BACKUP-RESTORE.md        # Backup, snapshot, khoi phuc
│   └── HUONG-DAN-TOAN-BO-HE-THONG.md  # Chinh file nay
├── RSSHUB-ROUTES.md             # Huong dan them route RSSHub dung cach
└── HUONG-DAN-CAC-BUOC-TIEP-THEO.md    # Huong dan chi tiet cac buoc tiep theo
```

Quy trình làm việc chuẩn với repo: sửa file ở máy local, kiểm tra cú
pháp (YAML bằng `python3 -c "import yaml"`, Python bằng `py_compile`),
đưa lên GitHub bằng trình duyệt, mở link raw để xác nhận nội dung mới,
rồi trên máy tải file về bằng `curl -O <link raw>` và chạy lại. Không
bao giờ dán file lớn qua terminal bằng heredoc, vì dễ lỗi, nhất là
file trên 10KB như `bot.py`.

## 5. Cách một app được tạo ra: mẫu chuẩn 7 bước

Mọi app trên máy đều đi qua đúng 7 bước này, học thuộc mẫu này là
hiểu được toàn bộ hệ thống.

**Bước 1 — Viết compose ở máy local.** Một file
`docker-compose.yml` tối thiểu gồm image, tên container, restart
`unless-stopped`, giới hạn RAM và CPU, log rotation, cổng host,
volume dữ liệu, múi giờ `Asia/Ho_Chi_Minh`. Mẫu đầy đủ:

```yaml
services:
  ten-app:
    image: tac-gia/ten-app:latest
    container_name: ten-app
    restart: unless-stopped
    mem_limit: 512m
    cpus: 0.5
    logging:
      driver: json-file
      options:
        max-size: 10m
        max-file: "3"
    ports:
      - "3005:80"
    volumes:
      - ./data:/duong/dan/du/lieu/trong/container
    environment:
      - TZ=Asia/Ho_Chi_Minh
```

Giải thích từng dòng: `image` là app muốn chạy, lấy từ Docker Hub;
`restart: unless-stopped` nghĩa là container tự chạy lại khi máy
khởi động; `mem_limit` và `cpus` chặn app không ăn hết tài nguyên;
`logging` giữ mỗi file log tối đa 10MB, giữ 3 file, để log không ăn
dần ổ hệ thống; `ports` là cổng host bên ngoài map vào cổng trong
container; `volumes` là nơi dữ liệu sống, xoá container không mất
dữ liệu nếu volume còn; `TZ` đặt múi giờ Việt Nam cho log và lịch.

**Bước 2 — Kiểm tra cú pháp ở máy local.** Chạy
`python3 -c "import yaml; yaml.safe_load(open('docker-compose.yml'))"`.
Nếu báo lỗi thì sửa file, không đưa file lỗi lên GitHub.

**Bước 3 — Đưa lên GitHub.** Tạo hoặc thay thế file trong repo, commit
lên nhánh `main`, mở link raw để xác nhận nội dung mới đã lên thật.

**Bước 4 — Tải về máy và chạy.** Trên terminal của máy:

```bash
mkdir -p ~/ten-app && cd ~/ten-app
curl -O https://raw.githubusercontent.com/pth6530lt-rgb/instabox-news-bot/main/ten-app/docker-compose.yml
docker compose up -d
docker compose ps
```

Ngoại lệ duy nhất: stack tin tức trong `~/news` dùng tên file
`docker-compose.news.yml`, không phải `docker-compose.yml`, nên mọi
lệnh compose trong thư mục đó phải thêm `-f`, ví dụ
`docker compose -f docker-compose.news.yml up -d freshrss rsshub webapp`.
Lệnh compose thường trong `~/news` sẽ báo không tìm thấy file cấu hình.

**Bước 5 — Kiểm tra bằng lệnh.** Dùng `docker inspect` để xem log và
RAM đã áp dụng chưa, dùng `curl http://localhost:<cong>` để xem app
có trả lời không. Chỉ khi nào localhost trả lời thì mới publish cổng.

**Bước 6 — Publish cổng dạng private.** Trên dashboard, publish cổng,
nhưng dashboard tạo public theo mặc định, nên phải chuyển ngay sang
private bằng lệnh `instabox-port publish --private --name <ten> <cong>`,
kiểm tra lại tab Ports phải hiện Private, rồi lưu link vào file
`~/<ten>-link.txt` trong máy. Nếu link đầu tiên báo token không hợp
lệ thì xoay token một lần bằng
`instabox-port publish --private --rotate-token --name <ten> <cong>`
rồi lưu link mới. Token trong link là bí mật, giữ như mật khẩu.

**Bước 7 — Cập nhật kiểm kê và Trang tổng.** Thêm một dòng vào
`docs/INVENTORY.md`, thêm dịch vụ vào Trang tổng bằng script
`gen-services.sh` nếu app có link private, rồi tạo lại Homepage.

---

## 6. Từng dịch vụ: làm gì, code nào, bước đầu tiên nào

Mỗi mục dưới đây trả lời 3 câu hỏi: app làm gì, code chính nằm ở
đâu, và việc đầu tiên chỉ bạn mới làm được là gì. Không có app nào
được tạo tài khoản hay đặt mật khẩu thay bạn.

### 6.1 FreshRSS — đọc tin RSS (cổng 8080)

- Làm gì: gom 11 feed tin Việt Nam và quốc tế, cập nhật mỗi 15 phút
  (`CRON_MIN: "*/15"`), đọc trên giao diện web, đánh dấu đã đọc.
- Code: `docker-compose.news.yml`, dịch vụ `freshrss`, image
  `freshrss/freshrss:latest`, volume `./freshrss/data` giữ dữ liệu.
- Feed: 11 feed trong `feeds.json` và file OPML đã import. Lúc import
  có 626 bài chưa đọc, trong đó feed CafeF bị lỗi 0 bài, xem mục 14.
- Việc của bạn: tài khoản admin đã tự tạo và đăng nhập với tên
  `jarvier_py`. Muốn đổi feed thì vào Subscription, sửa URL rồi bấm
  Update feeds. Muốn sao lưu feed thì xuất OPML từ giao diện.

### 6.2 RSSHub — tạo feed RSS (cổng 1200)

- Làm gì: tạo feed RSS cho trang không có RSS sẵn, dùng bộ nhớ đệm
  trong RAM, không cần Chromium hay Redis ở cấu hình hiện tại.
- Code: `docker-compose.news.yml`, dịch vụ `rsshub`, image
  `diygod/rsshub:latest`, cổng 1200.
- Cách dùng: copy route từ tài liệu chính thức
  `https://docs.rsshub.app`, không tự đoán route. Khi thêm feed vào
  FreshRSS thì dùng địa chỉ nội bộ `http://rsshub:1200/...`.
- Quy tắc: không dùng RSSHub để vượt paywall hay lấy nội dung trả phí.

### 6.3 WebApp tin — trang tin đã lọc (cổng 8000)

- Làm gì: trang web tĩnh hiển thị digest tin do bot tạo, có tìm kiếm,
  lọc theo quốc gia (Việt Nam / Quốc tế), chủ đề (Tin tức / Trading /
  Vĩ mô), nguồn tin, xem theo nhóm hoặc theo danh sách, có nút lọc
  nhanh và đặt lại bộ lọc.
- Code: `webapp/index.html` (9.286 byte), chạy bằng `nginx:alpine`,
  đọc file `webapp/digest.json` do bot tạo ra.
- Lưu ý: nếu bot chưa chạy thì trang hiện "chưa có digest", đó là
  bình thường, không phải lỗi. Digest có 60 tin mỗi lần chạy, trong
  đó trường tóm tắt chỉ có nội dung ở 4/60 tin, vì nhiều feed nguồn
  không trả về mô tả.

### 6.4 Changedetection — theo dõi trang web (cổng 5000)

- Làm gì: theo dõi trang web không có RSS, báo khi nội dung thay đổi.
- Code: `changedetection/docker-compose.yml`, image
  `dgtlmoon/changedetection.io:latest`, phiên bản đã kiểm tra là
  0.60.10, volume `./data:/datastore`.
- Việc của bạn: tự đặt mật khẩu trong Settings, tự thêm watch cho
  trang muốn theo dõi, tự cấu hình thông báo. Chưa có watch nào được
  thêm. Link private của app này chưa có file `*-link.txt` riêng,
  nên trong Trang tổng link của nó vẫn là `#`.

### 6.5 Vaultwarden — quản lý mật khẩu (cổng 8082)

- Làm gì: quản lý mật khẩu riêng, tương thích với ứng dụng Bitwarden.
- Code: `vaultwarden/docker-compose.yml`, image
  `vaultwarden/server:latest`, phiên bản đã kiểm tra là 1.37.4,
  cổng 8082, bật websocket, hiện đang cho phép đăng ký tài khoản
  (`SIGNUPS_ALLOWED=true`).
- Việc của bạn: tự tạo tài khoản đầu tiên, bật 2FA, xuất vault để
  sao lưu riêng. Sau khi tạo tài khoản xong, nên tắt đăng ký bằng
  cách đổi `SIGNUPS_ALLOWED` thành `false` rồi tạo lại container,
  để không ai khác tạo tài khoản trên máy của bạn. Đây là một trong
  các tối ưu hoá đề xuất ở mục 15.

### 6.6 FileBrowser — quản lý file (cổng 8083)

- Làm gì: quản lý file trong thư mục home trên máy qua giao diện web,
  dùng để tải file backup về máy tính của bạn.
- Code: `filebrowser/docker-compose.yml`, image
  `filebrowser/filebrowser:latest`, thư mục home gắn tại `/srv`,
  file `database.db` phải tạo trước lần chạy đầu để Docker không
  tạo nhầm thành thư mục.
- Việc của bạn: đổi mật khẩu mặc định ngay sau lần đăng nhập đầu.
  Dự án File Browser đã được lưu trữ (archived) từ 01/09/2026, nên
  không còn cập nhật tính năng hay bảo mật mới, chỉ dùng qua link
  private và không chia sẻ link ra ngoài.

### 6.7 Trilium — ghi chú (cổng 8084)

- Làm gì: ghi chú có cấu trúc cây, lưu trong volume
  `./data:/home/node/trilium-data`.
- Code: `trilium/docker-compose.yml`, image `triliumnext/trilium:latest`,
  RAM 1GB.
- Việc của bạn: tự làm bước thiết lập ban đầu (chọn ngôn ngữ, bấm
  Continue) rồi tự tạo tài khoản và mật khẩu.

### 6.8 Linkding — lưu link đọc sau (cổng 8085)

- Làm gì: lưu link để đọc sau, có gắn thẻ và tìm kiếm.
- Code: `linkding/docker-compose.yml`, image
  `sissbruecker/linkding:latest`, cổng host 8085 map vào 9090 trong
  container, volume `./data:/etc/linkding/data`.
- Việc của bạn: tự tạo tài khoản và mật khẩu.

### 6.9 Portainer — quản lý Docker (cổng 9000)

- Làm gì: xem và quản lý container, image, volume qua giao diện web.
- Code: `portainer/docker-compose.yml`, image
  `portainer/portainer-ce:latest`, gắn socket Docker
  `/var/run/docker.sock`, nên có toàn quyền Docker.
- Việc của bạn: tự tạo tài khoản quản trị đầu tiên, mật khẩu tối
  thiểu 12 ký tự. Vì có toàn quyền Docker nên app này bắt buộc phải
  ở dạng private, không bao giờ publish public. Nếu màn hình tạo
  tài khoản hỏi mã setup thì lấy mã đó trong log của Portainer.

### 6.10 Uptime Kuma — giám sát dịch vụ (cổng 3001)

- Làm gì: kiểm tra định kỳ xem từng dịch vụ có đang trả lời không,
  hiện trạng thái và lịch sử uptime.
- Code: `uptime-kuma/docker-compose.yml`, image
  `louislam/uptime-kuma:1`, volume `./data:/app/data`.
- Việc của bạn: tự tạo tài khoản quản trị lần đầu, rồi thêm monitor
  cho từng dịch vụ. Trang setup có hiện cảnh báo phiên bản cũ cho
  1.23.17, nhưng image được giữ nguyên theo yêu cầu, chưa update.
  Muốn nhận cảnh báo qua Ntfy thì cấu hình notification trong
  Uptime Kuma sau khi đã có tài khoản, dùng link private của Ntfy
  và tên topic trong file `~/ntfy-topic.txt`.

### 6.11 Trang tổng Homepage — gom link (cổng 3002)

- Làm gì: một trang duy nhất gom link private của các dịch vụ, chia
  3 nhóm Tin tức, Công việc, Hệ thống. Ngoài ra trang còn hiện 3
  nhóm mặc định của Homepage là Developer, Social và Entertainment,
  chưa dọn.
- Code: `homepage/docker-compose.yml`, image
  `ghcr.io/gethomepage/homepage:latest`, cổng host 3002 map vào
  3000 trong container, RAM 256MB.
- Điểm đặc biệt cần học: bản Homepage mới bắt buộc khai báo host
  được phép, nếu không sẽ trả lỗi 400 "Host validation failed" cả
  khi mở bằng localhost lẫn link private. Biến môi trường
  `HOMEPAGE_ALLOWED_HOSTS` trong compose liệt kê localhost, 127.0.0.1
  và host của cổng 3002. Host này không chứa token, token nằm trong
  query `?_token=...` nên vẫn an toàn.
- Cách điền link: file `homepage/config/services.yaml` trong repo
  chỉ có link tạm `#`. Trên máy, script
  `homepage/scripts/gen-services.sh` đọc link thật từ các file
  `*-link.txt` trong thư mục home rồi ghi lại file dịch vụ, sau đó
  chạy `docker compose up -d` để tạo lại Homepage. Lần chạy gần
  nhất đã điền được 11 trong 12 link, còn thiếu Changedetection.
- Dọn nhóm mặc định: Homepage tự tạo file `bookmarks.yaml` mặc định
  với 3 nhóm Developer, Social và Entertainment nếu file này không
  tồn tại, nên thư mục cấu hình phải có file
  `homepage/config/bookmarks.yaml` rỗng có chủ đích (nội dung là
  `[]` kèm comment giải thích). Đã áp dụng ngày 07/11/2026: file đã
  lên repo, tải về máy, Homepage tự nhận file mới mà không cần tạo
  lại container, API bookmarks trả về danh sách rỗng và trang chỉ
  còn 3 nhóm Tin tức, Công việc và Hệ thống.

### 6.12 Ntfy — gửi thông báo (cổng 3003)

- Làm gì: kênh thông báo nhẹ, để Uptime Kuma và Changedetection gửi
  cảnh báo khi dịch vụ sập hoặc trang thay đổi, mà không cần chờ bot
  Telegram xong.
- Code: `ntfy/docker-compose.yml`, image `binwiederhier/ntfy:latest`,
  cổng host 3003 map vào 80 trong container, RAM 256MB, cấu hình
  trong `ntfy/config/server.yml`.
- Cách dùng: tên topic riêng cho hệ thống được tạo bằng chuỗi ngẫu
  nhiên, lưu trong file `~/ntfy-topic.txt` với quyền 600, không gửi
  tên topic qua chat. Gửi thử bằng lệnh
  `curl -d "Kiem tra Ntfy" http://localhost:3003/<topic>`,
  rồi lấy lại topic để kiểm tra thông báo có hiện ra không.
- Lưu ý quan trọng: topic mặc định là công khai với bất kỳ ai biết
  tên topic, nên phải dùng tên khó đoán, chỉ dùng qua link private,
  không chia sẻ tên topic ra ngoài. Chưa cấu hình thông báo cho
  Uptime Kuma hay Changedetection, vì cần tài khoản quản trị của
  các app đó trước.

### 6.13 IT-Tools — công cụ web nhẹ (cổng 3004)

- Làm gì: bộ công cụ web dùng ngay trên trình duyệt, gồm tạo token,
  băm văn bản, Bcrypt, tạo UUID và ULID, mã hoá và giải mã văn bản,
  tạo cụm mật khẩu BIP39, tạo Hmac, tạo cặp khoá RSA, và nhiều công
  cụ khác, không gửi dữ liệu lên trang lạ.
- Code: `it-tools/docker-compose.yml`, image
  `corentinth/it-tools:latest`, cổng host 3004 map vào 80 trong
  container, RAM 256MB, không cần cấu hình thêm.

---

## 7. Hệ tin tức và bot Telegram: bot.py, feeds.json, WebApp, daily

### 7.1 feeds.json — danh sách feed

File `feeds.json` liệt kê 11 feed, mỗi feed có 4 trường chính: `url`,
`category` (ví dụ VN-Tin tức, VN-Trading, QT-Macro, QT-Trading,
QT-Tin tức), `country` (Việt Nam / Quốc tế) và `topic` (Tin tức /
Trading / Vĩ mô). Bot dùng `country` và `topic` để gom nhóm tin trong
digest và trong tin nhắn daily. Feed CafeF trong file này đã dùng link
Google News `site:cafef.vn`, còn subscription trong FreshRSS thì chưa
đổi, xem mục 14.

### 7.2 bot.py — 4 chế độ chạy

File `bot.py` (21.530 byte) chỉ dùng thư viện chuẩn của Python, không
cần cài thêm gói nào, và không dùng webhook, chỉ dùng polling khi chạy
nền. Bốn chế độ:

- `--once`: lấy feed mới một lần, viết `webapp/digest.json`, không gửi
  Telegram. Dùng để kiểm tra và để WebApp có tin hiển thị.
- `--daily`: lấy tin mới trong 24 giờ gần nhất (tuỳ chọn `--hours`),
  viết digest, gửi một tin nhắn gom nhóm theo từng category, mỗi nhóm
  tối đa 5 tin, mỗi tin có nguồn. Dùng cho chạy daily lúc 07:00.
- `--poll`: chạy nền, lặp lại `--once` mỗi 600 giây, nhận lệnh từ
  Telegram: `/moi`, `/trading`, `/macro`, `/vn`, `/market`, `/start`.
  Chỉ chạy một bot tại một thời điểm, không chạy trùng.
- `--market`: in bảng giá tham khảo: BTC và ETH bằng USD qua CoinGecko,
  USD/VND qua exchangerate-api, không cần API key. Bot cố tình không
  tự tạo giá VN-Index hay giá vàng trong nước, vì không có API công
  khai miễn phí đáng tin, mà in dòng nhắc kiểm tra trên sàn hoặc
  công ty chứng khoán, kèm cảnh báo chỉ tham khảo, không phải tín
  hiệu giao dịch.

Bot lưu các tin đã thấy trong SQLite tại `bot-data/seen.db`, để không
gửi trùng. Bảng `seen` tự nâng cấp thêm cột `summary`, `country`,
`topic` khi chạy bản mới, không cần xoá database cũ. Bot đọc token và
chat_id từ biến môi trường, hoặc từ file `~/news/.env` trong cùng thư
mục nếu không có biến môi trường. File `.env` phải đặt quyền 600 và
không bao giờ đưa vào repo hay gửi qua chat.

### 7.3 Tạo bot Telegram và chạy daily

Các bước này chỉ bạn mới làm được, tóm tắt theo file
`HUONG-DAN-CAC-BUOC-TIEP-THEO.md`:

1. Nhắn `@BotFather`, dùng lệnh `/newbot`, đặt tên bot, giữ token bí mật.
2. Nhắn `/start` cho bot vừa tạo, rồi lấy chat_id bằng cách gọi
   `getUpdates` của Telegram API.
3. Trên máy, tạo file `~/news/.env` với token và chat_id, đặt quyền 600.
4. Chạy thử `python3 bot.py --once`, rồi `python3 bot.py --daily`,
   rồi `python3 bot.py --poll` để kiểm tra các lệnh.
5. Muốn dùng kênh Telegram thì thêm bot làm quản trị viên của kênh.
6. Muốn gắn WebApp vào nút Menu của bot thì dùng link private của
   cổng 8000 trong file `~/webapp-link.txt`, lưu ý xoay token của
   cổng 8000 sẽ làm link cũ trong Menu bị hỏng, phải cập nhật lại.

### 7.4 Chạy daily tự động bằng GitHub Actions

File `.github/workflows/daily.yml` chạy lúc 00:00 UTC, tức 07:00 giờ
Việt Nam. Nó đánh thức máy bằng InstaBox API, rồi chạy
`python3 bot.py --daily` trên máy. Muốn bật, bạn phải tự tạo InstaBox
API key trên dashboard và lưu hai secret vào repo GitHub là
`INSTABOX_API_KEY` và `INSTABOX_MACHINE_ID`. Workflow không chứa
Telegram token. Trước khi tin vào lịch tự động, hãy chạy workflow
bằng tay một lần để kiểm tra. Hai trường hợp workflow sẽ thất bại:
máy đang trong thời gian nghỉ sau 8 giờ chạy liên tục, hoặc máy bị
tắt tay, vì lúc đó lệnh đánh thức không hoạt động.

### 7.5 Cảnh báo quan trọng về tin tức và giá

RSS là tin tức, không phải tín hiệu giao dịch, không phải giá realtime.
FreshRSS cập nhật mỗi 15 phút, bot kiểm tra mỗi 10 phút, nên cảnh báo
có thể chậm. Trước khi giao dịch, luôn kiểm tra giá, thanh khoản và
nguồn tin trên sàn hoặc công ty chứng khoán. Bot và WebApp chỉ là công
cụ đọc tin cho tiện, không phải công cụ ra quyết định đầu tư.

---

## 8. Mạng và cổng private: token hoạt động ra sao, xoay token khi nào

- Mỗi cổng publish có một link dạng
  `https://<cong>-<ma-may>.instabox.tech/?_token=ibp_...`.
  Phần host không chứa token, token nằm trong query `?_token=...`.
  Ai có link đầy đủ mới mở được, ai chỉ biết host thì không.
- Dashboard tạo publish dạng public theo mặc định, nên mỗi lần
  publish cổng mới đều phải chuyển ngay sang private và kiểm tra lại
  tab Ports phải hiện Private, không để lại publish public nào.
- Token chỉ hiện một lần lúc tạo. Vì vậy link luôn được lưu vào file
  `~/<ten>-link.txt` trong máy ngay sau khi publish, để lần sau không
  phải đọc lại token từ ảnh chụp màn hình, vì đọc token từ ảnh đã
  từng sai nhiều lần.
- Xoay token: lệnh
  `instabox-port publish --private --rotate-token --name <ten> <cong>`.
  Xoay xong thì link cũ chết ngay, mọi nơi đang dùng link cũ phải
  cập nhật: Trang tổng, nút Menu của bot Telegram, Uptime Kuma,
  bất kỳ chỗ nào đã lưu link cũ.
- Trường hợp link báo "token không hợp lệ" trong trình duyệt nhưng
  kiểm tra từ trong máy vẫn thấy app chạy: đây là lỗi hiển thị token
  đã gặp với Linkding, Portainer, Trilium và FileBrowser, không
  chứng minh app đã sập. Cách xử lý là xoay token từ terminal trên
  máy rồi dùng link mới trong file `*-link.txt` tương ứng.
- Khi kiểm tra link bằng `curl` thì link private thường trả về 303
  rồi chuyển hướng, và khi theo chuyển hướng mà không giữ cookie thì
  có thể trả về 401. Đó là cách cổng private hoạt động, không phải
  bằng chứng link đã hỏng. Muốn kết luận link có mở được không thì
  phải mở bằng trình duyệt, không chỉ dùng `curl -L`.

## 9. Giám sát và thông báo: Uptime Kuma, Ntfy, check-updates

### 9.1 Uptime Kuma

Uptime Kuma kiểm tra định kỳ từng dịch vụ có trả lời không, hiện
trạng thái và lịch sử. Muốn nhận cảnh báo thì cấu hình notification
trong Uptime Kuma sau khi đã có tài khoản quản trị, trỏ tới Ntfy
bằng link private và tên topic trong `~/ntfy-topic.txt`, hoặc trỏ
tới Telegram sau khi bot đã xong.

### 9.2 Ntfy

Ntfy là kênh thông báo nhẹ, xem mục 6.12. Muốn gửi thông báo từ
một script hay một app khác, chỉ cần gửi HTTP POST tới
`http://localhost:3003/<topic>` từ trong máy, hoặc tới link private
của Ntfy từ bên ngoài. Đừng bao giờ ghi tên topic vào repo public.

### 9.3 check-updates.py — kiểm tra bản mới, chỉ đọc

Script `scripts/check-updates.py` liệt kê container đang chạy, lấy
config digest trên registry bằng `docker manifest inspect --verbose`,
rồi so sánh với Id của image local. Kết quả có 3 loại: OK là đang
chạy bản mới nhất, UPDATE là có bản mới trên registry, UNKNOWN là
không lấy được digest để so sánh. Script không pull, không tạo lại,
không restart container nào.

Lịch sử sửa script, nên học kỹ vì đây là lỗi kinh điển khi làm việc
với Docker:

- Lỗi 1: bản kiểm tra manifest thường không có trường digest trong
  JSON trả về, digest chỉ có trong bản chi tiết ở `Descriptor.digest`.
- Lỗi 2: bản chi tiết trả về một danh sách, không phải một dict, nên
  gọi trực tiếp `.get("Descriptor")` sẽ làm script lỗi ngay trước khi
  in kết quả.
- Lỗi 3: so sánh với RepoDigest là sai, vì RepoDigest là digest của
  manifest list, không phải digest của image amd64. Cách đúng là so
  sánh config digest trong `OCIManifest` của mục amd64/linux với Id
  của image local.

Kết quả kiểm tra ngày 07/11/2026: báo UPDATE cho 11 container, gồm
IT-Tools, Homepage, FreshRSS, WebApp, RSSHub, Trilium, Portainer,
Vaultwarden, Linkding, Uptime Kuma và Changedetection; báo UNKNOWN
cho Ntfy và FileBrowser. Tín hiệu UPDATE đã được kiểm chứng tay cho
`nginx:alpine`: Id local bắt đầu bằng `785835ea65db`, config digest
trên registry bắt đầu bằng `7cac34a4d72b`, hai digest khác nhau nên
lúc đó thật sự có bản mới trên registry. Dù vậy, không update app nào
chỉ vì script báo UPDATE, mà phải tạo snapshot trước, rồi update
từng app một và kiểm tra lại sau mỗi app.

Lỗi đã phát hiện và đã sửa xong ngày 07/11/2026, xem thêm mục 16:
sau 3 đợt update, bản script cũ vẫn báo UPDATE cho cả những image
vừa pull và cho cả FreshRSS mà lệnh pull đã xác nhận là đã mới nhất.
Nguyên nhân thật sự, đã kiểm chứng bằng lệnh: trên Docker 29 dùng
kho image containerd, Id của image là digest của danh sách manifest
(manifest list, hay index), không phải config digest của một platform.
Lệnh `docker pull nginx:alpine` báo "Image is up to date", Id local
là `713fc2ebfd92`, nhưng trong 16 mục của manifest thì không mục nào
có config digest trùng với nó, mục amd64 có config digest là
`7cac34a4d72b`. Bản script cũ so sánh Id local với config digest của
mục amd64, hai thứ khác loại nhau nên không bao giờ bằng nhau, script
báo có bản mới mãi là đúng như vậy. Giả thuyết kiến trúc máy đã được
kiểm tra và loại bỏ: máy chạy đúng x86_64, Docker cũng báo x86_64.
Bản script mới sửa đúng chỗ: dùng `docker buildx imagetools inspect`
để lấy digest của danh sách manifest trên registry rồi so sánh với Id
local, hai thứ cùng loại nhau, và in cả hai digest (12 ký tự đầu) để
chẩn đoán bằng mắt. Đã kiểm chứng ngày 07/11/2026: buildx v0.37.1 có
sẵn trên máy, script mới báo OK cho cả 13 container, digest local
bằng digest remote trong mọi trường hợp, kể cả Ntfy và FileBrowser
trước đó báo không xác định. Từ giờ tín hiệu của script lại đáng tin
để kết luận một app có cần update không.

## 10. Log rotation và giới hạn tài nguyên

Mọi dịch vụ đều có cùng một khối cấu hình trong compose:

```yaml
mem_limit: 512m
cpus: 0.5
logging:
  driver: json-file
  options:
    max-size: 10m
    max-file: "3"
```

Bảng giới hạn đã áp dụng: Changedetection, Uptime Kuma, Linkding,
Vaultwarden, FileBrowser, Portainer, Ntfy, IT-Tools đều 512MB hoặc
256MB; Trilium và FreshRSS 1GB; RSSHub 512MB; WebApp 256MB;
Homepage 256MB. Tổng RAM giới hạn của các app cộng lại vẫn dưới 8GB
của máy, nhưng đây là giới hạn tối đa từng app, không phải RAM thật
sự đang dùng.

Cách áp dụng: sửa compose trong repo, đưa lên GitHub, tải về máy,
chạy `docker compose up -d` để tạo lại container, rồi kiểm tra bằng
`docker inspect` xem log và RAM đã áp dụng chưa, và kiểm tra bằng
`curl localhost` xem app có trả lời không. Dữ liệu nằm trong volume
nên tạo lại container không mất dữ liệu, nhưng tuyệt đối không chạy
`docker compose down -v`, vì lệnh đó xoá volume.

## 11. Backup, snapshot và khôi phục

### 11.1 health-backup.sh — kiểm tra và backup nhẹ

Script `scripts/health-backup.sh` làm 2 việc: ghi log sức khoẻ vào
`~/health-check.log` (dung lượng ổ, danh sách container, kiểm tra
9 dịch vụ mong đợi) và tạo file backup nhẹ
`~/backup-YYYY-MM-DD.tar.gz` chỉ chứa cấu hình, feed và digest.
Lần chạy ngày 07/11/2026: ổ `/data` 20GB, chỉ dùng 124MB, còn trống
20GB; cả 10 container đều Up; file backup 18K, chứa 10 file, đã
kiểm chứng bằng cách giải nén vào `/tmp/restore-test` và thấy đủ
`feeds.json`, `bot.py` và các compose. Chạy script không có tuỳ chọn
`--prune` thì không xoá gì. Chỉ khi ổ đĩa còn dưới 3GB trống thì
mới dọn image Docker cũ.

### 11.2 backup-encrypted.sh — backup mã hoá

Script `scripts/backup-encrypted.sh` mã hoá file backup nhẹ bằng
AES-256, ghi file `~/backup-YYYY-MM-DD.tar.gz.enc` và file hash
`~/backup-YYYY-MM-DD.sha256`, rồi tự kiểm chứng bằng cách giải mã
vào `/tmp/restore-test`, so sánh hash với bản gốc, liệt kê nội dung,
rồi xoá bản giải mã tạm. Script dừng lại nếu chưa có file mật khẩu
`~/scripts/backup-passphrase.txt` trên máy. Bạn phải tự tạo file
mật khẩu đó bằng lệnh:

```bash
echo -n 'mat-khau-ban-chon' > ~/scripts/backup-passphrase.txt
chmod 600 ~/scripts/backup-passphrase.txt
```

Mật khẩu này không có trong repo, không gửi qua chat, và nếu quên
thì file `.enc` không giải mã được nữa. Giải mã tay khi cần:

```bash
openssl enc -d -aes-256-cbc -pbkdf2 \
  -in backup-YYYY-MM-DD.tar.gz.enc \
  -out backup-YYYY-MM-DD.tar.gz \
  -pass file:~/scripts/backup-passphrase.txt
```

### 11.3 Snapshot máy

Snapshot tạo trên dashboard InstaBox, đặt tên có ngày, ví dụ
`pro-v1-2026-11-07`, đã tạo và kiểm tra ngày 07/11/2026. Gói free
cho tối đa 5 snapshot, nên giữ lại 2 snapshot gần nhất và xoá
snapshot quá cũ khi sắp hết chỗ. Snapshot giữ nguyên volume và dữ
liệu app, nên là cách khôi phục đầy đủ nhất. Nhưng snapshot vẫn nằm
trong hệ thống InstaBox, chưa phải bản sao ngoài thật sự.

### 11.4 Offsite — phần còn thiếu

Muốn có bản sao ngoài thật sự, phải tải file mã hoá ra khỏi máy.
Ba hướng đã đề xuất, cần bạn chọn một:

| Hướng | Cách làm | Cần bạn làm |
|---|---|---|
| Tải về máy tính của bạn | Mở FileBrowser bằng link private, tải file `.enc` và file `.sha256` về, giữ cùng file mật khẩu ở nơi riêng | Tải tay sau mỗi lần backup |
| Rclone lên Google Drive / Dropbox | Cài rclone trên máy, bạn tự đăng nhập và cấp quyền cho rclone, script chỉ chạy lệnh copy file `.enc` lên đó | Đăng nhập và cấp quyền cho rclone |
| Chỉ dùng snapshot InstaBox | Không có bản offsite thật, chỉ có điểm khôi phục trong hệ thống InstaBox | Không cần làm gì thêm, nhưng chấp nhận rủi ro |

### 11.5 Diễn tập khôi phục

Diễn tập kiểm chứng chỉ đọc file backup, không ghi đè dữ liệu thật:
chạy backup mới, chạy script mã hoá để kiểm chứng giải mã và hash,
giải nén bản kiểm chứng vào `/tmp/restore-test` và kiểm tra có đủ
file không, ghi lại ngày, tên file, hash khớp hay không, có thiếu
file nào không. Khôi phục thật chỉ làm khi máy hỏng hoặc dữ liệu
mất, theo thứ tự: khôi phục snapshot máy trước, nếu không có
snapshot thì dựng lại từng app bằng compose trong repo, rồi nhập
OPML vào FreshRSS và nhập vault vào Vaultwarden từ bản xuất riêng.

## 12. Bảo mật: những quy tắc không bao giờ phá vỡ

1. Mọi cổng đều private, không bao giờ publish public.
2. Link private có token giữ kín như mật khẩu, không gửi token, mật
   khẩu, API key hay file `.env` qua chat, không đưa vào repo.
3. Không tự tạo tài khoản hay đặt mật khẩu thay bạn: tài khoản admin
   FreshRSS, Vaultwarden, Uptime Kuma, Linkding, Portainer, Trilium,
   Changedetection, mật khẩu FileBrowser, mật khẩu backup, token
   Telegram, API key InstaBox đều do bạn tự tạo.
4. Không tự lấy tài khoản lưu trữ của bạn để làm offsite backup.
5. Không vượt qua chặn của trang web để lấy feed, chỉ chẩn đoán lỗi
   và dùng feed công khai hợp lệ thay thế.
6. Không tạo hay xoá máy, không đổi gói hay thanh toán khi chưa có
   xác nhận của bạn.
7. Portainer có toàn quyền Docker, bắt buộc phải ở dạng private.
8. FileBrowser đã bị lưu trữ từ 01/09/2026, chỉ dùng qua link private.
9. Vaultwarden đang cho phép đăng ký tài khoản, phải tắt sau khi tạo
   tài khoản đầu tiên, xem mục 6.5 và 15.
10. Khi một app hỏi mã setup hay mã xác thực, lấy mã đó từ log của
    app hoặc từ email của bạn, không đoán mã.

## 13. Vận hành định kỳ: lịch tuần, lịch tháng

**Mỗi tuần, khoảng 10 phút:**

- Mở Trang tổng Homepage, kiểm tra 13 dịch vụ có hiện đủ không.
- Mở Uptime Kuma, kiểm tra có dịch vụ nào sập không.
- Chạy `bash ~/scripts/health-backup.sh`, xem `~/health-check.log`.
- Chạy `python3 ~/scripts/check-updates.py`, ghi lại app nào báo UPDATE.

**Mỗi tháng, khoảng 30 phút:**

- Xuất OPML từ FreshRSS sau khi đổi feed, lưu cùng file backup.
- Xuất vault từ Vaultwarden, lưu riêng.
- Chạy script backup mã hoá sau khi đã có file mật khẩu, tải file
  `.enc` về máy tính hoặc lên nơi lưu offsite đã chọn.
- Tạo snapshot mới, xoá snapshot quá cũ nếu sắp hết 5 snapshot.
- Kiểm tra dung lượng ổ bằng `df -h`, nếu dưới 3GB trống thì dọn
  image Docker cũ, không xoá volume.

**Mỗi khi đổi feed, thêm app hay đổi cấu hình:**

- Cập nhật `docs/INVENTORY.md` và Trang tổng.
- Chạy lại script kiểm tra sức khoẻ để xác nhận mọi thứ vẫn Up.
- Tạo snapshot mới nếu thay đổi lớn.

## 14. Xử lý sự cố: bảng tra nhanh

| Hiện tượng | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Máy Paused, không mở được link | Máy tự pause sau 30 phút idle | Resume trên dashboard, hoặc mở link public để đánh thức, đợi tới 45 giây |
| Máy đang cooldown, resume bị từ chối | Máy vừa chạy đủ 8 giờ liên tục | Đợi 5–20 phút rồi resume lại, đừng bấm liên tục |
| Link báo token không hợp lệ | Token bị đọc sai từ ảnh, hoặc token đã xoay | Xoay token từ terminal trên máy, dùng link mới trong file `*-link.txt` |
| Link private trả về 303 rồi 401 khi dùng curl | Cổng private chuyển hướng và cần cookie, curl theo chuyển hướng mà không giữ cookie sẽ bị từ chối | Mở bằng trình duyệt để kết luận, không chỉ dùng `curl -L` |
| Homepage trả về 400 "Host validation failed" | Thiếu biến `HOMEPAGE_ALLOWED_HOSTS` | Thêm biến đó vào compose, liệt kê localhost, 127.0.0.1 và host của cổng 3002, rồi tạo lại container |
| Feed CafeF trong FreshRSS báo lỗi, 0 bài | Server CafeF trả về 302 tới trang sorry, không trả RSS | Đổi URL feed trong FreshRSS sang link Google News `site:cafef.vn`, rồi Update feeds, kiểm tra bài mới có hiện không |
| WebApp hiện "chưa có digest" | Bot chưa chạy | Chạy `python3 bot.py --once` trên máy, kiểm tra file `webapp/digest.json` có 60 tin không |
| Script check-updates báo UNKNOWN | Không lấy được digest để so sánh, thường do định dạng manifest khác | Ghi lại là UNKNOWN, không kết luận app đó lỗi thời hay mới nhất, kiểm chứng tay bằng lệnh manifest cho image đó |
| Script backup mã hoá dừng lại, báo chưa có mật khẩu | Chưa tạo file `~/scripts/backup-passphrase.txt` | Tự tạo file mật khẩu trên máy với quyền 600, rồi chạy lại script, không nhờ ai tạo mật khẩu thay |
| Container Up nhưng localhost không trả lời | App đang khởi động, hoặc cấu hình sai | Đợi một lúc rồi kiểm tra lại, xem log bằng `docker compose logs`, kiểm tra lại compose |
| Ổ đĩa gần đầy | Image Docker cũ, log lớn, dữ liệu lớn | Chạy `df -h`, dọn image cũ bằng `docker image prune` khi còn dưới 3GB trống, không xoá volume |

## 15. Tối ưu hoá tiếp theo: thứ tự đề xuất

Các tối ưu hoá dưới đây chưa làm, xếp theo thứ tự giá trị mang lại
so với rủi ro. Không làm app nào trong danh sách này chỉ vì cho đủ
app, mà chỉ làm khi bạn duyệt từng ý.

### 15.1 Update 11 app đã báo có bản mới — làm đầu tiên, sau khi có snapshot mới

Script kiểm tra đã báo UPDATE cho 11 container, và tín hiệu đã được
kiểm chứng tay là đúng với `nginx:alpine`. Cách làm an toàn: tạo
snapshot mới trước, rồi update từng app một theo từng đợt, mỗi đợt
xong kiểm tra lại bằng localhost và kiểm tra lại trang qua link
private trước khi sang đợt tiếp theo. Đợt 1: WebApp, RSSHub, FreshRSS.
Đợt 2: Homepage, IT-Tools, Ntfy. Đợt 3: Vaultwarden, Linkding,
Trilium, Uptime Kuma, Changedetection, Portainer. Không update tất
cả cùng một lúc, vì nếu một app lỗi thì khó biết app nào gây ra.

### 15.2 Nối Ntfy vào Uptime Kuma và Changedetection

Sau khi bạn đã tạo tài khoản quản trị Uptime Kuma và đặt mật khẩu
Changedetection, cấu hình notification trong hai app đó trỏ tới Ntfy
bằng link private và tên topic trong `~/ntfy-topic.txt`. Lúc đó
Uptime Kuma sẽ báo khi dịch vụ sập, Changedetection sẽ báo khi trang
thay đổi, mà không cần chờ bot Telegram.

### 15.3 Tắt đăng ký Vaultwarden và dọn Trang tổng

Đổi `SIGNUPS_ALLOWED` thành `false` trong compose của Vaultwarden
sau khi bạn đã tạo tài khoản đầu tiên, rồi tạo lại container. Đồng
thời dọn 3 nhóm mặc định của Homepage là Developer, Social và
Entertainment, và bổ sung link Changedetection vào Trang tổng sau khi
đã có file link riêng cho app này.

### 15.4 Hoàn thiện nền tảng còn dang dở

Đây không phải app mới, mà là những việc đã chuẩn bị xong nhưng chưa
làm: tạo bot Telegram và file `~/news/.env`, bật daily bằng GitHub
Actions, sửa feed CafeF trong FreshRSS, thêm watch cho Changedetection,
thêm route RSSHub theo trang bạn thật sự muốn theo dõi. Làm xong
những việc này thì giá trị của các app đã có mới hiện ra hết.

### 15.5 Chọn nơi lưu offsite cho backup mã hoá

Xem bảng ở mục 11.4. Khi bạn chọn một hướng, mình sẽ viết thêm bước
đó vào script backup và hướng dẫn, còn hiện tại script chỉ tạo và
kiểm chứng file mã hoá trong máy.

### 15.6 Không làm: Paperless-ngx, app nặng, app 24/7

Paperless-ngx đã được bạn chọn bỏ qua ngày 07/11/2026, vì nặng
khoảng 1GB RAM, cần thêm cơ sở dữ liệu, tốn disk theo tài liệu tải
lên, và chỉ có giá trị khi bạn thật sự tải tài liệu lên làm kho tìm
kiếm. Cũng không làm app lưu ảnh, xem phim, chạy mô hình AI local,
hay app cần chạy 24/7 trên máy free, vì ổ chỉ 20GB và máy sẽ tự
pause.

---

*Hết tài liệu. Khi hệ thống thay đổi, cập nhật file này cùng lúc với
`docs/INVENTORY.md`, để tài liệu học tập luôn khớp với máy thật.*

---

## 16. Nhật ký cập nhật 07/11/2026: 3 đợt update 11 app

Ngày 07/11/2026, sau khi script kiểm tra báo UPDATE cho 11 app, toàn
bộ 11 app đã được update theo 3 đợt, sau khi tạo snapshot mới trước.

### 16.1 Trước khi update

- Snapshot mới `pro-v2-2026-11-07` tạo ngày 07/11/2026 lúc 22:25,
  đã kiểm tra thấy trong Dashboard, bên cạnh snapshot cũ
  `pro-v1-2026-11-07`. Đã dùng 2 trong 5 snapshot miễn phí.
- Script kiểm tra báo UPDATE cho 11 app, UNKNOWN cho Ntfy và
  FileBrowser. Tín hiệu đã kiểm chứng tay cho `nginx:alpine` lúc
  22:11: Id local `785835ea65db`, config digest trên registry
  `7cac34a4d72b`, khác nhau nên lúc đó thật sự có bản mới.

### 16.2 Đợt 1 — stack tin tức: WebApp, RSSHub, FreshRSS

- WebApp (nginx:alpine, image mới `713fc2ebfd92` ngày 05/11/2026) và
  RSSHub (image mới `3e1607718bc0` ngày 07/10/2026) đã pull và tạo lại,
  cả hai đều Up, cổng 8000 và 1200.
- FreshRSS không tạo lại vì image đã mới nhất, vẫn Up ở cổng 8080.
- Kiểm tra bằng localhost: FreshRSS 302 chuyển hướng tới trang đăng
  nhập, RSSHub 200, WebApp 200 và vẫn hiện digest 60 tin từ 31/10.
- Bài học: file compose trong `~/news` tên là
  `docker-compose.news.yml`, phải dùng `-f` khi chạy lệnh compose.

### 16.3 Đợt 2 — Homepage, IT-Tools, Ntfy

- Cả 3 app đều pull và tạo lại, đều Running, localhost trả về 200 ở
  các cổng 3002, 3004 và 3003, tiêu đề IT-Tools đã kiểm tra đúng.
- File compose của Homepage không bị tải lại, nên biến
  `HOMEPAGE_ALLOWED_HOSTS` giữ nguyên, không bị lỗi 400 trở lại.
- File `~/ntfy-topic.txt` không bị chạm tới, tên topic giữ nguyên.
- Không tạo snapshot mới cho đợt 2.

### 16.4 Đợt 3 — 6 app còn lại

- Vaultwarden và Changedetection pull và tạo lại, localhost trả về
  200 ở các cổng 8082 và 5000. Vaultwarden lúc kiểm tra đang ở trạng
  thái sức khoẻ đang khởi động nhưng đã trả lời 200.
- Linkding, Trilium, Uptime Kuma và Portainer pull xong nhưng image
  đã mới nhất nên container giữ nguyên, không tạo lại. Localhost:
  Linkding 302, Trilium 200, Uptime Kuma 302, Portainer 307, đều là
  chuyển hướng tới trang đăng nhập hoặc setup, đúng như mong đợi.
- Portainer chỉ được dùng để pull và tạo lại chính nó, không dùng để
  update app nào khác.

### 16.5 Kết luận sau 3 đợt

- Cả 11 app đều đã ở bản image mới nhất mà registry có lúc pull, và
  đều trả lời được trên localhost, không app nào lỗi.
- Script kiểm tra cập nhật bản cũ báo UPDATE cho cả những image vừa
  pull, nên lúc đó kết luận là script không đáng tin. Nguyên nhân đã
  tìm ra và sửa xong ngày 07/11/2026, xem mục 9.3: bản cũ so sánh Id
  của image, vốn là digest của danh sách manifest, với config digest
  của mục amd64, hai thứ khác loại nhau nên không bao giờ bằng nhau.
  Bản script mới so sánh digest của danh sách manifest với nhau bằng
  `docker buildx imagetools inspect`, đã kiểm chứng trên máy: báo OK
  cho cả 13 container, digest local bằng digest remote trong mọi
  trường hợp. Từ giờ tín hiệu của script lại đáng tin.
- Link private của Trang tổng đã cũ và phải xoay token ngày
  07/11/2026, link mới đã lưu vào file `~/homepage-link.txt` trên
  máy và đã gửi cho bạn trong đoạn chat, link cũ đã chết.
- Ba nhóm mặc định của Trang tổng đã dọn xong ngày 07/11/2026 bằng
  file `bookmarks.yaml` rỗng có chủ đích, xem mục 6.11.

---

*Hết tài liệu. Khi hệ thống thay đổi, cập nhật file này cùng lúc với
`docs/INVENTORY.md`, để tài liệu học tập luôn khớp với máy thật.*
