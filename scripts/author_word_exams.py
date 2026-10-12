"""Explicitly authored content for the Word-based exams, with deterministic keys.

Each row is stem | correct option | three distractors | worked explanation | source keyword.
The six/eight/six difficulty matrix follows row order. No external model calls.
"""
import argparse
import json
import re
from build_docx_exams import WORK, PLAN, context_for, fold, validate, finalize_exam

CONTENT = {}

CONTENT[7] = '''
Sóng điện từ là loại sóng nào?|Sóng ngang|Sóng dọc|Sóng cơ dọc|Sóng cơ ngang|Trong sóng điện từ, các vectơ điện trường và từ trường vuông góc với phương truyền sóng; đây là sóng ngang.|sóng điện từ
Khác với sóng cơ, sóng điện từ có thể truyền trong môi trường nào sau đây?|Chân không|Chỉ chất rắn|Chỉ chất lỏng|Chỉ chất khí|Sóng điện từ không cần môi trường vật chất để truyền, nên có thể lan truyền trong chân không.|chân không
Trong chân không, tốc độ sóng điện từ xấp xỉ bằng bao nhiêu?|3 × 10⁸ m/s|3 × 10⁶ m/s|340 m/s|3 × 10⁸ km/s|Mọi sóng điện từ trong chân không đều truyền với tốc độ c xấp xỉ 3 × 10⁸ m/s.|sóng điện từ
Trong một sóng điện từ phẳng, điện trường và từ trường tại một điểm có phương như thế nào?|Vuông góc với nhau|Luôn cùng phương|Hợp nhau góc 45°|Không có quan hệ xác định|Điện trường, từ trường và phương truyền của sóng điện từ đôi một vuông góc.|điện từ
Đại lượng nào quyết định màu của ánh sáng đơn sắc khi xét các sóng trong vùng nhìn thấy?|Tần số|Biên độ của chùm sáng|Diện tích nguồn|Thời gian bật nguồn|Các thành phần ánh sáng đơn sắc có tần số khác nhau được cảm nhận thành các màu khác nhau.|ánh sáng
Sóng vô tuyến và tia X đều thuộc nhóm nào?|Sóng điện từ|Sóng cơ|Sóng âm|Sóng dọc trong không khí|Sóng vô tuyến và tia X thuộc phổ sóng điện từ, khác nhau chủ yếu về tần số và bước sóng.|điện từ
Khi ánh sáng đơn sắc truyền từ không khí vào thủy tinh, đại lượng nào không đổi?|Tần số|Tốc độ|Bước sóng|Tích tốc độ và tần số|Tần số do nguồn quyết định và giữ nguyên khi qua mặt phân cách; tốc độ và bước sóng thay đổi.|tần số
Hai sóng điện từ truyền trong chân không có tần số f và 2f. Tỉ số bước sóng λ₁/λ₂ bằng bao nhiêu?|2|1/2|1|4|Trong chân không λ = c/f. Do đó λ₁/λ₂ = (c/f)/(c/(2f)) = 2.|bước sóng
Tia hồng ngoại so với ánh sáng đỏ có đặc điểm nào?|Bước sóng dài hơn|Tần số lớn hơn|Tốc độ chân không lớn hơn|Không truyền được trong chân không|Hồng ngoại nằm phía bước sóng dài hơn ánh sáng đỏ trong phổ điện từ.|hồng ngoại
So với ánh sáng tím, tia tử ngoại có đặc điểm nào?|Tần số lớn hơn|Bước sóng dài hơn|Tốc độ chân không nhỏ hơn|Là sóng cơ|Tử ngoại nằm phía tần số cao hơn ánh sáng tím, tương ứng bước sóng ngắn hơn.|tử ngoại
Trong chân không, sóng vô tuyến và ánh sáng nhìn thấy có cùng đại lượng nào?|Tốc độ truyền|Tần số|Bước sóng|Chu kì|Chúng đều là sóng điện từ nên có cùng tốc độ c trong chân không dù tần số khác nhau.|chân không
Ánh sáng có tần số f truyền trong môi trường với tốc độ v. Biểu thức nào cho bước sóng?|λ = v/f|λ = vf|λ = f/v|λ = v²/f|Trong một chu kì T = 1/f, sóng đi được một bước sóng: λ = vT = v/f.|bước sóng
Một sóng điện từ có chu kì tăng gấp đôi. Tần số thay đổi như thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Tăng gấp bốn|Tần số và chu kì liên hệ f = 1/T; tăng T hai lần làm f giảm hai lần.|chu kì
Một chùm sáng đơn sắc vào môi trường có tốc độ truyền bằng 2/3 tốc độ trong chân không. Bước sóng bằng bao nhiêu lần bước sóng chân không?|2/3|3/2|1|4/9|Tần số không đổi, λ = v/f nên bước sóng cũng giảm còn 2/3 giá trị trong chân không.|bước sóng
Một đài phát sóng điện từ tần số 100 MHz. Lấy c = 3 × 10⁸ m/s, bước sóng trong chân không bằng bao nhiêu?|3 m|0,3 m|30 m|300 m|100 MHz = 10⁸ Hz. Bước sóng λ = c/f = 3 × 10⁸/10⁸ = 3 m.|bước sóng
Ánh sáng đơn sắc có bước sóng chân không 600 nm. Lấy c = 3 × 10⁸ m/s, tần số bằng bao nhiêu?|5 × 10¹⁴ Hz|5 × 10¹³ Hz|2 × 10¹⁴ Hz|1,8 × 10¹¹ Hz|600 nm = 6 × 10⁻⁷ m. Tần số f = c/λ = 5 × 10¹⁴ Hz.|bước sóng
Sóng điện từ tần số 2,4 GHz truyền trong chân không. Lấy c = 3 × 10⁸ m/s, bước sóng bằng bao nhiêu?|12,5 cm|1,25 cm|125 cm|0,125 cm|2,4 GHz = 2,4 × 10⁹ Hz. λ = c/f = 0,125 m = 12,5 cm.|bước sóng
Một sóng điện từ truyền với tốc độ 2 × 10⁸ m/s trong môi trường và có tần số 5 × 10¹⁴ Hz. Bước sóng trong môi trường bằng bao nhiêu?|400 nm|600 nm|250 nm|1000 nm|Bước sóng λ = v/f = 4 × 10⁻⁷ m = 400 nm. Phải dùng tốc độ trong môi trường đang xét.|bước sóng
Một tín hiệu vô tuyến đi từ trạm đến vệ tinh cách trạm 3,6 × 10⁷ m. Bỏ qua ảnh hưởng khí quyển, lấy c = 3 × 10⁸ m/s. Thời gian truyền một chiều bằng bao nhiêu?|0,12 s|0,24 s|1,2 s|12 s|Thời gian một chiều t = s/c = 3,6 × 10⁷/(3 × 10⁸) = 0,12 s.|sóng điện từ
Một rađa thu lại tín hiệu sau 20 μs kể từ khi phát. Lấy tốc độ sóng 3 × 10⁸ m/s và bỏ qua chuyển động mục tiêu. Khoảng cách từ rađa tới mục tiêu bằng bao nhiêu?|3 km|6 km|0,3 km|30 km|Tín hiệu đi và về nên 2d = ct. Suy ra d = 3 × 10⁸ × 20 × 10⁻⁶/2 = 3000 m = 3 km.|sóng điện từ
'''

CONTENT[8] = '''
Hai nguồn sóng kết hợp phải có đặc điểm nào?|Cùng tần số và độ lệch pha không đổi theo thời gian|Cùng biên độ nhưng tần số bất kì|Cùng công suất nhưng pha ngẫu nhiên|Chỉ cần đặt gần nhau|Hai nguồn kết hợp có cùng tần số và duy trì độ lệch pha không đổi, nhờ đó tạo giao thoa ổn định.|kết hợp
Hiện tượng giao thoa sóng thể hiện rõ tính chất nào?|Tính chất sóng|Tính chất dẫn điện|Tính chất từ của vật|Sự nóng chảy|Giao thoa là sự chồng chất tạo các vùng tăng cường và suy giảm ổn định, đặc trưng cho sóng.|giao thoa
Với hai nguồn kết hợp cùng pha, điều kiện cực đại giao thoa là gì, với k nguyên?|d₂ − d₁ = kλ|d₂ − d₁ = (k + 1/2)λ|d₂ − d₁ = λ/4 với mọi k|d₁ + d₂ = kλ|Hai sóng cùng pha tại điểm xét khi hiệu đường đi bằng số nguyên lần bước sóng.|cực đại
Với hai nguồn kết hợp cùng pha, điều kiện cực tiểu giao thoa là gì, với k nguyên?|d₂ − d₁ = (k + 1/2)λ|d₂ − d₁ = kλ|d₂ − d₁ = 2kλ|d₁ = d₂ với mọi điểm|Hiệu đường đi là số bán nguyên lần bước sóng làm hai sóng tới ngược pha, tạo cực tiểu.|cực tiểu
Hai nguồn cùng pha, cùng biên độ. Điểm trên đường trung trực đoạn nối hai nguồn là vị trí nào?|Cực đại giao thoa|Cực tiểu giao thoa|Luôn đứng yên|Không nhận được sóng|Điểm trên đường trung trực có d₁ = d₂ nên hiệu đường đi bằng 0, thỏa điều kiện cực đại.|trung trực
Tại một điểm, hai sóng tới cùng biên độ a và ngược pha. Biên độ tổng hợp bằng bao nhiêu?|0|a|2a|4a|Hai dao động cùng biên độ và ngược pha triệt tiêu nhau tại điểm đang xét.|biên độ
Tại một điểm, hai sóng tới cùng biên độ a và cùng pha. Biên độ tổng hợp bằng bao nhiêu?|2a|a|0|a/2|Khi hai dao động cùng pha, các li độ cộng cùng dấu và biên độ tổng hợp bằng tổng hai biên độ.|biên độ
Hai nguồn cùng pha tạo sóng bước sóng λ. Một điểm có hiệu đường đi 3λ thuộc loại nào?|Cực đại|Cực tiểu|Không thể giao thoa|Luôn có biên độ bằng một sóng tới|Hiệu đường đi 3λ là số nguyên lần bước sóng nên hai sóng tới cùng pha.|cực đại
Hai nguồn cùng pha tạo sóng bước sóng λ. Một điểm có hiệu đường đi 2,5λ thuộc loại nào?|Cực tiểu|Cực đại trung tâm|Cực đại bậc 2|Cực đại bậc 3|2,5λ = (2 + 1/2)λ là điều kiện để hai sóng tới ngược pha và tạo cực tiểu.|cực tiểu
Trên đoạn nối hai nguồn cùng pha, khoảng cách giữa hai cực đại liên tiếp bằng bao nhiêu?|λ/2|λ|2λ|λ/4|Khi dịch chuyển một đoạn Δx trên đoạn nối nguồn, hiệu đường đi đổi 2Δx. Hai cực đại liên tiếp có hiệu đường đi chênh λ nên Δx = λ/2.|giao thoa
Trên đoạn nối hai nguồn cùng pha, khoảng cách từ một cực đại tới cực tiểu gần nhất bằng bao nhiêu?|λ/4|λ/2|λ|2λ|Hiệu đường đi giữa cực đại và cực tiểu kề nhau chênh λ/2. Trên đoạn nối nguồn, hiệu đường đi đổi gấp đôi độ dịch chuyển nên khoảng cách là λ/4.|cực tiểu
Trong cùng môi trường không tán sắc, tăng gấp đôi tần số hai nguồn cùng pha thì khoảng cách các cực đại liên tiếp trên đoạn nối nguồn thay đổi thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Tăng gấp bốn|Tốc độ không đổi nên λ = v/f giảm hai lần; khoảng cách cực đại liên tiếp λ/2 cũng giảm hai lần.|bước sóng
Hai nguồn cùng pha, bước sóng 4 cm. Điểm có d₁ = 9 cm và d₂ = 17 cm là vị trí nào?|Cực đại|Cực tiểu|Không có sóng tới|Luôn đứng yên|Hiệu đường đi 17 − 9 = 8 cm = 2λ, thỏa điều kiện cực đại.|cực đại
Hai nguồn cùng pha, bước sóng 6 cm. Điểm có d₁ = 10 cm và d₂ = 19 cm là vị trí nào?|Cực tiểu|Cực đại trung tâm|Cực đại bậc 1|Cực đại bậc 2|Hiệu đường đi 9 cm = 1,5λ, là số bán nguyên lần bước sóng nên tạo cực tiểu.|cực tiểu
Hai nguồn cùng pha có tần số 20 Hz, truyền sóng với tốc độ 80 cm/s. Một điểm có hiệu đường đi 12 cm là vị trí nào?|Cực đại bậc 3|Cực tiểu|Cực đại bậc 2|Cực đại trung tâm|Bước sóng λ = v/f = 4 cm. Hiệu đường đi 12 cm = 3λ nên là cực đại bậc 3.|bước sóng
Hai nguồn cùng pha truyền sóng bước sóng 4 cm. Trên đoạn nối nguồn, hai cực đại cách nhau 3 khoảng cực đại liên tiếp. Khoảng cách giữa chúng bằng bao nhiêu?|6 cm|12 cm|3 cm|24 cm|Mỗi khoảng cực đại liên tiếp trên đoạn nối nguồn là λ/2 = 2 cm. Ba khoảng có độ dài 6 cm.|cực đại
Hai nguồn kết hợp cùng pha A, B cách nhau 20 cm, bước sóng 4 cm. Không tính A và B, trên đoạn AB có bao nhiêu cực đại?|9|10|11|5|Điểm bên trong AB có −20 < d₂ − d₁ < 20. Với d₂ − d₁ = 4k, ta có −5 < k < 5, gồm 9 số nguyên từ −4 đến 4.|cực đại
Hai nguồn cùng pha A, B cách nhau 20 cm, bước sóng 4 cm. Không tính hai nguồn, số cực tiểu trên đoạn AB bằng bao nhiêu?|10|9|11|5|Điều kiện −20 < (k + 1/2)4 < 20 cho −5,5 < k < 4,5. Có 10 giá trị nguyên k từ −5 đến 4.|cực tiểu
Trên đoạn nối hai nguồn cùng pha, khoảng cách giữa hai cực đại liên tiếp là 1,5 cm. Tần số nguồn bằng 40 Hz. Tốc độ truyền sóng bằng bao nhiêu?|120 cm/s|60 cm/s|30 cm/s|240 cm/s|Vì λ/2 = 1,5 cm nên λ = 3 cm. Tốc độ v = λf = 3 × 40 = 120 cm/s.|bước sóng
Hai nguồn cùng pha phát sóng có tốc độ 1,2 m/s và tần số 30 Hz. Trên đoạn nối nguồn, khoảng cách từ một cực đại đến cực tiểu gần nhất là bao nhiêu?|1 cm|2 cm|4 cm|8 cm|Bước sóng λ = 1,2/30 = 0,04 m = 4 cm. Khoảng cách từ cực đại đến cực tiểu kề là λ/4 = 1 cm.|cực tiểu
'''


CONTENT[9] = '''
Trong thí nghiệm Young, hai khe hẹp được chiếu bằng cùng một nguồn sáng đơn sắc nhằm mục đích gì?|Tạo hai nguồn sáng kết hợp|Tạo hai nguồn có tần số khác nhau|Loại bỏ hoàn toàn nhiễu xạ|Làm tốc độ ánh sáng tăng gấp đôi|Hai khe nhận ánh sáng từ cùng một nguồn giúp duy trì độ lệch pha ổn định, tạo hai nguồn kết hợp.|young
Trong thí nghiệm Young, khoảng vân là khoảng cách giữa hai vị trí nào?|Hai vân sáng liên tiếp|Vân sáng và vân tối gần nhất|Hai mép của màn|Hai khe hẹp|Khoảng vân i được định nghĩa là khoảng cách giữa hai vân sáng liên tiếp, cũng bằng khoảng cách hai vân tối liên tiếp.|khoảng vân
Với a là khoảng cách hai khe, D là khoảng cách tới màn, công thức khoảng vân trong gần đúng Young là gì?|i = λD/a|i = λa/D|i = aD/λ|i = λ/(aD)|Trong điều kiện D lớn hơn nhiều a, khoảng vân được tính bằng i = λD/a.|khoảng vân
Trong thí nghiệm Young đối xứng dùng ánh sáng đơn sắc, tại tâm màn có vân gì?|Vân sáng trung tâm|Vân tối thứ nhất|Luôn không có ánh sáng|Vân tối thứ hai|Tâm màn cách đều hai khe nên hiệu đường đi bằng 0; hai sóng tới cùng pha tạo vân sáng trung tâm.|vân sáng
Tọa độ vân sáng bậc k tính từ vân trung tâm trong thí nghiệm Young là gì?|x = ki|x = (k + 1/2)i với mọi k|x = k/i|x = i/k với mọi k|Vân sáng xuất hiện khi hiệu đường đi bằng kλ, nên tọa độ x = kλD/a = ki.|vân sáng
Vân tối gần vân sáng trung tâm nhất nằm cách tâm màn bao nhiêu?|i/2|i|2i|i/4|Vân tối thứ nhất ứng với hiệu đường đi λ/2 nên cách vân trung tâm một đoạn i/2.|vân tối
Giữ nguyên bước sóng và khoảng cách hai khe, đưa màn ra xa gấp đôi thì khoảng vân thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Tăng gấp bốn|Khoảng vân i = λD/a tỉ lệ thuận với D khi λ và a không đổi.|khoảng vân
Giữ nguyên bước sóng và khoảng cách tới màn, tăng khoảng cách hai khe gấp đôi thì khoảng vân thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Giảm còn một phần tư|Khoảng vân tỉ lệ nghịch với a, nên tăng a hai lần làm i giảm hai lần.|khoảng vân
Trong cùng một bố trí Young, thay ánh sáng bước sóng 0,4 μm bằng 0,6 μm thì khoảng vân tăng bao nhiêu lần?|1,5|2|2/3|2,25|Khi a và D cố định, tỉ số khoảng vân bằng tỉ số bước sóng: 0,6/0,4 = 1,5.|bước sóng
Một điểm trên màn có tọa độ x = 2,5i trong thí nghiệm Young đơn sắc. Đây là vị trí nào?|Vân tối thứ ba phía dương|Vân sáng bậc 2|Vân sáng bậc 3|Vân sáng trung tâm|Các vân tối phía dương lần lượt ở 0,5i; 1,5i; 2,5i. Vì vậy đây là vân tối thứ ba.|vân tối
Một điểm trên màn có tọa độ x = −3i. Đây là vị trí nào?|Vân sáng bậc −3|Vân tối thứ ba phía âm|Vân tối thứ tư phía âm|Vân sáng trung tâm|Tọa độ x bằng số nguyên lần khoảng vân nên là vân sáng; k = −3 biểu thị phía âm.|vân sáng
Nếu đồng thời tăng D và a lên ba lần, còn λ không đổi thì khoảng vân thay đổi thế nào?|Không đổi|Tăng ba lần|Giảm ba lần|Tăng chín lần|Tỉ số D/a được giữ nguyên nên i = λD/a không đổi.|khoảng vân
Trong thí nghiệm Young, một đoạn nối vân sáng bậc −2 và bậc +3 có độ dài bằng bao nhiêu?|5i|6i|i|2,5i|Hai tọa độ là −2i và 3i. Khoảng cách giữa chúng là 3i − (−2i) = 5i.|vân sáng
Khoảng cách từ vân tối thứ nhất đến vân tối thứ tư cùng phía so với vân trung tâm bằng bao nhiêu?|3i|4i|3,5i|2i|Hai vị trí lần lượt là 0,5i và 3,5i, nên khoảng cách bằng 3i.|vân tối
Trong thí nghiệm Young, λ = 0,6 μm, D = 2 m và a = 1,2 mm. Khoảng vân bằng bao nhiêu?|1 mm|0,1 mm|10 mm|2 mm|Đổi λ = 0,6 × 10⁻⁶ m và a = 1,2 × 10⁻³ m. i = λD/a = 10⁻³ m = 1 mm.|khoảng vân
Trong thí nghiệm Young, khoảng vân là 1,2 mm. Vân tối thứ ba phía dương cách vân trung tâm bao nhiêu?|3 mm|3,6 mm|2,4 mm|4,2 mm|Vân tối thứ ba ở x = (3 − 1/2)i = 2,5 × 1,2 = 3 mm.|vân tối
Khoảng cách từ vân sáng thứ nhất đến vân sáng thứ chín liên tiếp là 12 mm. Khoảng vân bằng bao nhiêu?|1,5 mm|1,33 mm|12 mm|0,75 mm|Chín vân sáng liên tiếp tạo tám khoảng vân. Vì vậy i = 12/8 = 1,5 mm.|khoảng vân
Trong thí nghiệm Young, a = 1 mm, D = 2 m. Vân sáng bậc 4 cách vân trung tâm 4 mm. Bước sóng bằng bao nhiêu?|0,5 μm|0,25 μm|1 μm|2 μm|i = x/4 = 1 mm. Suy ra λ = ia/D = 10⁻³ × 10⁻³/2 = 5 × 10⁻⁷ m = 0,5 μm.|bước sóng
Trong thí nghiệm Young có khoảng vân 2 mm, tính cả hai đầu đoạn màn từ x = −5 mm đến x = 5 mm, có bao nhiêu vân sáng?|5|6|7|4|Vân sáng thỏa x = 2k mm và −5 ≤ 2k ≤ 5. Các k là −2, −1, 0, 1, 2, gồm 5 vân.|vân sáng
Trong thí nghiệm Young, λ = 0,5 μm, a = 1 mm, D = 2 m. Khoảng cách từ vân sáng bậc −2 tới vân sáng bậc +4 bằng bao nhiêu?|6 mm|2 mm|4 mm|8 mm|Khoảng vân i = λD/a = 1 mm. Khoảng cách cần tìm bằng (4 − (−2))i = 6 mm.|khoảng vân
'''

CONTENT[10] = '''
Sóng dừng trên dây thường được tạo bởi sự chồng chất của hai sóng nào?|Sóng tới và sóng phản xạ cùng tần số truyền ngược chiều|Hai sóng khác tần số bất kì|Hai sóng cùng chiều không gặp nhau|Hai dao động chỉ tại hai đầu dây|Sóng tới và sóng phản xạ cùng tần số truyền ngược chiều giao thoa tạo các nút và bụng cố định.|sóng dừng
Nút sóng trên một dây có sóng dừng lý tưởng là điểm có biên độ thế nào?|Bằng 0|Lớn nhất|Bằng một bước sóng|Luôn bằng nửa biên độ bụng|Tại nút, hai sóng tới và phản xạ triệt tiêu, nên điểm đó không dao động.|nút sóng
Bụng sóng trên dây là điểm có đặc điểm nào?|Biên độ dao động cực đại|Li độ luôn bằng 0|Luôn đứng yên|Không chịu tác dụng của sóng|Bụng sóng là vị trí hai sóng tăng cường mạnh nhất, có biên độ cực đại.|bụng sóng
Khoảng cách giữa hai nút sóng liên tiếp bằng bao nhiêu?|λ/2|λ|λ/4|2λ|Trên một hình sóng dừng, hai nút kề nhau cách nhau nửa bước sóng.|nút
Khoảng cách từ một nút đến bụng gần nhất bằng bao nhiêu?|λ/4|λ/2|λ|2λ|Giữa hai nút liên tiếp có một bụng ở chính giữa, nên khoảng cách nút–bụng gần nhất là λ/4.|bụng
Đầu dây được giữ cố định trong sóng dừng là vị trí nào?|Nút sóng|Bụng sóng|Luôn dao động với biên độ cực đại|Luôn chuyển động cùng nguồn|Đầu cố định không dịch chuyển nên luôn là một nút của hệ sóng dừng.|cố định
Đầu dây tự do lý tưởng trong một hệ sóng dừng là vị trí nào?|Bụng sóng|Nút sóng|Điểm không có sóng phản xạ|Điểm có biên độ bằng 0|Tại đầu tự do, sóng phản xạ không đảo pha, nên đầu dây là bụng sóng.|tự do
Điều kiện sóng dừng trên dây dài L có hai đầu cố định là gì, n nguyên dương?|L = nλ/2|L = nλ/4 với mọi n|L = (2n − 1)λ|L = λ/n với mọi n|Hai đầu đều là nút nên chiều dài dây phải chứa số nguyên n nửa bước sóng.|hai đầu
Điều kiện sóng dừng trên dây dài L, một đầu cố định một đầu tự do, là gì, n nguyên dương?|L = (2n − 1)λ/4|L = nλ/2|L = nλ|L = λ/(4n)|Từ nút ở đầu cố định đến bụng ở đầu tự do phải có số lẻ một phần tư bước sóng.|tự do
Một dây hai đầu cố định có 4 bụng sóng. Tính cả hai đầu, số nút bằng bao nhiêu?|5|4|3|8|Mỗi bó sóng nằm giữa hai nút; với 4 bụng có 4 bó, nên tổng số nút là 4 + 1 = 5.|nút
Một dây hai đầu cố định đang dao động ở họa âm thứ ba. Số bụng sóng bằng bao nhiêu?|3|2|4|6|Với dây hai đầu cố định, họa âm thứ n tương ứng n bó sóng, tức n bụng.|bụng
Tần số cơ bản của dây hai đầu cố định, dài L và tốc độ sóng v, bằng bao nhiêu?|v/(2L)|v/L|2v/L|v/(4L)|Ở chế độ cơ bản, L = λ/2 nên λ = 2L. Vì f = v/λ, ta có f₁ = v/(2L).|hai đầu
Giữ tốc độ sóng không đổi, tăng chiều dài dây hai đầu cố định gấp đôi thì tần số cơ bản thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Giảm còn một phần tư|Tần số cơ bản f₁ = v/(2L) tỉ lệ nghịch với chiều dài dây.|sóng dừng
Một dây có hai đầu cố định và tần số cơ bản f₁. Tần số nào sau đây cũng tạo được sóng dừng?|3f₁|1,5f₁|0,5f₁|2,5f₁|Các tần số cho sóng dừng trên dây hai đầu cố định là fₙ = nf₁, với n nguyên dương.|hai đầu
Dây dài 1,2 m có hai đầu cố định, đang có 3 bụng sóng. Bước sóng bằng bao nhiêu?|0,8 m|0,4 m|1,2 m|2,4 m|Với 3 bụng, L = 3λ/2. Suy ra λ = 2L/3 = 0,8 m.|bụng
Sóng truyền trên dây dài 1 m với tốc độ 40 m/s. Hai đầu dây cố định. Tần số nhỏ nhất tạo sóng dừng bằng bao nhiêu?|20 Hz|40 Hz|10 Hz|80 Hz|Tần số cơ bản f₁ = v/(2L) = 40/(2 × 1) = 20 Hz.|hai đầu
Một dây hai đầu cố định có tần số cơ bản 20 Hz. Muốn trên dây có 3 bụng sóng, tần số phải bằng bao nhiêu?|60 Hz|30 Hz|40 Hz|80 Hz|Ba bụng tương ứng họa âm thứ ba, nên f₃ = 3f₁ = 60 Hz.|bụng
Dây hai đầu cố định dài 1 m, tốc độ sóng 40 m/s, tần số 100 Hz. Tính cả hai đầu, trên dây có bao nhiêu nút?|6|5|4|10|λ = v/f = 0,4 m; số bụng n = 2L/λ = 5. Do đó số nút là n + 1 = 6.|nút
Dây dài 0,75 m, một đầu cố định một đầu tự do, tốc độ sóng 60 m/s. Tần số cơ bản bằng bao nhiêu?|20 Hz|40 Hz|80 Hz|10 Hz|Ở chế độ cơ bản, λ = 4L = 3 m. Do đó f₁ = v/λ = 60/3 = 20 Hz.|tự do
Hai nút sóng liên tiếp cách nhau 20 cm. Sóng có tần số 50 Hz. Tốc độ truyền sóng trên dây bằng bao nhiêu?|20 m/s|10 m/s|40 m/s|5 m/s|Khoảng cách hai nút là λ/2 nên λ = 40 cm = 0,4 m. Tốc độ v = λf = 20 m/s.|nút
'''

CONTENT[11] = '''
Hai điện tích cùng dấu đứng yên tương tác với nhau như thế nào?|Đẩy nhau|Hút nhau|Không tương tác|Luôn chuyển động tròn quanh nhau|Theo quy luật tương tác điện, hai điện tích cùng dấu đẩy nhau, khác dấu hút nhau.|điện tích
Hai điện tích trái dấu đứng yên tương tác với nhau như thế nào?|Hút nhau|Đẩy nhau|Không tương tác|Chỉ tương tác khi tiếp xúc|Các điện tích trái dấu hút nhau mà không cần tiếp xúc trực tiếp.|điện tích
Đơn vị điện tích trong hệ SI là gì?|Coulomb (C)|Newton (N)|Volt (V)|Joule (J)|Điện tích được đo bằng coulomb, ký hiệu C; các đơn vị còn lại đo lực, điện thế và năng lượng.|điện tích
Lực tương tác giữa hai điện tích điểm đứng yên có phương nào?|Đường thẳng nối hai điện tích|Luôn thẳng đứng|Luôn vuông góc đường nối điện tích|Luôn nằm ngang|Lực Coulomb là lực hướng tâm theo đường nối hai điện tích, có chiều hút hoặc đẩy tùy dấu.|coulomb
Hai vật nhiễm điện có thể xem như điện tích điểm khi nào?|Kích thước của chúng rất nhỏ so với khoảng cách giữa chúng|Kích thước lớn hơn nhiều khoảng cách|Chỉ khi cả hai trung hòa|Chỉ khi chúng chạm nhau|Mô hình điện tích điểm phù hợp khi có thể bỏ qua kích thước của vật so với khoảng cách đang xét.|điện tích điểm
Độ lớn lực Coulomb trong chân không giữa q₁, q₂ cách nhau r là gì?|F = k·abs(q₁q₂)/r²|F = k·abs(q₁q₂)·r²|F = k·abs(q₁ + q₂)/r|F = k·r²/abs(q₁q₂)|Định luật Coulomb cho lực tỉ lệ với tích độ lớn hai điện tích và tỉ lệ nghịch với bình phương khoảng cách.|coulomb
Giữ nguyên hai điện tích, tăng khoảng cách gấp đôi thì độ lớn lực điện thay đổi thế nào?|Giảm bốn lần|Giảm hai lần|Tăng hai lần|Tăng bốn lần|F tỉ lệ nghịch với r², nên r tăng 2 lần làm F giảm 2² = 4 lần.|khoảng cách
Giữ nguyên khoảng cách, tăng độ lớn cả hai điện tích gấp đôi thì lực điện thay đổi thế nào?|Tăng bốn lần|Tăng hai lần|Giảm bốn lần|Không đổi|Tích độ lớn điện tích tăng 2 × 2 = 4 lần, nên lực Coulomb tăng 4 lần.|điện tích
Giữ nguyên điện tích và khoảng cách, chuyển từ chân không vào điện môi đồng nhất có hằng số điện môi tương đối 4 thì lực điện thế nào?|Bằng một phần tư lực ban đầu|Gấp bốn lần|Không đổi|Bằng một nửa|Trong điện môi, lực Coulomb giảm εr lần so với chân không. Với εr = 4, F = F₀/4.|điện môi
Hai quả cầu kim loại nhỏ giống nhau có điện tích +6 μC và −2 μC. Cho tiếp xúc rồi tách xa. Điện tích mỗi quả cầu bằng bao nhiêu?|+2 μC|+4 μC|−2 μC|+8 μC|Tổng điện tích được bảo toàn: 6 − 2 = 4 μC. Hai quả cầu giống nhau nên sau tiếp xúc mỗi quả nhận 2 μC.|điện tích
Một vật mất bớt electron và không có trao đổi hạt mang điện khác. Vật nhiễm điện loại nào?|Dương|Âm|Vẫn luôn trung hòa|Không thể xác định dù biết đã mất electron|Electron mang điện âm; mất electron làm vật thừa điện tích dương.|electron
Hai điện tích điểm tác dụng lực lên nhau. Độ lớn hai lực có quan hệ nào?|Bằng nhau|Tỉ lệ với khối lượng hai điện tích|Lực lên điện tích lớn luôn lớn hơn|Một lực có thể bằng 0 khi lực kia khác 0|Hai lực tương tác là cặp lực và phản lực, cùng độ lớn và ngược chiều theo định luật III Newton.|lực
Giữ nguyên hai điện tích, muốn độ lớn lực điện tăng chín lần phải thay khoảng cách thế nào?|Giảm ba lần|Tăng ba lần|Giảm chín lần|Tăng chín lần|Vì F tỉ lệ nghịch r², giảm r xuống r/3 làm lực tăng 3² = 9 lần.|khoảng cách
Hai điện tích +q và −q cách nhau r trong chân không. Thay −q bằng +q, độ lớn lực điện thay đổi thế nào?|Không đổi, nhưng chuyển từ hút sang đẩy|Tăng gấp đôi|Giảm một nửa|Lực bằng 0|Tích độ lớn điện tích không đổi nên độ lớn lực giữ nguyên; thay đổi dấu làm chiều tương tác đổi.|điện tích
Hai điện tích +2 μC và +3 μC cách nhau 0,3 m trong chân không. Lấy k = 9 × 10⁹ N·m²/C². Độ lớn lực điện bằng bao nhiêu?|0,6 N|6 N|0,06 N|1,8 N|F = k·abs(q₁q₂)/r² = 9 × 10⁹ × 6 × 10⁻¹²/0,09 = 0,6 N.|coulomb
Hai điện tích đều có độ lớn 2 μC trong chân không tương tác với lực 0,4 N. Lấy k = 9 × 10⁹ N·m²/C². Khoảng cách giữa chúng bằng bao nhiêu?|0,3 m|0,03 m|3 m|0,9 m|r² = kq²/F = 9 × 10⁹ × 4 × 10⁻¹²/0,4 = 0,09 m². Suy ra r = 0,3 m.|coulomb
Hai điện tích 1 μC và 3 μC cách nhau 0,3 m trong điện môi có εr = 3. Lấy k = 9 × 10⁹ N·m²/C². Độ lớn lực điện bằng bao nhiêu?|0,1 N|0,3 N|0,9 N|0,01 N|F = k·abs(q₁q₂)/(εr r²) = 9 × 10⁹ × 3 × 10⁻¹²/(3 × 0,09) = 0,1 N.|điện môi
Một vật nhiễm điện +3,2 nC do mất electron. Lấy độ lớn điện tích electron e = 1,6 × 10⁻¹⁹ C. Số electron vật đã mất bằng bao nhiêu?|2 × 10¹⁰|2 × 10⁹|5,12 × 10⁻²⁸|2 × 10¹¹|Số electron mất đi n = q/e = 3,2 × 10⁻⁹/(1,6 × 10⁻¹⁹) = 2 × 10¹⁰.|electron
Hai điện tích dương bằng nhau được giữ cố định tại A và B. Điện tích thử dương đặt đúng trung điểm AB chịu tổng lực điện bằng bao nhiêu?|0|Gấp đôi lực do một nguồn|Bằng lực do một nguồn|Không xác định dù hai nguồn bằng nhau|Hai nguồn cách điểm thử như nhau, gây hai lực đẩy bằng nhau nhưng ngược chiều, nên tổng lực bằng 0.|lực
Một điện tích chịu hai lực điện vuông góc, có độ lớn 3 N và 4 N. Độ lớn hợp lực bằng bao nhiêu?|5 N|7 N|1 N|12 N|Hai lực vuông góc nên độ lớn hợp lực F = √(3² + 4²) = 5 N.|lực
'''

CONTENT[12] = '''
Cường độ điện trường đặc trưng cho điện trường tại một điểm về phương diện nào?|Tác dụng lực lên điện tích|Khối lượng của nguồn|Nhiệt độ của môi trường|Thể tích của nguồn|Cường độ điện trường cho biết lực điện tác dụng trên một đơn vị điện tích thử dương.|cường độ điện trường
Nếu điện tích thử dương q chịu lực điện F, độ lớn cường độ điện trường bằng bao nhiêu?|E = F/q|E = Fq|E = q/F|E = F/q²|Theo định nghĩa, độ lớn E bằng độ lớn lực điện chia cho điện tích thử dương.|điện tích thử
Đơn vị nào sau đây là đơn vị của cường độ điện trường?|N/C|C/N|N·C|J·C|Cường độ điện trường có đơn vị N/C, tương đương V/m.|cường độ điện trường
Vectơ cường độ điện trường có chiều trùng với chiều lực điện tác dụng lên loại điện tích thử nào?|Điện tích dương|Điện tích âm|Mọi điện tích bất kể dấu|Vật trung hòa bất kì|Chiều của điện trường được quy ước là chiều lực điện tác dụng lên điện tích thử dương.|điện tích thử
Điện trường của một điện tích điểm dương có các đường sức hướng thế nào?|Ra xa điện tích|Về phía điện tích|Thành đường tròn quanh điện tích|Không có chiều xác định|Lực lên điện tích thử dương là lực đẩy, nên đường sức điện hướng ra khỏi nguồn dương.|đường sức
Điện trường của một điện tích điểm âm có các đường sức hướng thế nào?|Về phía điện tích|Ra xa điện tích|Song song nhau ở mọi nơi|Thành vòng tròn khép kín|Điện tích thử dương bị hút về nguồn âm nên vectơ điện trường hướng về nguồn.|đường sức
Thay điện tích thử dương q bằng 2q tại cùng điểm, không làm thay đổi nguồn, thì E thế nào?|Không đổi|Tăng gấp đôi|Giảm một nửa|Tăng gấp bốn|E phụ thuộc nguồn và vị trí, không phụ thuộc điện tích thử đủ nhỏ; lực tăng cùng tỉ lệ với q.|điện tích thử
Một điện tích âm được đặt trong điện trường. Lực điện có chiều nào so với E?|Ngược chiều E|Cùng chiều E|Luôn vuông góc E|Không phụ thuộc dấu điện tích|Từ vectơ F = qE, khi q âm, vectơ lực ngược hướng với vectơ cường độ điện trường.|cường độ điện trường
Giữ khoảng cách không đổi, tăng độ lớn điện tích nguồn điểm lên ba lần thì độ lớn E thế nào?|Tăng ba lần|Tăng chín lần|Giảm ba lần|Không đổi|Điện trường của điện tích điểm có E = k·abs(Q)/r², tỉ lệ thuận với độ lớn điện tích nguồn.|điện tích điểm
Đi xa điện tích điểm từ khoảng cách r đến 3r thì độ lớn E thay đổi thế nào?|Giảm chín lần|Giảm ba lần|Tăng chín lần|Không đổi|Vì E tỉ lệ nghịch bình phương khoảng cách, E ở 3r bằng E ở r chia cho 9.|điện tích điểm
Tại một điểm có hai điện trường thành phần, điện trường tổng hợp được xác định bằng cách nào?|Cộng vectơ các điện trường thành phần|Luôn cộng các độ lớn|Luôn lấy hiệu các độ lớn|Nhân hai độ lớn|Nguyên lý chồng chất điện trường yêu cầu cộng vectơ, có xét phương và chiều của từng thành phần.|điện trường
Vì sao hai đường sức của một điện trường tĩnh không cắt nhau?|Mỗi điểm chỉ có một hướng điện trường xác định|Điện trường luôn bằng 0|Đường sức là vật thể rắn|Điện tích không thể đứng yên|Nếu hai đường sức cắt nhau, tại giao điểm điện trường sẽ có hai hướng khác nhau, trái tính xác định của vectơ E.|đường sức
Tại trung điểm đoạn nối hai điện tích điểm dương bằng nhau, điện trường tổng hợp bằng bao nhiêu?|0|Gấp đôi điện trường một nguồn|Bằng điện trường một nguồn|Luôn vô hạn|Hai điện trường tại trung điểm có cùng độ lớn nhưng hướng ngược nhau nên triệt tiêu.|điện trường
Tại trung điểm đoạn nối hai điện tích +Q và −Q, điện trường tổng hợp hướng thế nào?|Từ +Q đến −Q|Từ −Q đến +Q|Vuông góc đoạn nối hai nguồn|Không có hướng vì luôn bằng 0|Điện trường do nguồn dương hướng ra xa và do nguồn âm hướng về nguồn, nên tại trung điểm chúng cùng hướng từ dương sang âm.|điện trường
Điện tích thử +2 μC chịu lực 0,006 N trong điện trường. Độ lớn E bằng bao nhiêu?|3000 N/C|300 N/C|12000 N/C|3 N/C|E = F/q = 0,006/(2 × 10⁻⁶) = 3000 N/C.|cường độ điện trường
Điện tích điểm Q = +4 nC nằm trong chân không. Lấy k = 9 × 10⁹ N·m²/C². Tại điểm cách Q 0,2 m, độ lớn E bằng bao nhiêu?|900 N/C|180 N/C|90 N/C|3600 N/C|E = kQ/r² = 9 × 10⁹ × 4 × 10⁻⁹/0,04 = 900 N/C.|điện tích điểm
Một điện tích q = −3 μC nằm trong điện trường đều 2000 N/C. Độ lớn lực điện bằng bao nhiêu?|0,006 N|6 N|0,0006 N|0,06 N|Độ lớn F = abs(q)E = 3 × 10⁻⁶ × 2000 = 0,006 N; dấu âm chỉ quyết định chiều lực.|cường độ điện trường
Hai điện trường vuông góc tại M có độ lớn 300 V/m và 400 V/m. Điện trường tổng hợp có độ lớn bao nhiêu?|500 V/m|700 V/m|100 V/m|120000 V/m|Do hai vectơ vuông góc, E = √(300² + 400²) = 500 V/m.|điện trường
Điện trường của một điện tích điểm tại khoảng cách 10 cm có độ lớn 3600 V/m. Tại khoảng cách 30 cm, độ lớn E bằng bao nhiêu?|400 V/m|1200 V/m|10800 V/m|32400 V/m|Khoảng cách tăng ba lần nên E giảm chín lần: E₂ = 3600/9 = 400 V/m.|điện tích điểm
Hai điện tích +1 nC và −1 nC cách nhau 20 cm trong chân không. Lấy k = 9 × 10⁹ N·m²/C². Tại trung điểm, độ lớn điện trường tổng hợp bằng bao nhiêu?|1800 V/m|900 V/m|0|450 V/m|Mỗi nguồn cách trung điểm 0,1 m nên gây E₁ = E₂ = 900 V/m. Hai vectơ cùng chiều nên tổng bằng 1800 V/m.|điện trường
'''

CONTENT[13] = '''
Điện trường đều là điện trường có vectơ cường độ điện trường như thế nào?|Giống nhau tại mọi điểm trong vùng xét|Chỉ có cùng độ lớn nhưng hướng tùy ý|Luôn bằng 0|Tăng theo khoảng cách tới nguồn|Trong điện trường đều, vectơ E có cùng phương, chiều và độ lớn tại mọi điểm thuộc vùng xét.|điện trường đều
Các đường sức của điện trường đều có hình dạng nào?|Các đường thẳng song song, cùng chiều và cách đều|Các đường tròn đồng tâm|Các đường thẳng cắt nhau|Các đường cong khép kín|Các đường thẳng song song cùng chiều biểu thị hướng không đổi; cách đều thể hiện cường độ không đổi.|điện trường đều
Giữa hai bản phẳng song song tích điện trái dấu, bỏ qua hiệu ứng mép, điện trường có tính chất nào?|Gần như đều|Luôn bằng 0|Có đường sức hình tròn|Chỉ tồn tại trên mặt bản|Xa mép bản, hai bản phẳng song song tạo điện trường gần như đều giữa chúng.|điện trường đều
Giữa hai bản phẳng trái dấu, đường sức điện có chiều nào?|Từ bản dương sang bản âm|Từ bản âm sang bản dương|Song song với mặt bản|Từ cả hai bản ra ngoài|Chiều điện trường là chiều lực lên điện tích thử dương, nên hướng từ bản dương đến bản âm.|điện trường đều
Trong điện trường đều giữa hai bản có khoảng cách d và độ lớn hiệu điện thế U, độ lớn E bằng bao nhiêu?|U/d|Ud|d/U|U/d²|Giữa hai bản phẳng với điện trường đều, U = Ed nên E = U/d.|điện trường đều
Một điện tích q trong điện trường đều E chịu lực có độ lớn bằng bao nhiêu?|abs(q)E|E/abs(q)|abs(q)/E|q²E²|Lực điện có vectơ F = qE, nên độ lớn bằng tích độ lớn điện tích và cường độ điện trường.|điện trường đều
Một electron chỉ chịu lực điện trong điện trường đều. Gia tốc hướng thế nào so với E?|Ngược chiều E|Cùng chiều E|Luôn vuông góc E|Luôn bằng 0|Electron mang điện âm nên lực điện và gia tốc của nó ngược chiều điện trường.|electron
Một hạt tích điện dương được thả không vận tốc đầu trong điện trường đều, bỏ qua trọng lực. Hạt chuyển động thế nào?|Nhanh dần đều theo chiều E|Thẳng đều theo chiều E|Nhanh dần đều ngược chiều E|Tròn đều|Lực qE không đổi, cùng chiều E, nên gia tốc không đổi; từ trạng thái nghỉ hạt nhanh dần đều theo chiều đó.|điện trường đều
Một hạt tích điện bay vào điện trường đều với vận tốc vuông góc E, chỉ chịu lực điện. Quỹ đạo trong vùng điện trường có dạng nào?|Parabol|Đường tròn|Đường thẳng vuông góc E|Đường elip|Chuyển động đều theo phương vuông góc E kết hợp với chuyển động biến đổi đều theo E tạo quỹ đạo parabol.|chuyển động
Với hạt bay vào điện trường đều theo phương vuông góc E và chỉ chịu lực điện, thành phần vận tốc theo phương ban đầu thế nào?|Không đổi|Tăng đều|Giảm đều|Luôn bằng 0|Lực điện chỉ theo phương E, nên gia tốc theo phương vận tốc ban đầu bằng 0.|chuyển động
Giữ U không đổi, tăng khoảng cách hai bản phẳng gấp đôi thì E giữa hai bản thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Giảm bốn lần|Trong gần đúng điện trường đều, E = U/d nên tăng d hai lần làm E giảm hai lần.|điện trường đều
Hai hạt có cùng khối lượng và điện tích lần lượt +q, −q trong cùng điện trường đều, bỏ qua lực khác. Hai gia tốc có quan hệ nào?|Cùng độ lớn, ngược chiều|Cùng độ lớn, cùng chiều|Một hạt không có gia tốc|Độ lớn luôn khác nhau|Độ lớn gia tốc là abs(q)E/m nên bằng nhau, nhưng dấu điện tích ngược nhau làm chiều gia tốc ngược nhau.|điện trường đều
Hạt tích điện dương chuyển động ngược chiều E và chỉ chịu lực điện. Trước khi dừng lại, hạt chuyển động thế nào?|Chậm dần đều|Nhanh dần đều|Thẳng đều|Tròn đều|Lực điện cùng chiều E nên ngược vận tốc ban đầu; gia tốc không đổi làm tốc độ giảm đều trước lúc dừng.|chuyển động
Một hạt tích điện dương đứng cân bằng trong điện trường đều thẳng đứng dưới tác dụng của trọng lực và lực điện. E hướng nào?|Thẳng đứng lên trên|Thẳng đứng xuống dưới|Nằm ngang|Không cần có điện trường|Trọng lực hướng xuống, nên lực điện phải hướng lên để cân bằng; q dương nên E cũng hướng lên.|điện trường đều
Hai bản phẳng cách nhau 3 cm, hiệu điện thế 150 V. Bỏ qua hiệu ứng mép. Cường độ điện trường giữa hai bản bằng bao nhiêu?|5000 V/m|50 V/m|450 V/m|0,0002 V/m|Đổi d = 0,03 m. E = U/d = 150/0,03 = 5000 V/m.|điện trường đều
Electron nằm trong điện trường đều E = 2000 V/m. Lấy e = 1,6 × 10⁻¹⁹ C. Độ lớn lực điện bằng bao nhiêu?|3,2 × 10⁻¹⁶ N|8 × 10⁻²³ N|3,2 × 10⁻²² N|1,25 × 10²² N|F = eE = 1,6 × 10⁻¹⁹ × 2000 = 3,2 × 10⁻¹⁶ N.|electron
Hạt có điện tích +2 μC, khối lượng 1 g nằm trong điện trường đều E = 500 V/m, bỏ qua lực khác. Gia tốc có độ lớn bao nhiêu?|1 m/s²|1000 m/s²|0,001 m/s²|250 m/s²|Lực F = 2 × 10⁻⁶ × 500 = 10⁻³ N; m = 10⁻³ kg. Do đó a = F/m = 1 m/s².|điện trường đều
Giọt dầu khối lượng 2 × 10⁻⁶ kg, điện tích +4 nC đứng cân bằng trong điện trường đều. Lấy g = 10 m/s². Độ lớn E bằng bao nhiêu?|5000 V/m|500 V/m|20000 V/m|0,0002 V/m|Cân bằng đòi hỏi qE = mg. E = 2 × 10⁻⁶ × 10/(4 × 10⁻⁹) = 5000 V/m.|điện trường đều
Electron khối lượng 9,1 × 10⁻³¹ kg, độ lớn điện tích 1,6 × 10⁻¹⁹ C chỉ chịu lực điện trong điện trường đều 910 V/m. Gia tốc có độ lớn bao nhiêu?|1,6 × 10¹⁴ m/s²|1,6 × 10¹¹ m/s²|9,1 × 10¹⁴ m/s²|1,456 × 10⁻¹⁶ m/s²|a = eE/m = (1,6 × 10⁻¹⁹ × 910)/(9,1 × 10⁻³¹) = 1,6 × 10¹⁴ m/s².|electron
Hạt q = 1 μC, m = 0,01 kg vào vùng điện trường đều E = 1000 V/m với vận tốc 2 m/s vuông góc E. Vùng điện trường dài 0,4 m theo phương vận tốc ban đầu, đủ rộng để hạt không chạm bản. Bỏ qua trọng lực. Độ lệch theo phương E khi ra khỏi vùng bằng bao nhiêu?|2 mm|2 cm|0,2 mm|20 cm|Thời gian trong trường t = 0,4/2 = 0,2 s. Gia tốc a = qE/m = 0,1 m/s². Độ lệch y = at²/2 = 0,002 m = 2 mm.|chuyển động
'''

CONTENT[14] = '''
Đơn vị điện thế trong hệ SI là gì?|Volt (V)|Coulomb (C)|Newton (N)|Ampere (A)|Điện thế được đo bằng volt; 1 V tương ứng 1 J/C.|điện thế
Hiệu điện thế U_AB được định nghĩa bằng biểu thức nào?|V_A − V_B|V_B − V_A|V_A + V_B|V_A·V_B|Theo quy ước, hiệu điện thế từ A đến B bằng điện thế tại A trừ điện thế tại B.|hiệu điện thế
Công của lực điện khi điện tích q đi từ A đến B được tính bằng biểu thức nào?|A_AB = qU_AB|A_AB = U_AB/q|A_AB = q/U_AB|A_AB = q²U_AB²|Hiệu điện thế đặc trưng khả năng sinh công trên một đơn vị điện tích, nên A_AB = qU_AB.|công
Công của lực điện tĩnh giữa hai điểm có phụ thuộc đường đi không?|Không, chỉ phụ thuộc điểm đầu và điểm cuối|Có, luôn tỉ lệ với độ dài đường đi|Chỉ phụ thuộc thời gian|Chỉ phụ thuộc tốc độ trung bình|Lực điện tĩnh là lực thế, nên công không phụ thuộc hình dạng quỹ đạo giữa hai điểm.|công
Khi điện tích di chuyển trên một mặt đẳng thế, công của lực điện bằng bao nhiêu?|0|Luôn dương|Luôn âm|Bằng độ lớn điện tích|Trên mặt đẳng thế, hiệu điện thế giữa hai điểm bằng 0 nên A = qU = 0.|điện thế
Với cùng mốc điện thế và thế năng, thế năng điện của điện tích q tại nơi có điện thế V là gì?|W = qV|W = V/q|W = q/V|W = q²/V|Điện thế bằng thế năng trên một đơn vị điện tích, nên thế năng W = qV.|thế năng
Điện thế tại A là 30 V, tại B là 10 V. U_AB bằng bao nhiêu?|20 V|40 V|−20 V|3 V|Theo định nghĩa hiệu điện thế, U_AB = V_A − V_B = 30 − 10 = 20 V.|hiệu điện thế
Nếu U_AB = 12 V thì U_BA bằng bao nhiêu?|−12 V|12 V|0|24 V|Đổi thứ tự hai điểm làm đổi dấu hiệu điện thế: U_BA = −U_AB.|hiệu điện thế
Điện tích dương đi từ nơi điện thế cao tới nơi điện thế thấp. Công của lực điện có dấu nào?|Dương|Âm|Luôn bằng 0|Không xác định dù biết q dương|A = q(V_đầu − V_cuối); cả q và hiệu điện thế đều dương nên công dương.|công
Điện tích âm đi từ nơi điện thế cao tới nơi điện thế thấp. Công của lực điện có dấu nào?|Âm|Dương|Luôn bằng 0|Luôn bằng độ giảm điện thế|Hiệu điện thế dương nhưng q âm, nên A = qU mang dấu âm.|công
Lực điện thực hiện công dương thì thế năng điện của hạt biến đổi thế nào?|Giảm|Tăng|Không đổi|Luôn tăng gấp đôi|Công của lực điện bằng độ giảm thế năng: A = W_đầu − W_cuối; A dương nghĩa là thế năng giảm.|thế năng
Điện tích chỉ chịu lực điện đi giữa hai điểm có cùng điện thế. Động năng cuối so với đầu thế nào?|Bằng nhau|Luôn lớn hơn|Luôn nhỏ hơn|Luôn bằng 0|Hiệu điện thế bằng 0 nên lực điện không sinh công tổng cộng; theo định lý động năng, động năng không đổi giữa hai điểm.|công
Trong điện trường đều, điện thế biến thiên theo chiều đường sức như thế nào?|Giảm dần|Tăng dần|Luôn bằng 0|Tăng rồi giảm tuần hoàn|Điện trường hướng theo chiều giảm điện thế; điện tích dương tự chuyển động theo chiều lực sẽ mất thế năng.|điện thế
Trong điện trường đều, dịch chuyển vuông góc với E thì hiệu điện thế giữa hai đầu dịch chuyển bằng bao nhiêu?|0|Ed với d là độ dài dịch chuyển|−Ed với mọi hướng|E/d|Hình chiếu của dịch chuyển lên phương E bằng 0, nên hiệu điện thế và công của lực điện đều bằng 0.|điện trường đều
Điện tích +2 μC đi từ A đến B, với U_AB = 50 V. Công của lực điện bằng bao nhiêu?|1 × 10⁻⁴ J|25 × 10⁶ J|1 × 10⁻² J|−1 × 10⁻⁴ J|A = qU = 2 × 10⁻⁶ × 50 = 10⁻⁴ J, dấu dương do điện tích và hiệu điện thế đều dương.|công
Điện tích −3 μC đi từ A đến B với U_AB = 20 V. Công của lực điện bằng bao nhiêu?|−6 × 10⁻⁵ J|6 × 10⁻⁵ J|−6 × 10⁻³ J|−60 J|A = qU = −3 × 10⁻⁶ × 20 = −6 × 10⁻⁵ J.|công
Lực điện thực hiện công 0,006 J khi điện tích +2 mC đi từ A đến B. U_AB bằng bao nhiêu?|3 V|3000 V|0,003 V|12 V|Đổi q = 2 × 10⁻³ C. U_AB = A/q = 0,006/0,002 = 3 V.|hiệu điện thế
Điện tích +4 μC tại điểm có điện thế −30 V, dùng cùng mốc thế năng, có thế năng bằng bao nhiêu?|−1,2 × 10⁻⁴ J|1,2 × 10⁻⁴ J|−7,5 × 10⁶ J|−120 J|W = qV = 4 × 10⁻⁶ × (−30) = −1,2 × 10⁻⁴ J; thế năng có thể âm tùy mốc chọn.|thế năng
Hai điểm A, B cách nhau 5 cm theo chiều điện trường đều E = 200 V/m, B nằm phía chiều E so với A. U_AB bằng bao nhiêu?|10 V|−10 V|1000 V|0,025 V|Theo chiều điện trường, điện thế giảm. U_AB = Ed = 200 × 0,05 = 10 V.|điện trường đều
Electron đi từ điểm có điện thế 0 V tới điểm có điện thế 100 V, chỉ chịu lực điện. Lấy e = 1,6 × 10⁻¹⁹ C. Động năng tăng bao nhiêu?|1,6 × 10⁻¹⁷ J|−1,6 × 10⁻¹⁷ J|1,6 × 10⁻²¹ J|100 J|Công điện A = q(V_đầu − V_cuối) = (−1,6 × 10⁻¹⁹)(−100) = 1,6 × 10⁻¹⁷ J. Độ tăng động năng bằng công này.|công
'''

CONTENT[15] = '''
Một tụ điện đơn giản gồm những bộ phận nào?|Hai vật dẫn đặt gần nhau, ngăn cách bởi lớp cách điện|Hai vật dẫn nối trực tiếp bằng dây kim loại|Một điện trở và một cuộn dây|Hai nam châm cùng cực|Tụ điện có hai bản dẫn điện được ngăn cách bởi chất cách điện, có khả năng tích điện.|tụ điện
Điện dung của tụ được xác định bằng biểu thức nào?|C = Q/U|C = QU|C = U/Q|C = Q²U|Điện dung đặc trưng khả năng tích điện, được tính bằng độ lớn điện tích một bản chia cho hiệu điện thế giữa hai bản.|điện dung
Đơn vị điện dung trong hệ SI là gì?|Farad (F)|Volt (V)|Coulomb (C)|Watt (W)|Đơn vị điện dung là farad; một tụ có C = 1 F tích điện 1 C khi hiệu điện thế là 1 V.|điện dung
Với tụ điện lý tưởng được tích điện từ nguồn, điện tích hai bản có quan hệ nào?|Cùng độ lớn, trái dấu|Cùng độ lớn, cùng dấu|Luôn bằng 0|Bản lớn luôn có điện tích lớn gấp đôi|Quá trình tích điện chuyển điện tích giữa các bản nên hai bản mang điện tích bằng nhau về độ lớn và trái dấu.|tụ điện
Đại lượng nào đặc trưng khả năng tích điện của tụ?|Điện dung|Điện trở dây nối|Thời gian phóng điện|Khối lượng dây dẫn|Điện dung càng lớn thì với cùng hiệu điện thế, tụ tích được điện tích càng lớn theo Q = CU.|điện dung
Năng lượng điện trường của tụ đã tích điện được tính bằng công thức nào?|W = CU²/2|W = CU/2|W = C/U²|W = 2C/U|Năng lượng dự trữ trong tụ bằng W = CU²/2, cũng có thể viết QU/2 hoặc Q²/(2C).|năng lượng
Giữ nguyên cấu tạo và điện môi của tụ, tăng U gấp đôi thì điện dung thế nào?|Không đổi|Tăng gấp đôi|Giảm một nửa|Tăng gấp bốn|Với tụ lý tưởng, điện dung do cấu tạo và điện môi quyết định, không phụ thuộc điện tích hay hiệu điện thế đặt vào.|điện dung
Giữ điện dung không đổi, tăng hiệu điện thế gấp đôi thì điện tích tụ thế nào?|Tăng gấp đôi|Không đổi|Giảm một nửa|Tăng gấp bốn|Điện tích tụ Q = CU, nên với C không đổi, Q tỉ lệ thuận U.|điện dung
Giữ điện dung không đổi, tăng hiệu điện thế gấp đôi thì năng lượng tụ thế nào?|Tăng gấp bốn|Tăng gấp đôi|Không đổi|Giảm bốn lần|Theo W = CU²/2, năng lượng tỉ lệ với bình phương hiệu điện thế nên tăng bốn lần.|năng lượng
Tụ ghi 10 μF – 50 V. Số 50 V cho biết điều gì?|Hiệu điện thế tối đa cho phép đặt lên tụ|Điện thế luôn có trên tụ kể cả khi chưa tích|Điện tích tối đa là 50 C|Tụ chỉ hoạt động đúng ở 50 V|Thông số điện áp cho biết giới hạn sử dụng để tránh phá hỏng lớp điện môi; không phải điện áp luôn có của tụ.|tụ điện
Trong tụ phẳng lý tưởng, giữ điện môi và khoảng cách không đổi, tăng diện tích đối diện hai bản gấp đôi thì C thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Tăng gấp bốn|Điện dung tụ phẳng tỉ lệ thuận với diện tích đối diện hai bản khi các yếu tố khác không đổi.|điện dung
Trong tụ phẳng lý tưởng, giữ điện môi và diện tích không đổi, tăng khoảng cách hai bản gấp đôi thì C thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Giảm bốn lần|Điện dung tụ phẳng tỉ lệ nghịch khoảng cách hai bản, nên khoảng cách tăng hai lần thì điện dung giảm hai lần.|điện dung
Ngắt tụ khỏi nguồn và cách điện hoàn toàn, điện dung giảm một nửa. Hiệu điện thế giữa hai bản thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Bằng 0|Khi cách điện, điện tích Q giữ nguyên. U = Q/C nên C giảm hai lần làm U tăng hai lần.|tụ điện
Tụ vẫn nối với nguồn có U không đổi. Nếu điện dung giảm một nửa, điện tích tụ thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Tăng gấp bốn|Nguồn giữ U không đổi, nên theo Q = CU, điện tích giảm cùng tỉ lệ với điện dung.|tụ điện
Một tụ được tích điện 45 μC ở hiệu điện thế 9 V. Điện dung bằng bao nhiêu?|5 μF|0,2 μF|405 μF|5 nF|Theo định nghĩa điện dung, C = Q/U = 45 μC/9 V = 5 μF.|điện dung
Tụ điện dung 10 μF được nối với nguồn 4,5 V. Độ lớn điện tích mỗi bản bằng bao nhiêu?|45 μC|2,22 μC|450 μC|0,45 μC|Điện tích Q = CU = 10 μF × 4,5 V = 45 μC.|điện dung
Tụ có điện dung 4 μF, được tích điện ở hiệu điện thế 10 V. Năng lượng điện trường bằng bao nhiêu?|0,2 mJ|0,02 mJ|2 mJ|20 mJ|W = CU²/2 = 4 × 10⁻⁶ × 100/2 = 2 × 10⁻⁴ J = 0,2 mJ.|năng lượng
Một tụ 4 μF dự trữ năng lượng 0,2 mJ. Độ lớn hiệu điện thế giữa hai bản bằng bao nhiêu?|10 V|5 V|20 V|100 V|U = √(2W/C) = √(2 × 0,2 × 10⁻³/(4 × 10⁻⁶)) = √100 = 10 V.|năng lượng
Tụ điện có C = 2 μF và điện tích Q = 20 μC. Năng lượng điện trường bằng bao nhiêu?|0,1 mJ|0,2 mJ|1 mJ|10 mJ|W = Q²/(2C) = (20 × 10⁻⁶)²/(4 × 10⁻⁶) = 10⁻⁴ J = 0,1 mJ.|năng lượng
Tụ của đèn flash có điện dung 100 μF và được tích điện tới 300 V. Nếu toàn bộ năng lượng tụ giải phóng trong 0,01 s, công suất trung bình của quá trình phóng điện bằng bao nhiêu?|450 W|45 W|900 W|4,5 W|W = CU²/2 = 100 × 10⁻⁶ × 300²/2 = 4,5 J. Công suất trung bình P = W/t = 4,5/0,01 = 450 W.|năng lượng
'''

CONTENT[16] = '''
Dòng điện là gì?|Dòng chuyển dời có hướng của các hạt mang điện|Mọi chuyển động nhiệt của phân tử|Chuyển động của các hạt trung hòa|Sự đứng yên của điện tích|Dòng điện được hình thành khi các hạt mang điện có chuyển dời có hướng, không chỉ chuyển động ngẫu nhiên.|dòng điện
Chiều dòng điện quy ước là chiều nào?|Chiều chuyển động có hướng của điện tích dương|Chiều chuyển động có hướng của electron trong mọi trường hợp|Chiều chuyển động của hạt trung hòa|Luôn từ dưới lên trên|Theo quy ước, chiều dòng điện là chiều chuyển dời của điện tích dương.|chiều dòng điện
Hạt tải điện chủ yếu trong kim loại là gì?|Electron tự do|Proton tự do|Neutron|Nguyên tử trung hòa|Các electron tự do chuyển dời có hướng tạo dòng điện trong kim loại; ion dương bị giữ ở nút mạng.|electron
Đơn vị cường độ dòng điện trong hệ SI là gì?|Ampere (A)|Volt (V)|Coulomb (C)|Ohm (Ω)|Cường độ dòng điện có đơn vị ampere, tương ứng coulomb điện lượng qua tiết diện trong một giây.|cường độ dòng điện
Cường độ dòng điện không đổi được tính bằng biểu thức nào?|I = Δq/Δt|I = Δq·Δt|I = Δt/Δq|I = Δq²/Δt|Cường độ dòng điện bằng điện lượng chuyển qua tiết diện trong một khoảng thời gian chia cho khoảng thời gian đó.|cường độ dòng điện
Dòng điện không đổi có đặc điểm nào?|Chiều và cường độ không đổi theo thời gian|Chiều đổi liên tục|Cường độ luôn tăng|Chỉ tồn tại trong một giây|Theo định nghĩa, dòng điện không đổi có chiều và cường độ giữ nguyên theo thời gian.|dòng điện không đổi
Trong kim loại, chiều chuyển dời có hướng của electron so với chiều dòng điện thế nào?|Ngược chiều|Cùng chiều|Luôn vuông góc|Không liên quan|Electron mang điện âm, nên chiều chuyển động có hướng của chúng ngược chiều dòng điện quy ước.|electron
Nếu cùng một điện lượng đi qua tiết diện trong thời gian giảm một nửa, cường độ trung bình thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Tăng gấp bốn|Theo I = Δq/Δt, giữ Δq mà giảm Δt hai lần thì I tăng hai lần.|cường độ dòng điện
Trong dây dẫn mang dòng điện không đổi, điện lượng qua tiết diện trong 2 phút so với trong 1 phút thế nào?|Gấp đôi|Bằng nhau|Bằng một nửa|Gấp bốn|Điện lượng q = It tỉ lệ thuận với thời gian khi dòng điện không đổi.|điện lượng
Một ampe kế phải được mắc thế nào để đo dòng điện qua một điện trở?|Nối tiếp với điện trở|Song song với điện trở|Không cần nối vào mạch|Chỉ nối một đầu với điện trở|Ampe kế mắc nối tiếp để dòng điện cần đo đi qua nó.|cường độ dòng điện
Đối với dây kim loại có mật độ electron tự do n, tiết diện S, tốc độ trôi v, công thức độ lớn dòng điện là gì?|I = neSv|I = neS/v|I = nv/(eS)|I = e/(nSv)|Trong một giây, số electron qua tiết diện là nSv; nhân điện tích mỗi electron e được I = neSv.|dịch chuyển
Trong cùng một dây kim loại có n và S không đổi, dòng điện tăng gấp đôi thì tốc độ trôi electron thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Tăng gấp bốn|Từ I = neSv, với n, e, S không đổi, tốc độ trôi v tỉ lệ thuận I.|dịch chuyển
Hai dây cùng vật liệu mang cùng dòng điện, dây thứ hai có tiết diện gấp đôi. Tốc độ trôi ở dây thứ hai so với dây thứ nhất thế nào?|Bằng một nửa|Gấp đôi|Bằng nhau|Gấp bốn|Từ v = I/(neS), khi I và n không đổi, tăng S hai lần làm tốc độ trôi giảm hai lần.|dịch chuyển
Hai tiết diện khác nhau của cùng một dây không phân nhánh mang dòng điện ổn định có cường độ dòng điện thế nào?|Bằng nhau|Luôn tỉ lệ với diện tích tiết diện|Luôn tỉ lệ nghịch chiều dài dây|Một tiết diện không có dòng điện|Ở trạng thái ổn định, điện tích không tích lũy giữa hai tiết diện, nên điện lượng qua mỗi tiết diện trong cùng thời gian bằng nhau.|dòng điện
Trong 5 s, có điện lượng 10 C qua một tiết diện dây dẫn. Cường độ dòng điện trung bình bằng bao nhiêu?|2 A|50 A|0,5 A|5 A|Theo định nghĩa, I = Δq/Δt = 10/5 = 2 A.|cường độ dòng điện
Dòng điện không đổi 0,5 A chạy trong 2 phút. Điện lượng qua tiết diện dây bằng bao nhiêu?|60 C|1 C|15 C|120 C|Đổi thời gian 2 phút = 120 s. Điện lượng q = It = 0,5 × 120 = 60 C.|điện lượng
Có 2 × 10¹⁸ electron đi qua tiết diện dây trong 1 s. Lấy e = 1,6 × 10⁻¹⁹ C. Cường độ dòng điện bằng bao nhiêu?|0,32 A|3,2 A|0,032 A|1,25 A|Điện lượng có độ lớn q = Ne = 2 × 10¹⁸ × 1,6 × 10⁻¹⁹ = 0,32 C. Chia cho 1 s được 0,32 A.|electron
Dòng điện không đổi 2 A truyền điện lượng 180 C qua một tiết diện trong thời gian bao lâu?|90 s|360 s|180 s|45 s|Từ q = It suy ra t = q/I = 180/2 = 90 s.|điện lượng
Dây kim loại có n = 8 × 10²⁸ m⁻³, S = 1 mm², tốc độ trôi 0,1 mm/s. Lấy e = 1,6 × 10⁻¹⁹ C. Cường độ dòng điện bằng bao nhiêu?|1,28 A|12,8 A|0,128 A|128 A|Đổi S = 10⁻⁶ m², v = 10⁻⁴ m/s. I = neSv = 8 × 10²⁸ × 1,6 × 10⁻¹⁹ × 10⁻⁶ × 10⁻⁴ = 1,28 A.|dịch chuyển
Dòng điện 1,6 A chạy qua dây kim loại trong 10 s. Lấy e = 1,6 × 10⁻¹⁹ C. Số electron qua tiết diện bằng bao nhiêu?|10²⁰|10¹⁹|10²¹|1,6 × 10²⁰|Điện lượng q = It = 16 C. Số electron N = q/e = 16/(1,6 × 10⁻¹⁹) = 10²⁰.|electron
'''

CONTENT[17] = '''
Với điện trở thuần ở nhiệt độ không đổi, định luật Ôm được viết thế nào?|I = U/R|I = UR|I = R/U|I = U²R|Cường độ dòng điện tỉ lệ thuận với hiệu điện thế và tỉ lệ nghịch với điện trở: I = U/R.|điện trở
Đơn vị SI của điện trở là gì?|Ohm (Ω)|Ampere (A)|Volt (V)|Watt (W)|Điện trở R = U/I có đơn vị volt trên ampere, gọi là ohm, kí hiệu Ω.|điện trở
Đo hiệu điện thế U và dòng điện I qua một điện trở, tính R bằng công thức nào?|R = U/I|R = UI|R = I/U|R = U²I|Từ định luật Ôm I = U/R, biến đổi đại số được R = U/I.|điện trở
Điện trở của dây đồng chất dài l, tiết diện S, điện trở suất ρ được tính thế nào?|R = ρl/S|R = ρS/l|R = lS/ρ|R = ρlS|Điện trở dây đồng chất tỉ lệ với chiều dài và tỉ lệ nghịch tiết diện: R = ρl/S.|điện trở
Khi nhiệt độ dây đồng tăng trong khoảng thông thường, điện trở thường biến đổi thế nào?|Tăng|Giảm về 0|Luôn không đổi|Đổi dấu|Kim loại như đồng có hệ số nhiệt điện trở dương, nên điện trở tăng khi nhiệt độ tăng.|điện trở
Điện trở suất của một vật liệu dẫn điện phụ thuộc trực tiếp vào yếu tố nào?|Bản chất vật liệu và nhiệt độ|Chỉ chiều dài dây|Chỉ tiết diện dây|Chỉ hình dạng dây|Điện trở suất đặc trưng cho vật liệu ở nhiệt độ xác định; kích thước dây quyết định R qua R = ρl/S.|điện trở
Giữ nhiệt độ một điện trở thuần không đổi, tăng U gấp đôi thì I thế nào?|Tăng gấp đôi|Giảm một nửa|Không đổi|Tăng gấp bốn|Vì R không đổi, từ I = U/R suy ra I tăng cùng tỉ lệ với U.|điện trở
Hai dây cùng vật liệu, cùng nhiệt độ và tiết diện; dây thứ hai dài gấp đôi. Điện trở dây thứ hai thế nào?|Gấp đôi dây thứ nhất|Bằng một nửa|Bằng nhau|Gấp bốn|Theo R = ρl/S, khi ρ và S giữ nguyên, điện trở tỉ lệ thuận chiều dài.|điện trở
Hai dây cùng vật liệu, nhiệt độ và chiều dài; tiết diện dây thứ hai gấp đôi. Điện trở dây thứ hai thế nào?|Bằng một nửa dây thứ nhất|Gấp đôi|Bằng nhau|Gấp bốn|Theo R = ρl/S, tăng tiết diện hai lần làm điện trở giảm hai lần.|điện trở
Hai dây tròn cùng vật liệu, nhiệt độ và chiều dài; bán kính dây thứ hai gấp đôi. Điện trở dây thứ hai thế nào?|Bằng một phần tư dây thứ nhất|Bằng một nửa|Gấp đôi|Gấp bốn|Tiết diện S = πr² tăng bốn lần khi bán kính tăng hai lần; R giảm bốn lần.|điện trở
Kéo một dây dài gấp đôi, giữ nguyên thể tích và điện trở suất. Điện trở mới so với ban đầu thế nào?|Gấp bốn|Gấp đôi|Bằng một nửa|Không đổi|Thể tích lS không đổi nên l tăng hai lần làm S giảm hai lần; R = ρl/S tăng bốn lần.|điện trở
Đồ thị U theo I của điện trở thuần ở nhiệt độ không đổi có dạng nào?|Đường thẳng qua gốc tọa độ|Đường tròn|Parabol|Đường thẳng song song trục U|Do U = RI và R không đổi, đồ thị U theo I là đường thẳng qua gốc tọa độ.|điện trở
Trên đồ thị U theo I với cùng tỉ lệ trục, đường thẳng dốc hơn ứng với điện trở thế nào?|Lớn hơn|Nhỏ hơn|Bằng 0|Không thể so sánh|Hệ số góc của đồ thị U theo I là ΔU/ΔI = R, nên độ dốc lớn hơn ứng với R lớn hơn.|điện trở
Vì sao dòng điện qua đèn sợi đốt thường không tỉ lệ thuận với điện áp khi tăng điện áp nhiều?|Sợi đốt nóng lên làm điện trở thay đổi|Điện tích electron tăng|Chiều dòng điện luôn đảo ngược|Đèn không có điện trở|Điện áp tăng làm sợi đốt nóng hơn; điện trở tăng nên điều kiện R không đổi của quan hệ tỉ lệ thuận không còn.|điện trở
Một điện trở có U = 12 V và I = 0,3 A. Giá trị điện trở là bao nhiêu?|40 Ω|3,6 Ω|0,025 Ω|4 Ω|Áp dụng R = U/I = 12/0,3 = 40 Ω cho điện trở đang xét.|điện trở
Đặt hiệu điện thế 24 V vào điện trở 120 Ω. Dòng điện bằng bao nhiêu?|0,2 A|5 A|2880 A|2 A|Theo định luật Ôm, I = U/R = 24/120 = 0,2 A.|điện trở
Dây có ρ = 1,7 × 10⁻⁸ Ωm, dài 20 m, tiết diện 1 mm². Điện trở bằng bao nhiêu?|0,34 Ω|3,4 Ω|0,034 Ω|34 Ω|Đổi S = 10⁻⁶ m². R = ρl/S = 1,7 × 10⁻⁸ × 20/10⁻⁶ = 0,34 Ω.|điện trở
Dây dài 10 m, tiết diện 0,5 mm² có điện trở 0,34 Ω. Điện trở suất bằng bao nhiêu?|1,7 × 10⁻⁸ Ωm|1,7 × 10⁻⁷ Ωm|6,8 × 10⁻⁸ Ωm|6,8 × 10⁻⁷ Ωm|ρ = RS/l = 0,34 × 0,5 × 10⁻⁶/10 = 1,7 × 10⁻⁸ Ωm.|điện trở
Một điện trở có R₀ = 20 Ω ở 20°C, α = 0,004 K⁻¹. Dùng R = R₀[1 + α(t − t₀)], tính R ở 70°C.|24 Ω|20,2 Ω|28 Ω|16 Ω|Độ tăng nhiệt độ là 50°C. R = 20[1 + 0,004 × 50] = 24 Ω.|điện trở
Điện trở thuần có dòng 2 A khi đặt 6 V. Giữ nhiệt độ không đổi, muốn dòng 4 A cần điện áp nào?|12 V|3 V|8 V|24 V|Trước hết R = 6/2 = 3 Ω. Điện áp cần đặt là U = IR = 4 × 3 = 12 V.|điện trở
'''

CONTENT[18] = '''
Trong đoạn mạch gồm các điện trở nối tiếp, đại lượng nào bằng nhau qua mỗi điện trở?|Cường độ dòng điện|Hiệu điện thế|Công suất|Điện trở|Mạch nối tiếp không phân nhánh nên dòng điện qua các điện trở có cùng cường độ.|điện trở
Hai điện trở mắc song song có đại lượng nào luôn bằng nhau?|Hiệu điện thế hai đầu|Cường độ dòng điện|Điện trở|Nhiệt lượng tỏa ra|Hai nhánh song song cùng nối vào hai nút nên có cùng hiệu điện thế giữa hai đầu.|điện trở
Điện trở tương đương của hai điện trở R₁ và R₂ nối tiếp là gì?|R₁ + R₂|R₁R₂/(R₁ + R₂)|R₁ − R₂|R₁R₂|Mạch nối tiếp có U = I(R₁ + R₂), nên điện trở tương đương bằng tổng hai điện trở.|điện trở
Điện trở tương đương của hai điện trở dương R₁ và R₂ song song là gì?|R₁R₂/(R₁ + R₂)|R₁ + R₂|R₁R₂|R₁/R₂|Từ I = U/R₁ + U/R₂ suy ra 1/R = 1/R₁ + 1/R₂, tức R = R₁R₂/(R₁ + R₂).|điện trở
Điện trở của ampe kế lí tưởng được coi bằng bao nhiêu?|0 Ω|1 Ω|Vô cùng lớn|Bằng điện trở cần đo|Ampe kế lí tưởng có điện trở bằng 0 để không làm thay đổi dòng điện khi mắc nối tiếp.|điện trở
Điện trở của vôn kế lí tưởng được coi thế nào?|Vô cùng lớn|Bằng 0|Luôn bằng 1 Ω|Bằng điện trở nguồn|Vôn kế lí tưởng có điện trở vô cùng lớn nên không có dòng điện đi qua nó.|điện trở
Hai điện trở giống nhau, mỗi chiếc R, mắc nối tiếp. Điện trở tương đương bằng bao nhiêu?|2R|R/2|R|R/4|Khi nối tiếp, điện trở tương đương bằng tổng: R tương đương = R + R = 2R.|điện trở
Hai điện trở giống nhau, mỗi chiếc R, mắc song song. Điện trở tương đương bằng bao nhiêu?|R/2|2R|R|4R|Theo công thức song song, R tương đương = R²/(R + R) = R/2.|điện trở
Điện trở tương đương của hai điện trở dương hữu hạn mắc song song so với điện trở nhỏ hơn thế nào?|Nhỏ hơn điện trở nhỏ hơn|Lớn hơn cả hai|Bằng tổng hai điện trở|Bằng điện trở lớn hơn|Vì 1/R tương đương = 1/R₁ + 1/R₂ lớn hơn mỗi số hạng nên R tương đương nhỏ hơn mỗi điện trở.|điện trở
Hai điện trở nối tiếp có R₂ = 3R₁. Tỉ số hiệu điện thế U₂/U₁ bằng bao nhiêu?|3|1/3|1|9|Mạch nối tiếp có cùng I, nên U₂/U₁ = IR₂/(IR₁) = R₂/R₁ = 3.|điện trở
Hai điện trở song song có R₂ = 3R₁. Tỉ số dòng điện I₂/I₁ bằng bao nhiêu?|1/3|3|1|9|Hai nhánh cùng U nên I₂/I₁ = (U/R₂)/(U/R₁) = R₁/R₂ = 1/3.|điện trở
Mắc vôn kế lí tưởng song song với một điện trở trong mạch đang hoạt động có làm thay đổi dòng qua điện trở không?|Không thay đổi|Tăng gấp đôi|Giảm một nửa|Giảm về 0|Vôn kế lí tưởng không lấy dòng điện, do đó không làm thay đổi trạng thái điện của mạch.|điện trở
Hai điện trở song song nối nguồn có hiệu điện thế không đổi. Ngắt một nhánh thì dòng qua nhánh còn lại thế nào?|Không đổi|Tăng gấp đôi|Giảm về 0|Luôn giảm một nửa|Hiệu điện thế và điện trở của nhánh còn lại không đổi nên dòng I = U/R giữ nguyên.|điện trở
Nối tắt hai đầu một điện trở bằng dây lí tưởng, hiệu điện thế giữa hai đầu điện trở bằng bao nhiêu?|0 V|Bằng suất điện động nguồn trong mọi mạch|Tăng vô hạn|Bằng điện trở của nó|Dây lí tưởng nối hai đầu thành cùng điện thế, nên hiệu điện thế trên điện trở bị nối tắt bằng 0.|điện trở
Hai điện trở 2 Ω và 4 Ω nối tiếp vào hiệu điện thế 12 V. Dòng điện mạch chính bằng bao nhiêu?|2 A|6 A|3 A|0,5 A|Điện trở tương đương R = 2 + 4 = 6 Ω. Dòng điện I = 12/6 = 2 A.|điện trở
Hai điện trở 6 Ω và 3 Ω song song vào hiệu điện thế 12 V. Dòng điện tổng bằng bao nhiêu?|6 A|4 A|2 A|1,33 A|Điện trở tương đương R = 6 × 3/(6 + 3) = 2 Ω. Dòng tổng I = 12/2 = 6 A.|điện trở
Hai điện trở 10 Ω và 20 Ω nối tiếp vào 12 V. Hiệu điện thế trên điện trở 20 Ω bằng bao nhiêu?|8 V|4 V|12 V|6 V|Dòng mạch I = 12/(10 + 20) = 0,4 A. U trên điện trở 20 Ω là 0,4 × 20 = 8 V.|điện trở
Hai điện trở 6 Ω và 3 Ω song song, dòng tổng bằng 6 A. Dòng qua điện trở 6 Ω bằng bao nhiêu?|2 A|4 A|6 A|3 A|R tương đương = 2 Ω, nên U = 6 × 2 = 12 V. Dòng qua điện trở 6 Ω là 12/6 = 2 A.|điện trở
Điện trở 2 Ω nối tiếp bộ 6 Ω song song 3 Ω. Đặt 12 V vào toàn mạch, dòng tổng bằng bao nhiêu?|3 A|6 A|2 A|1 A|Bộ song song có R = 2 Ω. Toàn mạch có R = 2 + 2 = 4 Ω nên I = 12/4 = 3 A.|điện trở
Điện trở 4 Ω nối tiếp bộ 12 Ω song song 6 Ω, toàn mạch đặt 24 V. Dòng qua điện trở 6 Ω bằng bao nhiêu?|2 A|3 A|4 A|1 A|Bộ song song có R = 4 Ω; dòng tổng = 24/8 = 3 A. Điện áp bộ song song = 12 V nên dòng nhánh 6 Ω = 2 A.|điện trở
'''

CONTENT[19] = '''
Suất điện động của nguồn đặc trưng cho khả năng nào?|Thực hiện công của nguồn trên một đơn vị điện tích|Cản trở dòng điện của dây|Tích điện của tụ|Truyền sóng của anten|Suất điện động bằng công của lực lạ trong nguồn chia cho điện tích dương được dịch chuyển.|nguồn điện
Đơn vị của suất điện động là gì?|Volt (V)|Ohm (Ω)|Coulomb (C)|Ampere (A)|Suất điện động là công trên điện tích, có đơn vị J/C, tức volt.|nguồn điện
Nguồn thực hiện công A khi dịch chuyển điện tích q bên trong nguồn. Suất điện động E bằng gì?|E = A/q|E = Aq|E = q/A|E = A/q²|Theo định nghĩa, suất điện động E bằng công của nguồn trên một đơn vị điện tích: E = A/q.|nguồn điện
Nguồn đang phát điện có suất điện động E, điện trở trong r và dòng I. Hiệu điện thế hai cực bằng gì?|U = E − Ir|U = E + Ir|U = Ir − E|U = E/I|Khi nguồn phát điện, phần điện áp Ir hao hụt trên điện trở trong, nên điện áp ngoài U = E − Ir.|nguồn điện
Mạch kín gồm nguồn E, điện trở trong r và điện trở ngoài R. Dòng điện bằng gì?|I = E/(R + r)|I = E/R + r|I = E(R + r)|I = (R + r)/E|Tổng điện trở của mạch là R + r; định luật Ôm cho toàn mạch cho I = E/(R + r).|nguồn điện
Khi nguồn có r > 0 bị đoản mạch bằng dây lí tưởng, dòng điện bằng gì?|I = E/r|I = 0|I = Er|I = r/E|Khi đoản mạch, điện trở ngoài bằng 0 nên I = E/(0 + r) = E/r.|nguồn điện
Nguồn hở mạch có dòng điện bằng 0. Điện áp hai cực bằng đại lượng nào?|Suất điện động E|0 V trong mọi trường hợp|Er|E/r|Khi hở mạch, I = 0 nên không có sụt áp trên điện trở trong; U = E − Ir = E.|nguồn điện
Giữ E và r > 0 không đổi, giảm điện trở ngoài R thì dòng điện mạch kín thế nào?|Tăng|Giảm|Không đổi|Đổi chiều|Theo I = E/(R + r), giảm R làm mẫu số nhỏ đi nên dòng điện tăng.|nguồn điện
Nguồn đang phát điện có E và r > 0 không đổi. Khi dòng I tăng, điện áp hai cực thế nào?|Giảm|Tăng|Không đổi|Luôn bằng 0|Điện áp hai cực U = E − Ir; dòng tăng làm sụt áp trong Ir lớn hơn nên U giảm.|nguồn điện
Một nguồn lí tưởng có điện trở trong bằng 0. Điện áp hai cực khi phát điện thế nào?|Bằng E|Bằng 0|Bằng Ir|Phụ thuộc R theo U = ER|Nguồn lí tưởng không có sụt áp bên trong, nên U = E − I × 0 = E.|nguồn điện
Vì sao đoản mạch có thể làm nguồn nóng mạnh?|Dòng lớn gây tỏa nhiệt mạnh trên điện trở trong|Điện trở trong luôn tăng vô hạn|Suất điện động bằng 0|Điện tích biến mất|Dòng đoản mạch E/r có thể rất lớn; công suất nhiệt trong nguồn I²r vì thế lớn, gây nóng.|nguồn điện
Một nguồn thực hiện cùng công nhưng dịch chuyển điện tích gấp đôi. Suất điện động tính theo A/q thế nào?|Giảm một nửa|Tăng gấp đôi|Không đổi|Tăng gấp bốn|Theo E = A/q, giữ A và tăng q hai lần làm thương A/q giảm hai lần.|nguồn điện
Vôn kế lí tưởng mắc vào hai cực nguồn hở mạch đo được gì?|Suất điện động của nguồn|Dòng đoản mạch|Điện trở trong trực tiếp|Công của nguồn|Vôn kế lí tưởng không lấy dòng; I = 0 nên điện áp đo được bằng suất điện động E.|nguồn điện
Hai nguồn có cùng E, cùng mắc riêng với điện trở ngoài R > 0. Nguồn có r nhỏ hơn cho dòng thế nào?|Lớn hơn|Nhỏ hơn|Luôn bằng nhau|Luôn bằng 0|Với cùng E và R, điện trở trong nhỏ hơn làm R + r nhỏ hơn nên I = E/(R + r) lớn hơn.|nguồn điện
Nguồn thực hiện công 18 J khi dịch chuyển điện tích 3 C. Suất điện động bằng bao nhiêu?|6 V|54 V|0,167 V|15 V|Áp dụng định nghĩa suất điện động E = A/q = 18/3 = 6 V.|nguồn điện
Nguồn E = 12 V, r = 1 Ω nối với R = 5 Ω. Dòng điện bằng bao nhiêu?|2 A|2,4 A|12 A|0,5 A|Điện trở toàn mạch là 5 + 1 = 6 Ω. I = 12/6 = 2 A.|nguồn điện
Nguồn E = 9 V, r = 0,5 Ω đang phát dòng 2 A. Điện áp hai cực bằng bao nhiêu?|8 V|10 V|4,5 V|1 V|Sụt áp trong nguồn Ir = 2 × 0,5 = 1 V. Điện áp ngoài U = 9 − 1 = 8 V.|nguồn điện
Nguồn E = 12 V đang phát dòng 2 A, điện áp hai cực 10 V. Điện trở trong bằng bao nhiêu?|1 Ω|6 Ω|5 Ω|11 Ω|Từ U = E − Ir suy ra r = (E − U)/I = (12 − 10)/2 = 1 Ω.|nguồn điện
Nguồn E = 6 V, r = 0,3 Ω bị nối tắt bằng dây lí tưởng. Dòng đoản mạch bằng bao nhiêu?|20 A|1,8 A|2 A|0,05 A|Khi điện trở ngoài bằng 0, dòng đoản mạch I = E/r = 6/0,3 = 20 A.|nguồn điện
Nguồn có điện áp hở mạch 12 V; khi nối điện trở 5 Ω, dòng điện là 2 A. Điện trở trong bằng bao nhiêu?|1 Ω|2 Ω|5 Ω|6 Ω|Điện áp hở mạch cho E = 12 V. Từ E/I = R + r suy ra r = 12/2 − 5 = 1 Ω.|nguồn điện
'''

CONTENT[20] = '''
Điện năng tiêu thụ của đoạn mạch có U và I không đổi trong thời gian t được tính thế nào?|W = UIt|W = UI/t|W = Ut/I|W = It/U|Điện năng bằng công suất nhân thời gian; với P = UI ta được W = UIt.|điện năng
Công suất điện của đoạn mạch một chiều được tính bằng công thức nào?|P = UI|P = U/I|P = I/U|P = UIt|Công suất là điện năng tiêu thụ trong một đơn vị thời gian, bằng tích hiệu điện thế và dòng điện.|công suất
Nhiệt lượng tỏa ra trên điện trở R có dòng I không đổi trong thời gian t là gì?|Q = I²Rt|Q = IRt|Q = I²R/t|Q = IR²t|Định luật Joule–Lenz cho nhiệt lượng tỏa ra trên điện trở: Q = I²Rt.|điện năng
Một kilowatt giờ tương đương bao nhiêu joule?|3,6 × 10⁶ J|3600 J|1000 J|3,6 × 10³ W|1 kWh = 1000 W × 3600 s = 3,6 × 10⁶ J, là đơn vị năng lượng.|điện năng
Hiệu suất của thiết bị bằng tỉ số nào?|Năng lượng có ích trên năng lượng cung cấp|Năng lượng cung cấp trên năng lượng có ích|Công suất hao phí trên công suất có ích|Năng lượng hao phí trên tổng năng lượng|Hiệu suất cho biết phần năng lượng đầu vào chuyển thành năng lượng có ích, H = W có ích/W cung cấp.|công suất
Công suất tỏa nhiệt của điện trở thuần khi biết U và R là gì?|P = U²/R|P = UR|P = U/R²|P = R/U²|Kết hợp P = UI với I = U/R được P = U²/R đối với điện trở thuần.|công suất
Giữ điện trở R không đổi, dòng điện tăng gấp đôi thì công suất tỏa nhiệt thế nào?|Tăng gấp bốn|Tăng gấp đôi|Giảm một nửa|Không đổi|Vì P = I²R, tăng I hai lần làm I² tăng bốn lần nên công suất tăng bốn lần.|công suất
Giữ điện trở R không đổi, giảm điện áp hai lần thì công suất thế nào?|Giảm bốn lần|Giảm hai lần|Tăng hai lần|Không đổi|Theo P = U²/R, giảm U hai lần làm U² giảm bốn lần, nên P còn một phần tư.|công suất
Hai điện trở nối tiếp có R₂ = 2R₁. Tỉ số công suất P₂/P₁ bằng bao nhiêu?|2|1/2|4|1|Mạch nối tiếp có cùng I, nên P₂/P₁ = I²R₂/(I²R₁) = R₂/R₁ = 2.|công suất
Hai điện trở song song có R₂ = 2R₁. Tỉ số công suất P₂/P₁ bằng bao nhiêu?|1/2|2|4|1|Hai điện trở cùng U, nên P₂/P₁ = (U²/R₂)/(U²/R₁) = R₁/R₂ = 1/2.|công suất
Đèn ghi 12 V – 6 W tiêu thụ công suất 6 W trong điều kiện nào?|Hoạt động ở hiệu điện thế định mức 12 V|Ở mọi điện áp|Chỉ khi không có dòng điện|Khi điện áp bằng 6 V|Công suất ghi trên đèn là công suất định mức khi đèn hoạt động đúng hiệu điện thế định mức.|công suất
Một thiết bị giữ công suất không đổi và hoạt động lâu gấp ba. Điện năng tiêu thụ thế nào?|Tăng gấp ba|Giảm ba lần|Không đổi|Tăng gấp chín|Theo W = Pt, với P không đổi, năng lượng tiêu thụ tỉ lệ thuận thời gian hoạt động.|điện năng
Nguồn E, r phát điện cho điện trở R. Hiệu suất truyền năng lượng ra mạch ngoài bằng gì?|R/(R + r)|1 − R/(R + r)|(R + r)/R|R/r|Công suất ngoài I²R chia công suất nguồn EI = I²(R + r) cho H = R/(R + r).|công suất
Với cùng nhiệt lượng cần cung cấp để đun nước, ấm có hiệu suất cao hơn cần điện năng thế nào?|Ít hơn|Nhiều hơn|Luôn như nhau|Bằng 0|Vì H = Q có ích/W điện, nên W điện = Q có ích/H; tăng H làm điện năng cần dùng giảm.|điện năng
Điện trở 10 Ω có dòng điện 2 A đi qua. Công suất tỏa nhiệt bằng bao nhiêu?|40 W|20 W|5 W|400 W|Áp dụng P = I²R = 2² × 10 = 40 W cho điện trở thuần.|công suất
Thiết bị 100 W hoạt động 5 giờ mỗi ngày trong 30 ngày. Điện năng tiêu thụ bằng bao nhiêu?|15 kWh|150 kWh|1,5 kWh|500 kWh|Đổi 100 W = 0,1 kW. Thời gian 5 × 30 = 150 h, nên W = 0,1 × 150 = 15 kWh.|điện năng
Máy sưởi 2 kW chạy 3 giờ. Giá điện giả định 2500 đồng/kWh, không tính phí khác. Tiền điện bằng bao nhiêu?|15000 đồng|5000 đồng|7500 đồng|30000 đồng|Điện năng W = 2 × 3 = 6 kWh. Tiền điện = 6 × 2500 = 15000 đồng.|điện năng
Đun 1 kg nước từ 20°C lên 100°C, c = 4200 J/(kg·K), hiệu suất 80%. Điện năng cần dùng bằng bao nhiêu?|420 kJ|336 kJ|268,8 kJ|525 kJ|Nhiệt có ích Q = mcΔT = 1 × 4200 × 80 = 336 kJ. Điện năng W = Q/0,8 = 420 kJ.|điện năng
Nguồn có r = 1 Ω cấp điện cho R = 4 Ω. Hiệu suất truyền năng lượng ra mạch ngoài bằng bao nhiêu?|80%|20%|25%|100%|Hiệu suất H = R/(R + r) = 4/(4 + 1) = 0,8, tương ứng 80%.|công suất
Đèn ghi 12 V – 6 W được đặt vào 6 V. Giả sử điện trở đèn không đổi bằng giá trị định mức, công suất bằng bao nhiêu?|1,5 W|3 W|6 W|12 W|Điện trở định mức R = 12²/6 = 24 Ω. Khi đặt 6 V, P = 6²/24 = 1,5 W.|công suất
'''

def build(number):
    chapter, title, keywords = PLAN[number - 1]
    source, excerpts = context_for(chapter, keywords)
    rows = [line.strip().split('|') for line in CONTENT[number].strip().splitlines() if line.strip()]
    assert len(rows) == 20
    questions = []
    for index, row in enumerate(rows, 1):
        assert len(row) == 7, (number, index, len(row))
        stem, correct, b, c, d, explanation, keyword = row
        candidates = [(key, text) for key, text in excerpts.items() if fold(keyword) in fold(text)]
        if not candidates:
            raise ValueError(f'No source match for exam {number} item {index}: {keyword}')
        # Prefer substantive source paragraphs over headings and isolated choices.
        candidates.sort(key=lambda pair: (bool(re.match(r'^[ABCD][.]', pair[1])), len(pair[1]) < 40, abs(len(pair[1]) - 140)))
        paragraph, quote = candidates[0]
        questions.append({'id': index, 'number': index, 'question': stem,
                          'options': {'A': correct, 'B': b, 'C': c, 'D': d}, 'correct_answer': 'A',
                          'explanation': explanation, 'difficulty': 'NB' if index <= 6 else ('TH' if index <= 14 else 'VD'),
                          'source_paragraph': int(paragraph), 'source_quote': quote})
    validate(questions, excerpts)
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / f'source-{number:02}.json').write_text(json.dumps(excerpts, ensure_ascii=False, indent=2), encoding='utf-8')
    return finalize_exam(number, questions, source, review_method='Explicit assistant-authored questions and worked calculations, source paragraph references checked; not a human certification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=int, required=True)
    args = parser.parse_args()
    for number in (args.stage * 2 - 1, args.stage * 2):
        build(number)
    print(f'STAGE {args.stage}/10 COMPLETE')
