"""Source and end-to-end checks for the grade-10 starter bank.

Run separately: python -B tests/test_grade10_exam_bank.py
"""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_grade10_exams import PLAN, build, paragraphs, parse_section
import test_role_flows as fixtures

web = fixtures.web
BANK = json.loads((ROOT / 'data/grade10_exams.json').read_text(encoding='utf-8'))['exams']


class Grade10BankTests(unittest.TestCase):
    def test_derived_from_sources_and_reviewable(self):
        self.assertEqual(build()['exams'], BANK)
        self.assertEqual(len(BANK), 5)
        self.assertEqual(sum(len(exam['questions']) for exam in BANK), 49)
        self.assertEqual(len({exam['id'] for exam in BANK}), 5)
        for exam, (_, lesson, section, _, selected, minutes) in zip(BANK, PLAN):
            source, lines = paragraphs(lesson)
            parsed = parse_section(lines, section)
            self.assertEqual(exam['source_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(exam['time_limit'], minutes)
            self.assertEqual([q['id'] for q in exam['questions']], list(range(1, len(selected) + 1)))
            for question in exam['questions']:
                original = parsed[question['source_question']]
                self.assertEqual(question['question'], original['question'])
                self.assertEqual(question['options'], original['options'])
                self.assertEqual(question['correct_answer'], original['correct_answer'])
                self.assertEqual(set(question['options']), set('ABCD'))
                self.assertTrue(all(question['options'].values()))
                self.assertNotIn('Biển báo  mang ý nghĩa', question['question'])

    def test_local_li_bank_preserves_other_grades(self):
        all_exams = json.loads((ROOT / 'data/li.json').read_text(encoding='utf-8-sig'))['exams']
        counts = {grade: sum(str(exam.get('grade')) == grade for exam in all_exams)
                  for grade in ('10', '11', '12')}
        self.assertEqual(counts, {'10': 9, '11': 22, '12': 24})
        self.assertTrue({exam['id'] for exam in BANK}.issubset(
            {exam['id'] for exam in all_exams if exam.get('grade') == '10'}))

    def test_all_grade10_exams_render_submit_and_history(self):
        case = fixtures.RoleFlowTests()
        case.setUp()
        web._save_subject_exam_data('li', {'exams': BANK})
        client = case.client
        response = client.get('/tracnghiem?grade=10')
        self.assertEqual(response.status_code, 200)
        for exam in BANK:
            self.assertIn(exam['title'].encode(), response.data)
            page = client.get('/tracnghiem/lam-bai/li/' + exam['id'])
            self.assertEqual(page.status_code, 200)
            self.assertNotIn(b'correct_answer', page.data)
            self.assertEqual(page.data.count(b'name="question_'), 4 * len(exam['questions']))
            answers = {str(question['id']): question['correct_answer'] for question in exam['questions']}
            result = client.post('/tracnghiem/nop-bai', json={
                'subject': 'li', 'exam_id': exam['id'], 'answers': answers})
            self.assertEqual(result.status_code, 200, result.data[:200])
            self.assertEqual(result.json['result']['total_score'], 10)
        history = client.get('/tracnghiem/lich-su')
        self.assertEqual(history.status_code, 200)
        for exam in BANK:
            self.assertIn(exam['title'].encode(), history.data)


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        fixtures.NETWORK.stop()
        fixtures.ENV.stop()
        fixtures.TEMP.cleanup()
