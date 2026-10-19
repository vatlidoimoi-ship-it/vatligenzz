# Quản lý học vụ và xuất bản video

## Admin

Từ dashboard quản trị chọn **Quản lý học vụ**, hoặc chọn **Học vụ** trên menu.
Admin xem tất cả khóa học và tiến độ/bài nộp thuộc các khóa học được hỗ trợ;
tạo, sửa, xóa khóa học/tài liệu; quản lý đề, câu hỏi game; chấm điểm và nhận xét.
Khi sửa nội dung của giáo viên khác, chủ sở hữu gốc được giữ nguyên. Admin có
thể xóa đề nhập sẵn không có created_by; giáo viên vẫn chỉ xóa đề của mình.

Trang video của admin hiển thị video toàn hệ thống, cho phép xem và quản lý
kịch bản, dựng, xuất bản hoặc gỡ xuất bản. Học sinh không có quyền vào studio;
giáo viên không được đọc hoặc thay đổi tác vụ của giáo viên khác.

## Giáo viên xuất bản

1. Vào **Tạo video bài giảng**, mở video đã hoàn tất trong lịch sử.
2. Xem lại nội dung, điền tên bài, lớp 10/11/12, chủ đề và mô tả nếu cần.
3. Chọn **Xuất bản**. Video xuất hiện trong kho video và kho tài liệu/bài giảng.
4. **Lưu thay đổi** cập nhật metadata của cùng bài giảng, không tạo bản sao.
5. **Gỡ xuất bản** ẩn bài giảng khỏi học sinh nhưng giữ tác vụ và MP4 riêng.

Admin có thể thực hiện các bước trên đối với mọi video. Học sinh đăng nhập
lọc kho video theo lớp/chủ đề; ở kho tài liệu, dùng bộ lọc lớp và loại Bài giảng.
Video có sẵn trong catalog tĩnh được giữ nguyên; studio quản lý các video được
tạo qua studio, không chỉnh sửa các bản biên soạn trong catalog tĩnh.

## Lưu trữ

Không cần bảng/bucket mới. Metadata xuất bản nằm trong trường `publication`
của row `video/jobs/<id>` trong Supabase `app_json_store`, cập nhật qua compare-and-swap
`updated_at`. Chỉ trạng thái `complete` có `object_key` mới được xuất bản; object_key,
owner_id và nội dung kịch bản không lấy từ payload xuất bản của trình duyệt.

Thư viện ghép catalog tĩnh với video xuất bản, truy vấn có phân trang và chỉ lấy
metadata cần thiết. Trang xem/phát đọc lại trạng thái row trước khi cấp link ký.
Không đưa MP4 vào bucket công khai. Khi gỡ xuất bản, link ký đã cấp trước đó có
thể còn dùng đến hết hạn một giờ; các yêu cầu lấy link mới bị từ chối ngay.

Nếu kho xuất bản không truy cập được, thư viện báo 503; trang tài liệu vẫn có
tài liệu thường và catalog tĩnh, kèm thông báo chưa tải được video mới.

## Kiểm thử

```powershell
python -B tests/test_role_flows.py
python -B tests/test_video_publication.py
python -B tests/publication_browser.py
python -B tests/role_flows_browser.py
python -B tests/test_teacher_videos.py
python -B -m unittest discover -s tests -p test_video_library.py
python -B -m unittest discover -s tests -p test_storage_performance.py
```

Kiểm thử dùng thư mục dữ liệu tạm, kho video giả lập, không dựng/tải video mới
hoặc gọi Gemini/Supabase thật. Browser dùng Chrome ở 1366×900 và 390×844.
Luồng kiểm tra: giáo viên xuất bản → học sinh thấy trong hai kho → admin gỡ →
học sinh không xem/cấp link mới; kèm kiểm tra CSRF, quyền, video chưa hoàn tất,
metadata không hợp lệ, cập nhật đồng thời, lỗi kho và phân trang.
