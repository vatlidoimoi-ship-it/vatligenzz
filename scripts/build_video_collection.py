"""Reviewed short physics lessons; preflight before the explicitly requested 20 renders."""
import argparse, copy, hashlib, json, math, os, shutil, subprocess, sys
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
WORK = ROOT / '.runtime_data/video-collection'
DATA = ROOT / 'data/video_lessons.json'

def collection():
    lessons=[]
    spring={'type':'spring','labels':{}}
    pendulum={'type':'pendulum','angle_deg':6,'show_angle':False,'labels':{'length':'ℓ'}}
    wave={'type':'wave'}
    def circuit(u,r):
        return {'type':'circuit','topology':'single','labels':{'U':u,'R':r}}
    def add(title, group, problem, method, formula, result, intro, explanation, conclusion, diagram, source=None):
        n=len(lessons)+1
        steps=[{'title':title,'slide_text':problem,'narration':intro},
               {'title':'Phương pháp và thay số','slide_text':method,'latex':formula,'narration':explanation},
               {'title':'Kết luận và lưu ý','slide_text':result,'narration':conclusion}]
        for step in steps:
            step['diagram']=copy.deepcopy(diagram)
            if n==9:step['diagram']['show_angle']=True
        lessons.append({'id':f'vl-{n:02d}','title':title,'group':group,'grade':'11','source':source,
                        'script':{'subject':'Vật lý','problem':problem,'design_template':['studio','warm','chalkboard'][((n-1)//5)%3],
                                  'include_full_solution':False,'steps':steps}})
    add('Đọc chu kì từ phương trình','Dao động',
        'Vật dao động: x = 4 cos(2πt) cm.\nXác định biên độ, chu kì và tần số.',
        'Đối chiếu x = A cos(ωt + φ).\nA = 4 cm; ω = 2π rad/s.',r'T=\frac{2\pi}{\omega}=1\,s;\quad f=\frac1T=1\,Hz',
        'Biên độ: 4 cm; chu kì: 1 s; tần số: 1 Hz.\nĐừng nhầm ω với tần số f.',
        'Vật có li độ bằng bốn nhân cô sin của hai pi t, đơn vị xen ti mét. Hãy tìm biên độ, chu kì và tần số.',
        'So sánh với dạng chuẩn, biên độ là bốn xen ti mét, tần số góc là hai pi ra đi an trên giây. Chu kì bằng hai pi chia tần số góc, được một giây. Tần số là nghịch đảo chu kì.',
        'Kết quả: biên độ bốn xen ti mét, chu kì một giây, tần số một héc. Tần số góc và tần số là hai đại lượng khác nhau.',spring)
    add('Tìm li độ tại một thời điểm','Dao động',
        'x = 6 cos(πt) cm; t = 1/3 s.\nTính li độ và xác định vật ở phía nào của O.',
        'Thay t vào pha: πt = π/3.\ncos(π/3) = 1/2.',r'x=6\cos\frac\pi3=3\,cm',
        'x = +3 cm: vật ở phía dương của O.\nLi độ có dấu; khoảng cách tới O không âm.',
        'Cho li độ bằng sáu nhân cô sin của pi t, đơn vị xen ti mét. Tại thời điểm một phần ba giây, vật nằm ở đâu so với vị trí cân bằng?',
        'Thay thời gian vào phương trình, pha dao động bằng pi chia ba. Cô sin của pi chia ba bằng một phần hai. Nhân với biên độ sáu, ta được li độ ba xen ti mét.',
        'Li độ dương ba xen ti mét cho biết vật nằm phía dương của vị trí cân bằng. Khoảng cách tới vị trí cân bằng là ba xen ti mét.',spring)
    add('Tốc độ khi biết li độ','Dao động',
        'A = 5 cm; ω = 4 rad/s; x = 3 cm.\nTính tốc độ của vật dao động điều hòa.',
        'Dùng hệ thức độc lập với thời gian.\nGiữ A và x cùng đơn vị cm.',r'|v|=\omega\sqrt{A^2-x^2}=4\sqrt{25-9}=16\,cm/s',
        'Tốc độ: 16 cm/s = 0,16 m/s.\nChưa đủ dữ kiện xác định dấu vận tốc.',
        'Một vật có biên độ năm xen ti mét và tần số góc bốn ra đi an trên giây. Tính tốc độ khi li độ bằng ba xen ti mét.',
        'Tốc độ bằng tần số góc nhân căn của biên độ bình phương trừ li độ bình phương. Năm bình phương trừ ba bình phương bằng mười sáu. Lấy căn rồi nhân bốn, được mười sáu xen ti mét trên giây.',
        'Đáp số là mười sáu xen ti mét trên giây. Đây là tốc độ. Muốn biết vận tốc mang dấu dương hay âm, cần biết chiều chuyển động.',spring)
    add('Gia tốc luôn hướng về cân bằng','Dao động',
        'ω = 5 rad/s; x = +2 cm.\nTính gia tốc tại vị trí này.',
        'Đổi x = 0,02 m để tính theo SI.\nGia tốc a = −ω²x, trái dấu với li độ.',r'a=-\omega^2x=-25\times0{,}02=-0{,}5\,m/s^2',
        'a = −0,5 m/s², hướng về O.\nKhông suy ra chiều vận tốc chỉ từ gia tốc.',
        'Vật dao động điều hòa với tần số góc năm ra đi an trên giây. Tại li độ dương hai xen ti mét, hãy tìm gia tốc.',
        'Đổi hai xen ti mét thành không phẩy không hai mét. Gia tốc bằng âm tần số góc bình phương nhân li độ. Thay số được âm không phẩy năm mét trên giây bình phương.',
        'Gia tốc âm vì vật đang ở phía dương, nên gia tốc hướng về vị trí cân bằng. Dấu của gia tốc không cho biết ngay vật đang đi theo chiều nào.',spring)
    add('Chia cơ năng thành động năng và thế năng','Dao động',
        'Lò xo ngang: k = 100 N/m; A = 4 cm.\nTại x = 2 cm, tính cơ năng và động năng.\nBỏ qua ma sát; thế năng bằng 0 tại O.',
        'Đổi A = 0,04 m; x = 0,02 m.\nW = kA²/2; Wđ = W − kx²/2.',r'W=0{,}08\,J;\quad W_t=0{,}02\,J;\quad W_d=0{,}06\,J',
        'Cơ năng: 0,08 J; động năng: 0,06 J.\nTại x = A/2, thế năng bằng W/4.',
        'Con lắc lò xo ngang có độ cứng một trăm niu tơn trên mét, biên độ bốn xen ti mét. Bỏ qua ma sát. Tìm cơ năng và động năng tại li độ hai xen ti mét.',
        'Đổi biên độ và li độ sang mét. Cơ năng bằng một nửa độ cứng nhân biên độ bình phương, được không phẩy không tám jun. Thế năng tại vị trí đang xét bằng không phẩy không hai jun. Lấy cơ năng trừ thế năng để tìm động năng.',
        'Động năng bằng không phẩy không sáu jun. Khi li độ bằng nửa biên độ, thế năng chỉ bằng một phần tư cơ năng vì thế năng phụ thuộc bình phương li độ.',spring)
    add('Con lắc đơn dài 25 cm','Con lắc đơn',
        'ℓ = 25 cm; g = π² m/s².\nDao động góc nhỏ, bỏ qua ma sát.\nTính chu kì.',
        'Đổi chiều dài: ℓ = 0,25 m.\nÁp dụng công thức chu kì góc nhỏ.',r'T\approx2\pi\sqrt{\frac\ell g}=2\pi\sqrt{\frac{0{,}25}{\pi^2}}=1\,s',
        'Chu kì gần đúng: 1 giây.\nChiều dài trong công thức phải tính bằng mét.',
        'Con lắc đơn có chiều dài hai mươi lăm xen ti mét. Lấy gia tốc trọng trường bằng pi bình phương. Với dao động góc nhỏ, chu kì bằng bao nhiêu?',
        'Đổi chiều dài sang không phẩy hai mươi lăm mét. Chu kì bằng hai pi nhân căn của chiều dài chia gia tốc trọng trường. Căn của không phẩy hai mươi lăm là không phẩy năm, nên kết quả bằng một giây.',
        'Chu kì xấp xỉ một giây trong gần đúng góc nhỏ. Sai lầm thường gặp là đưa số hai mươi lăm vào công thức mà chưa đổi sang mét.',pendulum)
    add('Tìm chiều dài từ chu kì','Con lắc đơn',
        'T = 3 s; g = π² m/s².\nCon lắc dao động góc nhỏ.\nTìm chiều dài dây.',
        'Bình phương công thức chu kì.\nRút ℓ = gT²/(4π²).',r'\ell\approx\frac{gT^2}{4\pi^2}=\frac{\pi^2\times9}{4\pi^2}=2{,}25\,m',
        'Chiều dài dây: khoảng 2,25 m.\nKhông dùng ℓ tỉ lệ thuận với T.',
        'Một con lắc đơn dao động góc nhỏ với chu kì ba giây. Lấy gia tốc trọng trường bằng pi bình phương. Hãy xác định chiều dài dây.',
        'Từ công thức chu kì, bình phương hai vế rồi rút chiều dài. Chiều dài bằng gia tốc trọng trường nhân chu kì bình phương, chia bốn pi bình phương. Thay số được chín chia bốn mét.',
        'Chiều dài xấp xỉ hai phẩy hai mươi lăm mét. Với cùng gia tốc trọng trường, chiều dài tỉ lệ với bình phương chu kì.',pendulum)
    add('Đếm dao động trong hai phút','Con lắc đơn',
        'ℓ = 1 m; g = π² m/s²; góc nhỏ.\nTính số dao động toàn phần trong 120 s.',
        'Tính T trước, sau đó N = t/T.\nMột dao động toàn phần ứng với một chu kì.',r'T\approx2\,s;\qquad N\approx\frac{120}{2}=60',
        'Khoảng 60 dao động toàn phần.\nTừ biên này sang biên kia chỉ mất T/2.',
        'Con lắc đơn dài một mét, dao động góc nhỏ ở nơi gia tốc trọng trường bằng pi bình phương. Trong hai phút, con lắc thực hiện bao nhiêu dao động toàn phần?',
        'Áp dụng công thức chu kì, ta được hai giây. Hai phút bằng một trăm hai mươi giây. Chia thời gian cho chu kì, được sáu mươi dao động.',
        'Kết quả gần đúng là sáu mươi dao động toàn phần. Đi từ một biên đến biên đối diện mới chỉ là nửa dao động, không phải một dao động hoàn chỉnh.',pendulum)
    add('Tốc độ cực đại của con lắc đơn','Con lắc đơn',
        'ℓ = 1 m; α₀ = 6°; g = π² m/s².\nBỏ qua ma sát. Tính tốc độ cực đại.',
        'Đổi α₀ = π/30 rad; s₀ = ℓα₀.\nDùng gần đúng góc nhỏ: vmax ≈ √(g/ℓ)s₀.',r'v_{max}\approx\sqrt{g\ell}\alpha_0=\frac{\pi^2}{30}\approx0{,}329\,m/s',
        'Tốc độ cực đại ≈ 0,329 m/s, tại O.\nGóc phải đổi sang radian trước khi nhân.',
        'Con lắc dài một mét, biên độ góc sáu độ. Lấy gia tốc trọng trường bằng pi bình phương. Tính tốc độ cực đại khi bỏ qua ma sát.',
        'Đổi sáu độ thành pi chia ba mươi ra đi an. Trong gần đúng góc nhỏ, tốc độ cực đại bằng căn của gia tốc trọng trường nhân chiều dài, rồi nhân biên độ góc. Thay số được pi bình phương chia ba mươi.',
        'Tốc độ cực đại xấp xỉ không phẩy ba hai chín mét trên giây, đạt được khi qua vị trí cân bằng. Không được đưa trực tiếp số sáu độ vào công thức này.',pendulum)
    add('Tăng chiều dài thì chu kì đổi thế nào?','Con lắc đơn',
        'Ban đầu T₁ = 1,5 s.\nTăng chiều dài dây lên 4 lần, giữ nguyên g.\nHai trường hợp đều dao động góc nhỏ.',
        'Chu kì tỉ lệ với căn bậc hai chiều dài.\nLập tỉ số để không cần biết g.',r'\frac{T_2}{T_1}=\sqrt{\frac{\ell_2}{\ell_1}}=2;\quad T_2=3\,s',
        'Chu kì mới: 3 giây, tăng 2 lần.\nChiều dài tăng 4 lần không làm T tăng 4 lần.',
        'Một con lắc có chu kì một phẩy năm giây. Tăng chiều dài dây lên bốn lần tại cùng một nơi. Chu kì mới bằng bao nhiêu, nếu góc dao động vẫn nhỏ?',
        'Ở cùng một nơi, chu kì tỉ lệ với căn bậc hai chiều dài. Tỉ số chiều dài bằng bốn nên tỉ số chu kì bằng hai. Lấy một phẩy năm nhân hai, được ba giây.',
        'Chu kì mới là ba giây. Hãy nhớ quan hệ căn bậc hai: chiều dài tăng bốn lần thì chu kì chỉ tăng hai lần.',pendulum)
    def src(file,index):
        path=next((ROOT/'datatm').glob(f'{file}.*.docx'))
        root=ET.fromstring(ZipFile(path).read('word/document.xml'));ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        rows=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in root.findall('.//w:p',ns)]
        return {'file':path.name,'paragraph_index':index,'quote':rows[index],'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    add('Tốc độ sóng từ hai gợn liên tiếp','Sóng · từ tài liệu',
        'f = 50 Hz; hai gợn liên tiếp có bán kính\n12,4 cm và 14,3 cm. Tính tốc độ sóng.',
        'Hai đỉnh liên tiếp cách nhau một bước sóng.\nλ = 14,3 − 12,4 = 1,9 cm = 0,019 m.',r'v=\lambda f=0{,}019\times50=0{,}95\,m/s',
        'Tốc độ truyền sóng: 0,95 m/s.\nPhải lấy hiệu hai bán kính, không lấy tổng.',
        'Cần rung dao động năm mươi héc. Hai gợn sóng tròn liên tiếp có bán kính mười hai phẩy bốn và mười bốn phẩy ba xen ti mét. Tìm tốc độ truyền sóng.',
        'Hiệu hai bán kính là một bước sóng, bằng một phẩy chín xen ti mét. Đổi sang không phẩy không một chín mét rồi nhân tần số năm mươi héc, ta được không phẩy chín năm mét trên giây.',
        'Tốc độ truyền sóng là không phẩy chín năm mét trên giây. Bước sóng là khoảng cách hai gợn liên tiếp, vì vậy phải lấy hiệu bán kính.',wave,src(2,1195))
    add('Phao nhô lên sáu lần: có mấy chu kì?','Sóng · từ tài liệu',
        'Từ lần nhô cao thứ nhất đến thứ sáu: 4 s.\nv = 0,5 m/s. Tìm khoảng cách hai đỉnh sóng.',
        'Sáu lần nhô cao tạo năm khoảng thời gian.\nT = 4/5 = 0,8 s.',r'\lambda=vT=0{,}5\times0{,}8=0{,}4\,m',
        'Khoảng cách hai đỉnh: 0,4 m.\nĐếm khoảng giữa các lần, không đếm số lần.',
        'Một phao nhô lên cao sáu lần. Từ lần đầu đến lần thứ sáu mất bốn giây. Tốc độ sóng là không phẩy năm mét trên giây. Tìm khoảng cách hai đỉnh liên tiếp.',
        'Giữa sáu lần nhô cao có năm chu kì, nên chu kì bằng bốn chia năm, được không phẩy tám giây. Bước sóng bằng tốc độ nhân chu kì, bằng không phẩy bốn mét.',
        'Đáp số là không phẩy bốn mét. Điểm dễ nhầm là lấy bốn chia sáu. Phải đếm năm khoảng thời gian giữa sáu lần nhô cao.',wave,src(2,1228))
    add('Tốc độ từ phương trình sóng','Sóng · từ tài liệu',
        'u = 3,2 cos(8,5t − 0,5x).\nx tính bằng cm; t tính bằng s. Tìm v.',
        'Dạng chuẩn: u = A cos(ωt − kx).\nω = 8,5 rad/s; k = 0,5 rad/cm.',r'v=\frac\omega k=\frac{8{,}5}{0{,}5}=17\,cm/s=0{,}17\,m/s',
        'Tốc độ truyền sóng: 17 cm/s.\nĐơn vị của x quyết định đơn vị của v.',
        'Sóng có phương trình ba phẩy hai nhân cô sin của tám phẩy năm t trừ không phẩy năm x. Tọa độ x tính bằng xen ti mét, thời gian bằng giây. Hãy tìm tốc độ sóng.',
        'Đối chiếu dạng chuẩn, tần số góc bằng tám phẩy năm, số sóng bằng không phẩy năm ra đi an trên xen ti mét. Tốc độ bằng tần số góc chia số sóng, được mười bảy xen ti mét trên giây.',
        'Kết quả là mười bảy xen ti mét trên giây, tức không phẩy mười bảy mét trên giây. Không được ghi ngay mười bảy mét trên giây.',wave,src(2,1243))
    add('Năm gợn lồi liên tiếp','Sóng · từ tài liệu',
        'f = 120 Hz; năm gợn lồi liên tiếp\ncùng phía nguồn trải dài 0,5 m. Tính v.',
        'Từ gợn thứ nhất đến thứ năm có 4λ.\nλ = 0,5/4 = 0,125 m.',r'v=\lambda f=0{,}125\times120=15\,m/s',
        'Tốc độ truyền sóng: 15 m/s.\nNăm đỉnh liên tiếp ứng với bốn bước sóng.',
        'Nguồn rung có tần số một trăm hai mươi héc. Năm gợn lồi liên tiếp ở cùng phía nguồn trải dài nửa mét. Tìm tốc độ truyền sóng.',
        'Từ đỉnh thứ nhất đến đỉnh thứ năm có bốn bước sóng. Bước sóng bằng không phẩy năm chia bốn, được không phẩy một hai năm mét. Nhân với một trăm hai mươi héc, được mười lăm mét trên giây.',
        'Tốc độ là mười lăm mét trên giây. Luôn vẽ các đỉnh và đếm khoảng cách: năm đỉnh tạo bốn khoảng, không phải năm.',wave,src(2,1315))
    add('Sóng đi được bốn xen ti mét','Sóng · từ tài liệu',
        'f = 0,5 Hz; sóng đi 4 cm trong 8 s.\nTính tốc độ truyền sóng và bước sóng.',
        'Tốc độ v = quãng đường / thời gian.\nSau đó λ = v/f.',r'v=\frac48=0{,}5\,cm/s;\quad\lambda=\frac{0{,}5}{0{,}5}=1\,cm',
        'v = 0,5 cm/s; λ = 1 cm.\nĐây là tốc độ truyền sóng, không phải tốc độ vật.',
        'Đầu dây dao động với tần số không phẩy năm héc. Trong tám giây, sóng đi được bốn xen ti mét. Hãy tìm tốc độ sóng và bước sóng.',
        'Lấy quãng đường bốn xen ti mét chia tám giây, được tốc độ không phẩy năm xen ti mét trên giây. Bước sóng bằng tốc độ chia tần số, nên bằng một xen ti mét.',
        'Kết quả: tốc độ không phẩy năm xen ti mét trên giây và bước sóng một xen ti mét. Không nhầm tốc độ truyền sóng với tốc độ dao động của từng điểm trên dây.',wave,src(2,1340))
    add('Đo điện trở bằng định luật Ôm','Mạch điện · từ tài liệu',
        'U = 12 V; I = 6,3 A.\nTính điện trở của vật dẫn.',
        'Định luật Ôm: I = U/R.\nSuy ra R = U/I.',r'R=\frac UI=\frac{12}{6{,}3}\approx1{,}90\,\Omega',
        'Điện trở xấp xỉ 1,90 Ω.\nKhông đảo thành I/U khi tìm R.',
        'Hiệu điện thế giữa hai đầu vật dẫn là mười hai vôn, dòng điện qua vật dẫn là sáu phẩy ba am pe. Điện trở bằng bao nhiêu?',
        'Theo định luật Ôm, điện trở bằng hiệu điện thế chia cường độ dòng điện. Lấy mười hai chia sáu phẩy ba, ta được xấp xỉ một phẩy chín ôm.',
        'Điện trở xấp xỉ một phẩy chín ôm. Kiểm tra lại bằng cách nhân điện trở với dòng điện, ta thu được gần mười hai vôn.',circuit('U = 12 V','R = ?'),src(4,2750))
    add('Dòng điện qua điện trở ba ôm','Mạch điện · từ tài liệu',
        'U = 6 V; R = 3 Ω.\nTính cường độ dòng điện.',
        'Vật dẫn tuân theo định luật Ôm.\nDùng I = U/R.',r'I=\frac UR=\frac63=2\,A',
        'Cường độ dòng điện: 2 A.\nVới R không đổi, I tỉ lệ thuận với U.',
        'Đặt hiệu điện thế sáu vôn vào hai đầu điện trở ba ôm. Hãy tính dòng điện chạy qua điện trở.',
        'Áp dụng định luật Ôm: dòng điện bằng hiệu điện thế chia điện trở. Sáu chia ba bằng hai, đơn vị là am pe.',
        'Cường độ dòng điện bằng hai am pe. Khi điện trở không đổi, tăng hiệu điện thế bao nhiêu lần thì dòng điện tăng bấy nhiêu lần.',circuit('U = 6 V','R = 3 Ω'),src(4,3214))
    add('Điện lượng đi qua trong một giây','Mạch điện · từ tài liệu',
        'U = 12 V; R = 4 Ω.\nTính điện lượng qua điện trở trong 1 s.',
        'Tính I = U/R, rồi q = It.\nDòng điện không đổi trong khoảng xét.',r'I=3\,A;\qquad q=It=3\times1=3\,C',
        'Điện lượng trong mỗi giây: 3 C.\nAmpe đo dòng điện; culông đo điện lượng.',
        'Đặt mười hai vôn vào điện trở bốn ôm. Trong một giây, lượng điện tích đi qua điện trở là bao nhiêu?',
        'Trước hết tính dòng điện bằng mười hai chia bốn, được ba am pe. Điện lượng bằng cường độ dòng điện nhân thời gian. Ba nhân một bằng ba cu lông.',
        'Mỗi giây có điện lượng ba cu lông đi qua tiết diện điện trở. Phân biệt đơn vị am pe của dòng điện với cu lông của điện lượng.',circuit('U = 12 V','R = 4 Ω'),src(4,3251))
    add('Công suất và nhiệt lượng trên điện trở','Mạch điện · từ tài liệu',
        'U = 12 V; R = 8 Ω; t = 1 phút.\nTính công suất tỏa nhiệt và nhiệt lượng.',
        'P = U²/R. Đổi t = 60 s.\nĐiện trở thuần: Q = Pt.',r'P=\frac{12^2}{8}=18\,W;\quad Q=18\times60=1080\,J',
        'Công suất: 18 W; nhiệt lượng: 1080 J.\nPhải đổi phút sang giây khi tính Q bằng jun.',
        'Hiệu điện thế mười hai vôn đặt vào điện trở tám ôm trong một phút. Tính công suất tỏa nhiệt và nhiệt lượng tỏa ra.',
        'Công suất bằng hiệu điện thế bình phương chia điện trở: một trăm bốn mươi bốn chia tám bằng mười tám oát. Một phút bằng sáu mươi giây. Nhiệt lượng bằng công suất nhân thời gian.',
        'Công suất là mười tám oát, nhiệt lượng là một nghìn không trăm tám mươi jun. Quên đổi phút sang giây sẽ làm kết quả sai sáu mươi lần.',circuit('U = 12 V','R = 8 Ω'),src(4,5748))
    add('Tìm hai điện trở từ hai cách mắc','Mạch điện · từ tài liệu',
        'Cùng U = 12 V: nối tiếp có P = 4 W;\nsong song có P = 18 W. Tìm R₁ và R₂.',
        'Rnt = 36 Ω; Rss = 8 Ω.\nSuy ra R₁ + R₂ = 36; R₁R₂ = 288.',r'R^2-36R+288=0\ \Rightarrow\ R=12\,\Omega\ \text{hoặc}\ 24\,\Omega',
        'Hai điện trở: 12 Ω và 24 Ω (có thể đổi tên).\nKiểm tra: tổng 36 Ω; song song 8 Ω.',
        'Hai điện trở cùng đặt dưới mười hai vôn. Khi mắc nối tiếp, công suất là bốn oát; mắc song song, công suất là mười tám oát. Tìm hai điện trở.',
        'Dùng điện trở tương đương bằng hiệu điện thế bình phương chia công suất. Ta được nối tiếp ba mươi sáu ôm, song song tám ôm. Vậy tổng hai điện trở là ba mươi sáu, tích bằng hai trăm tám mươi tám. Giải phương trình bậc hai cho hai nghiệm mười hai và hai mươi bốn.',
        'Hai điện trở là mười hai ôm và hai mươi bốn ôm. Kiểm tra tổng bằng ba mươi sáu; tích chia tổng bằng tám. Hai cách mắc đều khớp công suất của đề.',{'type':'circuit','topology':'series','resistors':['R₁ = ?','R₂ = ?'],'labels':{'U':'U = 12 V'}},src(4,5854))
    assert len(lessons)==20
    return lessons

def setup():
    from dotenv import load_dotenv
    load_dotenv(ROOT.parent/'.env',override=False)
    os.environ.update(TTS_PROVIDER='gtts',TTS_LANG='vi',RENDER_WORKERS='1',FFMPEG_THREADS='1')
    if os.name=='nt':
        os.environ['PLAYWRIGHT_CHANNEL']='msedge'
        ff=Path(os.environ.get('LOCALAPPDATA',''))/'Temp/ffmpeg-static-win64-gpl/bin'
        if ff.exists():os.environ['PATH']=str(ff)+os.pathsep+os.environ['PATH']
    WORK.mkdir(parents=True,exist_ok=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render',action='store_true');args=parser.parse_args()
    setup()
    from botvideo import core
    from playwright.sync_api import sync_playwright
    lessons=collection()
    # Independent numeric checks on all families, including source-specific unit conversions.
    checks=[(2*math.pi/(2*math.pi),1),(6*math.cos(math.pi/3),3),(4*math.sqrt(25-9),16),(-25*.02,-.5),(.5*100*(.04**2-.02**2),.06),
            (2*math.pi*math.sqrt(.25/math.pi**2),1),(math.pi**2*9/(4*math.pi**2),2.25),(120/2,60),
            (math.pi**2/30,.3289868133696453),(1.5*math.sqrt(4),3),((.143-.124)*50,.95),(.5*4/5,.4),(8.5/.5,17),(.5/4*120,15),(4/8/.5,1),
            (12/6.3,1.9047619047619),(6/3,2),(12/4*1,3),(12**2/8*60,1080),(12*24/(12+24),8)]
    assert all(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-9) for a,b in checks)
    if not args.render:
        with sync_playwright() as p:
            browser=p.chromium.launch(channel=os.getenv('PLAYWRIGHT_CHANNEL') or None)
            page=browser.new_page(viewport={'width':1280,'height':720})
            for lesson in lessons:
                folder=WORK/lesson['id'];folder.mkdir(exist_ok=True)
                script=core.sanitize_script_for_render(copy.deepcopy(lesson['script']),original_problem=lesson['script']['problem'],subject='Vật lý')
                assert len(script['steps'])==3,(lesson['id'],len(script['steps']))
                for i,scene in enumerate(script['steps']):
                    path=folder/f'slide-{i+1}.html';core.render_scene_html(scene,i,path,script['design_template'])
                    page.goto(path.as_uri());page.evaluate('document.fonts.ready');page.wait_for_timeout(400)
                    core.check_slide_layout(page)
                    assert page.locator('.physics-svg').count()==1
                    assert page.locator('.katex-error').count()==0
                    page.screenshot(path=str(folder/f'slide-{i+1}.png'))
                print('PREFLIGHT',lesson['id'],flush=True)
            browser.close()
        (WORK/'preflight.json').write_text(json.dumps({'count':20,'slides':60,'sha256':hashlib.sha256(json.dumps(lessons,ensure_ascii=False).encode()).hexdigest()}),encoding='utf-8')
        return
    check=json.loads((WORK/'preflight.json').read_text())
    assert check['sha256']==hashlib.sha256(json.dumps(lessons,ensure_ascii=False).encode()).hexdigest(),'Run preflight for this exact collection first'
    from utils.video_store import VideoStore
    store=VideoStore();assert store.ready
    published=[]
    for lesson in lessons:
        folder=WORK/lesson['id'];job_id='20261013'+lesson['id'][-2:]
        done=folder/'published.json'
        if done.exists():published.append(json.loads(done.read_text(encoding='utf-8')));continue
        marker=folder/'render-started.txt'
        job_dir=core.MEDIA_DIR/job_id;video=job_dir/'result.mp4'
        if marker.exists():
            if not video.exists():raise RuntimeError('Render already attempted: '+lesson['id']+'; inspect before retrying.')
            print('RESUME UPLOAD, NO RENDER',lesson['id'],flush=True)
        else:
            marker.write_text(job_id)
            core.jobs[job_id]={'status':'queued'}
            print('RENDER',lesson['id'],lesson['title'],flush=True)
            core.render_job(job_id,copy.deepcopy(lesson['script']))
        info=core.probe_media_info(video);assert info['has_audio'] and info['duration']>15
        volume=subprocess.run([shutil.which('ffmpeg'),'-i',str(video),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True,check=True)
        assert 'mean_volume: -inf' not in volume.stderr
        (folder/'audio-check.txt').write_text(volume.stderr,encoding='utf-8')
        object_key=store.upload(job_id,video)
        import requests
        url=store.signed_url(object_key)
        with requests.get(url,headers={'Range':'bytes=0-1023'},stream=True,timeout=30) as response:
            response.raise_for_status();assert response.headers.get('Content-Type','').startswith('video/')
        poster=ROOT/'static/video_posters'/f'{lesson["id"]}.png';poster.parent.mkdir(exist_ok=True)
        shutil.copyfile(folder/'slide-1.png',poster)
        row={k:v for k,v in lesson.items() if k!='script'}
        row.update(object_key=object_key,duration=round(info['duration'],1),size_bytes=video.stat().st_size,poster=f'video_posters/{lesson["id"]}.png')
        done.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
        published.append(row)
        # Keep exactly one final MP4 per lesson; remove only this job's segment files.
        assert job_dir.resolve().is_relative_to(core.MEDIA_DIR.resolve())
        for intermediate in job_dir.glob('scene-*.mp4'):intermediate.unlink()
        for frames in job_dir.glob('frames-scene-*'):
            if frames.is_dir():shutil.rmtree(frames)
        print('UPLOADED',lesson['id'],row['size_bytes'],row['duration'],flush=True)
    DATA.write_text(json.dumps(published,ensure_ascii=False,indent=2),encoding='utf-8')
    print('COMPLETE',len(published),'bytes',sum(x['size_bytes'] for x in published),flush=True)

if __name__=='__main__':main()
