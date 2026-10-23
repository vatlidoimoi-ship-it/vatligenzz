"""Build an isolated presentation dataset; never write to the live database."""
import copy
from datetime import datetime, timedelta
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / '.runtime_data' / 'presentation'


def build():
    rng = random.Random(20261024)
    plan = json.loads((ROOT / '.runtime_data/roster-migration/plan.json').read_text(encoding='utf-8'))
    data = copy.deepcopy(plan['output'])
    bank = json.loads((ROOT / 'data/li.json').read_text(encoding='utf-8'))
    provenance = {'origin': 'synthetic', 'purpose': 'customer_presentation'}
    students = [u for u in data['data/users.json'] if u.get('role') == 'student']
    courses = data['data/courses.json']
    selected = {}
    for course in courses:
        exams = [e for e in bank['exams'] if str(e.get('grade')) == str(course['grade'])
                 and e.get('questions') and all(q.get('options') and q.get('correct_answer') in q['options'] for q in e['questions'])][:5]
        if len(exams) < 5:
            raise ValueError('Each grade requires five valid multiple choice exams')
        selected[course['id']] = exams
        course['lessons'] = [dict(id=e['id'], title=e['title'], content='', video_url='', questions=e['questions']) for e in exams]
    memberships = {p['user_id']: p for p in data['data/progress.json']}
    results, submissions = [], []
    for student in students:
        membership = memberships[student['id']]
        count = rng.choice([4, 5, 5])
        ability = rng.uniform(.45, .9)
        membership['completed_lessons'] = []
        for index, exam in enumerate(selected[membership['course_id']][:count]):
            when = datetime(2026, 9, 3) + timedelta(days=index * 9 + rng.randrange(8), hours=rng.randrange(8, 22), minutes=rng.randrange(60))
            answers, wrong, correct = {}, [], 0
            for number, question in enumerate(exam['questions']):
                expected = question['correct_answer']
                answer = expected if rng.random() < min(.96, ability + index * .025) else rng.choice([k for k in question['options'] if k != expected])
                answers[str(number)] = answer
                correct += answer == expected
                if answer != expected:
                    wrong.append(dict(question_number=question.get('number', number + 1), question_text=question['question'], user_answer=answer, correct_answer=expected, explanation=question.get('explanation', '')))
            total = len(exam['questions'])
            score = round(correct * 10 / total, 2)
            results.append(dict(user_id=student['id'], username=student['username'], subject='li', subject_name='Vật Lý', subject_icon='⚡', subject_color='#0064B7', exam_id=exam['id'], exam_title=exam['title'], submitted_at=when.strftime('%d/%m/%Y %H:%M:%S'), ai_analysis=None, provenance=provenance, result=dict(essay=None, total_score=score, wrong_answers=wrong, multiple_choice=dict(correct_count=correct, total_questions=total, percentage=round(correct * 100 / total, 1), raw_score=score, weight=100))))
            submissions.append(dict(id=f"presentation_{student['id']}_{index}", user_id=student['id'], course_id=membership['course_id'], exercise_id=exam['id'], answers=answers, submitted_at=when.isoformat(), score=round(correct * 100 / total, 1), correct=correct, total=total, grading_status='automatic', graded_at=when.isoformat(), graded_by='automatic', provenance=provenance))
            if score >= 7:
                membership['completed_lessons'].append(exam['id'])
            membership['last_updated'] = when.isoformat()
    data['data/exam_results.json'] = results
    data['data/submissions.json'] = submissions
    data['data/li.json'] = bank
    for name in ['documents', 'career_assessments', 'video_lessons']:
        source = ROOT / 'data' / (name + '.json')
        if source.exists():
            data['data/' + name + '.json'] = json.loads(source.read_text(encoding='utf-8-sig'))
    for key, value in data.items():
        target = DEST / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    summary = dict(provenance=provenance, students=len(students), courses=len(courses), exam_attempts=len(results), submissions=len(submissions), completed_exercise_attempts=len(submissions), students_meeting_minimum=sum(len({r['exam_id'] for r in results if r['user_id'] == u['id']}) >= 4 for u in students))
    (DEST / 'manifest.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    build()
