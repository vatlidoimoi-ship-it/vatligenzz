/* These practice scores stay in memory; they are never submitted as school marks. */
(() => {
    'use strict';
    const data = JSON.parse(document.getElementById('activity-data').textContent);
    const el = id => document.getElementById(id);
    const cards = data.mode === 'flashcards';
    let questions = [], index = 0, score = 0, missed = [], answered = false;
    function shuffled(items) {
        const result = [...items];
        for (let i = result.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [result[i], result[j]] = [result[j], result[i]];
        }
        return result;
    }
    function show() {
        answered = false;
        const q = questions[index];
        el('progress').textContent = `Câu ${index + 1}/${questions.length} · ${cards ? 'Đã nhớ' : 'Đúng'}: ${score}`;
        el('question').textContent = q.question;
        el('question').focus();
        el('source').textContent = `Nguồn biên soạn: ${q.source} · Đoạn Word ${q.paragraph}.`;
        el('feedback').hidden = true;
        for (const id of ['next', 'remember', 'review']) el(id).hidden = true;
        el('reveal').hidden = !cards;
        el('options').replaceChildren();
        if (!cards) {
            for (const [key, value] of shuffled(Object.entries(q.options))) {
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = `${key}. ${value}`;
                button.dataset.key = key;
                button.addEventListener('click', () => answer(key));
                el('options').append(button);
            }
        }
    }
    function reveal() {
        const q = questions[index];
        el('feedback').textContent = `Đáp án: ${q.options[q.answer]}\n\n${q.explanation}`;
        el('feedback').hidden = false;
    }
    function answer(key) {
        if (answered) return;
        answered = true;
        const q = questions[index];
        if (key === q.answer) score++;
        for (const button of el('options').children) {
            button.disabled = true;
            if (button.dataset.key === q.answer) button.classList.add('correct');
            else if (button.dataset.key === key) button.classList.add('wrong');
        }
        reveal();
        el('feedback').textContent = `${key === q.answer ? 'Chính xác!' : 'Chưa đúng.'}\n${el('feedback').textContent}`;
        el('next').hidden = false;
    }
    function begin(items) {
        questions = shuffled(items).slice(0, 10);
        if (!questions.length) return;
        index = 0; score = 0; missed = [];
        el('setup').hidden = true; el('result').hidden = true; el('round').hidden = false;
        show();
    }
    function next() {
        index++;
        if (index < questions.length) return show();
        el('round').hidden = true; el('result').hidden = false;
        el('summary').textContent = cards
            ? `Bạn tự đánh giá đã nhớ ${score}/${questions.length} thẻ; còn ${missed.length} thẻ cần ôn.`
            : `Bạn trả lời đúng ${score}/${questions.length} câu · Điểm luyện tập: ${score * 10}/${questions.length * 10}.`;
        el('retry').hidden = !cards || !missed.length;
    }
    function reset() {
        el('setup').hidden = false; el('round').hidden = true; el('result').hidden = true;
        el('chapter').focus();
    }
    el('start').onclick = () => begin(data.chapters[Number(el('chapter').value)].questions);
    el('reveal').onclick = () => {
        reveal(); el('reveal').hidden = true;
        el('remember').hidden = false; el('review').hidden = false;
    };
    el('remember').onclick = () => { score++; next(); };
    el('review').onclick = () => { missed.push(questions[index]); next(); };
    el('next').onclick = next;
    el('retry').onclick = () => begin(missed);
    el('reset').onclick = reset;
    el('again').onclick = reset;
})();
