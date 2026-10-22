"""Inspect teacher class pages in Chrome with isolated temporary records."""
import tempfile
import threading
from pathlib import Path
from werkzeug.serving import make_server
from playwright.sync_api import sync_playwright
from test_teacher_class_reports import TeacherClassReportsTests, web

case = TeacherClassReportsTests('test_class_navigation_and_student_report')
case.setUp()
serializer = web.app.session_interface.get_signing_serializer(web.app)
cookie = serializer.dumps({'user_id': 'teacher', 'username': 'teacher', 'role': 'teacher'})
server = make_server('127.0.0.1', 0, web.app)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='chrome')
        context = browser.new_context(viewport={'width': 1440, 'height': 950})
        context.add_cookies([{'name': web.app.config.get('SESSION_COOKIE_NAME', 'session'),
                              'value': cookie, 'domain': '127.0.0.1', 'path': '/'}])
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        base = f'http://127.0.0.1:{server.server_port}'
        folder = Path(tempfile.mkdtemp(prefix='phyedu-teacher-class-'))
        page.goto(base + '/teacher/classes/course_a')
        assert page.locator('.class-table tbody tr').count() == 2
        page.screenshot(path=str(folder / 'class-desktop.png'), full_page=True)
        page.locator('#classStudentSearch').fill('Trần Bình')
        assert page.locator('.class-table tbody tr:visible').count() == 1
        page.locator('#classStudentSearch').fill('')
        page.locator('a[href$="/students/student"]').click()
        assert page.locator('#report-overview').is_visible()
        page.screenshot(path=str(folder / 'report-desktop.png'), full_page=True)
        for name in ('grades', 'errors', 'knowledge', 'notes'):
            page.locator(f'[data-report-tab="{name}"]').click()
            assert page.locator(f'#report-{name}').is_visible()
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('[data-report-tab="overview"]').click()
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        page.screenshot(path=str(folder / 'report-mobile.png'), full_page=True)
        assert not errors, errors
        print(f'PASS: class roster, search, report tabs, desktop and mobile. Screenshots: {folder}')
        browser.close()
finally:
    server.shutdown()
