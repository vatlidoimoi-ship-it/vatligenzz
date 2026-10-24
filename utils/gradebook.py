"""Validation, optimistic editing and audit history for term gradebooks."""
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json

from utils.storage import ConcurrentJSONUpdate

FIELDS_BY_TERM = {'hk1': ('tx1', 'tx2', 'tx3', 'midterm', 'final'),
                  'hk2': ('tx1', 'tx2', 'tx3', 'tx4', 'midterm', 'final')}
LABELS = {'tx1': 'TX1', 'tx2': 'TX2', 'tx3': 'TX3', 'tx4': 'TX4',
          'midterm': 'Giữa kì', 'final': 'Cuối kì'}
TERMS = {'hk1': 'Học kì I', 'hk2': 'Học kì II', 'year': 'Bảng tổng kết'}


def unverified_import(row):
    return bool(row and 'mon_toan' in str(row.get('source_file', '')).lower() and not row.get('updated_by'))


def scores_for(row, term):
    source = {} if unverified_import(row) else (row or {})
    if source and 'mon_toan' in str(source.get('source_file', '')).lower():
        confirmed = {field for entry in source.get('history', []) for field in entry.get('after', {})}
        if confirmed:
            return {f: source.get(f) if f in confirmed else None for f in FIELDS_BY_TERM[term]}
    return {f: source.get(f) for f in FIELDS_BY_TERM[term]}


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


def average(scores, term='hk1'):
    fields = FIELDS_BY_TERM[term]
    if any(scores.get(field) is None for field in fields):
        return None
    weights = {f: 2 if f == 'midterm' else 3 if f == 'final' else 1 for f in fields}
    result = sum(Decimal(str(scores[k])) * weight for k, weight in weights.items()) / sum(weights.values())
    return float(result.quantize(Decimal('.1'), rounding=ROUND_HALF_UP))


def annual_average(first, second):
    if first is None or second is None:
        return None
    return float(((Decimal(str(first)) + 2 * Decimal(str(second))) / 3).quantize(Decimal('.1'), rounding=ROUND_HALF_UP))


def student_result(rows, course_id, student_id, term):
    term_rows = {t: find_row(rows, course_id, student_id, t) for t in FIELDS_BY_TERM}
    term_scores = {t: scores_for(row, t) for t, row in term_rows.items()}
    averages = {t: average(scores, t) for t, scores in term_scores.items()}
    selected_average = annual_average(averages['hk1'], averages['hk2']) if term == 'year' else averages[term]
    return {'average': selected_average, 'term_averages': averages, 'term_scores': term_scores}


def view_rows(rows, course_id, students, term):
    output = []
    for student in students:
        row = find_row(rows, course_id, student['id'], term) if term != 'year' else None
        result = student_result(rows, course_id, student['id'], term)
        output.append({'student': {k: student.get(k) for k in ('id', 'display_name', 'student_code')}, 'version': version(row),
                       'scores': result['term_scores'].get(term, {}),
                       'average': result['average'], 'term_averages': result['term_averages'],
                       'unverified_import': unverified_import(row),
                       'history': list(reversed((row or {}).get('history', []))),
                       'legacy_scores': {f: row[f] for f in ('tx4', 'tx5') if row and not unverified_import(row) and f not in FIELDS_BY_TERM.get(term, ()) and row.get(f) is not None}})
    return output


def apply_changes(rows, course_id, students, term, changes, actor):
    if term not in FIELDS_BY_TERM:
        raise ValueError('Bảng tổng kết chỉ tính tự động, không nhập điểm trực tiếp.')
    fields = FIELDS_BY_TERM[term]
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
        if not isinstance(raw, dict) or set(raw) != set(fields):
            raise ValueError(f"{TERMS[term]} cần {len(fields) - 2} cột TX, giữa kì và cuối kì; để trống điểm chưa có.")
        scores = {}
        for field in fields:
            try:
                scores[field] = parse_score(raw[field])
            except ValueError as exc:
                raise ValueError(f"{roster[uid]['display_name']} · {LABELS[field]}: {exc}") from None
        previous = scores_for(row, term)
        if scores == previous:
            continue
        if row is None:
            row = {'student_id': roster[uid]['id'], 'student_code': roster[uid].get('student_code'),
                   'course_id': course_id, 'term': term}
            output.append(row)
        now = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
        if unverified_import(row):
            row.setdefault('original_import', {f: row.get(f) for f in ('source_file', 'tx1', 'tx2', 'tx3', 'tx4', 'tx5', 'midterm', 'final', 'average')})
        row.setdefault('history', []).append({'at': now, 'actor_id': actor['id'],
            'actor_name': actor.get('full_name') or actor.get('username'),
            'before': previous, 'after': scores,
            'average_before': average(previous, term), 'average_after': average(scores, term)})
        row.update(scores, average=average(scores, term), updated_at=now, updated_by=actor['id'], subject='li', entry_source='teacher_manual')
    return output
