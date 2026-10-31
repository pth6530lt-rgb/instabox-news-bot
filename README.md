# News bot cho InstaBox + Telegram daily

Repo này chứa code bot tin tức, **không chứa bí mật nào**.

- `bot.py` — bot đọc feed RSS, ghi `webapp/digest.json`, gửi Telegram.
  Chế độ `--daily` gửi 1 bản tin tổng hợp theo category, mỗi category tối đa 5 tin.
- `feeds.json` — 11 feed khởi điểm (VnExpress, Google News, Bloomberg, WSJ, Fed).
- `.github/workflows/daily.yml` — GitHub Actions chạy 07:00 giờ Việt Nam mỗi ngày,
  wake máy InstaBox rồi chạy `python3 bot.py --daily` trên máy.

## Cách dùng

1. Tạo repo GitHub mới, để **Public** (vì máy InstaBox sẽ tải file qua raw URL,
   repo private sẽ cần token và phức tạp hơn). Repo này không có token, mật khẩu
   hay API key nên public là an toàn.
2. Upload toàn bộ thư mục này lên repo, giữ nguyên cấu trúc:
   `bot.py` ở gốc repo, `feeds.json` ở gốc repo,
   `.github/workflows/daily.yml` ở đúng đường dẫn đó.
3. Ghi nhớ username và tên repo của bạn. Link raw sẽ là:

```
https://raw.githubusercontent.com/<username>/<repo>/main/bot.py
https://raw.githubusercontent.com/<username>/<repo>/main/feeds.json
```

Nếu branch mặc định của repo bạn là `master` thay vì `main`, đổi `main` thành
`master` trong 2 link trên.

4. Trên máy InstaBox, vào thư mục `~/news` và tải 2 file về:

```bash
cd ~/news
curl -O https://raw.githubusercontent.com/<username>/<repo>/main/bot.py
curl -O https://raw.githubusercontent.com/<username>/<repo>/main/feeds.json
python3 -m py_compile bot.py
python3 bot.py --once
ls -lh webapp/digest.json
```

Lần chạy `--once` này chưa cần token Telegram vẫn tạo được digest cho WebApp.
Sau đó mới tạo file `.env` trên máy để bot gửi Telegram, và tạo GitHub Secrets
để workflow daily chạy tự động (xem file hướng dẫn daily đi kèm).

## Không đưa lên repo

- File `.env` (chứa `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`)
- API key InstaBox, ID máy chỉ để trong GitHub Secrets, không để trong code
- Mật khẩu FreshRSS hay tài khoản InstaBox
