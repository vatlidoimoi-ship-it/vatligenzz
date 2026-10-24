"""Rebalance explicitly synthetic records without modifying real assessments."""
from collections import Counter
import random


def synthetic(row):
    return row.get('provenance') == {'origin': 'synthetic', 'purpose': 'customer_presentation'}


def rebalance(results, submissions, bank):
    rng = random.Random(20261024)
    rows = [r for r in results if synthetic(r)]
    exams = {e['id']: e for e in bank['exams']}
    pairs = {}
    for sub in submissions:
        if synthetic(sub):
            key = (sub['user_id'], sub['exercise_id'], sub['submitted_at'])
            if key in pairs:
                raise ValueError('Duplicate synthetic submission')
            pairs[key] = sub
    def choices(row, band):
        total = len(exams[row['exam_id']]['questions'])
        return [n for n in range(total + 1) if (band <= round(n * 10 / total, 2) < band + 1 if band < 10 else n == total)]
    targets = {7: round(len(rows) * .10), 8: round(len(rows) * .30), 9: round(len(rows) * .40)}
    targets[10] = len(rows) - sum(targets.values())
    remaining = list(range(len(rows)))
    assignments = {}
    # Short exams may have no possible score in [9, 10); allocate that band first.
    for band in [9, 10, 7, 8]:
        eligible = [i for i in remaining if choices(rows[i], band)]
        if len(eligible) < targets[band]:
            raise ValueError('Question counts cannot support requested distribution')
        picked = rng.sample(eligible, targets[band])
        for i in picked:
            assignments[i] = band
        used = set(picked)
        remaining = [i for i in remaining if i not in used]
    for i, row in enumerate(rows):
        questions = exams[row['exam_id']]['questions']
        total = len(questions)
        correct = rng.choice(choices(row, assignments[i]))
        correct_indices = set(rng.sample(range(total), correct))
        answers, wrong = {}, []
        for number, question in enumerate(questions):
            expected = question['correct_answer']
            answer = expected if number in correct_indices else rng.choice([k for k in question['options'] if k != expected])
            answers[str(number)] = answer
            if answer != expected:
                wrong.append(dict(question_number=question.get('number', number + 1), question_text=question['question'], user_answer=answer, correct_answer=expected, explanation=question.get('explanation', '')))
        from datetime import datetime
        submitted_at = datetime.strptime(row['submitted_at'], '%d/%m/%Y %H:%M:%S').isoformat()
        sub = pairs[(row['user_id'], row['exam_id'], submitted_at)]
        score = round(correct * 10 / total, 2)
        row['result'].update(total_score=score, wrong_answers=wrong)
        row['result']['multiple_choice'].update(correct_count=correct, total_questions=total, percentage=round(correct * 100 / total, 1), raw_score=score, weight=100)
        row['ai_analysis'] = None
        sub.update(answers=answers, correct=correct, total=total, score=round(correct * 100 / total, 1))
    actual = Counter(10 if r['result']['total_score'] == 10 else int(r['result']['total_score']) for r in rows)
    if dict(actual) != targets:
        raise ValueError('Distribution verification failed')
    return dict(records=len(rows), bands=dict(sorted(actual.items())), average=round(sum(r['result']['total_score'] for r in rows) / len(rows), 3))
