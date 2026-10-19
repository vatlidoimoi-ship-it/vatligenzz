"""Real browser flow checks against isolated test data; no AI or remote storage.

Run: python -B tests/role_flows_browser.py
"""
import contextlib
import io
import os
import threading
from datetime import datetime, timedelta
from urllib.parse import urlparse
from werkzeug.serving import make_server, WSGIRequestHandler
from playwright.sync_api import sync_playwright
import test_role_flows as fixtures


class QuietHandler(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


test = fixtures.RoleFlowTests()
web = fixtures.web
server = make_server('127.0.0.1', 0, web.app, request_handler=QuietHandler)
origin = f'http://127.0.0.1:{server.server_port}'
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


def set_session(context, role):
    test.login(role)
    cookie = test.client.get_cookie('session')
    context.clear_cookies()
    context.add_cookies([{'name': 'session', 'value': cookie.value, 'url': origin}])


try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, channel=os.getenv('TEST_BROWSER_CHANNEL', 'chrome'))
        for width, height in [(1366, 900), (390, 844)]:
            test.setUp()
            # Quotes and markup must remain literal text in question attributes.
            test.course['lessons'][0]['questions'][0]['question'] = 'A "quote" and <b>literal</b>'
            web.db._save_json(web.db.courses_file, [test.course])
            context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
            context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin)
                          else route.abort())
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            set_session(context, 'student')
            page.goto(origin + '/exercises')
            page.locator('[data-exercise]').click()
            page.locator('#exerciseModal').wait_for(state='visible')
            assert page.locator('#questionsContainer .question-text').inner_text() == 'A "quote" and <b>literal</b>'
            page.locator('#questionsContainer input[value="A"]').check()
            page.locator('#exerciseForm button[type="submit"]').click()
            page.locator('.score-number').filter(has_text='100%').wait_for()
            page.reload()
            assert '100.0/100' in page.locator('.submission-status').inner_text()
            set_session(context, 'teacher')
            page.goto(origin + '/teacher/view_submissions')
            page.locator('.grade-form input[name="score"]').fill('82.5')
            page.locator('.grade-form textarea').fill('Browser feedback')
            page.locator('.grade-form button').click()
            page.wait_for_function("document.querySelector('.submission-badge').textContent.includes('82.5')")
            page.reload()
            assert page.locator('.grade-form input').input_value() == '82.5'
            set_session(context, 'student')
            page.goto(origin + '/exercises')
            assert '82.5/100' in page.locator('.submission-status').inner_text()
            assert 'Browser feedback' in page.locator('.submissions-section').inner_text()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), page.evaluate("[...document.querySelectorAll('body *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1).slice(0, 12).map(e => [e.tagName, e.className, e.getBoundingClientRect().width])")

            # Follow a full game; the browser does not get an answer key before answering.
            test.start_game()
            set_session(context, 'student')
            page.goto(origin + '/enter_nickname')
            page.locator('form[action="/start_game"] button[type="submit"]').first.click()
            page.locator('.option').filter(has_text='A').click()
            page.locator('.result-score-big').wait_for(timeout=10000)
            assert page.locator('.result-score-big').inner_text() == '1/1'

            # Use a short remaining session and let the actual countdown submit.
            test.seed_exam()
            test.login('student')
            with test.client.session_transaction() as state:
                state['exam_start_li_exam_test'] = (datetime.now() - timedelta(seconds=56)).isoformat()
            cookie = test.client.get_cookie('session')
            context.add_cookies([{'name': 'session', 'value': cookie.value, 'url': origin}])
            with contextlib.redirect_stdout(io.StringIO()):
                page.goto(origin + '/tracnghiem/lam-bai/li/exam_test')
                page.locator('input[value="A"]').check()
                page.wait_for_url('**/tracnghiem/ket-qua/li/exam_test', timeout=15000)
            assert not errors, errors
            context.close()
            print(f'PASS browser {width}x{height}: exercise -> teacher grade -> student result; game; timed exam')
        browser.close()
finally:
    server.shutdown()
    thread.join(timeout=5)
    fixtures.NETWORK.stop()
    fixtures.ENV.stop()
    fixtures.TEMP.cleanup()
