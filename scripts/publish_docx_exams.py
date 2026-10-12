"""Assemble the verified 20-exam batch and optionally merge into live Supabase.

Never replaces unrelated exams. Use --publish --env-file ../.env after testing.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import requests
from migrate_json_to_supabase import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / '.runtime_data/docx-exams'


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args()
    exams = [json.loads((WORK / f'exam-{number:02}.json').read_text(encoding='utf-8')) for number in range(1, 21)]
    assert all(e['review_status'] == 'passed' and len(e['questions']) == 20 for e in exams)
    assert Counter(e['grade'] for e in exams) == {'11': 20}
    assert len({q['question'].strip().lower() for e in exams for q in e['questions']}) == 400
    save(ROOT / 'data/docx_exams_grade11.json', {'batch_id': 'word11-20x20-v1', 'exams': exams})
    seed_path = ROOT / 'data/li.json'
    seed = json.loads(seed_path.read_text(encoding='utf-8-sig'))
    ids = {e['id'] for e in exams}
    seed['exams'] = [e for e in seed.get('exams', []) if e.get('id') not in ids] + exams
    save(seed_path, seed)
    lines = ['# 20 đề trắc nghiệm Vật lí 11 từ bốn tài liệu Word', '',
             'Mỗi đề: 20 câu, 30 phút, 10 điểm; mỗi câu đúng được 0,5 điểm.', '',
             'Biên soạn mới theo tài liệu được cung cấp, không phải bản chép nguyên đề. '
             'Mỗi câu có nguồn đoạn Word trong dữ liệu JSON. Kiểm tra tự động và lượt giải độc lập bằng AI '
             'không thay thế việc thẩm định chuyên môn của giáo viên.', '']
    for exam in exams:
        lines += [f'## {exam["title"]}', '', f'Nguồn: {exam["source_file"]}', '']
        for q in exam['questions']:
            lines += [f'**Câu {q["number"]} ({q["difficulty"]}).** {q["question"]}', '']
            lines += [f'- {key}. {text}' for key, text in q['options'].items()]
            lines += ['']
        lines += ['### Đáp án và giải thích', '']
        for q in exam['questions']:
            lines += [f'**{q["number"]}. {q["correct_answer"]}** — {q["explanation"]}', '']
    (ROOT / 'docs/word-exams-grade11.md').write_text('\n'.join(lines), encoding='utf-8')
    print('Assembled 20 exams / 400 questions with answer explanations and source provenance.')
    if not args.publish:
        return
    load_dotenv(args.env_file)
    secret = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': secret, 'Authorization': 'Bearer ' + secret}
    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    params = {'key': 'eq.data/li.json', 'select': 'value,updated_at'}
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok:
        raise RuntimeError(f'Read physics bank: HTTP {response.status_code}')
    rows = response.json()
    if not rows:
        # Plain INSERT, never upsert: a concurrent creator must not be overwritten.
        response = requests.post(url, headers={**headers, 'Prefer': 'return=representation'},
                                 json={'key': 'data/li.json', 'value': seed}, timeout=60)
        if not response.ok:
            raise RuntimeError(f'Create physics bank: HTTP {response.status_code}; no overwrite attempted.')
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if not response.ok or response.json()[0]['value'] != seed:
            raise RuntimeError('Created bank readback mismatch')
        print(f'Supabase verified: created physics bank with {len(seed["exams"])} exams.')
        return
    if len(rows) != 1:
        raise RuntimeError('Ambiguous physics bank; no changes made.')
    previous, stamp = rows[0]['value'], rows[0]['updated_at']
    backup = ROOT / '.runtime_data/publish-backups'
    save(backup / ('li-' + hashlib.sha256(stamp.encode()).hexdigest()[:12] + '.json'), rows[0])
    existing = previous.get('exams', [])
    clashes = [e['id'] for e in existing if e.get('id') in ids and e.get('batch_id') != 'word11-20x20-v1']
    if clashes:
        raise RuntimeError('Unrelated exam ID collision; refusing replacement.')
    merged = {**previous, 'exams': [e for e in existing if e.get('id') not in ids] + exams}
    response = requests.patch(url, headers={**headers, 'Prefer': 'return=representation'},
        params={'key': params['key'], 'updated_at': 'eq.' + stamp}, json={'value': merged}, timeout=60)
    if not response.ok or not response.json():
        raise RuntimeError(f'Concurrent change or publish failure: HTTP {response.status_code}; retry after review.')
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok or response.json()[0]['value'] != merged:
        raise RuntimeError('Published bank readback mismatch')
    print(f'Supabase verified: {len(existing)} previous exams -> {len(merged["exams"])} exams. Unrelated exams preserved.')


if __name__ == '__main__':
    main()
