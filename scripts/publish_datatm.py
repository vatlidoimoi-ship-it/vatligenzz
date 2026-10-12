"""Publish the prepared five-file catalog to Supabase Storage and JSON store.

Usage: python scripts/publish_datatm.py --env-file ../.env
Only these documents are published. Existing entries are preserved; a timestamp
condition prevents replacing a catalog changed by another writer during upload.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote

import requests
from migrate_json_to_supabase import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BUCKET = 'phyedu-documents'


def checked(response, action):
    if not response.ok:
        raise RuntimeError(f'{action}: HTTP {response.status_code}; response withheld to protect configuration.')
    return response


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args()
    load_dotenv(args.env_file)
    base = os.environ['SUPABASE_URL'].rstrip('/')
    secret = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': secret, 'Authorization': 'Bearer ' + secret}
    table_url = base + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    local_path = ROOT / 'data/documents.json'
    local = json.loads(local_path.read_text(encoding='utf-8-sig'))
    wanted_ids = {f'doc_datatm_{i:02}' for i in range(1, 6)}
    selected = [dict(d) for d in local if d.get('id') in wanted_ids]
    if len(selected) != 5:
        raise RuntimeError('Expected all five prepared datatm entries.')
    for doc in selected:
        # Use the known filename even after local catalog URLs have been updated.
        name = doc['url'].rsplit('/', 1)[-1]
        source = ROOT / 'static/documents/datatm' / name
        with source.open('rb') as handle:
            checksum = hashlib.file_digest(handle, 'sha256').hexdigest()
        if checksum != doc['sha256']:
            raise RuntimeError('Prepared source checksum mismatch: ' + name)
        doc['_source'] = source
    initial = checked(requests.get(table_url, headers=headers, params={
        'key': 'eq.data/documents.json', 'select': 'value,updated_at'}, timeout=30), 'Read catalog').json()
    if len(initial) != 1 or not isinstance(initial[0]['value'], list):
        raise RuntimeError('Expected an existing document catalog row.')
    existing = initial[0]['value']
    stamp = initial[0]['updated_at']
    backup_dir = ROOT / '.runtime_data/publish-backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / ('documents-' + hashlib.sha256(stamp.encode()).hexdigest()[:12] + '.json')
    if not backup.exists():
        backup.write_text(json.dumps(initial[0], ensure_ascii=False, indent=2), encoding='utf-8')
    bucket_url = base + '/storage/v1/bucket'
    buckets = checked(requests.get(bucket_url, headers=headers, timeout=30), 'Read buckets').json()
    bucket = next((b for b in buckets if b['id'] == BUCKET), None)
    if bucket is None:
        checked(requests.post(bucket_url, headers=headers, json={
            'id': BUCKET, 'name': BUCKET, 'public': True, 'file_size_limit': 52428800,
            'allowed_mime_types': ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        }, timeout=30), 'Create document bucket')
    elif not bucket.get('public'):
        raise RuntimeError('Existing document bucket is private; no permissions changed.')

    def upload(doc):
        source = doc.pop('_source')
        object_key = 'datatm/' + doc['sha256'][:16] + '/' + source.name
        suffix = BUCKET + '/' + quote(object_key, safe='/')
        public_url = base + '/storage/v1/object/public/' + suffix
        check = requests.head(public_url, timeout=30)
        if check.status_code != 200:
            if check.status_code not in (400, 404):
                raise RuntimeError(f'Object lookup failed: HTTP {check.status_code}')
            mime = 'application/pdf' if source.suffix == '.pdf' else 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            with source.open('rb') as handle:
                checked(requests.post(base + '/storage/v1/object/' + suffix,
                    headers={**headers, 'Content-Type': mime, 'x-upsert': 'false'},
                    data=handle, timeout=(30, 240)), 'Upload ' + source.name)
        # Verify the public download without a token, not just the upload response.
        digest = hashlib.sha256()
        size = 0
        with checked(requests.get(public_url, stream=True, timeout=(30, 90)), 'Verify public file') as response:
            for chunk in response.iter_content(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
        if size != doc['file_size'] or digest.hexdigest() != doc['sha256']:
            raise RuntimeError('Public download verification failed: ' + source.name)
        doc['url'] = public_url
        # The currently deployed template recognizes ordinary links; 'file' also
        # displays through its fallback and gains download metadata after deploy.
        print('Uploaded and verified: ' + source.name, flush=True)
        return doc

    uploaded = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(upload, doc) for doc in selected]
        for future in as_completed(futures):
            uploaded.append(future.result())
    uploaded.sort(key=lambda d: d['id'])
    merged = list(existing)
    for doc in uploaded:
        previous = next((d for d in existing if d.get('id') == doc['id']), None)
        if previous is not None:
            if previous.get('sha256') != doc['sha256'] or previous.get('url') != doc['url']:
                raise RuntimeError('Existing document ID conflict; catalog not changed.')
        else:
            merged.append(doc)
    if len(merged) != len(existing):
        response = checked(requests.patch(table_url,
            headers={**headers, 'Prefer': 'return=representation'},
            params={'key': 'eq.data/documents.json', 'updated_at': 'eq.' + stamp},
            json={'value': merged}, timeout=30), 'Merge catalog')
        if not response.json():
            raise RuntimeError('Catalog changed during upload; rerun to merge against the latest version. Files are uploaded.')
    verification = checked(requests.get(table_url, headers=headers,
        params={'key': 'eq.data/documents.json', 'select': 'value'}, timeout=30), 'Verify catalog').json()[0]['value']
    for doc in uploaded:
        assert any(d.get('id') == doc['id'] and d.get('url') == doc['url'] for d in verification)
    by_id = {d['id']: d for d in uploaded}
    local_path.write_text(json.dumps([by_id.get(d.get('id'), d) for d in local], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Complete: {len(existing)} previous entries, {len(verification)} current entries. All five public downloads verified.', flush=True)


if __name__ == '__main__':
    main()
