// Questionnaire content is supplied by the server from the configured data store.
// Scoring stays deterministic; answers remain in browser memory.
export let packages = [];
let dimensions = {};
export function configureAssessments(catalog) {
    if (catalog?.version !== 1 || !Array.isArray(catalog.packages) || catalog.packages.length !== 5 || !catalog.dimensions) {
        throw new Error('Invalid assessment catalog');
    }
    packages = catalog.packages;
    dimensions = catalog.dimensions;
}
export function scoreAssessment(id, answers) {
    const pack = packages.find(p => p.id === id);
    if (!pack || !pack.items.length) throw new Error('Gói này không có bài tự chấm.');
    if (!Array.isArray(answers) || answers.length !== pack.items.length || Array.from(answers).some(a => !Number.isInteger(a) || a < pack.min || a >= pack.min + pack.options.length)) throw new Error('Bạn cần trả lời đầy đủ các câu hỏi.');
    if (id === 'who-5') {
        const raw = answers.reduce((sum, a) => sum + a, 0);
        return {title: 'Một lát cắt của hai tuần gần đây', rows: [{label: 'Sự khỏe mạnh tinh thần', value: raw * 4, detail: `${raw}/25 điểm gốc × 4 = ${raw * 4}/100. Đây là điểm thang đo, không phải xác suất mắc bệnh.`}],
            message: raw < 13 ? 'Điểm dưới 50/100 là gợi ý nên trao đổi thêm với chuyên viên về sức khỏe tinh thần. Điểm này không kết luận bạn mắc bệnh. Bạn có thể bắt đầu bằng một người lớn tin cậy hoặc người phụ trách tư vấn học đường.' : 'Điểm cao hơn phản ánh cảm nhận khỏe mạnh hơn trong hai tuần qua. Kết quả không loại trừ khó khăn tâm lý; nếu điều gì đang ảnh hưởng việc học, giấc ngủ hoặc sinh hoạt, bạn vẫn nên tìm người hỗ trợ.',
            next: 'Chọn một việc nhỏ có ích hôm nay: nghỉ ngơi, vận động nhẹ, hoặc trò chuyện với người bạn tin tưởng.'};
    }
    const sums = {}, counts = {};
    pack.items.forEach((item, index) => {sums[item.dimension] = (sums[item.dimension] || 0) + (item.reverse ? 6 - answers[index] : answers[index]); counts[item.dimension] = (counts[item.dimension] || 0) + 1;});
    const rows = Object.entries(dimensions[id]).map(([key, [label, detail]]) => ({key, label, detail, value: Math.round((sums[key] / counts[key] - 1) * 25), average: sums[key] / counts[key]}));
    if (id === 'holland') {
        rows.sort((a,b) => b.average - a.average);
        const top = rows.filter(r => r.average === rows[0].average).map(r => r.label).join(', ');
        return {title: 'Bản đồ sở thích của bạn', rows, message: `Nhóm có điểm cao nhất trong câu trả lời: ${top}. Các nhóm bằng điểm được giữ ngang nhau. Điểm cao nhất vẫn có thể thấp nếu bạn chưa hứng thú với các hoạt động này.`, next: 'Chọn 2–3 nhóm bạn muốn khám phá, thử một hoạt động thực tế rồi cân nhắc thêm môn học, điều kiện và mong muốn của bạn. Các ngành bên dưới chỉ là ví dụ.'};
    }
    if (id === 'mbti') {
        rows.forEach(row => {row.detail += row.value === 50 ? ' Câu trả lời cân bằng giữa hai phía.' : ` Câu trả lời nghiêng về ${row.value > 50 ? 'phía bên trái' : 'phía bên phải'} của cặp.`;});
        return {title: 'Bạn có thể linh hoạt giữa các xu hướng', rows, message: 'Thanh điểm thể hiện mức nghiêng về phía bên trái của mỗi cặp; 50 là cân bằng. Không phải phần trăm tính cách, không quy thành mã 4 chữ hay kết luận chọn nghề.', next: 'Chọn một cặp và nhớ lại một tình huống bạn đã hành động theo phía còn lại. Hoàn cảnh cũng có vai trò quan trọng.'};
    }
    return {title: 'Năm khía cạnh, một con người riêng biệt', rows, message: 'Điểm được quy đổi từ trung bình 1–5 sang thang 0–100 để dễ đọc. Đây không phải phần trăm dân số hay đánh giá tốt/xấu. Bản dịch chưa được chuẩn hóa tại Việt Nam.', next: 'Chọn một đặc điểm bạn nhận ra ở mình và một thói quen nhỏ bạn muốn thử trong học tập hoặc làm việc nhóm.'};
}
