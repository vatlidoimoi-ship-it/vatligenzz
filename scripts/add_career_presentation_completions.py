"""Add the requested 100 marked presentation events per smaller package, once."""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[1]
BATCH = 'career-three-packages-plus100-20261029'
PACKAGES = ('big-five', 'mbti', 'who-5')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    load_dotenv(ROOT.parent / '.env')
    secret = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    headers = {'apikey': secret, 'Authorization': 'Bearer ' + secret}
    query = {'key': 'eq.data/career_completions.json', 'select': 'value,updated_at'}
    response = requests.get(url, headers=headers, params=query, timeout=30)
    response.raise_for_status()
    rows = response.json()
    if len(rows) != 1 or not isinstance(rows[0]['value'], list):
        raise RuntimeError('Expected one completion catalog')
    row = rows[0]
    before = row['value']
    marked = [r for r in before if r.get('batch_id') == BATCH]
    if marked:
        if Counter(r['package_id'] for r in marked) != Counter({p: 100 for p in PACKAGES}):
            raise RuntimeError('Partial or changed batch; inspect before retrying')
        print('Batch already present; nothing added.')
        return
    now = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds')
    additions = [dict(id=f'{BATCH}-{package}-{i:03}', user_id=None,
                      package_id=package, completed_at=now, batch_id=BATCH,
                      provenance={'origin': 'synthetic', 'purpose': 'customer_presentation'})
                 for package in PACKAGES for i in range(1, 101)]
    intended = before + additions
    print('Before:', dict(Counter(r['package_id'] for r in before)))
    print('After:', dict(Counter(r['package_id'] for r in intended)))
    if not args.apply:
        return
    folder = ROOT / '.runtime_data/career-publish' / BATCH
    folder.mkdir(parents=True, exist_ok=True)
    backup = folder / 'before.json'
    if backup.exists():
        raise RuntimeError('Backup already exists; inspect remote state before retrying')
    backup.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
    (folder / 'intended.json').write_text(json.dumps(intended, ensure_ascii=False), encoding='utf-8')
    response = requests.patch(url, headers={**headers, 'Prefer': 'return=representation'},
                              params={'key': query['key'], 'updated_at': 'eq.' + row['updated_at']},
                              json={'value': intended}, timeout=60)
    response.raise_for_status()
    if len(response.json()) != 1:
        raise RuntimeError('Concurrent update; no automatic retry')
    check = requests.get(url, headers=headers, params=query, timeout=30)
    check.raise_for_status()
    if check.json()[0]['value'] != intended:
        raise RuntimeError('Readback mismatch; inspect before retrying')
    print('Published and verified: 300 marked simulated events, original records preserved.')


if __name__ == '__main__':
    main()
