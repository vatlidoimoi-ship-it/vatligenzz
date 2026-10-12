"""Create and independently solve 20 grade-11 exams from user-supplied Word sources.

Run one of ten stages: python scripts/build_docx_exams.py --stage 1 --env-file ../.env
Drafts and model review records stay in ignored .runtime_data; approved banks are
exported separately only after all stages have passed checks.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
import random
import re
import time
import unicodedata
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import requests
from migrate_json_to_supabase import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.runtime_data/docx-exams'
PLAN = [
    (1, 'Dao động điều hòa: các đại lượng và phương trình', ['dao động điều hòa', 'chu kì', 'pha ban đầu', 'biên độ']),
    (1, 'Đồ thị và pha dao động điều hòa', ['đồ thị', 'pha', 'li độ', 'mô tả dao động']),
    (1, 'Vận tốc và gia tốc trong dao động điều hòa', ['vận tốc', 'gia tốc', 'cực đại', 'li độ']),
    (1, 'Năng lượng trong dao động điều hòa', ['năng lượng', 'động năng', 'thế năng', 'cơ năng']),
    (1, 'Dao động tắt dần, cưỡng bức và cộng hưởng', ['tắt dần', 'cưỡng bức', 'cộng hưởng', 'dao động riêng']),
    (2, 'Mô tả sóng và sự truyền năng lượng', ['mô tả sóng', 'bước sóng', 'sóng ngang', 'sóng dọc', 'truyền năng lượng']),
    (2, 'Sóng điện từ và phổ sóng điện từ', ['sóng điện từ', 'hồng ngoại', 'tử ngoại', 'ánh sáng', 'chân không']),
    (2, 'Giao thoa sóng cơ', ['giao thoa sóng cơ', 'nguồn kết hợp', 'cực đại', 'cực tiểu', 'hiệu đường đi']),
    (2, 'Giao thoa ánh sáng Young', ['giao thoa ánh sáng', 'young', 'khoảng vân', 'vân sáng', 'vân tối']),
    (2, 'Sóng dừng và điều kiện trên dây', ['sóng dừng', 'bụng sóng', 'nút sóng', 'hai đầu', 'đầu cố định']),
    (3, 'Lực tương tác giữa các điện tích', ['coulomb', 'điện tích điểm', 'lực tương tác', 'hằng số điện môi']),
    (3, 'Cường độ điện trường và nguyên lý chồng chất', ['cường độ điện trường', 'đường sức', 'điện trường triệt tiêu', 'điện tích thử']),
    (3, 'Điện trường đều và chuyển động của điện tích', ['điện trường đều', 'bản kim loại', 'electron', 'chuyển động', 'proton']),
    (3, 'Thế năng điện, điện thế và hiệu điện thế', ['thế năng điện', 'điện thế', 'hiệu điện thế', 'công của lực điện']),
    (3, 'Tụ điện, điện dung và năng lượng điện trường', ['tụ điện', 'điện dung', 'năng lượng điện trường', 'tích điện']),
    (4, 'Cường độ dòng điện và chuyển động có hướng', ['cường độ dòng điện', 'điện lượng', 'dịch chuyển', 'hạt tải điện']),
    (4, 'Điện trở và định luật Ôm', ['điện trở', 'định luật ôm', 'điện trở suất', 'nhiệt độ']),
    (4, 'Mạch điện: ghép điện trở và đo lường', ['nối tiếp', 'song song', 'ampe kế', 'vôn kế', 'điện trở tương đương']),
    (4, 'Nguồn điện và suất điện động', ['nguồn điện', 'suất điện động', 'điện trở trong', 'mạch ngoài', 'lực lạ']),
    (4, 'Điện năng, công suất và hiệu suất', ['điện năng', 'công suất', 'nhiệt lượng', 'hiệu suất', 'jun']),
]


def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower().replace('đ', 'd')) if unicodedata.category(c) != 'Mn')


def source_paragraphs(chapter):
    source = next((ROOT / 'datatm').glob(f'{chapter}. *.docx'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with ZipFile(source) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    lines = []
    for index, paragraph in enumerate(root.findall('.//w:p', ns), 1):
        # Text and Office Math text only; do not flatten drawing attributes into prose.
        text = ''.join(n.text or '' for n in paragraph.iter() if n.tag.endswith('}t')).strip()
        if len(text) > 12:
            lines.append((index, re.sub(r'\s+', ' ', text)))
    return source, lines


def context_for(chapter, keywords):
    source, lines = source_paragraphs(chapter)
    terms = [fold(k) for k in keywords]
    ranked = sorted(range(len(lines)), key=lambda i: sum(1 for k in terms if k in fold(lines[i][1])), reverse=True)
    selected = set()
    size = 0
    for index in ranked:
        if not any(k in fold(lines[index][1]) for k in terms):
            continue
        for near in range(max(0, index - 2), min(len(lines), index + 5)):
            if near not in selected and size + len(lines[near][1]) < 24000:
                selected.add(near)
                size += len(lines[near][1])
    excerpts = {str(lines[i][0]): lines[i][1] for i in sorted(selected)}
    return source, excerpts


def call_json(prompt):
    raw = (os.getenv('GEMINI_API_KEYS') or '').replace(';', ',').replace('\n', ',')
    keys = list(dict.fromkeys([x.strip() for x in raw.split(',') if x.strip()] + [os.getenv('GEMINI_API_KEY', '')]))
    keys = [k for k in keys if k]
    if not keys:
        raise RuntimeError('Missing Gemini configuration')
    start_key = random.randrange(len(keys))
    for attempt in range(max(3, len(keys))):
        response = requests.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent',
            headers={'x-goog-api-key': keys[(start_key + attempt) % len(keys)]},
            json={'contents': [{'parts': [{'text': prompt}]}],
                  'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.25,
                                       'maxOutputTokens': 16000, 'thinkingConfig': {'thinkingBudget': 512}}},
            timeout=(30, 240))
        if response.status_code in (429, 500, 503):
            print(f'Generation service HTTP {response.status_code}; retrying configured connection', flush=True)
            time.sleep(3)
            continue
        if not response.ok:
            raise RuntimeError(f'Gemini returned HTTP {response.status_code}; details withheld.')
        payload = response.json()
        candidates = payload.get('candidates', [])
        if not candidates:
            raise RuntimeError('No generation candidate')
        if candidates[0].get('finishReason') != 'STOP':
            raise RuntimeError('Incomplete generation: ' + str(candidates[0].get('finishReason')))
        text = ''.join(p.get('text', '') for p in candidates[0]['content']['parts'] if not p.get('thought'))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if attempt + 1 == max(3, len(keys)):
                raise RuntimeError('Invalid JSON generation') from None
    raise RuntimeError('Gemini unavailable after retries')


def validate(questions, excerpts):
    if len(questions) != 20:
        raise ValueError('Need exactly 20 questions')
    stems = set()
    for index, q in enumerate(questions, 1):
        assert q['number'] == index
        assert set(q['options']) == set('ABCD')
        assert q['correct_answer'] in 'ABCD' and len(q['correct_answer']) == 1
        assert len({fold(x.strip()) for x in q['options'].values()}) == 4
        assert all(len(x.strip()) > 0 for x in q['options'].values())
        assert len(q['explanation']) >= 35
        assert q['difficulty'] in ('NB', 'TH', 'VD')
        assert str(q['source_paragraph']) in excerpts, f'Câu {index}: source_paragraph phải là số P thực sự xuất hiện trong đoạn trích.'
        quote = q['source_quote'].strip()
        assert len(quote) >= 12 and quote in excerpts[str(q['source_paragraph'])], 'Source quote must be verbatim'
        stem = fold(q['question'])
        assert stem not in stems
        assert not any(s in stem for s in ['hinh ve', 'hinh ben', 'do thi ben', 'nhu hinh', '<script']), f'Câu {index}: bỏ tham chiếu hình không có, nêu dữ kiện trực tiếp bằng lời.'
        stems.add(stem)
    matrix = {d: sum(q['difficulty'] == d for q in questions) for d in ['NB', 'TH', 'VD']}
    assert matrix == {'NB': 6, 'TH': 8, 'VD': 6}, f'Ma trận hiện tại {matrix}; phải là 6 NB, 8 TH, 6 VD. Câu 1-6 NB; 7-14 TH; 15-20 VD.'


def build_exam(number):
    WORK.mkdir(parents=True, exist_ok=True)
    target = WORK / f'exam-{number:02}.json'
    if target.exists():
        saved = json.loads(target.read_text(encoding='utf-8'))
        if saved.get('review_status') == 'passed':
            print(f'Exam {number:02} already checked', flush=True)
            return saved
    chapter, title, keywords = PLAN[number - 1]
    source, excerpts = context_for(chapter, keywords)
    source_text = '\n'.join(f'[P{k}] {v}' for k, v in excerpts.items())
    (WORK / f'source-{number:02}.json').write_text(json.dumps(excerpts, ensure_ascii=False, indent=2), encoding='utf-8')
    previous_stems = []
    for p in WORK.glob('exam-*.json'):
        previous_stems.extend(q['question'] for q in json.loads(p.read_text(encoding='utf-8')).get('questions', []))
    prompt = f'''Bạn là giáo viên Vật lí THPT Việt Nam. Soạn ĐỀ {number:02}, lớp 11, chủ đề: {title}.
Chỉ dùng phạm vi kiến thức trong các đoạn trích Word bên dưới, nhưng biên soạn câu hỏi mới có đủ dữ kiện.
Đây là đoạn trích có thể mất phân số/ký hiệu hoặc ảnh. KHÔNG suy đoán công thức hỏng, KHÔNG hỏi dựa trên ảnh không có.
Tuyệt đối không viết 'như hình vẽ', kể cả sau đó chú thích 'không có hình, giả sử'. Với đồ thị, mô tả đầy đủ tọa độ/chiều chuyển động bằng lời ngay trong đề.
20 câu, mỗi câu 4 phương án A/B/C/D và duy nhất một đúng. Câu 1-6 là NB, câu 7-14 là TH, câu 15-20 là VD. Tổng đúng 6 NB, 8 TH, 6 VD.
NB kiểm tra khái niệm; TH có suy luận; VD có bài tính/ứng dụng đủ giả thiết và lời giải số học.
Không chỉ thay số cùng một mẫu. Đa dạng thao tác, tình huống. Không dùng 'tất cả đều đúng' hoặc 'cả A B'.
Hằng số và điều kiện lý tưởng phải nêu rõ. Đơn vị SI nhất quán; ghi rõ làm tròn nếu cần.
Ưu tiên ký hiệu Unicode và văn bản dễ đọc, ví dụ x = 4cos(2πt + π/3) cm; không HTML, không LaTeX.
Đáp án giải thích 2-4 câu: nêu nguyên lý, thay số và kết quả nếu có tính toán.
Mỗi câu phải chỉ đúng source_paragraph (số P), source_quote là đoạn trích NGUYÊN VĂN ≥12 ký tự trong đoạn đó hỗ trợ kiến thức, không bịa nguồn.
Không sao chép nguyên một bài có lời giải sẵn. Không viện dẫn 'theo tài liệu' trong câu hỏi.
Không trùng các câu đã có: {json.dumps(previous_stems[-200:], ensure_ascii=False)}
TỰ GIẢI TRƯỚC khi tạo phương án: viết explanation trước options, đưa đúng kết quả vừa tính vào 1 phương án, rồi chỉ correct_answer tương ứng.
Trả JSON {{"questions":[{{"number":1,"question":"...","explanation":"...","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct_answer":"A","difficulty":"NB","source_paragraph":123,"source_quote":"..."}}]}}.
NGUỒN: {source.name}\n{source_text}'''
    questions = None
    last_problem = ''
    for attempt in range(3):
        print(f'Exam {number:02}: drafting attempt {attempt+1}', flush=True)
        draft = call_json(prompt + ('\nLần trước không đạt kiểm tra: ' + last_problem if last_problem else ''))
        questions = draft['questions']
        # Store the actual paragraph from the document, never a model-reconstructed
        # quote (Word equations and whitespace are often normalized by the model).
        for q in questions:
            if str(q.get('source_paragraph')) in excerpts:
                q['source_quote'] = excerpts[str(q['source_paragraph'])]
        (WORK / f'draft-{number:02}.json').write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding='utf-8')
        try:
            validate(questions, excerpts)
        except (AssertionError, KeyError, ValueError) as error:
            last_problem = str(error) or 'Sai ma trận 6 NB/8 TH/6 VD hoặc thiếu trường, nguồn trích dẫn không nguyên văn.'
            print(f'Exam {number:02}: validation retry: {last_problem[:160]}', flush=True)
            continue
        # Reviewer solves without seeing the proposed answer or explanation.
        blind = [{k: q[k] for k in ('number', 'question', 'options')} for q in questions]
        print(f'Exam {number:02}: independently solving 20 questions', flush=True)
        review = call_json('''Bạn là người kiểm định đề Vật lí lớp 11. TỰ GIẢI từng câu, kiểm tra số học, đơn vị,
giả thiết, không có hai phương án tương đương, không thiếu hình. Không được mặc định câu hỏi đúng.
Giải và tính số TRƯỚC, rồi mới điền ký tự đáp án cuối cùng khớp với kết quả vừa tính.
Trả JSON {"results":[{"number":1,"reason":"Lời giải độc lập; nếu sai/thiếu điều kiện, giải thích vấn đề","valid":true,"answer":"A"}]}.
Nếu câu không có duy nhất 1 đáp án đúng, valid=false và answer="".
Đề: ''' + json.dumps(blind, ensure_ascii=False))
        results = review.get('results', [])
        if len(results) != 20 or [r.get('number') for r in results] != list(range(1, 21)):
            last_problem = 'Không kiểm định đủ 20 câu.'
            continue
        issues = [r for q, r in zip(questions, results) if not r.get('valid') or r.get('answer') != q['correct_answer']]
        (WORK / f'review-{number:02}-attempt-{attempt+1}.json').write_text(json.dumps({'draft': questions, 'review': results, 'issues': issues}, ensure_ascii=False, indent=2), encoding='utf-8')
        if issues:
            last_problem = json.dumps(issues, ensure_ascii=False)
            print(f'Exam {number:02}: revising {len(issues)} flagged items (attempt {attempt+1})', flush=True)
            continue
        break
    else:
        raise RuntimeError(f'Exam {number:02} did not pass review: {last_problem[:200]}')
    return finalize_exam(number, questions, source)


def finalize_exam(number, questions, source, review_method="schema, source quotes, independent AI solution; not a human certification"):
    title = PLAN[number - 1][1]
    target = WORK / f"exam-{number:02}.json"
    # Balance answer positions exactly, without changing the question or answer content.
    letters = list('ABCD' * 5)
    rng = random.Random(1100 + number)
    rng.shuffle(letters)
    for q, desired in zip(questions, letters):
        correct = q['options'][q['correct_answer']]
        distractors = [v for k, v in q['options'].items() if k != q['correct_answer']]
        rng.shuffle(distractors)
        q['options'] = {k: correct if k == desired else distractors.pop() for k in 'ABCD'}
        # Do not retain option-letter references in explanations after shuffling.
        q['explanation'] = re.sub(r'(?i)(?:chọn|đáp án)\s+[ABCD]\b[.:]?', '', q['explanation']).strip()
        q['correct_answer'] = desired
        q['id'] = q['number']
        q['source_file'] = source.name
    exam = {'id': f'exam_li11_word_{number:02}', 'title': f'Vật lí 11 · Đề {number:02}: {title}',
            'grade': '11', 'time_limit': 30, 'description': '20 câu, 30 phút. Biên soạn theo tài liệu Word được cung cấp; 6 nhận biết, 8 thông hiểu, 6 vận dụng.',
            'topic': title, 'source_file': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'batch_id': 'word11-20x20-v1', 'stage': (number + 1)//2,
            'created_at': datetime.now(timezone(timedelta(hours=7))).isoformat(),
            'created_by': None, 'review_status': 'passed', 'review_method': review_method,
            'scoring_config': {'multiple_choice': {'weight_percent': 100, 'points': 10}}, 'questions': questions}
    target.write_text(json.dumps(exam, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS exam {number:02}: {title} — 20 questions, content/schema/source checks passed', flush=True)
    return exam


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=int, required=True, choices=range(1, 11))
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args()
    load_dotenv(args.env_file)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(build_exam, (args.stage * 2 - 1, args.stage * 2)))
    print(f'STAGE {args.stage}/10 COMPLETE', flush=True)


if __name__ == '__main__':
    main()
