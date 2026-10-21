"""Validate grade-12 content, physics identities, source pages and actual web handlers."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

import test_docx_exam_bank as existing

ROOT = Path(__file__).resolve().parents[1]


def physics_result(c):
    p=c['inputs']; kind=c['kind']
    if kind=='force': return p['B']*p['I']*p['l']*p['s']
    if kind=='field_from_force': return p['F']/p['I']/p['l']/p['s']
    if kind=='current_from_force': return p['F']/p['B']/p['l']/p['s']
    if kind=='length_from_force': return p['F']/p['B']/p['I']/p['s']
    if kind=='scale': return p['base']*p['factor']
    if kind=='wire_field': return .2*p['I']/p['r']
    if kind=='wire_distance': return 2e-5*p['I']/p['B']
    if kind=='loop_field': return .2*p['pi']*p['N']*p['I']/p['R']
    if kind=='solenoid_field': return 4*p['pi']*1e-4*p['N']*p['I']/p['l']
    if kind=='levitate_current': return p['m']*p['g']/p['B']/p['l']
    if kind=='levitate_mass': return 1000*p['B']*p['I']*p['l']/p['g']
    if kind=='parallel_fields': return abs(p['B1']+p['sign']*p['B2'])
    if kind=='perpendicular_fields': return math.hypot(p['B1'],p['B2'])
    if kind=='flux': return 1000*p['B']*p['S']*p['c']*p['N']
    if kind=='faraday': return p['N']*abs(p['delta'])/p['t']
    if kind=='changing_field': return p['N']*p['S']*p['deltaB']/p['t']
    if kind=='induced_current': return p['emf']/p['R']
    if kind=='joule_power': return p['emf']**2/p['R']
    if kind=='joule_heat': return p['emf']**2/p['R']*p['t']
    if kind=='motional_emf': return p['B']*p['l']*p['v']
    if kind=='motional_current': return p['B']*p['l']*p['v']/p['R']
    if kind=='wavelength': return p['c']/p['f']
    if kind=='frequency': return p['c']/p['wavelength']/1e6
    if kind=='radar': return p['c']*p['t']/2
    if kind=='induced_charge': return 1000*p['delta']/p['R']
    if kind=='induction_time': return p['S']*p['deltaB']/p['emf']
    if kind=='identity': return p['value']
    if kind=='rms': return round(p['peak']/math.sqrt(2),p['round'])
    if kind=='peak': return round(p['rms']*math.sqrt(2),p['round'])
    if kind=='frequency_from_omega': return p['pi_coefficient']/2
    if kind=='period_ms': return 1000/p['f']
    if kind=='cycles': return p['t']/p['T']
    if kind=='instant_current': return p['peak']*p['cos']
    if kind=='resistor_power': return p['I']**2*p['R']
    if kind=='ohm': return p['U']/p['R']
    if kind=='resistor_heat': return p['I']**2*p['R']*p['t']
    if kind=='transformer_voltage': return p['U1']*p['N2']/p['N1']
    if kind=='transformer_turns': return p['N1']*p['U2']/p['U1']
    if kind=='transformer_current': return p['U2']*p['I2']/p['U1']
    if kind=='transmission_loss': return (p['P']/p['U'])**2*p['R']
    if kind=='loss_scale': return p['loss']/p['ratio']**2
    if kind=='generator_peak': return p['N']*p['B']*p['S']*p['omega']
    if kind=='generator_frequency': return p['p']*p['rpm']/60
    if kind=='neutrons': return p['A']-p['Z']
    if kind=='nuclear_charge': return p['Z']*1.6
    if kind=='binding_per_nucleon': return p['E']/p['A']
    if kind=='mass_energy': return p['dm']*p['conversion']
    if kind=='alpha_A': return p['A']-4
    if kind=='beta_Z': return p['Z']+1
    if kind=='decay_remaining': return p['initial']/2**p['halflives']
    if kind=='decay_lost': return p['initial']*(1-2**(-p['halflives']))
    if kind=='elapsed_halflives': return p['T']*p['n']
    if kind=='decay_constant': return p['ln2']/p['T']
    if kind=='activity': return p['N']*p['lam']/1e6
    if kind=='dose_distance': return p['dose']*(p['r1']/p['r2'])**2
    if kind=='efficiency': return p['input']*p['eta']
    if kind=='fission_energy': return p['N']*p['Q']*p['conversion']/1e6
    raise AssertionError('Unchecked formula: '+kind)


class PdfExamTests(existing.WordExamTests):
    bank_path = ROOT/'data/pdf_exams_grade12.json'
    grade = '12'

    def test_matrix_and_unique_content(self):
        self.assertEqual(len(self.exams),20)
        self.assertEqual(len({e['id'] for e in self.exams}),20)
        self.assertEqual(sorted(Counter(e['topic'] for e in self.exams).values()),[5]*4)
        stems=[]
        for e in self.exams:
            self.assertEqual(e['grade'],'12')
            self.assertEqual(e['time_limit'],30)
            self.assertEqual(len(e['questions']),20)
            self.assertEqual(e['scoring_config'],{'multiple_choice':{'weight_percent':100,'points':10}})
            self.assertEqual([q['id'] for q in e['questions']],list(range(1,21)))
            self.assertEqual(Counter(q['correct_answer'] for q in e['questions']),dict.fromkeys('ABCD',5))
            for q in e['questions']:
                self.assertEqual(q['number'],q['id'])
                self.assertEqual(set(q['options']),set('ABCD'))
                self.assertEqual(len(set(q['options'].values())),4)
                self.assertGreater(len(q['explanation']),35)
                self.assertEqual(q['source_file'],e['source_file'])
                self.assertNotRegex(q['question'],r'<[^>]+>|hình vẽ|hình dưới|hình bên')
                self.assertNotIn('\ufffd',json.dumps(q,ensure_ascii=False))
                stems.append(' '.join(q['question'].lower().split()))
        self.assertEqual(len(stems),len(set(stems)))

    def test_original_sources_when_available(self):
        source=ROOT/'datatm'/self.exams[0]['source_file']
        if not source.exists(): self.skipTest('Local supplied PDF unavailable')
        import pymupdf
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        with pymupdf.open(source) as pdf:
            pages=[' '.join(page.get_text().split()) for page in pdf]
        for e in self.exams:
            self.assertEqual(e['source_sha256'],digest)
            for q in e['questions']:
                self.assertGreater(len(q['source_quote']),100)
                self.assertTrue(pages[q['source_page']-1].startswith(q['source_quote']))
                self.assertEqual(q['source_printed_page'],q['source_page']-1)

    def test_all_numerical_answers_against_physics(self):
        count=0
        for e in self.exams:
            for q in e['questions']:
                if 'calculation' not in q: continue
                with self.subTest(exam=e['id'],question=q['id']):
                    c=q['calculation']; expected=physics_result(c)
                    self.assertTrue(math.isclose(c['result'],expected,rel_tol=1e-9))
                    choices={k:float(v.split()[0].replace(',','.')) for k,v in q['options'].items()}
                    matches=[k for k,v in choices.items() if math.isclose(v,expected,rel_tol=5e-6)]
                    self.assertEqual(matches,[q['correct_answer']])
                    count+=1
        self.assertEqual(count,360)

    def test_known_answers_from_question_data(self):
        # Independently hand-calculated anchors cover unit conversions and angular conventions.
        anchors={(1,3):'0,2 N',(1,4):'0,08 N',(1,10):'8 μT',
                 (6,3):'2 mWb',(6,5):'0,8 mWb',(6,18):'0,4 V',
                 (11,4):'141,42 V',(11,20):'20 Hz',
                 (16,3):'12 neutron',(16,7):'18,63 MeV',(16,20):'64 MJ'}
        for (exam,question),answer in anchors.items():
            q=self.exams[exam-1]['questions'][question-1]
            self.assertEqual(q['options'][q['correct_answer']],answer)

    def test_merge_preserves_existing_bank_and_is_idempotent(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from publish_pdf12_exams import merge
        prior={'exams':[{'id':'teacher-owned-exam','grade':'12','questions':[{'custom':True}]}],
               'custom_metadata':{'keep':'unchanged'}}
        original=json.loads(json.dumps(prior))
        merged=merge(prior,self.exams)
        self.assertEqual(prior,original)
        self.assertEqual(merged['exams'][0],original['exams'][0])
        self.assertEqual(merged['custom_metadata'],original['custom_metadata'])
        self.assertEqual(len(merged['exams']),21)
        self.assertEqual(merge(merged,self.exams),merged)
        collision={'exams':[{'id':self.exams[0]['id'],'batch_id':'someone-elses-batch'}]}
        with self.assertRaises(ValueError): merge(collision,self.exams)
        with self.assertRaises(ValueError): merge({'exams':'bad-data'},self.exams)


if __name__=='__main__': unittest.main()
