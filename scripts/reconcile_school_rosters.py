"""Prepare and apply the six class rosters supplied in thaydoiquantrong.

Default mode is read-only: fetch current Supabase JSON, validate the Excel
files, and write an ignored local plan. --apply writes a remote archive first,
then replaces active documents. --resume retries an existing local plan.
"""
import argparse
from collections import Counter
from datetime import datetime
import json
import os
from pathlib import Path
import sys

import requests
import xlrd
from dotenv import dotenv_values
from werkzeug.security import generate_password_hash

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'thaydoiquantrong'
PLAN_FILE = ROOT / '.runtime_data' / 'roster-migration' / 'plan.json'
COURSES = {
    '10A1': ('Nguyễn Trọng Duy', 'gv_excel_10a1'),
    '10A2': ('Vũ Thị Hiếu', 'gv_excel_10a2'),
    '11A4': ('Nguyễn Thị Lan', 'gv_excel_11a4'),
    '11A5': ('Trần Văn Nguyên', None),
    '12A4': ('Nguyễn Đình Thu', 'gv_excel_12a4'),
    '12A7': ('Trần Văn Nguyên', None),
}
EXPECTED = {'10A1': 44, '10A2': 44, '11A4': 45, '11A5': 42, '12A4': 37, '12A7': 35}
START_DATE = '2026-09-01T08:00:00+07:00'
ARCHIVE_KEY = 'archive/2026-10-22-before-excel-rosters'
DOCUMENTS = [
    'users', 'courses', 'progress', 'exam_results', 'submissions', 'exercises',
    'forum_posts', 'forum_comments', 'forum_points', 'chat_messages',
    'mbti_results', 'holland_results', 'career_completions', 'gift_events',
    'shop_orders', 'user_inventory', 'user_profiles', 'notifications',
    'forum_reports', 'forum_bans', 'physics_grades',
]
ID_FIELDS = {'user_id', 'student_id', 'author_id', 'recipient_id', 'target_user_id',
             'reporter_id', 'buyer_id', 'owner_id'}


def excel_rosters():
    result = {}
    for path in SOURCE.glob('so_diem_chi_tiet_lop_*_mon_toan_hoc.xls'):
        class_name = path.stem.split('_lop_', 1)[1].split('_mon_', 1)[0].upper()
        if class_name not in EXPECTED:
            raise ValueError(f'Unexpected class file: {path.name}')
        with open(os.devnull, 'w') as log:
            workbook = xlrd.open_workbook(str(path), ignore_workbook_corruption=True, logfile=log)
        sheet = workbook.sheet_by_index(0)
        records = []
        for index in range(7, sheet.nrows):
            row = sheet.row_values(index)
            if not isinstance(row[0], (int, float)) or not row[1] or not (row[2] or row[3]):
                continue
            code = str(int(row[1])) if isinstance(row[1], (int, float)) else str(row[1]).strip()
            if not code.isdigit():
                raise ValueError(f'Invalid student code in {path.name} row {index + 1}')
            name = f'{str(row[2]).strip()} {str(row[3]).strip()}'.strip()
            values = {field: (float(row[column]) if isinstance(row[column], (int, float)) else None)
                      for field, column in [('tx1', 5), ('tx2', 6), ('tx3', 7), ('tx4', 8),
                                            ('tx5', 9), ('midterm', 10), ('final', 11), ('average', 12)]}
            if any(value is not None and not 0 <= value <= 10 for value in values.values()):
                raise ValueError(f'Invalid score in {path.name} row {index + 1}')
            records.append({'code': code, 'name': name, 'class_name': class_name,
                            'source_file': path.name, 'scores': values})
        if len(records) != EXPECTED[class_name]:
            raise ValueError(f'{class_name}: expected {EXPECTED[class_name]}, got {len(records)}')
        result[class_name] = records
    if set(result) != set(EXPECTED):
        raise ValueError(f'Missing class files: {set(EXPECTED) - set(result)}')
    codes = [row['code'] for rows in result.values() for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError('Duplicate student code across class files')
    return result


class RemoteStore:
    def __init__(self, env_path):
        env = dotenv_values(env_path)
        key = env.get('SUPABASE_SERVICE_ROLE_KEY') or env.get('SUPABASE_KEY')
        if not key or not env.get('SUPABASE_URL'):
            raise ValueError('Supabase connection is not configured')
        self.url = env['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + env.get('SUPABASE_JSON_TABLE', 'app_json_store')
        self.headers = {'apikey': key, 'Authorization': f'Bearer {key}',
                        'Accept': 'application/json', 'Content-Type': 'application/json'}

    def get(self, key):
        response = requests.get(self.url, headers=self.headers,
                                params={'key': f'eq.{key}', 'select': 'value'}, timeout=30)
        response.raise_for_status()
        rows = response.json()
        return rows[0]['value'] if rows else None

    def put(self, key, value):
        response = requests.post(self.url,
                                 headers={**self.headers, 'Prefer': 'resolution=merge-duplicates,return=minimal'},
                                 params={'on_conflict': 'key'}, json={'key': key, 'value': value}, timeout=60)
        response.raise_for_status()


def references_removed(record, removed_ids):
    return any(str(record.get(field)) in removed_ids for field in ID_FIELDS)


def build_plan(before, rosters):
    old_users = before['data/users.json']
    old_courses = before['data/courses.json']
    if not isinstance(old_users, list) or not isinstance(old_courses, list):
        raise ValueError('Unexpected users or courses shape')
    old_students = [u for u in old_users if u.get('role') == 'student']
    removed_ids = {str(u['id']) for u in old_students}
    if len(old_students) != 258 or len([u for u in old_students if not u.get('class_name')]) != 18:
        raise ValueError('Active student counts changed; rebuild and review the plan')
    admins = [u for u in old_users if u.get('role') == 'admin']
    if len(admins) != 1:
        raise ValueError('Expected exactly one admin')
    admin = dict(admins[0], username='Trần Văn Nguyên', full_name='Trần Văn Nguyên')
    password = generate_password_hash('VatLi2026')
    new_teachers = [{'id': teacher_id, 'username': name, 'full_name': name,
                     'role': 'teacher', 'email': teacher_id + '@phyedu.local',
                     'password': password, 'created_at': START_DATE}
                    for name, teacher_id in COURSES.values() if teacher_id]
    # Existing teachers remain with their original identities; they no longer
    # own the six replaced classes, so their older authored content stays linked.
    new_users = [dict(u) for u in old_users if u.get('role') == 'teacher'] + [admin] + new_teachers
    all_students = [row for class_rows in rosters.values() for row in class_rows]
    new_users += [{'id': 'hs_excel_' + row['code'], 'username': row['code'],
                   'full_name': row['name'], 'student_code': row['code'],
                   'class_name': row['class_name'], 'role': 'student',
                   'email': row['code'] + '@phyedu.local', 'password': password,
                   'created_at': START_DATE} for row in all_students]
    if len({u['username'] for u in new_users}) != len(new_users):
        raise ValueError('Username collision after import')
    if len({str(u['id']) for u in new_users}) != len(new_users):
        raise ValueError('User ID collision after import')
    classes = []
    for class_name, (teacher_name, teacher_id) in COURSES.items():
        classes.append({'id': 'lop2026_' + class_name.lower(),
                        'teacher_id': teacher_id or admin['id'],
                        'title': 'Vật lí lớp ' + class_name,
                        'description': '', 'grade': class_name[:2],
                        'lessons': [], 'created_at': START_DATE})
    old_course_ids = {str(course['id']) for course in old_courses}
    output = {}
    output['data/users.json'] = new_users
    output['data/courses.json'] = [course for course in old_courses
                                   if str(course.get('id')) not in old_course_ids] + classes
    output['data/progress.json'] = [row for row in (before.get('data/progress.json') or [])
                                    if str(row.get('user_id')) not in removed_ids
                                    and str(row.get('course_id')) not in old_course_ids]
    output['data/progress.json'] += [{'user_id': 'hs_excel_' + row['code'],
                                     'course_id': 'lop2026_' + row['class_name'].lower(),
                                     'completed_lessons': []} for row in all_students]
    for name in DOCUMENTS:
        key = 'data/' + name + '.json'
        if key in output or name == 'physics_grades':
            continue
        value = before.get(key)
        if not isinstance(value, list):
            continue
        if name == 'exercises':
            output[key] = [row for row in value if str(row.get('course_id')) not in old_course_ids]
        else:
            output[key] = [row for row in value if not references_removed(row, removed_ids)]
    removed_posts = {row.get('id') for row in (before.get('data/forum_posts.json') or [])
                     if str(row.get('author_id')) in removed_ids}
    removed_comments = {row.get('id') for row in (before.get('data/forum_comments.json') or [])
                        if str(row.get('author_id')) in removed_ids or row.get('post_id') in removed_posts}
    for name in ('forum_comments', 'forum_points', 'forum_reports'):
        key = 'data/' + name + '.json'
        output[key] = [row for row in output.get(key, [])
                       if row.get('post_id') not in removed_posts
                       and row.get('target_id') not in removed_posts | removed_comments]
    output['data/physics_grades.json'] = [
        {'student_id': 'hs_excel_' + row['code'], 'student_code': row['code'],
         'course_id': 'lop2026_' + row['class_name'].lower(), 'term': 'hk1',
         'source_file': row['source_file'], **row['scores']}
        for row in all_students]
    return output, removed_ids


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path, default=ROOT.parent / '.env')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.resume:
        plan = json.loads(PLAN_FILE.read_text(encoding='utf-8'))
    else:
        rosters = excel_rosters()
        remote = RemoteStore(args.env_file)
        before = {key: remote.get(key) for key in ['data/' + name + '.json' for name in DOCUMENTS]}
        output, removed_ids = build_plan(before, rosters)
        plan = {'archive_key': ARCHIVE_KEY, 'before': before, 'output': output,
                'removed_student_count': len(removed_ids),
                'new_student_count': sum(map(len, rosters.values()))}
        PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
        PLAN_FILE.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Archive key:', plan['archive_key'])
    print('Old students archived:', plan['removed_student_count'])
    print('New students:', plan['new_student_count'])
    print('New class sizes:', dict(Counter(u['class_name'] for u in plan['output']['data/users.json']
                                           if u.get('role') == 'student')))
    print('Plan:', PLAN_FILE)
    if not args.apply:
        print('Read-only preparation complete. No remote writes.')
        return
    remote = RemoteStore(args.env_file)
    for key in ('data/users.json', 'data/courses.json', 'data/progress.json',
                'data/exam_results.json', 'data/submissions.json'):
        current = remote.get(key)
        if current != plan['before'].get(key) and current != plan['output'].get(key):
            raise RuntimeError(f'Remote data changed after preparation: {key}')
    archive = remote.get(plan['archive_key'])
    if archive is not None and archive != plan['before']:
        raise RuntimeError('Existing archive differs from the prepared snapshot')
    if archive is None:
        remote.put(plan['archive_key'], plan['before'])
    for key, value in plan['output'].items():
        remote.put(key, value)
        if remote.get(key) != value:
            raise RuntimeError(f'Readback mismatch: {key}')
        print('Verified:', key)
    print('Remote import complete.')


if __name__ == '__main__':
    main()
