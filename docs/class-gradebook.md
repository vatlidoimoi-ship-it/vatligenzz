# Bảng điểm giáo viên nhập và tổng kết cả năm

Truy cập **Học vụ → Tổng quan lớp → Nhập bảng điểm**. Có ba bảng:

| Bảng | Cột giáo viên nhập | Công thức |
| --- | --- | --- |
| Học kì I | TX1, TX2, TX3, giữa kì, cuối kì | `(TX1 + TX2 + TX3 + 2*GK + 3*CK)/8` |
| Học kì II | TX1, TX2, TX3, TX4, giữa kì, cuối kì | `(TX1 + TX2 + TX3 + TX4 + 2*GK + 3*CK)/9` |
| Tổng kết | Không nhập; tự cập nhật từ hai học kì | `(HK1 + 2*HK2)/3` |

Điểm học kì và điểm năm làm tròn một chữ số thập phân bằng ROUND_HALF_UP.
Trung bình học kì chỉ xuất hiện khi đủ các điểm của học kì đó; cả năm phải đủ
cả HK1 và HK2. Không xem điểm còn thiếu là 0. Giá trị `0` vẫn là điểm hợp lệ.

Giáo viên nhập 0–10, tối đa một chữ số thập phân, nhận dấu phẩy hoặc dấu chấm.
Tab để chuyển ô; nút **Lưu thay đổi** ghi các học sinh đã sửa. Kiểm tra toàn
bộ danh sách trước khi ghi. Giáo viên chỉ sửa lớp được giao; admin sửa mọi lớp.
Mỗi lần sửa có người thực hiện, thời gian và điểm trước/sau. Bản ghi thay đổi
ở nơi khác sẽ bị từ chối ghi đè. Chuyển trang khi chưa lưu có nhắc nhở.

Sổ điểm giáo viên nhập tách khỏi điểm đề trắc nghiệm. Tổng quan lớp có hai
cột riêng; báo cáo từng em hỗ trợ chọn học kì hoặc cả năm. Hệ thống không
tự đưa điểm bài mô phỏng vào sổ điểm và không sinh điểm giáo viên.

Các bản nhập từ file có tên `mon_toan` chưa được giáo viên sửa không được
hiển thị thành điểm Vật lí. Bản gốc vẫn giữ trong dữ liệu. Khi giáo viên nhập
điểm Vật lí vào bản ghi đó, hệ thống giữ bản nhập ban đầu trong `original_import`
và lưu lịch sử chỉnh sửa. Điểm giáo viên nhập ở phiên bản TX1 cũ được giữ;
các cột mới còn thiếu phải được bổ sung để tính trung bình theo công thức mới.

Kiểm tra:

```powershell
python -m unittest discover -s tests -p test_gradebook.py
python -m unittest discover -s tests -p test_presentation_scores.py
```

Ảnh kiểm tra cục bộ: `../ANH/bang-diem-3-bang-local/`.
Phân bố bài mô phỏng được kiểm tra trước bằng
`python scripts/publish_presentation_scores.py`; chỉ có `--apply` mới ghi lên Supabase.
