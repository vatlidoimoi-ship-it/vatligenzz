import unittest
from unittest.mock import Mock, patch
from flask import Flask
from utils import storage

class StorageReadTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        storage._catalog_cache.clear()
        self.http = Mock()
        self.http.get.return_value.json.return_value = [{'value': [{'id':'1','role':'student'}]}]
        self.patch = patch.object(storage, 'http_session', return_value=self.http)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        storage._catalog_cache.clear()

    def test_repeated_user_reads_only_fetch_once_and_are_independent(self):
        with self.app.test_request_context('/'):
            first = storage._supabase_get_json('data/users.json')
            first[0]['role'] = 'teacher'
            second = storage._supabase_get_json('data/users.json')
            self.assertEqual(second[0]['role'], 'student')
            self.http.get.assert_called_once()

    def test_roles_are_refetched_on_next_request(self):
        for _ in range(2):
            with self.app.test_request_context('/'):
                storage._supabase_get_json('data/users.json')
        self.assertEqual(self.http.get.call_count, 2)

    def test_reference_catalog_cached_between_gets_but_post_reads_fresh(self):
        for _ in range(2):
            with self.app.test_request_context('/'):
                storage._supabase_get_json('data/documents.json')
        self.assertEqual(self.http.get.call_count, 1)
        with self.app.test_request_context('/', method='POST'):
            storage._supabase_get_json('data/documents.json')
        self.assertEqual(self.http.get.call_count, 2)

    def test_catalog_expires(self):
        with patch.object(storage.time, 'monotonic', return_value=100):
            with self.app.test_request_context('/'):
                storage._supabase_get_json('data/documents.json')
        with patch.object(storage.time, 'monotonic', return_value=131):
            with self.app.test_request_context('/'):
                storage._supabase_get_json('data/documents.json')
        self.assertEqual(self.http.get.call_count, 2)

    def test_write_invalidates_catalog_and_updates_current_request(self):
        with self.app.test_request_context('/'):
            storage._supabase_get_json('data/documents.json')
            storage._supabase_upsert_json('data/documents.json', [{'id':'new'}])
            self.assertEqual(storage._supabase_get_json('data/documents.json'), [{'id':'new'}])
        self.assertNotIn('data/documents.json', storage._catalog_cache)

    def test_failed_fetch_not_cached(self):
        self.http.get.return_value.raise_for_status.side_effect = RuntimeError('network')
        with self.app.test_request_context('/'):
            for _ in range(2):
                with self.assertRaises(RuntimeError):
                    storage._supabase_get_json('data/documents.json')
        self.assertEqual(self.http.get.call_count, 2)
        self.assertNotIn('data/documents.json', storage._catalog_cache)

    def test_background_reads_are_not_memoized(self):
        for _ in range(2):storage._supabase_get_json('data/documents.json')
        self.assertEqual(self.http.get.call_count, 2)

if __name__ == '__main__':unittest.main()
