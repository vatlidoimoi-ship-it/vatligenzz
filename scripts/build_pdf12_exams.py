"""Reproducible grade-12 practice exams based on the supplied semester-II PDF."""
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
BATCH = 'pdf12-hk2-20x20-v1'
SOURCE = 'VẬT LÍ 12 CTM - GHÉP HỌC KÌ 2.pdf'
TOPICS = ['Từ trường và lực từ', 'Từ thông, cảm ứng điện từ và sóng điện từ',
          'Dòng điện xoay chiều, máy phát điện và máy biến áp',
          'Hạt nhân, phóng xạ và công nghiệp hạt nhân']


def fmt(x):
    return f'{x:.6g}'.replace('.', ',')


def numeric(stem, value, unit, explanation, page, kind, inputs, difficulty='TH', wrong=None):
    candidates = wrong if wrong is not None else [value / 2, value * 2, value * 4]
    values = [value] + candidates
    options = [f'{fmt(v)} {unit}'.strip() for v in values]
    assert len(set(options)) == 4, (stem, options)
    return dict(question=stem, choices=options,
                explanation=explanation + f' Kết quả: {fmt(value)} {unit}.',
                source_page=page, difficulty=difficulty,
                calculation=dict(kind=kind, inputs=inputs, result=value, unit=unit))


def theory(stem, correct, wrong, explanation, page):
    return dict(question=stem, choices=[correct] + wrong, explanation=explanation,
                source_page=page, difficulty='NB')


def magnetic(v):
    k = v + 2
    q = []
    def add(*a, **kw): q.append(numeric(*a, **kw))
    add(f'Dây dẫn dài 20 cm mang dòng điện {k} A, đặt vuông góc với từ trường đều B = 0,5 T. Lực từ tác dụng lên dây bằng bao nhiêu?',
        .1*k, 'N', 'Đổi l = 0,20 m. Dây vuông góc với B nên F = BIl.',24,'force',dict(B=.5,I=k,l=.2,s=1))
    add(f'Dây dài 40 cm mang dòng điện {k} A, hợp với vectơ cảm ứng từ B = 0,2 T một góc 30°. Tính độ lớn lực từ.',
        .04*k,'N','F = BIl sin(30°), với l = 0,40 m và sin(30°) = 0,5.',24,'force',dict(B=.2,I=k,l=.4,s=.5))
    add(f'Một dây dài 0,5 m mang dòng điện {k} A vuông góc với từ trường đều. Lực từ đo được là {fmt(.15*k)} N. Cảm ứng từ bằng bao nhiêu?',
        .3,'T',f'B = F/(Il) = {fmt(.15*k)}/({k} × 0,5).',25,'field_from_force',dict(F=.15*k,I=k,l=.5,s=1))
    add(f'Dây dài 25 cm đặt vuông góc với từ trường B = 0,4 T, chịu lực từ {fmt(.1*k)} N. Dòng điện qua dây có cường độ bao nhiêu?',
        k,'A','Đổi l = 0,25 m; từ F = BIl suy ra I = F/(Bl).',24,'current_from_force',dict(F=.1*k,B=.4,l=.25,s=1))
    add(f'Một phần dây thẳng mang dòng điện 4 A nằm vuông góc trong từ trường đều 0,5 T. Lực từ là {fmt(.2*k)} N. Chiều dài phần dây trong từ trường bằng bao nhiêu?',
        .1*k,'m','Chỉ phần dây trong từ trường chịu lực; l = F/(BI).',24,'length_from_force',dict(F=.2*k,B=.5,I=4,s=1))
    add(f'Dây dẫn chịu lực từ {k} N khi vuông góc với B. Giữ nguyên B, I và chiều dài dây, xoay dây để góc với B bằng 30°. Lực từ mới bằng bao nhiêu?',
        k/2,'N','F mới/F ban đầu = sin(30°)/sin(90°) = 1/2.',24,'scale',dict(base=k,factor=.5))
    add(f'Một dây dẫn có lực từ ban đầu {fmt(.02*k)} N. Giữ nguyên chiều dài và góc đặt dây, tăng dòng điện gấp 3 và cảm ứng từ gấp 2. Lực từ mới bằng bao nhiêu?',
        .12*k,'N','F tỉ lệ với BI khi chiều dài và góc không đổi; lực tăng 6 lần.',24,'scale',dict(base=.02*k,factor=6))
    add(f'Dây thẳng rất dài trong không khí mang dòng điện {k} A. Điểm M cách dây 5 cm. Cho B = 2×10⁻⁷ I/r (SI). B tại M bằng bao nhiêu μT?',
        4*k,'μT','Đổi r = 0,05 m; B = 2×10⁻⁷ I/r và 1 T = 10⁶ μT.',25,'wire_field',dict(I=k,r=.05))
    add(f'Cách dây thẳng rất dài mang dòng điện {k} A một khoảng r, cảm ứng từ bằng 10 μT. Dùng B = 2×10⁻⁷ I/r (SI). Tính r theo cm.',
        2*k,'cm','r = 2×10⁻⁷ I/B, với B = 10⁻⁵ T; đổi m sang cm.',25,'wire_distance',dict(I=k,B=1e-5))
    add(f'Điểm M cách dây thẳng dài 2 cm có cảm ứng từ {3*k} μT. Điểm N cách cùng dây 6 cm. Cường độ dòng điện không đổi. Cảm ứng từ tại N là bao nhiêu?',
        k,'μT','Với dây thẳng dài, B tỉ lệ nghịch r; B_N = B_M × 2/6.',25,'scale',dict(base=3*k,factor=1/3))
    add(f'Vòng dây tròn bán kính 10 cm trong không khí mang dòng điện {k} A. Cho B tại tâm = 2π×10⁻⁷ I/R và π = 3,14. Tính B theo μT.',
        6.28*k,'μT','Đổi R = 0,10 m; thay vào B = 2π×10⁻⁷ I/R rồi đổi sang μT.',25,'loop_field',dict(I=k,R=.1,N=1,pi=3.14))
    add(f'Cuộn dây tròn gồm {10*k} vòng sát nhau, bán kính 20 cm, dòng điện 2 A. Cho B tại tâm = 2π×10⁻⁷ NI/R, π = 3,14. B bằng bao nhiêu μT?',
        62.8*k,'μT','Các vòng cùng chiều tạo từ trường cộng nhau: B = 2π×10⁻⁷ NI/R.',25,'loop_field',dict(I=2,R=.2,N=10*k,pi=3.14))
    add(f'Ống dây dài 0,5 m gồm {200*k} vòng, mang dòng điện 1 A. Bỏ qua hiệu ứng ở hai đầu. Cho B = 4π×10⁻⁷ NI/l, π = 3,14. B trong ống bằng bao nhiêu mT?',
        .5024*k,'mT','Mật độ vòng n = N/l; B = 4π×10⁻⁷ nI. Đổi T sang mT.',26,'solenoid_field',dict(N=200*k,I=1,l=.5,pi=3.14))
    add(f'Thanh dẫn nằm ngang dài 0,5 m có khối lượng {10*k} g. Từ trường đều B = 0,2 T vuông góc với thanh. Chọn chiều dòng điện để lực từ hướng lên. Bỏ qua lực khác, lấy g = 10 m/s². Dòng điện bao nhiêu để thanh cân bằng?',
        k,'A','Cân bằng khi BIl = mg. Đổi khối lượng sang kg; I = mg/(Bl).',31,'levitate_current',dict(m=.01*k,g=10,B=.2,l=.5),difficulty='VD')
    add(f'Thanh dẫn dài 40 cm mang dòng điện {k} A trong từ trường 0,5 T vuông góc với thanh. Lực từ hướng lên cân bằng trọng lực. Lấy g = 10 m/s², bỏ qua lực khác. Khối lượng thanh bằng bao nhiêu gam?',
        20*k,'g','BIl = mg nên m = BIl/g (kg), sau đó nhân 1000 để đổi sang gam.',31,'levitate_mass',dict(B=.5,I=k,l=.4,g=10),difficulty='VD')
    add(f'Tại M có hai từ trường cùng phương cùng chiều, độ lớn lần lượt {k} μT và {k+3} μT. Cảm ứng từ tổng hợp có độ lớn bao nhiêu?',
        2*k+3,'μT','Hai vectơ cùng phương cùng chiều có độ lớn tổng bằng tổng hai độ lớn.',29,'parallel_fields',dict(B1=k,B2=k+3,sign=1),difficulty='VD')
    add(f'Tại N, hai vectơ cảm ứng từ vuông góc nhau có độ lớn {3*k} μT và {4*k} μT. Độ lớn vectơ tổng hợp bằng bao nhiêu?',
        5*k,'μT','Hai vectơ vuông góc: B = √(B₁² + B₂²), áp dụng bộ ba 3–4–5.',29,'perpendicular_fields',dict(B1=3*k,B2=4*k),difficulty='VD')
    add(f'Tại P, hai vectơ cảm ứng từ cùng phương ngược chiều có độ lớn {5*k} μT và {2*k} μT. Cảm ứng từ tổng hợp có độ lớn bao nhiêu?',
        3*k,'μT','Hai vectơ ngược chiều: B = |B₁ − B₂|; hướng theo vectơ lớn hơn.',29,'parallel_fields',dict(B1=5*k,B2=2*k,sign=-1),difficulty='VD')
    return q


def induction(v):
    k=v+2; q=[]
    def add(*a,**kw): q.append(numeric(*a,**kw))
    add(f'Vòng dây phẳng có diện tích {20*k} cm² đặt trong từ trường đều 0,5 T. Pháp tuyến cùng chiều B. Từ thông qua vòng bằng bao nhiêu mWb?',
        k,'mWb','S = số cm² × 10⁻⁴ m²; Φ = BS cos(0°). Đổi Wb sang mWb.',46,'flux',dict(B=.5,S=20*k*1e-4,c=1,N=1))
    add(f'Vòng dây diện tích {40*k} cm² trong từ trường đều 0,2 T; pháp tuyến hợp với B góc 60°. Từ thông qua vòng bằng bao nhiêu mWb?',
        .4*k,'mWb','Φ = BS cos(60°), với cos(60°) = 0,5 và S tính bằng m².',46,'flux',dict(B=.2,S=40*k*1e-4,c=.5,N=1))
    add(f'Mặt phẳng vòng dây diện tích {20*k} cm² hợp với B góc 30°. B = 0,4 T. Độ lớn từ thông qua vòng bằng bao nhiêu mWb?',
        .4*k,'mWb','Góc với pháp tuyến là 60° nên |Φ| = BS cos(60°) = BS/2.',46,'flux',dict(B=.4,S=20*k*1e-4,c=.5,N=1))
    add(f'Cuộn dây {50*k} vòng, mỗi vòng diện tích 20 cm². B = 0,1 T vuông góc với mặt vòng dây. Độ lớn tổng từ thông móc vòng NΦ bằng bao nhiêu mWb?',
        10*k,'mWb','Từ thông mỗi vòng là BS; tổng từ thông móc vòng là NBS.',46,'flux',dict(B=.1,S=.002,c=1,N=50*k))
    add(f'Từ thông qua một vòng dây giảm đều từ {6*k} mWb xuống {2*k} mWb trong 0,2 s. Độ lớn suất điện động cảm ứng là bao nhiêu V?',
        .02*k,'V','|e| = |ΔΦ|/Δt; đổi mWb sang Wb trước khi tính.',47,'faraday',dict(N=1,delta=.004*k,t=.2))
    add(f'Cuộn dây 100 vòng có từ thông qua mỗi vòng tăng đều thêm {k} mWb trong 0,5 s. Độ lớn suất điện động cảm ứng là bao nhiêu V?',
        .2*k,'V','|e| = N|ΔΦ|/Δt với ΔΦ là biến thiên từ thông của một vòng.',47,'faraday',dict(N=100,delta=.001*k,t=.5))
    add(f'Cuộn dây {100*k} vòng, diện tích mỗi vòng 50 cm², pháp tuyến cùng hướng B. B tăng đều từ 0,1 T lên 0,3 T trong 0,2 s. Tính độ lớn suất điện động cảm ứng.',
        .5*k,'V','|e| = NS|ΔB|/Δt; S = 0,005 m² và ΔB = 0,2 T.',47,'changing_field',dict(N=100*k,S=.005,deltaB=.2,t=.2))
    add(f'Vòng dây kín có điện trở {k} Ω, từ thông qua vòng biến thiên đều với tốc độ {3*k} Wb/s. Bỏ qua tự cảm. Dòng điện cảm ứng có độ lớn bao nhiêu?',
        3,'A','|e| = |dΦ/dt|; theo định luật Ohm, I = |e|/R.',50,'induced_current',dict(emf=3*k,R=k))
    add(f'Vòng dây kín điện trở 4 Ω có suất điện động cảm ứng không đổi {2*k} V. Bỏ qua tự cảm. Công suất tỏa nhiệt trên vòng bằng bao nhiêu?',
        k*k,'W','I = e/R và P = I²R = e²/R.',50,'joule_power',dict(emf=2*k,R=4))
    add(f'Vòng dây kín có điện trở 2 Ω, suất điện động cảm ứng không đổi {k} V trong 8 s. Bỏ qua tự cảm. Nhiệt lượng tỏa ra là bao nhiêu?',
        4*k*k,'J','Q = (e²/R)t, với e không đổi trong khoảng xét.',50,'joule_heat',dict(emf=k,R=2,t=8))
    add(f'Thanh dẫn dài 0,5 m chuyển động đều với tốc độ {k} m/s. Thanh, vận tốc và B đôi một vuông góc; B = 0,4 T. Suất điện động giữa hai đầu thanh bằng bao nhiêu?',
        .2*k,'V','Với ba phương đôi một vuông góc, suất điện động chuyển động e = Blv.',52,'motional_emf',dict(B=.4,l=.5,v=k))
    add(f'Thanh dẫn dài 0,4 m chuyển động với tốc độ {k} m/s trên hai ray trong từ trường 0,5 T; thanh, vận tốc và B đôi một vuông góc. Mạch kín có tổng điện trở 2 Ω, bỏ qua tự cảm. Dòng điện cảm ứng bằng bao nhiêu?',
        .1*k,'A','e = Blv; I = Blv/R với R là tổng điện trở mạch.',53,'motional_current',dict(B=.5,l=.4,v=k,R=2))
    add(f'Sóng điện từ truyền trong chân không có tần số {30*k} MHz. Cho c = 3×10⁸ m/s. Bước sóng bằng bao nhiêu mét (chọn giá trị gần nhất)?',
        10/k,'m','λ = c/f; 1 MHz = 10⁶ Hz.',47,'wavelength',dict(c=3e8,f=30*k*1e6))
    add(f'Sóng điện từ trong chân không có bước sóng {k} m. Cho c = 3×10⁸ m/s. Tần số bằng bao nhiêu MHz?',
        300/k,'MHz','f = c/λ, sau đó chia 10⁶ để đổi Hz sang MHz.',47,'frequency',dict(c=3e8,wavelength=k))
    add(f'Radar nhận sóng phản xạ sau {2*k} μs kể từ lúc phát. Cho c = 3×10⁸ m/s; bỏ qua thời gian xử lí. Vật phản xạ cách radar bao nhiêu mét?',
        300*k,'m','Sóng đi rồi quay lại nên 2d = ct, với t đổi sang giây.',47,'radar',dict(c=3e8,t=2*k*1e-6),difficulty='VD')
    add(f'Cuộn dây 200 vòng, mỗi vòng 10 cm², ban đầu pháp tuyến cùng chiều từ trường B = {fmt(.1*k)} T. Xoay cuộn để pháp tuyến vuông góc B trong 0,1 s. Độ lớn suất điện động cảm ứng trung bình là bao nhiêu?',
        .2*k,'V','Từ thông mỗi vòng giảm từ BS xuống 0: |e_tb| = NBS/Δt.',47,'faraday',dict(N=200,delta=.0001*k,t=.1),difficulty='VD')
    add(f'Vòng dây kín điện trở 5 Ω có từ thông thay đổi từ 0 đến {5*k} mWb. Bỏ qua tự cảm. Độ lớn điện lượng qua tiết diện dây trong quá trình này là bao nhiêu mC?',
        k,'mC','q = ∫I dt = |ΔΦ|/R; đổi Wb/Ω sang C rồi sang mC.',50,'induced_charge',dict(delta=.005*k,R=5),difficulty='VD')
    add(f'Khung dây có diện tích 0,02 m², pháp tuyến cùng chiều B. Từ trường tăng đều từ 0 lên {fmt(.1*k)} T. Để suất điện động cảm ứng trong một vòng là 0,04 V, thời gian tăng phải bằng bao nhiêu?',
        .05*k,'s','|e| = S|ΔB|/Δt nên Δt = S|ΔB|/|e|.',47,'induction_time',dict(S=.02,deltaB=.1*k,emf=.04),difficulty='VD')
    return q


def alternating(v):
    k=v+2; q=[]
    def add(*a,**kw): q.append(numeric(*a,**kw))
    add(f'Dòng điện có biểu thức i = {2*k}cos(100πt) A (t tính bằng s). Cường độ dòng điện cực đại là bao nhiêu?',
        2*k,'A','Biên độ đứng trước hàm cos chính là cường độ cực đại I₀.',79,'identity',dict(value=2*k),difficulty='NB')
    add(f'Điện áp u = {100*k}cos(100πt) V (t tính bằng s). Điện áp hiệu dụng bằng bao nhiêu V (làm tròn đến 0,01 V)?',
        round(100*k/math.sqrt(2),2),'V','Điện áp hình sin có U = U₀/√2.',79,'rms',dict(peak=100*k,round=2))
    add(f'Dòng điện hình sin có cường độ hiệu dụng {k} A. Cường độ cực đại bằng bao nhiêu A (làm tròn đến 0,01 A)?',
        round(k*math.sqrt(2),2),'A','Cường độ cực đại I₀ = I√2.',79,'peak',dict(rms=k,round=2))
    add(f'Dòng điện i = 3cos({20*k}πt) A, với t tính bằng giây. Tần số dòng điện bằng bao nhiêu?',
        10*k,'Hz','ω = 2πf nên f = (hệ số của π)/2.',78,'frequency_from_omega',dict(pi_coefficient=20*k))
    add(f'Điện áp hình sin có tần số {25*k} Hz. Chu kì điện áp bằng bao nhiêu ms (chọn giá trị gần nhất)?',
        40/k,'ms','T = 1/f (s); nhân 1000 để đổi sang mili giây.',78,'period_ms',dict(f=25*k))
    add(f'Dòng điện hình sin có chu kì {k} ms. Trong 1 giây, dòng điện thực hiện bao nhiêu chu kì (chọn giá trị gần nhất)?',
        1000/k,'chu kì','Số chu kì n = t/T, với T đổi từ ms sang s.',78,'cycles',dict(t=1,T=k*.001))
    add(f'Cho i = {2*k}cos(100πt) A. Tại t = 0 s, dòng điện có giá trị bao nhiêu?',
        2*k,'A','Tại t = 0, cos(0) = 1 nên i = I₀.',79,'instant_current',dict(peak=2*k,cos=1),wrong=[-2*k,k,0])
    add(f'Cho i = {2*k}cos(100πt) A. Tại t = 1/300 s, dòng điện có giá trị bao nhiêu?',
        k,'A','Pha là 100π/300 = π/3; cos(π/3) = 1/2.',79,'instant_current',dict(peak=2*k,cos=.5),wrong=[-k,2*k,-2*k])
    add(f'Điện trở thuần R = {10*k} Ω có dòng điện hình sin với cường độ hiệu dụng 2 A chạy qua. Công suất tỏa nhiệt trung bình bằng bao nhiêu?',
        40*k,'W','Với điện trở thuần, P = I²R và I là giá trị hiệu dụng.',79,'resistor_power',dict(I=2,R=10*k))
    add(f'Điện trở thuần 20 Ω chịu điện áp hình sin có giá trị hiệu dụng {20*k} V. Dòng điện hiệu dụng qua điện trở bằng bao nhiêu?',
        k,'A','Đối với điện trở thuần, I = U/R với các giá trị hiệu dụng.',79,'ohm',dict(U=20*k,R=20))
    add(f'Dòng điện hình sin có giá trị hiệu dụng {k} A chạy qua điện trở thuần 10 Ω trong 5 s. Nhiệt lượng tỏa ra bằng bao nhiêu?',
        50*k*k,'J','Định luật Joule–Lenz với dòng xoay chiều: Q = I²Rt, I là hiệu dụng.',79,'resistor_heat',dict(I=k,R=10,t=5))
    add(f'Máy biến áp lí tưởng có N₁ = 1000 vòng, N₂ = {100*k} vòng. Điện áp hiệu dụng sơ cấp 200 V. Điện áp hiệu dụng thứ cấp bằng bao nhiêu?',
        20*k,'V','Máy biến áp lí tưởng: U₂/U₁ = N₂/N₁.',93,'transformer_voltage',dict(U1=200,N1=1000,N2=100*k))
    add(f'Máy biến áp lí tưởng có U₁ = 220 V, U₂ = {22*k} V và N₁ = 1000 vòng. Cuộn thứ cấp có bao nhiêu vòng?',
        100*k,'vòng','N₂ = N₁U₂/U₁ theo tỉ số điện áp và số vòng.',93,'transformer_turns',dict(N1=1000,U1=220,U2=22*k))
    add(f'Máy biến áp lí tưởng đang cấp tải có U₁ = 200 V, U₂ = 100 V và I₂ = {k} A. Tải thuần trở. Cường độ hiệu dụng sơ cấp bằng bao nhiêu?',
        k/2,'A','Bảo toàn công suất của máy lí tưởng: U₁I₁ = U₂I₂.',93,'transformer_current',dict(U1=200,U2=100,I2=k),difficulty='VD')
    add(f'Truyền công suất {10*k} kW ở điện áp hiệu dụng 1000 V, hệ số công suất bằng 1. Tổng điện trở đường dây 2 Ω. Công suất hao phí bằng bao nhiêu?',
        200*k*k,'W','I = P/U; ΔP = I²R, đổi kW sang W trước khi tính.',93,'transmission_loss',dict(P=10000*k,U=1000,R=2),difficulty='VD')
    add(f'Đường dây đang hao phí {100*k*k} W. Giữ nguyên công suất truyền, hệ số công suất và điện trở đường dây; tăng điện áp truyền tải gấp {k} lần. Hao phí mới bằng bao nhiêu?',
        100,'W','ΔP tỉ lệ nghịch U² khi các đại lượng còn lại không đổi: ΔP mới = ΔP cũ/k².',93,'loss_scale',dict(loss=100*k*k,ratio=k),difficulty='VD')
    add(f'Khung dây {100*k} vòng, diện tích mỗi vòng 0,01 m², quay đều với tốc độ góc 100 rad/s trong từ trường 0,2 T. Trục quay nằm trong mặt phẳng khung và vuông góc B. Suất điện động cực đại bằng bao nhiêu?',
        20*k,'V','Từ thông móc vòng có biên độ NBS; e₀ = NBSω.',78,'generator_peak',dict(N=100*k,B=.2,S=.01,omega=100),difficulty='VD')
    add(f'Máy phát điện xoay chiều có {k} cặp cực. Rôto quay 600 vòng/phút. Tần số suất điện động tạo ra bằng bao nhiêu?',
        10*k,'Hz','Mỗi vòng quay tạo p chu kì: f = pn/60 với n tính bằng vòng/phút.',97,'generator_frequency',dict(p=k,rpm=600),difficulty='VD')
    return q


def nuclear(v):
    k=v+2; q=[]
    def add(*a,**kw): q.append(numeric(*a,**kw))
    nuclei=[(23,11,'Na'),(27,13,'Al'),(56,26,'Fe'),(63,29,'Cu'),(208,82,'Pb')]
    A,Z,symbol=nuclei[v]
    add(f'Hạt nhân {symbol} có số khối A = {A}, số proton Z = {Z}. Số neutron là bao nhiêu?',
        A-Z,'neutron','Số khối A = Z + N nên số neutron N = A − Z.',110,'neutrons',dict(A=A,Z=Z),difficulty='NB',wrong=[A,Z,A+Z])
    add(f'Nguyên tử {symbol} trung hòa có hạt nhân gồm {Z} proton và {A-Z} neutron. Vỏ nguyên tử có bao nhiêu electron?',
        Z,'electron','Nguyên tử trung hòa có số electron bằng số proton của hạt nhân.',110,'identity',dict(value=Z),difficulty='NB',wrong=[A,A-Z,A+Z])
    add(f'Hạt nhân có điện tích +{Z}e, với e = 1,6×10⁻¹⁹ C. Điện tích hạt nhân tính theo đơn vị 10⁻¹⁹ C bằng bao nhiêu?',
        1.6*Z,'(×10⁻¹⁹ C)','Điện tích hạt nhân q = Ze; nhân Z với 1,6 để được hệ số cần tìm.',110,'nuclear_charge',dict(Z=Z))
    add(f'Hạt nhân giả định có số khối {4*k} và năng lượng liên kết {32*k} MeV. Năng lượng liên kết riêng bằng bao nhiêu?',
        8,'MeV/nucleon','Năng lượng liên kết riêng ε = E_lk/A.',123,'binding_per_nucleon',dict(E=32*k,A=4*k))
    add(f'Hạt nhân có độ hụt khối {fmt(.01*k)} u. Cho 1 u·c² = 931,5 MeV. Năng lượng liên kết bằng bao nhiêu?',
        9.315*k,'MeV','E_lk = Δm·c² = Δm(u) × 931,5 MeV.',123,'mass_energy',dict(dm=.01*k,conversion=931.5))
    add(f'Một phản ứng hạt nhân có tổng khối lượng trước phản ứng lớn hơn sau phản ứng {fmt(.002*k)} u. Cho 1 u·c² = 931,5 MeV. Năng lượng tỏa ra là bao nhiêu?',
        1.863*k,'MeV','Q = (m_trước − m_sau)c² > 0, nên phản ứng tỏa năng lượng.',124,'mass_energy',dict(dm=.002*k,conversion=931.5))
    parents=[(238,92),(226,88),(210,84),(222,86),(232,90)]
    a,z=parents[v]
    add(f'Hạt nhân mẹ có A = {a}, Z = {z}, phân rã alpha một lần. Số khối hạt nhân con là bao nhiêu?',
        a-4,'','Hạt alpha mang số khối 4; bảo toàn số nucleon cho A_con = A_mẹ − 4.',142,'alpha_A',dict(A=a),wrong=[a,a-2,a+4])
    beta=[(14,6),(32,15),(60,27),(131,53),(90,38)]
    a,z=beta[v]
    add(f'Hạt nhân A = {a}, Z = {z} phân rã beta trừ (β⁻). Số proton của hạt nhân con là bao nhiêu?',
        z+1,'proton','Trong β⁻, một neutron chuyển thành proton; Z tăng 1, A không đổi.',142,'beta_Z',dict(Z=z),wrong=[z,z-1,z+2])
    add(f'Mẫu phóng xạ ban đầu có {8*k} mg đồng vị mẹ. Sau 3 chu kì bán rã, khối lượng đồng vị mẹ còn lại là bao nhiêu?',
        k,'mg','m = m₀·2⁻³ = m₀/8; chỉ tính đồng vị mẹ còn lại.',143,'decay_remaining',dict(initial=8*k,halflives=3))
    add(f'Mẫu có {4*k}×10¹² hạt nhân mẹ lúc đầu. Sau 2 chu kì bán rã, số hạt nhân mẹ đã phân rã bằng bao nhiêu (đơn vị 10¹² hạt)?',
        3*k,'(×10¹² hạt)','ΔN = N₀(1 − 2⁻²) = 3N₀/4.',143,'decay_lost',dict(initial=4*k,halflives=2))
    add(f'Đồng vị có chu kì bán rã {k} giờ. Bao lâu thì số hạt nhân mẹ còn 12,5% ban đầu?',
        3*k,'giờ','12,5% = 1/8 = 2⁻³ nên thời gian bằng 3 chu kì bán rã.',143,'elapsed_halflives',dict(T=k,n=3))
    add(f'Mẫu phóng xạ có hoạt độ ban đầu {800*k} Bq. Sau 3 chu kì bán rã, hoạt độ bằng bao nhiêu?',
        100*k,'Bq','Hoạt độ tuân theo cùng quy luật H = H₀ × 2^(−t/T); ở đây H = H₀/8.',144,'decay_remaining',dict(initial=800*k,halflives=3))
    add(f'Chất phóng xạ có chu kì bán rã {100*k} s. Lấy ln2 = 0,693. Hằng số phóng xạ bằng bao nhiêu s⁻¹ (chọn giá trị gần nhất)?',
        .00693/k,'s⁻¹','λ = ln2/T; T đã tính bằng giây.',144,'decay_constant',dict(T=100*k,ln2=.693))
    add(f'Mẫu chứa {k}×10¹² hạt nhân phóng xạ, có hằng số phóng xạ 2×10⁻⁶ s⁻¹. Hoạt độ mẫu bằng bao nhiêu MBq?',
        2*k,'MBq','H = λN (Bq); 1 MBq = 10⁶ Bq.',144,'activity',dict(N=k*1e12,lam=2e-6),difficulty='VD')
    add(f'Mẫu gỗ cổ có hoạt độ riêng C-14 bằng 1/{2**k} mẫu gỗ mới cùng loại. Giả sử hoạt độ ban đầu như gỗ mới, mẫu kín sau khi chết; T = 5730 năm. Tuổi mẫu gỗ là bao nhiêu?',
        5730*k,'năm','H/H₀ = 2⁻ᵗ/ᵀ; tỉ số cho trước là 2⁻ᵏ nên t = kT.',171,'elapsed_halflives',dict(T=5730,n=k),difficulty='VD')
    add(f'Nguồn phóng xạ điểm phát đều mọi hướng. Ở khoảng cách 1 m, suất liều là {10*k*k} μSv/h. Bỏ qua hấp thụ và tán xạ. Ở khoảng cách {k} m, suất liều bằng bao nhiêu?',
        10,'μSv/h','Suất liều tỉ lệ nghịch bình phương khoảng cách: D₂ = D₁(r₁/r₂)².',144,'dose_distance',dict(dose=10*k*k,r1=1,r2=k),difficulty='VD')
    add(f'Nhà máy điện hạt nhân có công suất nhiệt {100*k} MW và hiệu suất chuyển thành điện 30%. Công suất điện bằng bao nhiêu?',
        30*k,'MW','Công suất có ích P_điện = ηP_nhiệt, với η = 0,30.',181,'efficiency',dict(input=100*k,eta=.3),difficulty='VD')
    add(f'Có {k}×10¹⁸ phản ứng phân hạch, mỗi phản ứng tỏa 200 MeV. Lấy 1 MeV = 1,6×10⁻¹³ J. Tổng năng lượng tỏa ra bằng bao nhiêu MJ?',
        32*k,'MJ','E = NQ; đổi MeV sang J rồi chia 10⁶ để đổi sang MJ.',181,'fission_energy',dict(N=k*1e18,Q=200,conversion=1.6e-13),difficulty='VD')
    return q


THEORY = [
 [
 ('Đại lượng nào đặc trưng cho từ trường về mặt tác dụng lực tại một điểm?', 'Vectơ cảm ứng từ', ['Điện thế','Điện trở suất','Điện dung'], 'Vectơ cảm ứng từ B mô tả hướng và độ mạnh của từ trường về tác dụng lực.',4),
 ('Đường sức từ bên ngoài một thanh nam châm có chiều nào?', 'Từ cực Bắc đến cực Nam', ['Từ cực Nam đến cực Bắc','Luôn hướng từ dưới lên trên','Luôn hướng từ trái sang phải'], 'Bên ngoài nam châm, đường sức đi ra từ cực Bắc và đi vào cực Nam.',4),
 ('Dùng quy tắc nào xác định chiều từ trường quanh dây dẫn thẳng mang dòng điện?', 'Quy tắc nắm tay phải', ['Quy tắc bàn tay trái','Định luật bảo toàn điện tích','Quy tắc cộng điện trở nối tiếp'], 'Nắm tay phải, ngón cái chỉ chiều dòng điện; các ngón còn lại chỉ chiều đường sức.',5),
 ('Hai dây thẳng dài song song mang dòng điện cùng chiều tương tác như thế nào?', 'Hút nhau', ['Đẩy nhau','Không tương tác từ','Luôn xoắn quanh nhau'], 'Từ trường của mỗi dòng điện tác dụng lên dòng điện kia; hai dòng song song cùng chiều hút nhau.',25),
 ('Một đoạn dây mang dòng điện đặt song song với vectơ B trong từ trường đều. Lực từ lên dây là bao nhiêu?', 'Bằng không', ['Bằng BIl','Bằng 2BIl','Luôn bằng trọng lượng dây'], 'F = BIl sin α; khi dây song song với B thì α = 0° hoặc 180°, sin α = 0.',24),
 ('Trong từ trường đều, các đường sức từ được biểu diễn như thế nào?', 'Các đường thẳng song song, cùng chiều và cách đều', ['Các đường tròn đồng tâm','Các đường thẳng cắt nhau','Các đường thẳng có chiều xen kẽ'], 'Từ trường đều có cùng vectơ B tại mọi điểm nên các đường sức thẳng, song song, cùng chiều và đều nhau.',5),
 ('Chiều lực từ tác dụng lên đoạn dây mang dòng điện được xác định bằng quy tắc nào?', 'Quy tắc bàn tay trái', ['Quy tắc nắm tay phải để xác định B','Định luật Ohm','Quy tắc đổi đơn vị'], 'Đặt bàn tay trái để B xuyên vào lòng bàn tay, các ngón theo dòng điện; ngón cái chỉ chiều lực từ.',24),
 ('Giữ nguyên dây và từ trường, chỉ đảo chiều dòng điện. Lực từ thay đổi thế nào nếu ban đầu khác không?', 'Đảo chiều và giữ nguyên độ lớn', ['Giữ cả chiều và độ lớn','Tăng độ lớn gấp đôi','Triệt tiêu hoàn toàn'], 'Lực từ phụ thuộc hướng dòng điện; đảo I làm đảo vectơ lực, còn B, |I|, l và sin α không đổi.',24),
 ('Đơn vị SI của cảm ứng từ là gì?', 'Tesla (T)', ['Weber (Wb)','Volt (V)','Ampere (A)'], 'Cảm ứng từ B đo bằng tesla, với 1 T = 1 N/(A·m).',25),
 ('Tại một điểm có từ trường khác không, vectơ B có phương như thế nào với đường sức qua điểm đó?', 'Tiếp tuyến với đường sức tại điểm đó', ['Luôn vuông góc đường sức','Luôn thẳng đứng','Luôn hướng về tâm Trái Đất'], 'Theo định nghĩa đường sức, tiếp tuyến tại mỗi điểm trùng phương của vectơ B tại điểm đó.',4),
 ],
 [
 ('Trong Φ = BS cos α, góc α được đo giữa hai hướng nào?', 'Vectơ B và pháp tuyến của mặt vòng dây', ['Vectơ B và mặt phẳng vòng dây','Dòng điện và mặt phẳng vòng dây','Lực từ và chiều dòng điện'], 'Công thức từ thông dùng góc giữa cảm ứng từ và pháp tuyến, không phải góc với mặt phẳng.',46),
 ('Đơn vị SI của từ thông là gì?', 'Weber (Wb)', ['Tesla (T)','Watt (W)','Coulomb (C)'], 'Từ thông Φ = BS cos α có đơn vị Wb = T·m².',46),
 ('Điều kiện gây suất điện động cảm ứng trong vòng dây là gì?', 'Từ thông qua vòng biến thiên theo thời gian', ['Từ thông có giá trị lớn nhưng không đổi','Vòng dây chỉ cần nằm yên trong từ trường đều không đổi','Điện trở vòng dây bằng không'], 'Theo Faraday, e phụ thuộc tốc độ biến thiên từ thông; từ thông không đổi không tạo suất điện động cảm ứng.',47),
 ('Theo định luật Lenz, từ trường của dòng điện cảm ứng có tác dụng nào?', 'Chống lại sự biến thiên từ thông gây ra nó', ['Luôn ngược chiều từ trường ngoài','Luôn cùng chiều từ trường ngoài','Luôn làm tăng từ thông ban đầu'], 'Lenz nói chống lại sự biến thiên từ thông, nên hướng từ trường cảm ứng phụ thuộc từ thông đang tăng hay giảm.',47),
 ('Vòng dây kín đứng yên trong từ trường đều không đổi; diện tích và góc đặt vòng không đổi. Dòng điện cảm ứng thế nào?', 'Không xuất hiện', ['Luôn tăng đều','Luôn giảm đều','Luôn có cường độ khác không'], 'B, S và α không đổi nên Φ không đổi; suất điện động và dòng điện cảm ứng bằng không.',46),
 ('Cắt hở một vòng dây rồi làm từ thông qua diện tích vòng biến thiên. Nhận xét nào đúng?', 'Có thể có suất điện động cảm ứng nhưng không có dòng điện chạy vòng quanh mạch hở', ['Không thể có suất điện động cảm ứng','Dòng điện vẫn chạy vòng quanh mạch hở như mạch kín','Điện trở của mạch hở bằng không'], 'Từ thông biến thiên tạo suất điện động; dòng điện chạy quanh vòng cần một mạch dẫn kín.',47),
 ('Sóng điện từ có thể truyền trong môi trường nào sau đây?', 'Chân không', ['Chỉ trong chất rắn','Chỉ trong chất lỏng','Chỉ trong kim loại'], 'Sóng điện từ là sự lan truyền điện từ trường và có thể truyền trong chân không.',47),
 ('Trong sóng điện từ phẳng, vectơ điện trường và vectơ từ trường có quan hệ nào?', 'Vuông góc nhau và đều vuông góc phương truyền', ['Song song nhau và song song phương truyền','Song song nhau nhưng vuông góc phương truyền','Một vectơ luôn bằng không'], 'Sóng điện từ là sóng ngang: E, B và phương truyền đôi một vuông góc.',47),
 ('Tại một điểm trong sóng điện từ hình sin truyền trong chân không, E và B dao động thế nào?', 'Cùng pha', ['Ngược pha','Lệch pha π/2','Có hai tần số khác nhau'], 'Điện trường và từ trường của sóng điện từ trong chân không biến thiên cùng pha tại cùng một điểm.',47),
 ('Đưa cực Bắc nam châm lại gần mặt một vòng dây kín. Nhìn từ phía nam châm, mặt vòng dây sẽ tương đương cực nào để chống lại chuyển động đến gần?', 'Cực Bắc', ['Cực Nam','Không thể xuất hiện cực từ','Luôn đổi cực dù nam châm chuyển động đều một chiều'], 'Theo Lenz, vòng dây tạo từ trường chống lại sự tăng từ thông; mặt gần nam châm thành cực Bắc để đẩy cực Bắc đang đến.',47),
 ],
 [
 ('Cường độ dòng điện xoay chiều hình sin biến thiên theo thời gian như thế nào?', 'Theo hàm sin hoặc cos', ['Luôn không đổi','Luôn tăng tuyến tính','Chỉ nhận giá trị dương'], 'Dòng xoay chiều hình sin có dạng i = I₀cos(ωt + φ), biến thiên điều hòa và đổi chiều tuần hoàn.',78),
 ('Ampe kế xoay chiều thông thường được hiệu chuẩn cho dòng hình sin chỉ giá trị nào?', 'Cường độ hiệu dụng', ['Cường độ cực đại','Giá trị tức thời tại t = 0','Trung bình đại số trong một chu kì'], 'Số chỉ ampe kế xoay chiều là giá trị hiệu dụng, liên hệ I = I₀/√2 đối với dòng hình sin.',79),
 ('Máy phát điện xoay chiều hoạt động dựa trên hiện tượng nào?', 'Cảm ứng điện từ', ['Phóng xạ alpha','Nhiệt hạch','Nhiễm điện do cọ xát'], 'Sự biến thiên từ thông qua cuộn dây sinh suất điện động cảm ứng trong máy phát.',92),
 ('Bộ phận tạo từ trường trong máy phát điện xoay chiều gọi là gì?', 'Phần cảm', ['Phần ứng','Tải tiêu thụ','Bộ chỉnh lưu'], 'Phần cảm là nam châm điện hoặc nam châm vĩnh cửu tạo từ trường; phần ứng là cuộn dây xuất hiện suất điện động.',92),
 ('Bộ phận đứng yên của máy phát điện được gọi là gì?', 'Stato', ['Rôto','Piston','Thanh điều khiển'], 'Stato là phần đứng yên; rôto là phần quay quanh trục của máy phát điện.',92),
 ('Máy biến áp lí tưởng có số vòng thứ cấp lớn hơn sơ cấp. Máy này là loại nào?', 'Máy tăng áp', ['Máy hạ áp','Máy đổi tần số','Máy chỉnh lưu'], 'U₂/U₁ = N₂/N₁ > 1 nên điện áp thứ cấp cao hơn sơ cấp: máy tăng áp.',93),
 ('Lõi máy biến áp được ghép từ các lá thép mỏng cách điện nhằm mục đích gì?', 'Giảm hao phí do dòng điện xoáy', ['Tăng dòng điện xoáy đến cực đại','Biến điện xoay chiều thành một chiều','Triệt tiêu hoàn toàn từ thông'], 'Các lá cách điện hạn chế vòng dòng điện xoáy trong lõi, giảm công suất tỏa nhiệt hao phí.',92),
 ('Máy biến áp thông thường có thể duy trì điện áp cảm ứng thứ cấp khi cấp nguồn nào?', 'Nguồn điện xoay chiều', ['Nguồn điện một chiều không đổi sau khi đã ổn định','Pin một chiều với dòng điện không đổi mãi','Nguồn không tạo từ thông biến thiên'], 'Máy biến áp cần từ thông biến thiên; nguồn xoay chiều tạo từ thông biến thiên liên tục trong lõi.',92),
 ('Tăng điện áp truyền tải khi giữ nguyên công suất và hệ số công suất giúp giảm hao phí chủ yếu vì sao?', 'Dòng điện trên đường dây giảm', ['Điện trở đường dây trở thành bằng không','Dòng điện trên đường dây tăng','Tần số tăng theo điện áp'], 'I = P/(U cos φ) giảm khi U tăng; hao phí I²R vì vậy giảm.',93),
 ('Khi phát hiện chỗ dây điện bị hở, cách xử lí phù hợp là gì?', 'Ngắt nguồn điện trước khi xử lí chỗ hở', ['Chạm tay ướt để kiểm tra','Dùng tay trần giữ chỗ hở khi có điện','Tiếp tục dùng vì điện xoay chiều không nguy hiểm'], 'Cần cắt nguồn trước khi xử lí dây hở; không chạm vào phần dẫn điện khi chưa ngắt điện.',93),
 ],
 [
 ('Các đồng vị của cùng một nguyên tố có đặc điểm nào?', 'Cùng số proton, khác số neutron', ['Cùng số neutron, khác số proton','Cùng số khối và khác số proton','Có số electron luôn bằng không'], 'Đồng vị có cùng Z và khác A, tương ứng cùng số proton nhưng khác số neutron.',110),
 ('Phần lớn hạt alpha xuyên qua lá vàng trong thí nghiệm Rutherford cho thấy điều gì?', 'Phần lớn thể tích nguyên tử là khoảng trống', ['Điện tích dương phân bố đều khắp nguyên tử','Hạt nhân chiếm toàn bộ thể tích nguyên tử','Nguyên tử không có hạt nhân'], 'Phần lớn alpha đi qua vì hạt nhân rất nhỏ so với nguyên tử; rất ít hạt gặp gần hạt nhân bị lệch mạnh.',109),
 ('Đại lượng nào thường dùng để so sánh mức độ bền vững của các hạt nhân?', 'Năng lượng liên kết riêng', ['Chỉ số neutron','Chỉ tổng năng lượng liên kết mà không xét số nucleon','Thể tích bình chứa mẫu'], 'Năng lượng liên kết tính trên một nucleon càng lớn thì hạt nhân nhìn chung càng bền vững.',123),
 ('Trong phản ứng hạt nhân, đại lượng nào sau đây được bảo toàn?', 'Tổng điện tích', ['Tổng khối lượng nghỉ trong mọi phản ứng','Số neutron riêng rẽ trong mọi phản ứng','Tổng động năng trong mọi phản ứng'], 'Phản ứng hạt nhân bảo toàn điện tích và số nucleon; khối lượng nghỉ có thể chuyển thành năng lượng.',123),
 ('Bản chất của tia gamma là gì?', 'Bức xạ điện từ', ['Chùm hạt nhân helium','Chùm electron','Chùm proton'], 'Gamma là photon năng lượng cao, không mang điện và là bức xạ điện từ.',143),
 ('Một hạt nhân phát gamma đơn thuần chuyển từ mức kích thích xuống mức thấp hơn. A và Z thay đổi thế nào?', 'Cả A và Z đều không đổi', ['A giảm 4 và Z giảm 2','A không đổi và Z tăng 1','A giảm 1 và Z không đổi'], 'Phát gamma chỉ làm giảm năng lượng kích thích của hạt nhân, không đổi số nucleon hay điện tích.',143),
 ('Chu kì bán rã là khoảng thời gian để đại lượng nào giảm còn một nửa?', 'Số hạt nhân mẹ chưa phân rã', ['Tổng số proton của cả mẫu và mọi sản phẩm luôn giảm một nửa','Khối lượng bình đựng mẫu','Năng lượng của từng photon gamma'], 'Chu kì bán rã T đặc trưng thời gian số hạt nhân mẹ còn lại giảm còn 1/2 giá trị đầu khoảng xét.',143),
 ('Thanh điều khiển chứa boron hoặc cadmium trong lò phản ứng có vai trò chủ yếu nào?', 'Hấp thụ bớt neutron để điều khiển phản ứng dây chuyền', ['Tạo thêm neutron vô hạn','Chuyển điện năng thành nhiên liệu','Loại bỏ toàn bộ chất thải ngay lập tức'], 'Thanh điều khiển hấp thụ neutron, giúp điều chỉnh hệ số nhân neutron và công suất lò.',124),
 ('Biện pháp nào phù hợp với nguyên tắc an toàn phóng xạ?', 'Giảm thời gian tiếp xúc, tăng khoảng cách và dùng che chắn thích hợp', ['Tăng thời gian tiếp xúc để cơ thể quen dần','Đứng sát nguồn khi không có che chắn','Bỏ qua biển cảnh báo nếu nguồn không phát sáng'], 'An toàn phóng xạ dựa trên thời gian, khoảng cách và che chắn để giảm phơi nhiễm.',144),
 ('Chiếu xạ thực phẩm với quy trình và liều phù hợp có mục đích nào?', 'Diệt vi sinh vật và ức chế nảy mầm để bảo quản', ['Biến mọi thực phẩm thành nguồn phóng xạ mạnh','Làm thực phẩm tự phát điện','Tạo phản ứng phân hạch trong thực phẩm'], 'Tài liệu nêu chiếu xạ giúp diệt vi sinh vật, hạn chế nảy mầm và kéo dài thời gian bảo quản khi dùng đúng liều.',180),
 ],
]


def build():
    import pymupdf
    source=ROOT/'datatm'/SOURCE
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    with pymupdf.open(source) as pdf:
        pages=[page.get_text() for page in pdf]
    exams=[]
    for group, make in enumerate([magnetic,induction,alternating,nuclear]):
        for variant in range(5):
            number=group*5+variant+1
            questions=[theory(*args) for args in THEORY[group][variant*2:variant*2+2]]+make(variant)
            assert len(questions)==20
            rng=random.Random(12000+number)
            answer_slots=list('ABCD')*5; rng.shuffle(answer_slots)
            for idx,question in enumerate(questions,1):
                choices=question.pop('choices'); correct=choices[0]; wrong=choices[1:]; rng.shuffle(wrong)
                answer=answer_slots[idx-1]; options={}
                for letter in 'ABCD': options[letter]=correct if letter==answer else wrong.pop()
                page=question['source_page']
                quote=' '.join(pages[page-1].split())[:350].rsplit(' ',1)[0]
                question.update(id=idx,number=idx,options=options,correct_answer=answer,
                    source_file=SOURCE,source_printed_page=page-1,source_quote=quote,
                    source_relation='Biên soạn theo kiến thức/bài tập ở trang nguồn; số liệu được tạo mới.')
            exams.append(dict(id=f'exam_li12_pdf_{number:02}',
                title=f'Vật lí 12 · Đề {number:02}: {TOPICS[group]} — Bài luyện {variant+1}',
                grade='12',time_limit=30,topic=TOPICS[group],
                description='20 câu trắc nghiệm, 30 phút, thang điểm 10. Ôn tập học kì II theo tài liệu được cung cấp; mỗi câu có một đáp án đúng.',
                source_file=SOURCE,source_sha256=digest,batch_id=BATCH,
                created_at='2026-10-16T00:00:00+07:00',created_by=None,
                review_status='pending',
                review_method='Biên soạn và rà soát bằng AI; kiểm tra công thức, nguồn PDF, cấu trúc và luồng chấm điểm tự động.',
                scoring_config={'multiple_choice':{'weight_percent':100,'points':10}},questions=questions))
    return {'batch_id':BATCH,'exams':exams}


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def write_docs(bank):
    lines=['# 20 đề trắc nghiệm Vật lí 12 — Học kì II','',
           'Mỗi đề: 20 câu, 30 phút, 10 điểm; mỗi câu đúng được 0,5 điểm.',
           'Biên soạn theo PDF được cung cấp, không phải chép nguyên đề. Có các bài cùng dạng với số liệu khác nhau giữa các đề luyện.',
           'Trang PDF tính từ 1; số trang in trong tài liệu bằng trang PDF trừ 1.',
           'Đáp án được rà soát bằng AI và kiểm tra tự động; chưa có thẩm định riêng của giáo viên.','']
    for e in bank['exams']:
        lines += [f'## {e["title"]}','']
        for q in e['questions']:
            lines += [f'**Câu {q["number"]}.** {q["question"]}','']
            lines += [f'- {k}. {v}' for k,v in q['options'].items()]
            lines += ['']
        lines += ['### Đáp án và giải thích','']
        for q in e['questions']:
            lines += [f'**{q["number"]}. {q["correct_answer"]}** — {q["explanation"]} (PDF trang {q["source_page"]}.)','']
    (ROOT/'docs/pdf-exams-grade12.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__':
    bank=build()
    save(ROOT/'data/pdf_exams_grade12.json',bank)
    write_docs(bank)
    print('Built 20 exams / 400 questions / 30 minutes each. Awaiting validation; nothing published.')
