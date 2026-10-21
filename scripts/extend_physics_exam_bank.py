"""Build original practice exams for gaps in the Physics 10–12 question bank."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / 'data' / 'li.json'
BATCH = 'curriculum-gaps-2026-v1'


def question(stem, correct, distractors, explanation):
    assert len(distractors) == 3 and correct not in distractors
    return (stem, correct, distractors, explanation)


EXAMS = [
    ('10', 'hk1', 'Đo lường và chuyển động thẳng', [
        question('Đơn vị SI của tốc độ là gì?', 'm/s', ['km/h', 'm/s²', 'N'], 'Tốc độ bằng quãng đường chia thời gian.'),
        question('Một xe đi 120 m trong 10 s. Tốc độ trung bình là bao nhiêu?', '12 m/s', ['10 m/s', '1200 m/s', '0,083 m/s'], '120 : 10 = 12 m/s.'),
        question('Độ dịch chuyển của người đi 3 m về đông rồi 3 m về tây là bao nhiêu?', '0 m', ['3 m', '6 m', '-6 m'], 'Vị trí cuối trùng vị trí đầu.'),
        question('Trong chuyển động thẳng đều, đồ thị tọa độ theo thời gian có dạng nào?', 'Đường thẳng', ['Parabol', 'Đường tròn', 'Đường gấp khúc bất kì'], 'Tọa độ x = x₀ + vt là hàm bậc nhất của t.'),
        question('Một vật chuyển động thẳng đều với v = 5 m/s trong 4 s. Quãng đường đi được là bao nhiêu?', '20 m', ['1,25 m', '9 m', '40 m'], 's = vt = 5 × 4 = 20 m.'),
        question('Đại lượng nào có cả độ lớn và hướng?', 'Vận tốc', ['Quãng đường', 'Tốc độ', 'Thời gian'], 'Vận tốc là đại lượng vectơ.'),
        question('1 km/h xấp xỉ bằng bao nhiêu m/s?', '0,278 m/s', ['3,6 m/s', '10 m/s', '1000 m/s'], 'Đổi 1000 m trong 3600 s.'),
        question('Kết quả đo lặp lại 9,8 cm; 10,0 cm; 10,2 cm có giá trị trung bình là bao nhiêu?', '10,0 cm', ['9,8 cm', '10,2 cm', '30,0 cm'], 'Trung bình cộng ba lần đo là 10,0 cm.'),
        question('Một người đi 40 m về đông rồi 30 m về bắc. Độ lớn độ dịch chuyển là bao nhiêu?', '50 m', ['70 m', '10 m', '35 m'], 'Dùng định lí Pythagoras: √(40² + 30²) = 50 m.'),
        question('Hai xe đi ngược chiều với tốc độ 10 m/s và 15 m/s. Tốc độ tiến lại gần nhau là bao nhiêu?', '25 m/s', ['5 m/s', '10 m/s', '150 m/s'], 'Tốc độ tiến lại gần bằng tổng hai tốc độ.'),
    ]),
    ('10', 'hk1', 'Chuyển động biến đổi đều và rơi tự do', [
        question('Đơn vị SI của gia tốc là gì?', 'm/s²', ['m/s', 'N', 'kg·m/s'], 'Gia tốc là độ biến thiên vận tốc trong một đơn vị thời gian.'),
        question('Xe tăng tốc từ 2 m/s lên 10 m/s trong 4 s. Gia tốc là bao nhiêu?', '2 m/s²', ['3 m/s²', '8 m/s²', '32 m/s²'], 'a = (10 − 2)/4 = 2 m/s².'),
        question('Vật bắt đầu từ nghỉ, gia tốc 3 m/s². Vận tốc sau 4 s là bao nhiêu?', '12 m/s', ['7 m/s', '1,33 m/s', '24 m/s'], 'v = at = 3 × 4.'),
        question('Vật xuất phát từ nghỉ với gia tốc 2 m/s² trong 5 s. Quãng đường là bao nhiêu?', '25 m', ['10 m', '50 m', '5 m'], 's = at²/2 = 2 × 25/2.'),
        question('Vật đang đi 20 m/s và hãm với độ lớn gia tốc 4 m/s². Thời gian dừng là bao nhiêu?', '5 s', ['4 s', '16 s', '80 s'], 't = v₀/|a| = 20/4.'),
        question('Bỏ qua sức cản không khí, vật rơi tự do gần mặt đất có gia tốc hướng nào?', 'Thẳng đứng xuống dưới', ['Thẳng đứng lên trên', 'Theo phương ngang', 'Luôn ngược chiều vận tốc'], 'Gia tốc trọng trường hướng xuống dưới.'),
        question('Lấy g = 10 m/s². Vật thả rơi từ nghỉ trong 2 s có tốc độ bao nhiêu?', '20 m/s', ['5 m/s', '10 m/s', '40 m/s'], 'v = gt = 10 × 2.'),
        question('Lấy g = 10 m/s². Vật thả rơi từ nghỉ trong 3 s đi được bao nhiêu?', '45 m', ['15 m', '30 m', '90 m'], 's = gt²/2 = 10 × 9/2.'),
        question('Trên đồ thị vận tốc–thời gian, độ dốc của một đoạn thẳng biểu thị đại lượng nào?', 'Gia tốc', ['Quãng đường', 'Khối lượng', 'Lực ma sát'], 'Độ dốc Δv/Δt bằng gia tốc.'),
        question('Một xe giảm tốc đều từ 12 m/s xuống 4 m/s trong 2 s. Gia tốc là bao nhiêu?', '-4 m/s²', ['4 m/s²', '-8 m/s²', '8 m/s²'], 'a = (4 − 12)/2 = −4 m/s².'),
    ]),
    ('10', 'hk1', 'Các định luật Newton và lực ma sát', [
        question('Khi hợp lực tác dụng lên vật bằng 0, vật có thể ở trạng thái nào?', 'Đứng yên hoặc chuyển động thẳng đều', ['Chỉ đứng yên', 'Chỉ tăng tốc', 'Chuyển động tròn đều'], 'Định luật I Newton cho phép vật giữ nguyên vận tốc.'),
        question('Vật khối lượng 2 kg chịu hợp lực 6 N. Gia tốc là bao nhiêu?', '3 m/s²', ['12 m/s²', '4 m/s²', '0,33 m/s²'], 'a = F/m = 6/2.'),
        question('Đơn vị SI của lực là gì?', 'N', ['J', 'W', 'Pa'], 'Đơn vị lực là newton (N).'),
        question('Lấy g = 10 m/s². Trọng lượng của vật 3 kg là bao nhiêu?', '30 N', ['3 N', '13 N', '300 N'], 'P = mg = 3 × 10.'),
        question('Lực và phản lực theo định luật III Newton tác dụng lên đâu?', 'Hai vật khác nhau', ['Cùng một vật', 'Chỉ vật đứng yên', 'Chỉ vật chuyển động'], 'Cặp tương tác tác dụng lên hai vật khác nhau.'),
        question('Vật trượt trên mặt phẳng ngang; lực ma sát trượt hướng nào?', 'Ngược chiều chuyển động tương đối', ['Cùng chiều chuyển động tương đối', 'Luôn thẳng đứng lên', 'Luôn thẳng đứng xuống'], 'Ma sát trượt cản chuyển động tương đối giữa hai bề mặt.'),
        question('Lực ép 20 N, hệ số ma sát trượt 0,2. Độ lớn lực ma sát trượt là bao nhiêu?', '4 N', ['0,01 N', '20,2 N', '100 N'], 'Fms = μN = 0,2 × 20.'),
        question('Hai lực cùng phương, cùng chiều 5 N và 7 N có hợp lực bao nhiêu?', '12 N', ['2 N', '35 N', '7 N'], 'Hai lực cùng chiều có độ lớn hợp lực bằng tổng.'),
        question('Hai lực ngược chiều 10 N và 6 N có hợp lực độ lớn bao nhiêu?', '4 N', ['16 N', '60 N', '10 N'], 'Độ lớn hợp lực bằng hiệu hai độ lớn.'),
        question('Một vật khối lượng 5 kg có gia tốc 2 m/s². Hợp lực là bao nhiêu?', '10 N', ['2,5 N', '7 N', '25 N'], 'F = ma = 5 × 2.'),
    ]),
    ('10', 'hk2', 'Công, năng lượng và động lượng', [
        question('Đơn vị SI của công cơ học là gì?', 'J', ['N', 'W', 'kg'], 'Đơn vị công là joule (J).'),
        question('Lực 10 N cùng hướng chuyển dời 5 m thực hiện công bao nhiêu?', '50 J', ['2 J', '15 J', '500 J'], 'A = Fs = 10 × 5.'),
        question('Lực vuông góc với độ dịch chuyển thực hiện công bao nhiêu?', '0 J', ['Bằng Fs', 'Bằng F/s', 'Luôn âm'], 'A = Fs cos 90° = 0.'),
        question('Vật 2 kg chuyển động 3 m/s có động năng bao nhiêu?', '9 J', ['3 J', '6 J', '18 J'], 'Wđ = mv²/2 = 2 × 9/2.'),
        question('Lấy g = 10 m/s², vật 2 kg ở cao 5 m có thế năng trọng trường bao nhiêu so với mặt đất?', '100 J', ['10 J', '25 J', '50 J'], 'Wt = mgh = 2 × 10 × 5.'),
        question('Công suất của máy thực hiện công 600 J trong 3 s là bao nhiêu?', '200 W', ['1800 W', '603 W', '20 W'], 'P = A/t = 600/3.'),
        question('Động lượng của vật 2 kg chuyển động 4 m/s có độ lớn bao nhiêu?', '8 kg·m/s', ['2 kg·m/s', '4 kg·m/s', '16 kg·m/s'], 'p = mv = 2 × 4.'),
        question('Trong hệ kín, đại lượng nào được bảo toàn khi các vật tương tác?', 'Tổng động lượng', ['Động lượng từng vật', 'Tốc độ từng vật', 'Động năng trong mọi va chạm'], 'Tổng động lượng của hệ kín không đổi.'),
        question('Nếu tốc độ tăng gấp đôi và khối lượng không đổi, động năng thay đổi thế nào?', 'Tăng gấp 4', ['Tăng gấp 2', 'Không đổi', 'Giảm một nửa'], 'Động năng tỉ lệ với bình phương tốc độ.'),
        question('Hiệu suất của máy cho 80 J công có ích từ 100 J năng lượng cung cấp là bao nhiêu?', '80%', ['20%', '125%', '180%'], 'H = 80/100 × 100%.'),
    ]),
    ('11', 'hk1', 'Ôn tập dao động và sóng', [
        question('Trong dao động điều hòa, gia tốc luôn hướng về đâu?', 'Vị trí cân bằng', ['Biên dương', 'Biên âm', 'Theo chiều vận tốc'], 'a = -ω²x nên gia tốc hướng về vị trí cân bằng.'),
        question('Con lắc dao động điều hòa có chu kì 2 s. Tần số bằng bao nhiêu?', '0,5 Hz', ['2 Hz', '4 Hz', '0,25 Hz'], 'f = 1/T = 1/2 Hz.'),
        question('Sóng truyền với tốc độ 6 m/s và tần số 3 Hz. Bước sóng là bao nhiêu?', '2 m', ['0,5 m', '9 m', '18 m'], 'λ = v/f = 6/3 m.'),
        question('Trong môi trường truyền sóng cơ, đại lượng nào được truyền đi?', 'Năng lượng', ['Toàn bộ phần tử vật chất theo sóng', 'Khối lượng của nguồn', 'Điện tích của nguồn'], 'Sóng cơ truyền dao động và năng lượng.'),
        question('Hai nguồn kết hợp cần có đặc điểm nào?', 'Cùng tần số và độ lệch pha không đổi', ['Chỉ cùng biên độ', 'Chỉ cùng tốc độ', 'Tần số thay đổi liên tục'], 'Điều kiện nguồn kết hợp đảm bảo vân giao thoa ổn định.'),
        question('Trong sóng dừng, nút sóng có biên độ dao động bằng bao nhiêu?', '0', ['Cực đại', 'Bằng bước sóng', 'Bằng tốc độ truyền sóng'], 'Hai sóng giao thoa triệt tiêu tại nút.'),
        question('Khoảng cách giữa hai nút sóng liên tiếp bằng bao nhiêu?', 'Một nửa bước sóng', ['Một bước sóng', 'Hai bước sóng', 'Một phần tư bước sóng'], 'Các nút liền kề cách nhau λ/2.'),
        question('Ở vị trí cân bằng của dao động điều hòa không ma sát, tốc độ có độ lớn thế nào?', 'Cực đại', ['Bằng 0', 'Không xác định', 'Luôn bằng gia tốc'], 'Tại x = 0, toàn bộ cơ năng là động năng.'),
        question('Sóng điện từ truyền được trong môi trường nào?', 'Chân không', ['Chỉ chất rắn', 'Chỉ chất lỏng', 'Chỉ không khí'], 'Sóng điện từ không cần môi trường vật chất.'),
        question('Biên độ dao động tăng gấp đôi khi khối lượng và tần số góc không đổi. Cơ năng thay đổi thế nào?', 'Tăng gấp 4', ['Tăng gấp 2', 'Không đổi', 'Giảm một nửa'], 'Cơ năng E = mω²A²/2 tỉ lệ với A².'),
    ]),
    ('11', 'hk2', 'Ôn tập điện trường và mạch điện', [
        question('Đơn vị SI của cường độ điện trường là gì?', 'V/m', ['V·m', 'C/m', 'A/m'], 'E = F/q có đơn vị N/C, tương đương V/m.'),
        question('Điện tích 2 C đi qua tiết diện dây trong 4 s. Cường độ dòng điện là bao nhiêu?', '0,5 A', ['2 A', '4 A', '8 A'], 'I = q/t = 2/4 A.'),
        question('Điện trở 5 Ω có hiệu điện thế 10 V. Dòng điện qua điện trở là bao nhiêu?', '2 A', ['0,5 A', '5 A', '50 A'], 'I = U/R = 10/5 A.'),
        question('Hai điện trở 3 Ω và 6 Ω mắc nối tiếp có điện trở tương đương bao nhiêu?', '9 Ω', ['2 Ω', '3 Ω', '18 Ω'], 'Mắc nối tiếp: Rtđ = R₁ + R₂.'),
        question('Hai điện trở 3 Ω và 6 Ω mắc song song có điện trở tương đương bao nhiêu?', '2 Ω', ['3 Ω', '9 Ω', '18 Ω'], 'Rtđ = R₁R₂/(R₁ + R₂) = 18/9 Ω.'),
        question('Tụ điện có điện dung 2 μF đặt dưới hiệu điện thế 5 V tích điện bao nhiêu?', '10 μC', ['0,4 μC', '2,5 μC', '25 μC'], 'Q = CU = 2 × 5 μC.'),
        question('Công suất tiêu thụ của điện trở dưới U = 12 V, I = 2 A là bao nhiêu?', '24 W', ['6 W', '12 W', '144 W'], 'P = UI = 12 × 2 W.'),
        question('Điện trường đều có E = 100 V/m. Độ lớn lực tác dụng lên điện tích 0,02 C là bao nhiêu?', '2 N', ['0,02 N', '100 N', '5000 N'], 'F = |q|E = 0,02 × 100 N.'),
        question('Dòng điện không đổi 2 A chạy trong 5 s tải qua tiết diện bao nhiêu điện tích?', '10 C', ['0,4 C', '2,5 C', '20 C'], 'q = It = 2 × 5 C.'),
        question('Điện trở 4 Ω có dòng điện 3 A. Nhiệt tỏa ra trong 2 s là bao nhiêu?', '72 J', ['12 J', '24 J', '36 J'], 'Q = I²Rt = 3² × 4 × 2 J.'),
    ]),
    ('12', 'hk1', 'Cấu trúc chất và sự chuyển thể', [
        question('Trong chất rắn kết tinh, các hạt cấu tạo thường có đặc điểm nào?', 'Sắp xếp có trật tự trong mạng tinh thể', ['Chuyển động tự do khắp bình chứa', 'Không dao động', 'Không tương tác'], 'Các hạt dao động quanh vị trí cân bằng trong mạng tinh thể.'),
        question('Ở cùng điều kiện, chất nào thường có hình dạng và thể tích xác định?', 'Chất rắn', ['Chất khí', 'Hơi nước', 'Không khí'], 'Chất rắn giữ hình dạng và thể tích riêng.'),
        question('Quá trình chuyển từ thể rắn sang thể lỏng gọi là gì?', 'Nóng chảy', ['Đông đặc', 'Ngưng tụ', 'Thăng hoa'], 'Nóng chảy là rắn chuyển thành lỏng.'),
        question('Quá trình chuyển trực tiếp từ thể rắn sang thể khí gọi là gì?', 'Thăng hoa', ['Hóa lỏng', 'Đông đặc', 'Nóng chảy'], 'Thăng hoa bỏ qua pha lỏng.'),
        question('Trong khi một chất rắn kết tinh tinh khiết đang nóng chảy ở áp suất không đổi, nhiệt độ thường thế nào?', 'Không đổi', ['Tăng đều', 'Giảm đều', 'Bằng 0 °C với mọi chất'], 'Nhiệt cung cấp dùng để chuyển pha.'),
        question('Giọt nước đọng ngoài ly nước lạnh chủ yếu do quá trình nào?', 'Ngưng tụ hơi nước trong không khí', ['Nóng chảy của ly', 'Bay hơi từ mặt ngoài ly', 'Thăng hoa của nước'], 'Hơi nước gặp bề mặt lạnh và ngưng tụ.'),
        question('Sự bay hơi của chất lỏng diễn ra ở đâu?', 'Trên mặt thoáng ở nhiều nhiệt độ', ['Chỉ trong toàn bộ chất lỏng ở nhiệt độ sôi', 'Chỉ ở 0 °C', 'Chỉ trong bình kín'], 'Bay hơi xảy ra trên bề mặt chất lỏng.'),
        question('Sự sôi khác sự bay hơi thông thường ở điểm nào?', 'Xảy ra cả trong lòng và trên mặt thoáng', ['Chỉ xảy ra trên mặt thoáng', 'Không cần nhiệt', 'Không tạo hơi'], 'Khi sôi, bong bóng hơi hình thành trong lòng chất lỏng.'),
        question('Cùng nhiệt độ, các phân tử trong chất khí có đứng yên không?', 'Không, chúng chuyển động hỗn loạn', ['Có, tất cả đứng yên', 'Chỉ chuyển động khi có gió', 'Chỉ dao động tại nút mạng'], 'Chuyển động nhiệt của phân tử khí là hỗn loạn.'),
        question('Trong nhiệt kế thủy ngân, nhiệt độ tăng làm cột thủy ngân thường thế nào?', 'Dâng lên', ['Hạ xuống', 'Không đổi', 'Biến thành khí ngay'], 'Thủy ngân nở vì nhiệt khi nóng lên.'),
    ]),
    ('12', 'hk1', 'Nội năng và định luật I nhiệt động lực học', [
        question('Nội năng của một vật là tổng của những dạng năng lượng vi mô nào?', 'Động năng và thế năng tương tác của các phân tử', ['Động năng chuyển động cả vật và thế năng trọng trường', 'Chỉ động năng chuyển động cả vật', 'Chỉ điện năng'], 'Nội năng gắn với chuyển động và tương tác vi mô.'),
        question('Có thể thay đổi nội năng của vật bằng cách nào?', 'Truyền nhiệt hoặc thực hiện công', ['Chỉ truyền nhiệt', 'Chỉ thực hiện công', 'Chỉ đổi vị trí vật'], 'Hai cách cơ bản là truyền nhiệt và thực hiện công.'),
        question('Theo quy ước ΔU = Q + A, hệ nhận nhiệt 100 J và nhận công 20 J. ΔU bằng bao nhiêu?', '120 J', ['80 J', '-120 J', '5 J'], 'Cộng nhiệt và công mà hệ nhận: 100 + 20.'),
        question('Theo quy ước ΔU = Q + A, hệ tỏa 50 J và nhận công 80 J. ΔU bằng bao nhiêu?', '30 J', ['130 J', '-30 J', '-130 J'], 'Q = -50 J, A = +80 J nên ΔU = 30 J.'),
        question('Khi cọ xát hai bàn tay, nội năng tăng chủ yếu vì điều gì?', 'Công của lực ma sát chuyển thành nội năng', ['Nhiệt độ môi trường giảm', 'Khối lượng tay tăng', 'Áp suất khí quyển tăng'], 'Ma sát thực hiện công làm nóng tay.'),
        question('Nhiệt tự truyền từ vật nóng sang vật lạnh khi tiếp xúc cho đến khi nào?', 'Đạt cân bằng nhiệt', ['Cả hai cùng đạt 0 °C', 'Vật lạnh nóng hơn vật ban đầu', 'Cả hai ngừng chuyển động'], 'Truyền nhiệt dừng khi hai vật cùng nhiệt độ.'),
        question('Đơn vị SI của nhiệt lượng là gì?', 'J', ['°C', 'K', 'W'], 'Nhiệt lượng là năng lượng nên dùng joule.'),
        question('Một hệ không trao đổi nhiệt nhưng nhận 40 J công. Theo ΔU = Q + A, nội năng thay đổi bao nhiêu?', 'Tăng 40 J', ['Giảm 40 J', 'Không đổi', 'Tăng 80 J'], 'Q = 0 và A = +40 J.'),
        question('Nếu một hệ nhận nhiệt 70 J và tự thực hiện công 30 J, ΔU theo ΔU = Q + A là bao nhiêu?', '40 J', ['100 J', '-40 J', '-100 J'], 'Công do hệ thực hiện tương ứng A = -30 J.'),
        question('Đơn vị của nhiệt dung riêng là gì?', 'J/(kg·K)', ['J/kg', 'W/K', 'kg/J'], 'Từ Q = mcΔT suy ra đơn vị của c.'),
    ]),
    ('12', 'hk1', 'Nhiệt dung riêng và nhiệt chuyển thể', [
        question('Công thức tính nhiệt lượng làm một vật tăng nhiệt độ mà không chuyển pha là gì?', 'Q = mcΔT', ['Q = m/ cΔT', 'Q = c/(mΔT)', 'Q = mλ'], 'Nhiệt lượng tỉ lệ khối lượng, nhiệt dung riêng và độ tăng nhiệt độ.'),
        question('Nước 1 kg, c = 4200 J/(kg·K), tăng 2 °C cần nhiệt lượng bao nhiêu?', '8400 J', ['2100 J', '4200 J', '16800 J'], 'Q = 1 × 4200 × 2.'),
        question('Nếu giữ nguyên khối lượng và độ tăng nhiệt độ, chất có nhiệt dung riêng gấp đôi cần nhiệt lượng thế nào?', 'Gấp đôi', ['Một nửa', 'Không đổi', 'Gấp bốn'], 'Q tỉ lệ thuận với c.'),
        question('Đơn vị SI của nhiệt nóng chảy riêng là gì?', 'J/kg', ['J', 'J/(kg·K)', 'K/kg'], 'Từ Q = λm suy ra λ có đơn vị J/kg.'),
        question('Làm tan 0,5 kg nước đá ở nhiệt độ nóng chảy, λ = 3,4×10⁵ J/kg, cần bao nhiêu nhiệt?', '1,7×10⁵ J', ['3,4×10⁵ J', '6,8×10⁵ J', '1,7×10⁶ J'], 'Q = λm = 3,4×10⁵ × 0,5.'),
        question('Nhiệt hóa hơi riêng cho biết nhiệt cần để hóa hơi bao nhiêu chất lỏng ở nhiệt độ sôi?', '1 kg', ['1 g', '1 mol ở mọi chất', 'Toàn bộ chất lỏng bất kì'], 'Nhiệt hóa hơi riêng tính trên một đơn vị khối lượng.'),
        question('Hóa hơi hoàn toàn 2 kg chất lỏng tại nhiệt độ sôi với L = 2×10⁶ J/kg cần bao nhiêu nhiệt?', '4×10⁶ J', ['1×10⁶ J', '2×10⁶ J', '8×10⁶ J'], 'Q = Lm = 2×10⁶ × 2.'),
        question('Khi nước đá ở 0 °C đang nóng chảy, nhiệt cấp thêm chủ yếu dùng để làm gì?', 'Chuyển pha', ['Tăng ngay nhiệt độ của phần đá', 'Tăng khối lượng', 'Tạo công cơ học ngoài'], 'Nhiệt nóng chảy làm thay đổi trạng thái.'),
        question('Vật 2 kg có c = 500 J/(kg·K) nhận 5000 J. Độ tăng nhiệt độ là bao nhiêu?', '5 K', ['2 K', '10 K', '50 K'], 'ΔT = Q/(mc) = 5000/(2 × 500).'),
        question('Khi ngưng tụ ở cùng nhiệt độ, hơi nước sẽ thế nào?', 'Tỏa nhiệt', ['Thu nhiệt', 'Không trao đổi năng lượng', 'Luôn tăng nhiệt độ'], 'Ngưng tụ là quá trình tỏa nhiệt.'),
    ]),
    ('12', 'hk1', 'Khí lí tưởng và các định luật chất khí', [
        question('Nhiệt độ 27 °C xấp xỉ bao nhiêu kelvin?', '300 K', ['27 K', '246 K', '327 K'], 'T(K) = t(°C) + 273.'),
        question('Định luật Boyle cho lượng khí xác định ở nhiệt độ không đổi biểu thị quan hệ nào?', 'pV không đổi', ['p/V không đổi', 'pT không đổi', 'V/T không đổi khi áp suất thay đổi'], 'Trong quá trình đẳng nhiệt, áp suất tỉ lệ nghịch thể tích.'),
        question('Khí đẳng nhiệt có thể tích giảm một nửa. Áp suất biến đổi thế nào?', 'Tăng gấp đôi', ['Giảm một nửa', 'Không đổi', 'Tăng gấp bốn'], 'p₁V₁ = p₂V₂.'),
        question('Trong quá trình đẳng áp của lượng khí xác định, V/T tuyệt đối thế nào?', 'Không đổi', ['Tăng đều', 'Giảm đều', 'Bằng áp suất'], 'Định luật Charles: V/T = hằng số.'),
        question('Khí đẳng áp từ 300 K lên 600 K, thể tích ban đầu 2 lít. Thể tích cuối là bao nhiêu?', '4 lít', ['1 lít', '2 lít', '8 lít'], 'V tỉ lệ T tuyệt đối nên tăng gấp đôi.'),
        question('Trong quá trình đẳng tích của lượng khí xác định, p/T tuyệt đối thế nào?', 'Không đổi', ['Tỉ lệ nghịch T', 'Luôn bằng 0', 'Bằng V'], 'Áp suất tỉ lệ với nhiệt độ tuyệt đối khi V không đổi.'),
        question('Khí đẳng tích có p = 100 kPa tại 300 K. Tại 600 K, p bằng bao nhiêu?', '200 kPa', ['50 kPa', '100 kPa', '400 kPa'], 'p/T không đổi nên áp suất tăng gấp đôi.'),
        question('Phương trình trạng thái khí lí tưởng của n mol khí là gì?', 'pV = nRT', ['p/V = nRT', 'pT = nRV', 'V = nRpT'], 'Đây là phương trình trạng thái của khí lí tưởng.'),
        question('Trong phương trình pV = nRT, nhiệt độ T cần dùng thang nào?', 'Kelvin', ['Celsius', 'Fahrenheit', 'Bất kì thang nào'], 'Phương trình dùng nhiệt độ tuyệt đối.'),
        question('Lượng khí giữ V và n không đổi, nhiệt độ tuyệt đối giảm còn một nửa. Áp suất thế nào?', 'Giảm một nửa', ['Tăng gấp đôi', 'Không đổi', 'Giảm còn một phần tư'], 'p tỉ lệ thuận với T khi V, n không đổi.'),
    ]),
]


def build_exam(grade, semester, topic, raw, index):
    assert len(raw) == 10
    questions = []
    for number, (stem, correct, distractors, explanation) in enumerate(raw, 1):
        options = [correct, *distractors]
        shift = (number - 1) % 4
        options = options[shift:] + options[:shift]
        questions.append({'id': number, 'number': number, 'question': stem,
                          'options': dict(zip('ABCD', options)),
                          'correct_answer': 'ABCD'[options.index(correct)],
                          'explanation': explanation})
    return {'id': f'exam_li{grade}_gap_{index:02d}',
            'title': f'Vật lí {grade} · {topic}', 'grade': grade,
            'semester': semester, 'topic': topic, 'time_limit': 20,
            'description': '10 câu trắc nghiệm, 20 phút, thang điểm 10. Câu hỏi biên soạn mới theo kiến thức Vật lí phổ thông.',
            'batch_id': BATCH, 'created_by': None,
            'scoring_config': {'multiple_choice': {'weight_percent': 100, 'points': 10}},
            'questions': questions}


def build_bank(grades=None):
    current = json.loads(BANK.read_text(encoding='utf-8-sig'))
    for exam in current['exams']:
        if exam.get('batch_id') == 'pdf12-hk2-20x20-v1':
            exam['semester'] = 'hk2'
        elif exam.get('batch_id') == 'word11-20x20-v1':
            number = int(exam['id'].rsplit('_', 1)[-1])
            exam['semester'] = 'hk1' if number <= 10 else 'hk2'
        elif exam.get('batch_id') == 'word10-intro-v1':
            exam['semester'] = 'hk1'
    selected = []
    grade_counts = {}
    for entry in EXAMS:
        grade_counts[entry[0]] = grade_counts.get(entry[0], 0) + 1
        if grades is None or entry[0] in grades:
            selected.append(build_exam(*entry, grade_counts[entry[0]]))
    ids = {exam['id'] for exam in selected}
    existing = {exam['id']: exam for exam in current['exams']}
    for exam in selected:
        if exam['id'] in existing and existing[exam['id']].get('batch_id') != BATCH:
            raise ValueError(f'Exam ID collision: {exam["id"]}')
    current['exams'] = [exam for exam in current['exams']
                        if not (exam.get('batch_id') == BATCH
                                and (grades is None or exam.get('grade') in grades))
                        and exam['id'] not in ids] + selected
    BANK.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return selected


if __name__ == '__main__':
    import sys
    built = build_bank(set(sys.argv[1:]) or None)
    print(f'Wrote {len(built)} exams to {BANK}')
