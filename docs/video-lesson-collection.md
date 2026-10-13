# Kho video bài giảng

Đường dẫn: `/documents` → **Video bài giảng có minh họa** → `/video-lessons`.
Giáo viên cũng có liên kết từ `/teacher/videos`. Học sinh và giáo viên đã đăng nhập
đều được xem bộ bài đã xuất bản; bản nháp và video cá nhân của giáo viên vẫn riêng tư.

Bộ đầu tiên gồm 20 video: 5 bài dao động, 5 bài con lắc đơn, 5 bài sóng và 5 bài
mạch điện. Mười bài cuối đối chiếu trực tiếp các Word trong `datatm`; manifest lưu
tên file, SHA-256, đoạn đề và chỉ số đoạn XML (bắt đầu từ 0, không phải số trang).

MP4 lưu trong bucket Supabase riêng tư `teacher-videos`. Trang phát xin signed URL
mới từ server; không lưu signed URL đã hết hạn vào dữ liệu. Catalog phiên bản hóa
tại `data/video_lessons.json`. Không thêm bộ video mẫu vào lịch sử của một giáo viên
ngẫu nhiên. Trang thư viện và redirect phát video không được service worker cache.

`scripts/build_video_collection.py` chứa lời giải, lời đọc, nguồn đề, kiểm tra số học
và quy trình xuất bản. Chạy không tham số để kiểm tra 60 ảnh slide. Chỉ chạy
`--render` khi đã có phạm vi render được người dùng yêu cầu. Mỗi bài có marker chống
render lặp; bài đã xong được bỏ qua. Nếu chỉ upload lỗi, có thể tiếp tục upload MP4
sẵn có. Không tự render lại bài đã bắt đầu nhưng thiếu MP4.

Các bài dùng kết luận viết riêng và `include_full_solution: false` để không tự thêm
slide tổng hợp đọc lại công thức. Chế độ mặc định của studio giáo viên được giữ nguyên.
Sơ đồ con lắc đơn ghi “Góc nhỏ” khi đề không cho số đo góc; số 6° chỉ xuất hiện ở bài
có dữ kiện đó. Sơ đồ lò xo là mô hình minh họa ngang, không phải mô phỏng chuyển động.

Ảnh bìa ban đầu lấy từ slide đầu. Prompt riêng và quy tắc đặt tên ảnh thay thế có tại
[video-cover-prompts.md](video-cover-prompts.md). Khi nhận ảnh mới, thay các file
`static/video_posters/vl-XX.png` và tăng phiên bản URL nếu cần làm mới cache trình duyệt.
