"""Validation, optimistic editing and audit history for term gradebooks."""
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json

from utils.storage import ConcurrentJSONUpdate

FIELDS = ('tx1', 'midterm', 'final')
LABELS = {'tx1': 'TX1', 'midterm': 'Giữa kì', 'final': 'Cuối kì'}
TERMS = {'hk1': 'Học kì I', 'hk2': 'Học kì II'}


def version(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def find_row(rows, course_id, student_id, term):
    matches = [r for r in rows if r.get('course_id') == course_id
               and str(r.get('student_id')) == str(student_id) and r.get('term', 'hk1') == term]
    if len(matches) > 1:
        raise ValueError('Có bản ghi điểm trùng. Cần kiểm tra dữ liệu trước khi sửa.')
    return matches[0] if matches else None


def parse_score(value):
    if value is None or value == '':
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError('Điểm phải là số từ 0 đến 10.')
    text = str(value).strip().replace(',', '.')
    if not text:
        return None
    try:
        score = Decimal(text)
    except InvalidOperation:
        raise ValueError('Điểm phải là số từ 0 đến 10.') from None
    if not score.is_finite() or not 0 <= score <= 10:
        raise ValueError('Điểm phải từ 0 đến 10.')
    if score != score.quantize(Decimal('.1')):
        raise ValueError('Điểm chỉ có tối đa một chữ số thập phân.')
    return float(score)


def average(scores):
    if any(scores.get(field) is None for field in FIELDS):
        return None
    weights = dict(tx1=1, midterm=2, final=3)
    result = sum(Decimal(str(scores[k])) * weight for k, weight in weights.items()) / 6
    return float(result.quantize(Decimal('.1'), rounding=ROUND_HALF_UP))


def view_rows(rows, course_id, students, term):
    output = []
    for student in students:
        row = find_row(rows, course_id, student['id'], term)
        output.append({'student': {k: student.get(k) for k in ('id', 'display_name', 'student_code')}, 'version': version(row),
                       'scores': {f: (row or {}).get(f) for f in FIELDS},
                       'average': (row or {}).get('average'),
                       'imported_average': bool(row and row.get('source_file') and not row.get('updated_by')),
                       'history': list(reversed((row or {}).get('history', []))),
                       'legacy_scores': {f: row[f] for f in ('tx2', 'tx3', 'tx4', 'tx5') if row and row.get(f) is not None}})
    return output


def apply_changes(rows, course_id, students, term, changes, actor):
    if not isinstance(rows, list):
        raise ValueError('Dữ liệu bảng điểm không hợp lệ.')
    if not isinstance(changes, list) or not changes or len(changes) > len(students):
        raise ValueError('Danh sách thay đổi không hợp lệ.')
    roster = {str(s['id']): s for s in students}
    output, seen = copy.deepcopy(rows), set()
    for change in changes:
        if not isinstance(change, dict):
            raise ValueError('Dữ liệu thay đổi không hợp lệ.')
        uid = str(change.get('student_id', ''))
        if uid not in roster or uid in seen:
            raise ValueError('Học sinh không thuộc lớp hoặc xuất hiện nhiều lần.')
        seen.add(uid)
        row = find_row(output, course_id, uid, term)
        if change.get('version') != version(row):
            raise ConcurrentJSONUpdate()
        raw = change.get('scores')
        if not isinstance(raw, dict) or set(raw) != set(FIELDS):
            raise ValueError('Chỉ nhập TX1, giữa kì và cuối kì; để trống điểm chưa có.')
        scores = {}
        for field in FIELDS:
            try:
                scores[field] = parse_score(raw[field])
            except ValueError as exc:
                raise ValueError(f"{roster[uid]['display_name']} · {LABELS[field]}: {exc}") from None
        previous = {f: (row or {}).get(f) for f in FIELDS}
        if scores == previous:
            continue
        if row is None:
            row = {'student_id': roster[uid]['id'], 'student_code': roster[uid].get('student_code'),
                   'course_id': course_id, 'term': term}
            output.append(row)
        now = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
        row.setdefault('history', []).append({'at': now, 'actor_id': actor['id'],
            'actor_name': actor.get('full_name') or actor.get('username'),
            'before': previous, 'after': scores,
            'average_before': row.get('average'), 'average_after': average(scores)})
        row.update(scores, average=average(scores), updated_at=now, updated_by=actor['id'])
    return output
