# Video bài giảng cho giáo viên

Đường dẫn: `/teacher/videos`, có thẻ trên dashboard giáo viên.

Cập nhật 20/10/2026: admin có thể quản lý video toàn hệ thống. Video hoàn tất
có form xuất bản theo tên/lớp/chủ đề và nút gỡ xuất bản. Xem
[quyền học vụ và xuất bản video](admin-academics-video-publication.md).

1. Đăng nhập tài khoản giáo viên, dán đề Vật lí có đầy đủ dữ kiện.
2. Chờ AI tạo kịch bản. Chỉnh từng tiêu đề, chữ trên slide, lời đọc, công thức.
3. Chọn một trong năm mẫu rồi bấm dựng video.
4. Theo dõi tiến độ hoặc quay lại lịch sử. Video hoàn tất có nút phát có tiếng và mở/tải MP4.

Phiên bản tích hợp nhận đề bằng văn bản. Chưa tích hợp upload Word/ảnh hay các
chức năng Lịch sử của ứng dụng botvideo độc lập.

## Lưu trữ và vận hành

- Cần `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, Gemini API key hiện có của website.
- Tác vụ lưu riêng từng row `video/jobs/<id>` trong `app_json_store`.
- MP4 lưu trong bucket **private** `teacher-videos`, tối đa 50 MiB mỗi file.
  Khởi tạo một lần bằng `python scripts/setup_video_storage.py`.
- Mọi API kiểm tra tài khoản giáo viên và chủ sở hữu. POST có CSRF token.
  Link phát ký hạn một giờ chỉ cấp sau kiểm tra quyền; không trả service key cho trình duyệt.
- Worker nền nhận tác vụ bằng compare-and-swap `updated_at`, tuần tự từng video.
  Heartbeat 5 giây. Tác vụ bị ngắt quá 180 giây chuyển lỗi, không tự dựng lại gây tốn tài nguyên.
  Kịch bản đã lưu còn để giáo viên chủ động thử lại. Render có thể sleep khi website
  không có truy cập; tác vụ sẽ được kiểm tra lại khi dịch vụ thức dậy.
- Máy chủ khởi động tự chuẩn bị ffmpeg/ffprobe qua `static-ffmpeg` nếu chưa có PATH;
  tải Chromium nền nếu cần. Trong lúc khởi tạo, API render trả 503 để không nhận tác vụ
  thiếu công cụ. Máy chủ thiếu thư viện hệ thống Chromium dùng renderer PIL với font
  Noto Sans tiếng Việt đi kèm. Từ bản thiết kế mới, luồng dựng HTML sẽ dừng nếu
  Chromium lỗi, không âm thầm đổi sang sơ đồ PIL thiếu chính xác. Cần cài các thư
  viện Chromium của hệ điều hành nếu host thiếu chúng.
- Mặc định `TTS_PROVIDER=gtts`, `RENDER_WORKERS=1`, một thread encoder; có thể chỉnh env.
  Edge TTS vẫn có trong engine nhưng không phải lựa chọn mặc định do lỗi âm thanh ở lần kiểm tra.
- `VIDEO_WORKER_ENABLED=0` tắt worker khi chạy các phép kiểm tra tích hợp.
- Không giữ video trung gian sau khi tải thành công lên Storage. Audio cache cục bộ
  dùng lại trong vòng đời dịch vụ. Không commit cache/media/.env.

## Kiểm tra

`python tests/test_teacher_videos.py` kiểm tra quyền, CSRF, phân tách giáo viên,
chặn dựng trùng, lỗi công cụ, validation, claim tác vụ và lỗi Storage. Encoder và
API AI được thay thế trong kiểm thử: **không render video mới**.

Kiểm tra trình duyệt: mở studio, đọc lịch sử, sửa lời thuyết minh, gửi tác vụ,
bố cục desktop/mobile. Không xác nhận render thật trên Render vì ba lượt thử đã
được dùng hết trong đợt rà soát trước. Engine gốc có video cuối đã kiểm tra ở
thư mục botvideo ngoài repository.

## Nâng cấp thiết kế slide

- AI chia mỗi bước thành một ý chính, chữ slide ngắn hơn lời đọc và công thức riêng.
- Font Noto Sans thống nhất; tiêu đề 42 px, chữ 25–28 px, công thức 32 px trước khi
  tự co. Ngưỡng thấp nhất của khối chữ chính là 22 px; kiểm tra tràn chữ trước khi
  chụp ảnh/dựng, báo lỗi khi cần người dùng chia nội dung.
- Lựa chọn A–D thành thẻ, công thức trong khung, sơ đồ ở cột riêng. Chữ xuất hiện
  từng khối nhưng giữ kích thước bố cục để tránh nhảy dòng.
- SVG hỗ trợ mạch một điện trở hoặc hai điện trở nối tiếp/song song; lực có hướng
  chỉ định; sóng hình sin theo vị trí; thấu kính hội tụ với vật ngoài tiêu điểm;
  sơ đồ nhận nhiệt. Không vẽ các trường hợp thiếu dữ kiện/ngoài phạm vi hỗ trợ.
- Không đổi đơn vị ngầm khi suy luận sơ đồ; không tự vẽ N, P hay ampe kế.
- Giáo viên chọn bước và bấm **Xem slide trước khi dựng** để kiểm tra nội dung đang
  chỉnh. API preview có cùng kiểm tra chủ sở hữu và CSRF; tạo PNG, không tạo audio/MP4.
- Đã kiểm tra năm ảnh preview bằng Chromium: không tràn khối chữ, font chính ≥22 px,
  KaTeX không báo lỗi. Có kiểm thử riêng hình học sơ đồ và bảo vệ endpoint preview.
- Độ đúng của dữ kiện do AI suy ra vẫn cần giáo viên duyệt; không hứa tự vẽ đúng
  mọi dạng bài hoặc mọi mạch phức tạp.
