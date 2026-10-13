# Video bài giảng cho giáo viên

Đường dẫn: `/teacher/videos`, có thẻ trên dashboard giáo viên.

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
  Noto Sans tiếng Việt đi kèm; công thức phức tạp nên dùng môi trường có Chromium.
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
