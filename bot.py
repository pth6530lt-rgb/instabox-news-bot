#!/usr/bin/env python3
"""
Bot tin tức nhẹ, chỉ dùng thư viện chuẩn của Python.
- Đọc feeds.json
- Ghi tin đã gửi vào bot-data/seen.db để không gửi trùng
- Ghi bản tin mới nhất vào webapp/digest.json để WebApp trong Telegram đọc
- Gửi cảnh báo qua Telegram Bot API

Cách dùng:
  TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 bot.py --once
  TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python3 bot.py --poll
  python3 bot.py --daily
  python3 bot.py --daily --hours 48

Token và chat_id có thể để trong file .env cùng thư mục với bot.py
(TELEGRAM_BOT_TOKEN=..., TELEGRAM_CHAT_ID=...). Bot ưu tiên biến môi trường
thật, sau đó mới đọc .env. Không có token thì bot vẫn tạo digest.json,
chỉ không gửi Telegram.

Chế độ --daily: lấy feed mới, ghi digest.json, rồi gửi 1 bản tin tổng hợp
theo category (mỗi category tối đa 5 tin), thay vì gửi từng tin lẻ như --once.
Phù hợp để chạy 1 lần mỗi ngày bằng cron ngoài hoặc GitHub Actions wake máy.
"""
import argparse
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
FEEDS_FILE = BASE / "feeds.json"
DB_FILE = BASE / "bot-data" / "seen.db"
DIGEST_FILE = BASE / "webapp" / "digest.json"
OFFSET_FILE = BASE / "bot-data" / "offset.txt"

# Sửa danh sách này theo mã và chủ đề bạn theo dõi.
# Tin thuộc category QT-Macro luôn được gửi, vì số lượng ít và thường quan trọng.
IMPORTANT_KEYWORDS = [
    "fomc", "fed", "lãi suất", "vn-index", "vnindex", "chứng khoán",
    "vàng", "dầu", "bitcoin", "btc", "lạm phát", "cpi", "gdp",
    "khủng hoảng", "suy thoái", "tăng trưởng", "tỷ giá", "usd",
    "đổ vỡ", "phá sản", "ipo", "cổ tức", "lợi nhuận",
]

USER_AGENT = "NewsBot/1.0 (+personal RSS reader)"


def load_dotenv():
    """Đọc file .env cùng thư mục bot.py, không ghi đè biến môi trường thật."""
    env_file = BASE / ".env"
    if not env_file.exists():
        return
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception as exc:
        print(f"Không đọc được .env: {exc}", file=sys.stderr)


def clean_text(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_time(value):
    if not value:
        return 0
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt is None:
            return 0
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        pass
    try:
        text = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def item_text(tag, element):
    # Tìm thẻ con mà không phụ thuộc namespace.
    for child in element:
        local = child.tag.rsplit("}", 1)[-1]
        if local == tag:
            return child.text or ""
    return ""


def all_text(element):
    parts = []
    for node in element.iter():
        if node.text:
            parts.append(node.text)
        if node.tail:
            parts.append(node.tail)
    return " ".join(parts)


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    # RSS: channel/item, Atom: entry, RDF: item
    nodes = []
    for node in root.iter():
        local = node.tag.rsplit("}", 1)[-1]
        if local in ("item", "entry"):
            nodes.append(node)
    for node in nodes[:30]:
        title = clean_text(item_text("title", node))
        link = clean_text(item_text("link", node))
        if not link:
            # Atom link thường nằm ở thuộc tính href.
            for child in node:
                if child.tag.rsplit("}", 1)[-1] == "link" and child.get("href"):
                    link = child.get("href")
                    break
        summary = clean_text(
            item_text("description", node)
            or item_text("summary", node)
            or item_text("content", node)
        )
        if len(summary) > 400:
            summary = summary[:397] + "..."
        published = parse_time(
            item_text("pubDate", node)
            or item_text("published", node)
            or item_text("updated", node)
            or item_text("date", node)
        )
        if title and link:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": published,
                }
            )
    return items


def derive_country_topic(feed):
    """Suy ra quốc gia và chủ đề từ feed, ưu tiên trường có sẵn trong feeds.json."""
    category = feed.get("category", "")
    country = feed.get("country") or ("Việt Nam" if category.startswith("VN-") else "Quốc tế")
    if feed.get("topic"):
        topic = feed["topic"]
    elif "Macro" in category:
        topic = "Vĩ mô"
    elif "Trading" in category:
        topic = "Trading"
    else:
        topic = "Tin tức"
    return country, topic


def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen (
            id TEXT PRIMARY KEY,
            title TEXT,
            link TEXT,
            source TEXT,
            category TEXT,
            published INTEGER,
            created INTEGER
        )
        """
    )
    # Nâng cấp DB cũ: thêm cột summary, country, topic nếu chưa có.
    # DB trên máy đã tạo từ bản bot cũ sẽ tự nâng cấp ở lần chạy đầu tiên,
    # không cần xóa bot-data/seen.db.
    for column, definition in [
        ("summary", "TEXT"),
        ("country", "TEXT"),
        ("topic", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE seen ADD COLUMN {column} {definition}")
        except Exception:
            pass
    conn.commit()
    return conn


def is_important(category, title, summary):
    if category == "QT-Macro":
        return True
    text = (title + " " + summary).lower()
    return any(k in text for k in IMPORTANT_KEYWORDS)


def telegram_api(token, method, payload):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))


def send_telegram(token, chat_id, text):
    if not token or not chat_id:
        return False
    if len(text) > 4000:
        text = text[:3997] + "..."
    try:
        telegram_api(token, "sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        })
        return True
    except Exception as exc:
        print(f"Telegram lỗi: {exc}", file=sys.stderr)
        return False


def format_item(item):
    meta = " · ".join(
        part for part in [item.get("country", ""), item.get("topic", "")]
        if part
    )
    if meta:
        return f"📰 [{item['category']}] {item['source']}\n{meta}\n{item['title']}\n{item['link']}"
    return f"📰 [{item['category']}] {item['source']}\n{item['title']}\n{item['link']}"


def check_feeds(conn, token, chat_id, send_alerts=True):
    try:
        feeds = json.loads(FEEDS_FILE.read_text(encoding="utf-8"))["feeds"]
    except Exception as exc:
        print(f"Không đọc được feeds.json: {exc}", file=sys.stderr)
        return []
    new_alerts = []
    now = int(time.time())
    for feed in feeds:
        try:
            items = fetch_feed(feed["url"])
        except Exception as exc:
            print(f"Feed lỗi {feed['name']}: {exc}", file=sys.stderr)
            continue
        country, topic = derive_country_topic(feed)
        for item in items[:10]:
            item_id = item["link"]
            row = conn.execute(
                "SELECT 1 FROM seen WHERE id = ?", (item_id,)
            ).fetchone()
            if row:
                continue
            conn.execute(
                "INSERT INTO seen (id, title, link, source, category, published, created, summary, country, topic)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    item_id,
                    item["title"],
                    item["link"],
                    feed["name"],
                    feed["category"],
                    item["published"],
                    now,
                    item["summary"],
                    country,
                    topic,
                ),
            )
            record = {
                "title": item["title"],
                "link": item["link"],
                "summary": item["summary"],
                "source": feed["name"],
                "category": feed["category"],
                "published": item["published"],
                "country": country,
                "topic": topic,
            }
            if send_alerts and is_important(
                feed["category"], item["title"], item["summary"]
            ):
                new_alerts.append(record)
    conn.commit()
    # Giới hạn cảnh báo mỗi lần chạy để không spam.
    for record in new_alerts[:10]:
        send_telegram(token, chat_id, format_item(record))
    write_digest(conn)
    print(f"Đã kiểm tra xong. Tin quan trọng mới gửi: {len(new_alerts[:10])}")
    return new_alerts


def write_digest(conn):
    rows = conn.execute(
        "SELECT title, link, source, category, published, summary, country, topic FROM seen"
        " ORDER BY COALESCE(NULLIF(published, 0), created) DESC LIMIT 60"
    ).fetchall()
    items = []
    for title, link, source, category, published, summary, country, topic in rows:
        # Tin cũ trong DB chưa có country/topic/summary thì suy ra lại từ category.
        if not country or not topic:
            fallback_country, fallback_topic = derive_country_topic(
                {"category": category}
            )
            country = country or fallback_country
            topic = topic or fallback_topic
        items.append({
            "title": title,
            "link": link,
            "source": source,
            "category": category,
            "country": country,
            "topic": topic,
            "summary": summary or "",
            "published": published,
            "published_text": (
                datetime.fromtimestamp(published, tz=timezone.utc)
                .astimezone()
                .strftime("%d/%m %H:%M")
                if published else ""
            ),
        })
    DIGEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    DIGEST_FILE.write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "items": items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def latest_items(conn, category=None, limit=10):
    if category:
        rows = conn.execute(
            "SELECT title, link, source, category, country, topic FROM seen WHERE category = ?"
            " ORDER BY COALESCE(NULLIF(published, 0), created) DESC LIMIT ?",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT title, link, source, category, country, topic FROM seen"
            " ORDER BY COALESCE(NULLIF(published, 0), created) DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [
        {"title": t, "link": l, "source": s, "category": c, "country": co, "topic": to}
        for t, l, s, c, co, to in rows
    ]


def read_offset():
    try:
        return int(OFFSET_FILE.read_text().strip())
    except Exception:
        return 0


def write_offset(value):
    OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
    OFFSET_FILE.write_text(str(value), encoding="utf-8")


def handle_updates(conn, token, chat_id):
    offset = read_offset()
    try:
        result = telegram_api(token, "getUpdates", {
            "offset": offset,
            "timeout": 5,
            "allowed_updates": ["message"],
        })
    except Exception as exc:
        print(f"getUpdates lỗi: {exc}", file=sys.stderr)
        return
    if not result.get("ok"):
        return
    for update in result.get("result", []):
        update_id = update.get("update_id", 0)
        write_offset(update_id + 1)
        message = update.get("message", {})
        chat = message.get("chat", {})
        # Chỉ trả lời đúng người đã cấu hình, tránh người lạ dùng bot.
        if str(chat.get("id")) != str(chat_id):
            continue
        text = (message.get("text") or "").strip().lower()
        if text == "/start":
            reply = (
                "Chào bạn. Bot tin tức của bạn đã sẵn sàng.\n"
                "/moi - 10 tin mới nhất\n"
                "/trading - tin trading\n"
                "/macro - tin macro, Fed, lãi suất\n"
                "/vn - tin Việt Nam"
            )
            send_telegram(token, chat_id, reply)
        elif text == "/moi":
            items = latest_items(conn, limit=10)
            send_list(token, chat_id, items, "Tin mới nhất")
        elif text == "/trading":
            items = latest_items(conn, category="VN-Trading", limit=10)
            items += latest_items(conn, category="QT-Trading", limit=10)
            send_list(token, chat_id, items[:10], "Tin trading")
        elif text == "/macro":
            items = latest_items(conn, category="QT-Macro", limit=10)
            send_list(token, chat_id, items, "Tin macro")
        elif text == "/vn":
            items = latest_items(conn, category="VN-Tin tức", limit=5)
            items += latest_items(conn, category="VN-Trading", limit=5)
            send_list(token, chat_id, items[:10], "Tin Việt Nam")


def send_daily(conn, token, chat_id, hours=24):
    """Gửi bản tin daily theo category, mỗi category tối đa 5 tin mới nhất."""
    cutoff = int(time.time()) - hours * 3600
    rows = conn.execute(
        "SELECT title, link, source, category, published, created FROM seen"
        " WHERE COALESCE(NULLIF(published, 0), created) >= ?"
        " ORDER BY COALESCE(NULLIF(published, 0), created) DESC",
        (cutoff,),
    ).fetchall()
    grouped = {}
    for title, link, source, category, published, created in rows:
        grouped.setdefault(category, [])
        if len(grouped[category]) < 5:
            grouped[category].append({
                "title": title, "link": link, "source": source,
                "category": category,
            })
    if not grouped:
        print("Daily: không có tin mới trong khoảng thời gian đã chọn.")
        return
    today = datetime.now().astimezone().strftime("%d/%m/%Y")
    header = f"🗞️ Bản tin daily {today} ({hours}h qua, mỗi mục tối đa 5 tin)"
    if token and chat_id:
        send_telegram(token, chat_id, header)
    else:
        print(header)
    for category in sorted(grouped):
        lines = [f"📌 {category}"]
        for i, item in enumerate(grouped[category], 1):
            lines.append(f"{i}. {item['title']} ({item['source']})")
            lines.append(f"   {item['link']}")
        text = "\n".join(lines)
        if token and chat_id:
            send_telegram(token, chat_id, text)
        else:
            print(text)
    print(f"Daily: đã gửi {sum(len(v) for v in grouped.values())} tin, {len(grouped)} mục.")


def send_list(token, chat_id, items, heading):
    if not items:
        send_telegram(token, chat_id, f"{heading}: chưa có tin mới trong cơ sở dữ liệu.")
        return
    for item in items:
        send_telegram(token, chat_id, format_item(item))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Kiểm tra feed một lần rồi thoát")
    parser.add_argument("--poll", action="store_true", help="Chạy vòng lặp nhận lệnh Telegram")
    parser.add_argument("--daily", action="store_true", help="Lấy feed mới và gửi bản tin daily theo category")
    parser.add_argument("--hours", type=int, default=24, help="Số giờ nhìn lại cho --daily, mặc định 24")
    args = parser.parse_args()
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("Chưa có TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID: vẫn tạo digest, không gửi Telegram.")
    conn = init_db()
    if args.daily:
        check_feeds(conn, token, chat_id, send_alerts=False)
        send_daily(conn, token, chat_id, hours=args.hours)
        conn.close()
        return
    if args.poll and token and chat_id:
        print("Bot đang poll. Bấm Ctrl-C để dừng.")
        last_check = 0
        try:
            while True:
                now = time.time()
                if now - last_check >= 600:
                    check_feeds(conn, token, chat_id, send_alerts=True)
                    last_check = now
                handle_updates(conn, token, chat_id)
                time.sleep(10)
        except KeyboardInterrupt:
            print("Đã dừng bot.")
    else:
        check_feeds(conn, token, chat_id, send_alerts=True)
    conn.close()


if __name__ == "__main__":
    main()
