# Rà soát và sửa luồng vai trò — 20/10/2026

## Giai đoạn 1

- Phòng chat chỉ đọc tin thuộc phòng chung. Tin AI cũ được nhận diện qua các
  trường response/processed/quiz, tin mới có channel rõ ràng. Lịch sử AI chỉ trả
  tin của tài khoản đang đăng nhập. Không cho trả lời tin AI qua phòng chat.
- Giáo viên chỉ xóa đề do chính mình tạo; đề nhập sẵn không có chủ sở hữu không
  thể bị giáo viên xóa. Giao diện ẩn nút xóa khi không có quyền.
- API khóa học chỉ trả đáp án cho giáo viên sở hữu khóa học. Dữ liệu bài tập
  gửi tới trang luyện tập không chứa đáp án hoặc giải thích.
- Bài nộp và tiến độ phải tham chiếu bài học có thật; kiểm tra kiểu câu trả lời.
- Game lưu lượt chơi ở máy chủ, chấm từng câu theo thứ tự, từ chối gửi lại câu
  đã trả lời. Chỉ công bố đáp án sau khi nhận câu trả lời. Điểm bảng xếp hạng
  lấy từ kết quả máy chủ, không lấy score/total do trình duyệt gửi.
- Game có giới hạn 20 giây/câu cộng 2 giây truyền yêu cầu; lượt chơi hết hạn
  sau 2 giờ. Nút tải lại bắt đầu lượt mới. Kết quả có thể thử lưu lại nếu mạng lỗi.

## Giai đoạn 2

- Nút làm bài dùng JSON trong data attribute và escape nội dung khi dựng câu hỏi.
- Điểm tự chấm được lưu cùng bài nộp. Bài thiếu đáp án chuẩn chuyển sang chờ chấm.
- Giáo viên nhập điểm 0–100 và nhận xét; endpoint kiểm tra chủ sở hữu khóa học,
  bài học còn tồn tại và giá trị điểm hữu hạn. Học sinh xem lại tại Bài tập & kết quả.
- Bài đạt ít nhất 70/100 cập nhật tiến độ; hỗ trợ bỏ đánh dấu hoàn thành.
- Trắc nghiệm tự nộp ngay khi hết giờ và khóa lựa chọn. Máy chủ cho phép 10 giây
  nhận yêu cầu sau hạn; quá thời gian này vẫn từ chối. Chặn gửi trùng tại giao diện.
- Menu có tên đúng trang và đường tới kho video. Sửa menu điện thoại gây tràn
  ngang/đóng khi bấm nhóm liên kết; game quay về dashboard theo vai trò.
- Service worker v10 xóa cache cũ, không lưu HTML chứa dữ liệu tài khoản để đọc
  offline. Khi mất mạng dùng trang offline chung; tài nguyên tĩnh vẫn được cache.

## Kiểm chứng

Chạy tại thư mục vatligenzz, mỗi lệnh kiểm thử trong tiến trình riêng:

```powershell
python -B tests/test_role_flows.py
python -B tests/role_flows_browser.py
python -B tests/test_teacher_videos.py
python -B -m unittest discover -s tests -p test_video_library.py
python -B -m unittest discover -s tests -p test_storage_performance.py
```

- 14 kiểm thử mới: riêng tư tin AI, quyền giáo viên, dữ liệu bài học, điểm game,
  lưu điểm/nhận xét, giới hạn thời gian và dashboard theo vai trò.
- 23 kiểm thử sẵn có về video và lưu trữ đạt.
- Chrome ở 1366×900 và 390×844: làm bài, nộp, tải lại kết quả, giáo viên chấm lại,
  học sinh đọc nhận xét, chơi game, tự nộp đề khi hết giờ.
- Browser test dùng Chrome cài trên máy; có thể đặt TEST_BROWSER_CHANNEL=msedge.
  Kiểm thử dùng dữ liệu tạm, chặn kết nối AI/Supabase và tài nguyên CDN bên ngoài.

## Phạm vi

Chưa triển khai lên hosting hoặc kiểm tra AI/Supabase thật. Sau khi người dùng
chọn bổ sung cả hai chức năng, quyền quản lý học vụ của admin và xuất bản video
đã được triển khai; xem [hướng dẫn mở rộng](admin-academics-video-publication.md).
Khóa đồng thời hiện áp dụng trong một tiến trình, phù hợp Procfile một worker;
chưa thay kho JSON thành cơ sở dữ liệu giao dịch cho nhiều worker.
