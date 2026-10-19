"""Durable individual jobs with optimistic concurrency; private video objects."""
import os
from urllib.parse import quote
import requests
from .http_client import http_session


class VideoStore:
    prefix = 'video/jobs/'

    def __init__(self):
        self.base = os.getenv('SUPABASE_URL', '').rstrip('/')
        key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
        self.headers = {'apikey': key, 'Authorization': 'Bearer ' + key}
        self.table = os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
        self.bucket = os.getenv('VIDEO_STORAGE_BUCKET', 'teacher-videos')
        self.ready = bool(self.base and key)

    def call(self, method, path, **kwargs):
        if not self.ready:
            raise RuntimeError('Chưa cấu hình Supabase cho video.')
        headers = {**self.headers, **kwargs.pop('headers', {})}
        response = http_session().request(method, self.base + path, headers=headers, timeout=kwargs.pop('timeout', 30), **kwargs)
        if not response.ok:
            raise RuntimeError(f'Kho video chưa sẵn sàng (HTTP {response.status_code}).')
        return response

    def get(self, job_id):
        rows = self.call('GET', '/rest/v1/' + self.table, params={
            'key': 'eq.' + self.prefix + job_id, 'select': 'value,updated_at'}).json()
        return rows[0] if rows else None

    def list(self, owner=None, status=None):
        params = {'key': 'like.' + self.prefix + '*', 'select': 'value,updated_at',
                  'order': 'updated_at.desc,key.asc', 'limit': '100'}
        if owner is not None:
            params['value->>owner_id'] = 'eq.' + str(owner)
        if status:
            params['value->>status'] = 'eq.' + status
        rows = []
        while True:
            page = self.call('GET', '/rest/v1/' + self.table,
                             params={**params, 'offset': str(len(rows))}).json()
            rows.extend(page)
            if len(page) < 100:
                return rows

    def create(self, value):
        self.call('POST', '/rest/v1/' + self.table, json={'key': self.prefix + value['id'], 'value': value})

    def list_published(self):
        """Read only public metadata, without truncating catalogs over 100 jobs."""
        if not self.ready:
            return []
        items = []
        while True:
            rows = self.call('GET', '/rest/v1/' + self.table, params={
                'key': 'like.' + self.prefix + '*',
                'value->>status': 'eq.complete',
                'value->publication->>published': 'eq.true',
                'select': 'id:value->>id,status:value->>status,owner_id:value->>owner_id,object_key:value->>object_key,duration_seconds:value->duration_seconds,publication:value->publication',
                'order': 'key.asc', 'limit': '100', 'offset': str(len(items)),
            }).json()
            items.extend(rows)
            if len(rows) < 100:
                return items

    def change(self, row, value):
        rows = self.call('PATCH', '/rest/v1/' + self.table,
            headers={'Prefer': 'return=representation'},
            params={'key': 'eq.' + self.prefix + value['id'], 'updated_at': 'eq.' + row['updated_at']},
            json={'value': value}).json()
        return rows[0] if rows else None

    def upload(self, job_id, path):
        # Private bucket, provisioned once with scripts/setup_video_storage.py.
        object_key = job_id + '/result.mp4'
        with path.open('rb') as stream:
            self.call('POST', '/storage/v1/object/' + self.bucket + '/' + object_key,
                headers={'Content-Type': 'video/mp4', 'x-upsert': 'true'}, data=stream, timeout=180)
        return object_key

    def signed_url(self, object_key):
        data = self.call('POST', '/storage/v1/object/sign/' + self.bucket + '/' + quote(object_key, safe='/'),
                         json={'expiresIn': 3600}).json()
        return self.base + '/storage/v1' + data['signedURL']
