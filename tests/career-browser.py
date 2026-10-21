"""UI regression check with real templates/assets, isolated Flask shell, mocked chat.

Requires flask and playwright plus its Chromium browser. Does not import production
app.py, connect to Gemini, or touch student data. Run: python tests/career-browser.py
"""
from pathlib import Path
import re
import json
import os
import tempfile
import threading
from flask import Flask, render_template, session
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
app.secret_key = 'isolated-ui-test-only'


@app.route('/tam-li-huong-nghiep', endpoint='career_guidance')
def page():
    session['user_id'] = 'ui-test'
    session['username'] = 'Học sinh'
    session['role'] = 'student'
    return render_template('career_guidance.html', assessment_catalog=json.loads((ROOT / 'data/career_assessments.json').read_text(encoding='utf-8')))


for endpoint in set(re.findall(r"url_for\('([^']+)'", (ROOT / 'templates/base.html').read_text(encoding='utf-8'))):
    if endpoint not in app.view_functions:
        app.add_url_rule('/stub/' + endpoint, endpoint, lambda: '')

server = make_server('127.0.0.1', 0, app)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.environ.get('CARE_TEST_BROWSER') or None)
        context = browser.new_context(viewport={'width': 1440, 'height': 1050}, reduced_motion='reduce', service_workers='block')
        page = context.new_page()
        errors, outgoing = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: outgoing.append(request.url) if request.method == 'POST' else None)
        page.route('**/api/career-guidance/chat', lambda route: route.fulfill(json={'success': True, 'response': 'Phản hồi thử nghiệm.'}))
        page.route('**/api/career-guidance/completion', lambda route: route.fulfill(json={'success': True}))
        page.goto(f'http://127.0.0.1:{server.server_port}/tam-li-huong-nghiep')
        page.locator('.care-card').first.wait_for()
        assert page.locator('.care-card').count() == 5
        assert page.locator('#chatPanel').is_hidden()
        page.locator('.care-card img').evaluate_all('(images) => images.forEach(i => i.loading = "eager")')
        page.wait_for_function('Array.from(document.querySelectorAll(".care-card img")).every(i => i.complete && i.naturalWidth > 0)')
        screenshot_dir = Path(tempfile.mkdtemp(prefix='phyedu-care-'))
        page.screenshot(path=str(screenshot_dir / 'desktop.png'), full_page=True)
        page.locator('[data-filter="wellbeing"]').click()
        assert page.locator('.care-card').count() == 2
        page.locator('[data-open="dass-21"]').click()
        assert page.locator('[data-action="start"]').count() == 0
        assert page.locator('#assessmentContent').inner_text().find('không mở bài test') >= 0
        page.locator('#closeAssessment').click()
        page.locator('[data-filter="all"]').click()

        for package_id, count in [('holland', 30), ('big-five', 50), ('mbti', 16), ('who-5', 5)]:
            page.locator(f'[data-open="{package_id}"]').click()
            page.locator('[data-action="start"]').click()
            assert page.locator('[data-action="next"]').is_disabled()
            for index in range(count):
                page.locator('input[name="care-answer"]').last.check()
                page.locator('[data-action="next"]').click()
            assert page.locator('[data-action="share"]').is_visible()
            if package_id == 'who-5':
                assert '100/100' in page.locator('#assessmentContent').inner_text()
                page.locator('[data-action="review"]').click()
                assert page.locator('input[name="care-answer"]').last.is_checked()
                page.locator('input[name="care-answer"]').first.check()
                for _ in range(count):
                    page.locator('[data-action="next"]').click()
                assert '80/100' in page.locator('#assessmentContent').inner_text()
                page.locator('[data-action="share"]').click()
                assert page.locator('#chatPanel').is_visible()
                assert 'WHO-5' in page.locator('#advisorInput').input_value()
                completion_requests = [url for url in outgoing if url.endswith('/api/career-guidance/completion')]
                assert len(completion_requests) == 4
                page.locator('#sendBtn').click()
                page.locator('.bot-message').filter(has_text='Phản hồi thử nghiệm.').wait_for()
                assert len([url for url in outgoing if url.endswith('/api/career-guidance/chat')]) == 1
                page.locator('#exploreTab').click()
            else:
                page.locator('#closeAssessment').click()

        page.locator('[data-open="holland"]').click()
        page.locator('[data-action="start"]').click()
        page.locator('input[name="care-answer"]').first.check()
        page.locator('[data-action="next"]').click()
        page.locator('[data-action="previous"]').click()
        assert page.locator('input[name="care-answer"]').first.is_checked()
        page.keyboard.press('Escape')
        page.locator('[data-action="keep"]').click()
        assert page.locator('input[name="care-answer"]').first.is_checked()
        page.locator('#closeAssessment').click()
        page.locator('[data-action="discard"]').click()
        page.locator('[data-open="holland"]').click()
        page.locator('[data-action="start"]').click()
        assert page.locator('input:checked').count() == 0
        page.keyboard.press('Escape')

        for width in [390, 768, 1024]:
            page.set_viewport_size({'width': width, 'height': 844})
            if page.evaluate('document.documentElement.scrollWidth > innerWidth'):
                print(page.evaluate('Array.from(document.querySelectorAll("body *")).filter(e => e.getBoundingClientRect().right > innerWidth + 1).map(e => [e.tagName,e.className,e.getBoundingClientRect().right]).slice(0,20)'))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
            if width == 390:
                page.screenshot(path=str(screenshot_dir / 'mobile.png'), full_page=True)
                page.locator('[data-open="who-5"]').click()
                page.locator('[data-action="start"]').click()
                assert page.locator('[data-action="next"]').is_visible()
                page.screenshot(path=str(screenshot_dir / 'question-mobile.png'), full_page=True)
                page.keyboard.press('Escape')
            page.locator('#chatTab').click()
            assert page.locator('#mobileNewChatBtn').is_visible()
            assert page.locator('#advisorInput').is_visible()
            page.locator('#mobileNewChatBtn').click()
            assert 'Mình đã mở' in page.locator('#messages').inner_text()
            page.locator('#exploreTab').click()
        # Delayed chat completion must not leak into a newly reset conversation.
        page.locator('#chatTab').click()
        page.evaluate('''() => {
            window.careFetchOriginal = window.fetch;
            window.carePending = [];
            window.fetch = (url, options) => url === '/api/career-guidance/chat'
                ? new Promise(resolve => window.carePending.push(resolve))
                : window.careFetchOriginal(url, options);
        }''')
        page.locator('#advisorInput').fill('First message')
        page.locator('#advisorInput').press('Enter')
        page.locator('#advisorInput').fill('Second message')
        page.locator('#advisorInput').press('Enter')
        assert page.evaluate('window.carePending.length') == 1
        page.locator('#mobileNewChatBtn').click()
        page.evaluate('window.carePending[0]({json: async () => ({success:true,response:"STALE_RESPONSE"})})')
        assert 'STALE_RESPONSE' not in page.locator('#messages').inner_text()
        assert page.locator('#sendBtn').is_enabled()
        page.evaluate('window.fetch = window.careFetchOriginal')
        assert not errors, errors
        print(f'PASS: 4 questionnaire flows, DASS info, scoring review, privacy handoff, cancellation, filters, 3 responsive widths. Screenshots: {screenshot_dir}')
        browser.close()
finally:
    server.shutdown()
