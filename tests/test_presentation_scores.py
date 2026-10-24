import copy
import unittest
from scripts.presentation_scores import rebalance


class PresentationScoresTests(unittest.TestCase):
    def test_exact_distribution_answer_consistency_and_real_records_preserved(self):
        bank = {'exams': [{'id': str(n), 'questions': [{'question': 'Q', 'options': {'A': 'Yes', 'B': 'No'}, 'correct_answer': 'A'} for _ in range(n)]} for n in [8, 9, 16, 20]]}
        results, submissions = [], []
        real = {'user_id': 'real', 'result': {'total_score': 2}}
        for i in range(100):
            n = [8, 9, 16, 20][i % 4]
            origin = {'origin': 'synthetic', 'purpose': 'customer_presentation'}
            results.append({'user_id': str(i), 'exam_id': str(n), 'submitted_at': '01/09/2026 10:00:00', 'result': {'multiple_choice': {}}, 'provenance': origin})
            submissions.append({'user_id': str(i), 'exercise_id': str(n), 'submitted_at': '2026-09-01T10:00:00', 'provenance': origin})
        results.append(copy.deepcopy(real))
        summary = rebalance(results, submissions, bank)
        self.assertEqual(summary['bands'], {7: 10, 8: 30, 9: 40, 10: 20})
        self.assertEqual(results[-1], real)
        for result, sub in zip(results, submissions):
            correct = sum(a == 'A' for a in sub['answers'].values())
            self.assertEqual(correct, sub['correct'])
            self.assertEqual(len(result['result']['wrong_answers']), sub['total'] - correct)
            self.assertEqual(result['result']['total_score'], round(correct * 10 / sub['total'], 2))
