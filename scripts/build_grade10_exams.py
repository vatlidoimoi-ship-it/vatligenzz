"""Build the grade-10 starter bank from the two user-supplied Word lessons.

Run `python scripts/build_grade10_exams.py` from vatligenzz. The output is a
reviewable JSON draft. The separate publish script merges it into li.json.
"""
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT.parent / 'botvideo'
OUTPUT = ROOT / 'data/grade10_exams.json'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
QUESTION = re.compile(r'^Câu\s+(\d+)\s*[.:]\s*(.*)$', re.I)
OPTION = re.compile(r'([A-D])\.\s*')
KEY = re.compile(r'^(\d+)\s*[-–]?\s*([A-D])$', re.I)

# Chọn câu có thể đọc độc lập; loại câu thiếu hình và câu/đáp án nguồn mơ hồ.
PLAN = [
    ('exam_li10_intro_01', 1, 0, 'Làm quen với Vật lí: đối tượng và mục tiêu', list(range(1, 10)), 15),
    ('exam_li10_intro_02', 1, 1, 'Quá trình phát triển của Vật lí', [1, 3, 5, 6, 7, 9, 10, 11], 15),
    ('exam_li10_intro_03', 1, 2, 'Vai trò của Vật lí trong đời sống', [1, 2, 3, 4, 5, 7, 8, 9], 15),
    ('exam_li10_intro_04', 1, 3, 'Phương pháp nghiên cứu Vật lí', [2, 3, 4, 5, 6, 7, 8, 9], 15),
    ('exam_li10_safety_01', 2, 0, 'Quy tắc an toàn trong phòng thực hành',
     list(range(1, 13)) + [35, 36, 39, 40], 25),
]


def paragraphs(lesson):
    matches = list(SOURCE_DIR.glob(f'*{lesson:02d}.*.docx'))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one Word source for lesson {lesson}')
    source = matches[0]
    with ZipFile(source) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    lines = []
    for index, paragraph in enumerate(root.findall('.//w:p', NS), 1):
        text = ''.join(node.text or '' for node in paragraph.findall('.//w:t', NS)).strip()
        lines.append((index, re.sub(r'\s+', ' ', text)))
    return source, lines


def parse_section(lines, section_index):
    def answer_heading(text):
        return text.startswith('ĐÁP ÁN') and 'TRẮC NGHIỆM' in text

    indexes = [i for i, (_, text) in enumerate(lines) if text.startswith('III. BÀI TẬP TRẮC NGHIỆM')]
    if len(indexes) != 1:
        raise ValueError('Cannot identify quiz section')
    start = indexes[0] + 1
    for _ in range(section_index):
        previous_key = next(i for i in range(start, len(lines)) if answer_heading(lines[i][1]))
        start = previous_key + 1
    # A new section starts at its first question, skipping the answer key and heading.
    first_question = next(i for i in range(start, len(lines)) if QUESTION.match(lines[i][1]))
    key_start = next(i for i in range(first_question, len(lines)) if answer_heading(lines[i][1]))
    question_lines = lines[first_question:key_start]
    keys = {}
    for _, text in lines[key_start + 1:]:
        match = KEY.match(text)
        if not match:
            if keys:
                break
            continue
        keys[int(match.group(1))] = match.group(2).upper()
    questions = {}
    for offset, (paragraph, text) in enumerate(question_lines):
        match = QUESTION.match(text)
        if not match:
            continue
        number = int(match.group(1))
        next_offset = next((j for j in range(offset + 1, len(question_lines))
                           if QUESTION.match(question_lines[j][1])), len(question_lines))
        body = ' '.join([match.group(2)] + [line[1] for line in question_lines[offset + 1:next_offset]])
        markers = list(OPTION.finditer(body))
        if [marker.group(1) for marker in markers] != list('ABCD'):
            questions[number] = None
            continue
        stem = body[:markers[0].start()].strip()
        options = {marker.group(1): body[marker.end():markers[i + 1].start() if i < 3 else len(body)].strip()
                   for i, marker in enumerate(markers)}
        if not stem or not all(options.values()) or len(set(options.values())) != 4:
            questions[number] = None
            continue
        questions[number] = {'question': stem, 'options': options, 'correct_answer': keys.get(number),
                             'source_paragraph': paragraph, 'source_quote': text}
    return questions


def build():
    sources = {lesson: paragraphs(lesson) for lesson in (1, 2)}
    exams = []
    for exam_id, lesson, section, title, selected, minutes in PLAN:
        source, lines = sources[lesson]
        parsed = parse_section(lines, section)
        questions = []
        for number, original_number in enumerate(selected, 1):
            question = parsed.get(original_number)
            if not question or question['correct_answer'] not in 'ABCD':
                raise ValueError(f'Incomplete source question: lesson {lesson}, section {section}, #{original_number}')
            questions.append({**question, 'id': number, 'number': number,
                              'source_question': original_number, 'source_file': source.name,
                              'explanation': f"Theo tài liệu bài {lesson}, đáp án là {question['correct_answer']}: {question['options'][question['correct_answer']]}."})
        exams.append({'id': exam_id, 'title': 'Vật lí 10 · ' + title, 'grade': '10',
                      'time_limit': minutes, 'description': f'{len(questions)} câu từ tài liệu Word bài {lesson}.',
                      'topic': title, 'source_file': source.name,
                      'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                      'batch_id': 'word10-intro-v1', 'created_by': None,
                      'scoring_config': {'multiple_choice': {'weight_percent': 100, 'points': 10}},
                      'questions': questions})
    return {'exams': exams}


if __name__ == '__main__':
    bank = build()
    OUTPUT.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"Wrote {len(bank['exams'])} exams, {sum(len(e['questions']) for e in bank['exams'])} questions to {OUTPUT}")
