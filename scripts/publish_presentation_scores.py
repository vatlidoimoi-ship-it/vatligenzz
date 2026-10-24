"""Read-only by default. --apply updates only marked presentation assessments."""
import argparse
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from presentation_scores import rebalance, synthetic

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    load_dotenv(ROOT.parent / '.env')
    key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
    url = os.environ['SUPABASE_URL'].rstrip('/') + '/rest/v1/' + os.getenv('SUPABASE_JSON_TABLE', 'app_json_store')
    session = requests.Session()
    session.headers.update({'apikey': key, 'Authorization': 'Bearer ' + key})
    names = ['exam_results', 'submissions', 'progress', 'li']
    response = session.get(url, params={'key': 'in.(' + ','.join('data/' + n + '.json' for n in names) + ')', 'select': 'key,value,updated_at'}, timeout=40)
    response.raise_for_status()
    prior = {r['key'].split('/')[-1][:-5]: r for r in response.json()}
    values = {n: copy.deepcopy(prior[n]['value']) for n in names}
    summary = rebalance(values['exam_results'], values['submissions'], values['li'])
    for name in ['exam_results', 'submissions']:
        assert [r for r in values[name] if not synthetic(r)] == [r for r in prior[name]['value'] if not synthetic(r)]
        assert len(values[name]) == len(prior[name]['value'])
    for membership in values['progress']:
        completed = membership.setdefault('completed_lessons', [])
        for sub in values['submissions']:
            if synthetic(sub) and sub['user_id'] == membership['user_id'] and sub['course_id'] == membership['course_id'] and sub['score'] >= 70 and sub['exercise_id'] not in completed:
                completed.append(sub['exercise_id'])
    print(json.dumps(summary), flush=True)
    if not args.apply:
        return
    folder = ROOT / '.runtime_data/presentation-publish' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-scores')
    folder.mkdir(parents=True)
    (folder / 'before.json').write_text(json.dumps(prior, ensure_ascii=False), encoding='utf-8')
    (folder / 'intended.json').write_text(json.dumps(values, ensure_ascii=False), encoding='utf-8')
    for name in ['exam_results', 'submissions', 'progress']:
        payload = json.dumps({'value': values[name]}, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        response = session.patch(url, params={'key': 'eq.data/' + name + '.json', 'updated_at': 'eq.' + prior[name]['updated_at'], 'select': 'key'}, headers={'Prefer': 'return=representation', 'Content-Type': 'application/json; charset=utf-8'}, data=payload, timeout=90)
        response.raise_for_status()
        if len(response.json()) != 1:
            raise RuntimeError('Concurrent modification: ' + name + '; inspect backup before retrying')
        check = session.get(url, params={'key': 'eq.data/' + name + '.json', 'select': 'value'}, timeout=40)
        check.raise_for_status()
        assert check.json()[0]['value'] == values[name]
        print('Published and verified:', name, flush=True)


if __name__ == '__main__':
    main()
