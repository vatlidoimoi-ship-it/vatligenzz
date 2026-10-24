# Nhập bảng điểm cả lớp

Truy cập **Học vụ → Tổng quan lớp → Nhập bảng điểm**. Chọn Học kì I hoặc
Học kì II, nhập TX1, giữa kì và cuối kì, sau đó chọn **Lưu thay đổi**.
Mỗi giáo viên chỉ sửa lớp mình quản lý; admin được sửa mọi lớp.

- Điểm từ 0 đến 10, tối đa một chữ số thập phân. Chấp nhận `8,5` và `8.5`.
- Ô trống là chưa có điểm; `0` là điểm hợp lệ. Tab chuyển giữa các ô.
- Hiện chỉ có một cột thường xuyên TX1; không mở nhập TX2/TX3.
- Điểm trung bình chỉ tính khi đủ ba điểm, theo `(TX1 + 2*GK + 3*CK)/6`,
  làm tròn một chữ số thập phân, 0,05 làm tròn lên.
- Lưu cả lớp chỉ cập nhật những học sinh có thay đổi. Mọi dòng được kiểm tra
  trước khi ghi; nếu có lỗi, không ghi một phần danh sách.
- Mỗi lần sửa lưu người thực hiện, thời điểm, điểm trước và sau trong cùng bản ghi.
- Khi có người khác sửa cùng bản ghi hoặc dữ liệu thay đổi trong lúc lưu,
  hệ thống từ chối ghi đè và yêu cầu tải lại sau khi ghi lại nội dung đang nhập.
- Chuyển trang khi còn điểm chưa lưu sẽ được trình duyệt nhắc nhở.

Hai học kì lưu riêng trong `physics_grades.json`. Điểm có sẵn từ Excel,
TX2/TX3/TX4/TX5 cũ và thông tin nguồn được giữ nguyên; trung bình nhập từ sổ cũ chỉ
được tính lại khi giáo viên thay đổi một trong ba điểm. Báo cáo lớp và báo cáo
từng học sinh có lựa chọn học kì; lịch sử làm đề vẫn hiển thị toàn bộ.

Kiểm tra cục bộ:

```powershell
python -m unittest discover -s tests -p test_gradebook.py
```

Ảnh duyệt giao diện nằm tại `../ANH/nhap-diem-tx1-local/`. Phiên bản này chưa push
hoặc deploy; việc kiểm tra dùng dữ liệu tách biệt, không ghi vào Supabase thật.
