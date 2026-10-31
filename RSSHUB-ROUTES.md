# Mở rộng RSSHub: thêm route đúng cách

RSSHub đã chạy trên máy ở cổng 1200, cùng mạng Docker với FreshRSS.
Khi thêm feed trong FreshRSS, bạn dùng địa chỉ nội bộ `http://rsshub:1200/...`,
vì FreshRSS tự tải feed từ phía server, không phải từ trình duyệt của bạn.

Quy tắc quan trọng: đừng đoán route. Vào tài liệu chính thức tại
https://docs.rsshub.app, tìm đúng trang bạn muốn, copy đúng route ở đó,
rồi mới thêm vào FreshRSS.

Một số dạng route thường dùng, thay `<...>` bằng giá trị thật từ tài liệu:

- Kênh Telegram công khai:
  `http://rsshub:1200/telegram/channel/<ten_kenh>`
- Kênh YouTube:
  `http://rsshub:1200/youtube/channel/<channel_id>`
- Người dùng YouTube:
  `http://rsshub:1200/youtube/user/<username>`

Sau khi thêm route vào FreshRSS, bấm Update feeds và kiểm tra feed có bài
mới và không báo lỗi hay không. Nếu route báo lỗi, quay lại tài liệu để
kiểm tra lại route, đừng thử đoán thêm nhiều biến thể.

RSSHub không dùng để vượt qua paywall, không dùng để lấy nội dung trả phí,
và không dùng cho trang chặn bot một cách cố ý. Nếu một trang không cho
RSSHub lấy, hãy dùng RSS chính thức của trang đó nếu có, hoặc bỏ qua nguồn đó.
