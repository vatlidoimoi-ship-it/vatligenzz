"""Merge curated grade-10 exams locally; optionally publish to live Supabase.

Local: python scripts/publish_grade10_exams.py
Remote: python scripts/publish_grade10_exams.py --publish --env-file ../.env
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import requests
from migrate_json_to_supabase import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
BATCH = 'word10-intro-v1'


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def merge(existing, exams):
    ids = {exam['id'] for exam in exams}
    clashes = [exam['id'] for exam in existing.get('exams', [])
               if exam.get('id') in ids and exam.get('batch_id') != BATCH]
    if clashes:
        raise RuntimeError(f'Existing unrelated exam ID collision: {clashes}')
    result = dict(existing)
    result['exams'] = [exam for exam in existing.get('exams', []) if exam.get('id') not in ids] + exams
    return result


def publish_remote(exams, env_file):
    load_dotenv(env_file)
    secret = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': secret, 'Authorization': 'Bearer ' + secret}
    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    params = {'key': 'eq.data/li.json', 'select': 'value,updated_at'}
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok:
        raise RuntimeError(f'Read physics bank: HTTP {response.status_code}')
    rows = response.json()
    if len(rows) != 1:
        raise RuntimeError('Expected exactly one remote physics bank; no changes made')
    row = rows[0]
    merged = merge(row['value'], exams)
    if merged == row['value']:
        print('Remote bank already contains this batch; nothing changed.')
        return
    backup_dir = ROOT / '.runtime_data/publish-backups'
    backup_name = 'li-before-word10-' + hashlib.sha256(row['updated_at'].encode()).hexdigest()[:12] + '.json'
    save(backup_dir / backup_name, row)
    response = requests.patch(url, headers={**headers, 'Prefer': 'return=representation'},
        params={'key': 'eq.data/li.json', 'updated_at': 'eq.' + row['updated_at']},
        json={'value': merged}, timeout=60)
    if not response.ok or not response.json():
        raise RuntimeError(f'Concurrent edit or publish failure: HTTP {response.status_code}')
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok or response.json()[0]['value'] != merged:
        raise RuntimeError('Remote bank readback mismatch')
    print(f"Supabase verified: {len(merged['exams'])} total exams; grade-10 batch published.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--env-file', type=Path, default=ROOT.parent / '.env')
    args = parser.parse_args()
    exams = json.loads((ROOT / 'data/grade10_exams.json').read_text(encoding='utf-8'))['exams']
    if len(exams) != 5 or any(exam.get('batch_id') != BATCH or exam.get('grade') != '10' for exam in exams):
        raise ValueError('Grade-10 batch is incomplete')
    seed_path = ROOT / 'data/li.json'
    existing = json.loads(seed_path.read_text(encoding='utf-8-sig'))
    merged = merge(existing, exams)
    if merged != existing:
        save(seed_path, merged)
    print(f"Local bank: {len(merged['exams'])} exams, including {len(exams)} grade-10 starter exams.")
    if args.publish:
        publish_remote(exams, args.env_file)


if __name__ == '__main__':
    main()
