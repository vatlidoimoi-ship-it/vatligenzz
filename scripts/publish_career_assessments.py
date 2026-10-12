"""Publish only the questionnaire catalog, never student answers or other tables."""
import argparse
import json
import os
from pathlib import Path
import requests
from migrate_json_to_supabase import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    args = parser.parse_args()
    load_dotenv(args.env_file)
    catalog = json.loads((ROOT / 'data/career_assessments.json').read_text(encoding='utf-8'))
    assert catalog['version'] == 1
    assert [len(p['items']) for p in catalog['packages']] == [30, 50, 16, 5, 0]
    key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers = {'apikey': key, 'Authorization': 'Bearer ' + key}
    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    params = {'key': 'eq.data/career_assessments.json', 'select': 'value,updated_at'}
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok:
        raise RuntimeError(f'Read catalog: HTTP {response.status_code}')
    previous = response.json()
    if previous:
        backup = ROOT / '.runtime_data/publish-backups'
        backup.mkdir(parents=True, exist_ok=True)
        import hashlib
        name = hashlib.sha256(previous[0]['updated_at'].encode()).hexdigest()[:12]
        (backup / f'career-{name}.json').write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding='utf-8')
        response = requests.patch(url, headers={**headers, 'Prefer': 'return=representation'},
            params={'key': params['key'], 'updated_at': 'eq.' + previous[0]['updated_at']}, json={'value': catalog}, timeout=30)
        if not response.ok or not response.json():
            raise RuntimeError(f'Catalog update failed or concurrent change: HTTP {response.status_code}')
    else:
        response = requests.post(url, headers=headers, json={'key': 'data/career_assessments.json', 'value': catalog}, timeout=30)
        if not response.ok:
            raise RuntimeError(f'Catalog insert: HTTP {response.status_code}')
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if not response.ok or response.json()[0]['value'] != catalog:
        raise RuntimeError('Catalog readback mismatch')
    print('Verified Supabase catalog: 5 packages, 101 questions, 1 information-only package. No student answers stored.')


if __name__ == '__main__':
    main()
