import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from flask import Flask
from utils.video_library import register_video_library
from botvideo.core import sanitize_script_for_render
from botvideo.visual_design import physics_svg
from botvideo.settings import get_design_template

class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'catalog.json'
        self.path.write_text(json.dumps([{'id':'vl-01','title':'Test','group':'Test','grade':'11','source':None,'poster':'video_posters/vl-01.png','duration':50,'size_bytes':1000,'object_key':'2026101301/result.mp4'}]))
        self.app=Flask(__name__,template_folder=str(Path(__file__).resolve().parents[1]/'templates'))
        self.app.secret_key='test'
        self.app.add_url_rule('/login','login',lambda:'login')
        self.store=Mock();self.store.signed_url.return_value='https://example.test/signed'
        register_video_library(self.app,lambda uid:{'id':uid} if uid=='test' else None,self.store,self.path)
        self.client=self.app.test_client()
    def tearDown(self):self.tmp.cleanup()
    def login(self):
        with self.client.session_transaction() as session:session['user_id']='test'
    def test_guest_cannot_get_private_playback(self):
        self.assertEqual(self.client.get('/video-lessons/vl-01/play').status_code,302)
        self.store.signed_url.assert_not_called()
    def test_signed_in_student_can_play_only_catalog_items(self):
        self.login()
        response=self.client.get('/video-lessons/vl-01/play')
        self.assertEqual(response.location,'https://example.test/signed')
        self.assertIn('no-store',response.headers['Cache-Control'])
        self.store.signed_url.assert_called_once_with('2026101301/result.mp4')
        self.assertEqual(self.client.get('/video-lessons/private-job/play').status_code,404)
    def test_storage_failure_is_recoverable(self):
        self.login();self.store.signed_url.side_effect=RuntimeError('private details')
        response=self.client.get('/video-lessons/vl-01/play')
        self.assertEqual(response.status_code,503)
        self.assertNotIn(b'private details',response.data)
    def test_curated_conclusion_does_not_get_synthetic_summary(self):
        script={'subject':'Vật lý','problem':'Con lắc dao động góc nhỏ, tính chu kì.','include_full_solution':False,'steps':[{'title':'Chu kì','slide_text':'T = 2 s','narration':'Chu kì bằng hai giây.'}]}
        result=sanitize_script_for_render(script,original_problem=script['problem'],subject='Vật lý')
        self.assertEqual(len(result['steps']),1)
    def test_pendulum_never_labels_an_unspecified_angle(self):
        svg=physics_svg({'type':'pendulum','show_angle':False},get_design_template('studio'))
        self.assertNotIn('6°',svg)
        self.assertEqual(physics_svg({'type':'pendulum','angle_deg':90},get_design_template('studio')),'')

if __name__=='__main__':unittest.main()
