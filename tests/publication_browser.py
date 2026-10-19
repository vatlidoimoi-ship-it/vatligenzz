"""Browser checks with an already-rendered fake video; no rendering or uploads."""
import os
import threading
from werkzeug.serving import make_server, WSGIRequestHandler
from playwright.sync_api import sync_playwright
import test_role_flows as fixtures
from video_publication_support import attach_store


class QuietHandler(WSGIRequestHandler):
    def log(self, *args, **kwargs):
        pass


test = fixtures.RoleFlowTests()
web = fixtures.web
server = make_server('127.0.0.1', 0, web.app, request_handler=QuietHandler)
origin = f'http://127.0.0.1:{server.server_port}'
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()


def login(context, role):
    test.login(role)
    context.clear_cookies()
    context.add_cookies([{'name': 'session', 'value': test.client.get_cookie('session').value, 'url': origin}])


try:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, channel=os.getenv('TEST_BROWSER_CHANNEL', 'chrome'))
        for width, height in [(1366, 900), (390, 844)]:
            test.setUp()
            memory, patches = attach_store(web)
            with patches:
                context = browser.new_context(viewport={'width': width, 'height': height}, service_workers='block')
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin) else route.abort())
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('dialog', lambda dialog: dialog.accept())
                login(context, 'teacher')
                page.goto(origin + '/teacher/videos')
                page.locator('#video-history button').click()
                page.locator('#video-publication').wait_for(state='visible')
                page.locator('#video-publish-title').fill('Physics published browser')
                page.locator('#video-publish-grade').select_option('10')
                page.locator('#video-publish-group').fill('Motion')
                page.locator('#video-publish-description').fill('A student lesson')
                page.locator('#video-publish-button').click()
                page.locator('#video-published-link').wait_for(state='visible')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
                page.reload()
                page.locator('#video-history button').click()
                page.locator('#video-unpublish').wait_for(state='visible')
                assert page.locator('#video-publish-title').input_value() == 'Physics published browser'

                login(context, 'student')
                page.goto(origin + '/video-lessons')
                page.locator('#lesson-grade').select_option('10')
                page.locator('#lesson-filter').select_option(label='Motion')
                card = page.locator('.lesson-card:visible')
                assert card.count() == 1
                card.click()
                assert page.locator('h1').inner_text() == 'Physics published browser'
                page.goto(origin + '/documents?grade=10&type=lecture')
                assert 'Physics published browser' in page.locator('.lecture-video-card').inner_text()

                login(context, 'admin')
                page.goto(origin + '/admin')
                page.locator('.admin-header-actions a[href="/teacher/dashboard"]').click()
                assert 'Test course' in page.locator('.courses-grid').inner_text()
                assert page.locator('a[href="/teacher/edit_course/course_a"]').count() == 1
                page.locator('a.management-card[href="/teacher/videos"]').click()
                page.locator('#video-history button').click()
                page.locator('#video-unpublish').click()
                page.wait_for_function("document.getElementById('video-unpublish').hidden")
                assert memory.get('1234567890')['value']['publication']['published'] is False
                login(context, 'student')
                page.goto(origin + '/video-lessons')
                assert page.locator('a[href="/video-lessons/teacher-1234567890"]').count() == 0
                assert page.request.get(origin + '/video-lessons/teacher-1234567890/play').status == 404
                assert not errors, errors
                context.close()
            print(f'PASS browser {width}x{height}: teacher publishes -> student library/documents -> admin removes publication')
        browser.close()
finally:
    server.shutdown()
    thread.join(timeout=5)
    fixtures.NETWORK.stop()
    fixtures.ENV.stop()
    fixtures.TEMP.cleanup()
