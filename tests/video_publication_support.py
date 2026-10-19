"""In-memory video store for isolated full-app tests (no rendering or uploads)."""
import copy
from contextlib import ExitStack
from unittest.mock import patch
from test_teacher_videos import MemoryStore


class PublishedMemoryStore(MemoryStore):
    def list_published(self):
        return [copy.deepcopy(row['value']) for row in self.rows.values()
                if row['value'].get('status') == 'complete'
                and row['value'].get('publication', {}).get('published') is True]


def attach_store(web):
    memory = PublishedMemoryStore()
    memory.create({'id': '1234567890', 'owner_id': 'teacher', 'status': 'complete',
                   'problem': 'A completed physics lesson', 'created_at': '2026-10-20T00:00:00+00:00',
                   'object_key': '1234567890/result.mp4', 'duration_seconds': 45,
                   'script': {'steps': [{'narration': 'PRIVATE_SCRIPT_NOT_FOR_CATALOG'}]}})
    stack = ExitStack()
    store = web.app.extensions['teacher_videos']['store']
    for name in ['get', 'list', 'create', 'change', 'list_published', 'signed_url']:
        stack.enter_context(patch.object(store, name, side_effect=getattr(memory, name)))
    return memory, stack
