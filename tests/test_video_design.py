import sys
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from botvideo.visual_design import physics_svg, slide_markup
from botvideo.core import scene_html, infer_physics_diagram_from_text
from botvideo.settings import get_design_template


class DesignTests(unittest.TestCase):
    def svg(self, value):
        result=physics_svg(value,get_design_template('studio'))
        if result:
            ET.fromstring(result)
        return result

    def test_force_requires_explicit_directions(self):
        self.assertEqual(self.svg({'type':'force','labels':{'F':'10 N'}}),'')
        result=self.svg({'type':'force','vectors':[{'label':'F','direction':'right'}]})
        self.assertIn('x2="348"',result)
        self.assertNotIn('>N<',result)
        self.assertNotIn('>P<',result)

    def test_wave_is_spatial_and_amplitude_at_crest(self):
        result=self.svg({'type':'wave'})
        self.assertIn('80.00,95.00',result)
        self.assertIn('240.00,95.00',result)
        self.assertIn('x1="80" y1="69" x2="240"',result)

    def test_circuit_needs_known_topology(self):
        self.assertEqual(self.svg({'type':'circuit','topology':'mixed'}),'')
        self.assertEqual(self.svg({'type':'circuit','topology':'parallel'}),'')
        result=self.svg({'type':'circuit','topology':'parallel','resistors':['R₁','R₂']})
        self.assertIn('y="78"',result)
        self.assertIn('y="160"',result)
        self.assertNotIn('>A<',result)

    def test_lens_rejects_missing_or_unsupported_geometry(self):
        for diagram in [{'type':'optics'},{'type':'optics','focal_length':10,'object_distance':5},
                        {'type':'optics','focal_length':float('nan'),'object_distance':30}]:
            self.assertEqual(self.svg(diagram),'')
        self.assertTrue(self.svg({'type':'optics','focal_length':10,'object_distance':30}))

    def test_no_wrong_unit_or_topology_inference(self):
        self.assertIsNone(infer_physics_diagram_from_text('Hai điện trở mắc song song, R = 3 Ω.','Vật lý'))
        self.assertIsNone(infer_physics_diagram_from_text('Điện trở R = 2 kΩ.','Vật lý'))

    def test_question_cards_escape_markup_and_keep_choices(self):
        markup=slide_markup('Câu hỏi\nA. <script>bad()</script>\nB. Hai\nC. Ba\nD. Bốn')
        self.assertEqual(markup.count('choice-letter'),4)
        self.assertNotIn('<script>',markup)
        self.assertIn('&lt;script&gt;',markup)

    def test_layout_removes_unavailable_diagram(self):
        html=scene_html({'title':'Quang học','narration':'Tia sáng','slide_text':'Tia sáng',
                         'diagram':{'type':'optics'}},0)
        self.assertIn('text-only',html)
        self.assertNotIn('<aside class="visual">',html)
        self.assertIn('PHYEDU',html)

if __name__=='__main__': unittest.main()
