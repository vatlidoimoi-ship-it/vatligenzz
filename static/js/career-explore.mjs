import {packages, scoreAssessment, configureAssessments} from './career-assessments.mjs';

configureAssessments(JSON.parse(document.getElementById('assessmentCatalog').textContent));

const $ = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const dialog = $('assessmentDialog');
const content = $('assessmentContent');
let active, answers = [], step = 0, stage = 'intro', result, opener;
let recordedResult = false;

function switchPanel(chat) {
    $('explorePanel').hidden = chat;
    $('chatPanel').hidden = !chat;
    $('exploreTab').setAttribute('aria-pressed', String(!chat));
    $('chatTab').setAttribute('aria-pressed', String(chat));
    if (chat) $('advisorInput').focus();
}
$('exploreTab').addEventListener('click', () => switchPanel(false));
$('chatTab').addEventListener('click', () => switchPanel(true));

function renderCards(filter = 'all') {
    const shown = packages.filter(p => filter === 'all' || p.category === filter);
    $('packageCount').textContent = `${String(shown.length).padStart(2, '0')} gói khám phá`;
    $('packageGrid').innerHTML = shown.map(pack => `<article class="care-card" data-id="${pack.id}">
        <div class="care-card-art"><img src="/static/images/career/${pack.image}.webp" alt="" width="1200" height="670" ${pack.id === 'holland' ? 'fetchpriority="high"' : 'loading="lazy"'}><span class="care-card-tag">${escape(pack.tag)}</span><span class="care-card-number" aria-hidden="true">0${packages.indexOf(pack) + 1}</span></div>
        <div class="care-card-body"><h3>${escape(pack.title)}</h3><p class="care-card-subtitle">${escape(pack.subtitle)}</p><p class="care-card-description">${escape(pack.description)}</p>
        <div class="care-card-foot"><small>${pack.items.length ? `${pack.items.length} câu · ` : ''}${pack.duration}</small><button type="button" data-open="${pack.id}" aria-label="${pack.items.length ? 'Khám phá' : 'Tìm hiểu'} ${escape(pack.title)}">${pack.items.length ? 'Khám phá' : 'Tìm hiểu'}<span aria-hidden="true">↗</span></button></div></div></article>`).join('');
}
document.querySelector('.care-filters').addEventListener('click', event => {
    const button = event.target.closest('[data-filter]');
    if (!button) return;
    document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
    renderCards(button.dataset.filter);
});
$('packageGrid').addEventListener('click', event => {
    const button = event.target.closest('[data-open]');
    if (!button) return;
    active = packages.find(p => p.id === button.dataset.open);
    answers = Array(active.items.length).fill(null);
    step = 0;
    result = null;
    opener = button;
    stage = 'intro';
    recordedResult = false;
    renderIntro();
    dialog.showModal();
});
function focusTitle() {
    dialog.scrollTop = 0;
    content.querySelector('h2')?.focus({preventScroll: true});
}
function sourceMarkup() {
    return `<p class="care-source"><a href="${active.source[1]}" target="_blank" rel="noopener noreferrer">${escape(active.source[0])} ↗</a></p>${active.license ? `<details><summary>Nguồn, bản dịch và giấy phép</summary><p>${escape(active.license)}</p><a href="https://creativecommons.org/licenses/by-nc-sa/3.0/igo/" target="_blank" rel="noopener noreferrer">CC BY-NC-SA 3.0 IGO</a></details>` : ''}`;
}
const help = '<div class="care-help"><p><strong>Bạn không cần tự vượt qua một mình.</strong> Nếu cảm xúc kéo dài hoặc ảnh hưởng việc học, giấc ngủ, sinh hoạt, hãy nói với người lớn tin cậy hoặc chuyên viên. Nếu đang có nguy cơ làm hại bản thân hay gặp nguy hiểm ngay lúc này, đến nơi an toàn, nhờ người ở cùng và gọi cấp cứu địa phương (115 tại Việt Nam).</p></div>';
function renderIntro() {
    content.innerHTML = `<p class="care-eyebrow">${escape(active.tag)}</p><h2 id="assessmentTitle" tabindex="-1">${escape(active.title)}</h2><p>${escape(active.description)}</p><p class="care-disclosure">${escape(active.note)}</p>${sourceMarkup()}
    ${active.items.length ? `<p>${escape(active.instruction)}</p><p class="care-source">Không lưu câu trả lời hoặc điểm lên máy chủ. Khi hoàn thành, hệ thống ghi nhận tên gói và lượt làm để thống kê. Đóng bài hoặc tải lại trang sẽ xóa câu trả lời. Bạn có thể dừng bất cứ lúc nào.</p><button class="care-action" type="button" data-action="start">Mình đã hiểu · Bắt đầu ${active.items.length} câu →</button>` : `<h3>Một bước nhỏ để tìm hỗ trợ</h3><p>Ghi lại điều đang làm bạn khó chịu, khi nào bắt đầu và ảnh hưởng tới sinh hoạt ra sao. Bạn không cần tự gắn nhãn cho cảm xúc của mình.</p><p>Hãy nhờ người lớn tin cậy kết nối với chuyên viên tâm lý hoặc người phụ trách tư vấn học đường. Bạn có thể nói: “Gần đây em đang gặp khó khăn và muốn có người cùng tìm cách hỗ trợ.”</p>${help}<button class="care-action" type="button" data-action="talk">Chuẩn bị lời nhắn để trò chuyện →</button>`}`;
}
function renderQuestion() {
    const item = active.items[step];
    const completed = answers.filter(a => a !== null).length;
    content.innerHTML = `<h2 id="assessmentTitle" tabindex="-1">${escape(active.title)}</h2><div class="care-progress-label"><span>Câu ${step + 1} / ${active.items.length}</span><span>${completed} câu đã trả lời</span></div><progress value="${completed}" max="${active.items.length}" aria-label="Số câu đã trả lời"></progress><p class="care-source">${escape(active.instruction)}</p>
        <fieldset class="care-question"><legend>${escape(item.text)}</legend>${active.options.map((option, i) => `<label class="care-option"><input type="radio" name="care-answer" value="${i + active.min}" ${answers[step] === i + active.min ? 'checked' : ''}><span>${escape(option)}</span></label>`).join('')}</fieldset>
        <div class="care-actions"><button class="care-action secondary" type="button" data-action="previous" ${step === 0 ? 'disabled' : ''}>← Câu trước</button><button class="care-action" type="button" data-action="next" ${answers[step] === null ? 'disabled' : ''}>${step === active.items.length - 1 ? 'Xem kết quả' : 'Câu tiếp theo →'}</button></div>`;
    focusTitle();
}
content.addEventListener('change', event => {
    if (event.target.name !== 'care-answer') return;
    answers[step] = Number(event.target.value);
    content.querySelector('[data-action="next"]').disabled = false;
    content.querySelector('progress').value = answers.filter(a => a !== null).length;
    content.querySelector('.care-progress-label span:last-child').textContent = `${answers.filter(a => a !== null).length} câu đã trả lời`;
});
function renderResult() {
    result = scoreAssessment(active.id, answers);
    stage = 'result';
    if (!recordedResult) {
        recordedResult = true;
        fetch('/api/career-guidance/completion', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({package_id: active.id})
        }).then(response => { if (!response.ok) recordedResult = false; })
          .catch(() => { recordedResult = false; });
    }
    content.innerHTML = `<p class="care-eyebrow">${escape(active.title)} · KẾT QUẢ THAM KHẢO</p><h2 id="assessmentTitle" tabindex="-1">${escape(result.title)}</h2><p>${escape(result.message)}</p>
        ${result.rows.map(row => `<div class="care-result-row"><div class="care-result-label"><span>${escape(row.label)}</span><span>${row.value}/100</span></div><div class="care-meter" aria-hidden="true"><span style="width:${row.value}%"></span></div><p>${escape(row.detail)}</p></div>`).join('')}
        <p class="care-disclosure">${escape(result.next)}</p>${active.category === 'wellbeing' ? help : ''}<details><summary>Hiểu đúng kết quả và nguồn câu hỏi</summary><p>${escape(active.note)}</p>${sourceMarkup()}</details>
        <p class="care-source">“Trao đổi về kết quả” chỉ điền bản tóm tắt vào ô chat. Khi bấm Gửi, nội dung sẽ được chuyển tới AI Gemini. Bạn có thể sửa hoặc xóa trước khi gửi.</p><div class="care-actions"><button class="care-action secondary" type="button" data-action="review">Xem lại câu trả lời</button><button class="care-action" type="button" data-action="share">Trao đổi về kết quả ↗</button></div>`;
    focusTitle();
}
function finishShare(text) {
    dialog.close();
    switchPanel(true);
    document.dispatchEvent(new CustomEvent('care:share', {detail: text}));
}
content.addEventListener('click', event => {
    const action = event.target.closest('[data-action]')?.dataset.action;
    if (!action) return;
    if (action === 'start') {stage = 'questions'; renderQuestion();}
    if (action === 'previous' && step > 0) {step--; renderQuestion();}
    if (action === 'next' && answers[step] !== null) {
        if (step < active.items.length - 1) {step++; renderQuestion();} else renderResult();
    }
    if (action === 'review') {stage = 'questions'; step = 0; renderQuestion();}
    if (action === 'share' && result) finishShare(`Mình vừa làm gói ${active.title} trên PHYEDU. Đây là kết quả tham khảo, bản câu hỏi/dịch chưa được chuẩn hóa cho học sinh Việt Nam, không dùng để chẩn đoán hay quyết định nghề nghiệp. ${result.rows.map(row => `${row.label}: ${row.value}/100`).join('; ')}. ${active.id === 'mbti' ? 'Điểm mỗi cặp biểu thị mức nghiêng về phía bên trái, không phải phần trăm tính cách.' : ''} Hãy giúp mình hiểu kết quả, hỏi thêm về hoàn cảnh và gợi ý một bước nhỏ phù hợp.`);
    if (action === 'talk') finishShare('Mình muốn chuẩn bị lời nhắn cho người lớn tin cậy hoặc chuyên viên để chia sẻ những khó khăn gần đây. Bạn giúp mình bắt đầu nhé.');
    if (action === 'keep') {stage = 'questions'; renderQuestion();}
    if (action === 'discard') dialog.close();
});
function requestClose() {
    if (stage === 'questions' && answers.some(a => a !== null)) {
        stage = 'closing';
        content.innerHTML = '<h2 id="assessmentTitle" tabindex="-1">Dừng bài khám phá?</h2><p>Câu trả lời hiện tại sẽ được xóa. Bạn cũng có thể tiếp tục từ câu đang làm.</p><div class="care-actions"><button class="care-action secondary" type="button" data-action="discard">Dừng và xóa câu trả lời</button><button class="care-action" type="button" data-action="keep">Tiếp tục làm bài</button></div>';
        focusTitle();
    } else dialog.close();
}
$('closeAssessment').addEventListener('click', requestClose);
dialog.addEventListener('cancel', event => {event.preventDefault(); requestClose();});
dialog.addEventListener('close', () => {answers = []; result = null; active = null; stage = 'intro'; content.replaceChildren(); if (!$('explorePanel').hidden) opener?.focus();});
renderCards();
