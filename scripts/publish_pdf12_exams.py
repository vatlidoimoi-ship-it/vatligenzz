"""Validate locally with --prepare; merge into Supabase with --publish --env-file ../.env."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import requests
from build_pdf12_exams import BATCH, ROOT, save
from migrate_json_to_supabase import load_dotenv

BANK = ROOT/'data/pdf_exams_grade12.json'
AUDIT = ROOT/'docs/pdf-exams-grade12-validation.json'


class UploadChunks:
    """Bound each TLS write while retaining Content-Length (no chunked HTTP encoding)."""
    def __init__(self, payload): self.payload=payload
    def __len__(self): return len(self.payload)
    def __iter__(self):
        for start in range(0,len(self.payload),8192):
            yield self.payload[start:start+8192]


def merge(previous, exams):
    if not isinstance(previous,dict) or not isinstance(previous.get('exams'),list):
        raise ValueError('Unexpected existing bank shape; no replacement attempted.')
    ids={e['id'] for e in exams}
    if len(ids)!=20 or len(exams)!=20:
        raise ValueError('Expected exactly 20 unique new exams.')
    for e in previous['exams']:
        if e.get('id') in ids and e.get('batch_id')!=BATCH:
            raise ValueError('Exam ID collision with unrelated content.')
    return {**previous,'exams':[e for e in previous['exams'] if e.get('id') not in ids]+exams}


def prepare():
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),
                           '-p','test_*exam_bank.py','-v'],capture_output=True,text=True,encoding='utf-8',
                          env={**os.environ,'PYTHONIOENCODING':'utf-8'})
    logs=ROOT/'.runtime_data/pdf12/test-results.txt'
    logs.parent.mkdir(parents=True,exist_ok=True)
    logs.write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Exam validation failed. See .runtime_data/pdf12/test-results.txt')
    bank=json.loads(BANK.read_text(encoding='utf-8'))
    for e in bank['exams']: e['review_status']='passed'
    save(BANK,bank)
    seed=ROOT/'data/li.json'
    save(seed,merge(json.loads(seed.read_text(encoding='utf-8-sig')),bank['exams']))
    save(AUDIT,dict(batch_id=BATCH,bank_sha256=hashlib.sha256(BANK.read_bytes()).hexdigest(),
        source_sha256=bank['exams'][0]['source_sha256'],exam_count=20,question_count=400,
        time_limit_minutes=30,score_per_question=.5,numerical_checks=360,
        checks=['unique stems and IDs','four distinct options; five A/B/C/D answers per exam',
                'PDF checksum and exact page references','360 numerical formula checks',
                'hand-calculated answer anchors','real template rendering for every exam',
                'real submission handler: 20/10/0 correct produces 10/5/0 points',
                'merge preservation, collision rejection and idempotence','grade-11 regression checks'],
        review_scope='AI-authored and reviewed; automated validation, not human subject-matter certification'))
    print('Prepared verified 20 grade-12 exams; local seed preserves existing exams. No remote writes.')


def curl_patch(url, headers, params, payload):
    """Alternate Windows TLS transport. Credentials travel through stdin, never argv/files."""
    work=ROOT/'.runtime_data/pdf12'
    work.mkdir(parents=True,exist_ok=True)
    body=work/'publish-payload.json'; response=work/'publish-response.json'
    body.write_bytes(payload)
    target=requests.Request('PATCH',url,params=params).prepare().url
    def quote(s): return '"'+s.replace('\\','\\\\').replace('"','\\"')+'"'
    config='url = '+quote(target)+'\n'
    config+=''.join('header = '+quote(k+': '+v)+'\n' for k,v in headers.items())
    result=subprocess.run(['curl.exe' if os.name=='nt' else 'curl','--config','-',
        '--silent','--show-error','--max-time','55','--request','PATCH',
        '--data-binary','@'+str(body),'--output',str(response),'--write-out','%{http_code}'],
        input=config,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError(f'curl transport failed (exit {result.returncode}); read remote before retrying.')
    if result.stdout.strip()!='200':
        raise RuntimeError('Supabase PATCH HTTP '+result.stdout.strip())
    rows=json.loads(response.read_text(encoding='utf-8'))
    if not isinstance(rows,list) or len(rows)!=1:
        raise RuntimeError('Concurrent edit: timestamp guard matched no row.')


def publish(env_file, transport='requests'):
    bank=json.loads(BANK.read_text(encoding='utf-8'))
    audit=json.loads(AUDIT.read_text(encoding='utf-8'))
    if hashlib.sha256(BANK.read_bytes()).hexdigest()!=audit['bank_sha256']:
        raise RuntimeError('Bank changed after validation. Run --prepare again.')
    exams=bank['exams']
    if not all(e['review_status']=='passed' and e['grade']=='12' and e['time_limit']==30
               and len(e['questions'])==20 and e['batch_id']==BATCH for e in exams):
        raise RuntimeError('Unverified or invalid grade-12 batch.')
    load_dotenv(env_file)
    load_dotenv(ROOT/'.env')
    secret=os.environ['SUPABASE_SERVICE_ROLE_KEY']
    headers={'apikey':secret,'Authorization':'Bearer '+secret}
    url=os.environ['SUPABASE_URL'].rstrip('/')+'/rest/v1/'+os.getenv('SUPABASE_JSON_TABLE','app_json_store')
    query={'key':'eq.data/li.json','select':'value,updated_at'}
    r=requests.get(url,headers=headers,params=query,timeout=30)
    if not r.ok: raise RuntimeError(f'Supabase bank read: HTTP {r.status_code}')
    rows=r.json()
    if len(rows)!=1 or not rows[0].get('updated_at'):
        raise RuntimeError('Expected one existing bank with concurrency timestamp; no changes made.')
    row=rows[0]; previous=row['value']; stamp=row['updated_at']
    backup_name='li-before-pdf12-'+hashlib.sha256(stamp.encode()).hexdigest()[:16]+'.json'
    backup=ROOT/'.runtime_data/publish-backups'/backup_name
    if not backup.exists(): save(backup,row)
    merged=merge(previous,exams)
    if merged!=previous:
        payload=json.dumps({'value':merged},ensure_ascii=False,separators=(',',':')).encode('utf-8')
        print(f'Uploading {len(payload)} UTF-8 bytes with timestamp guard.',flush=True)
        write_headers={**headers,'Prefer':'return=representation','Content-Type':'application/json; charset=utf-8'}
        write_query={'key':query['key'],'updated_at':'eq.'+stamp}
        if transport=='curl':
            curl_patch(url,write_headers,write_query,payload)
        else:
            r=requests.patch(url,headers=write_headers,params=write_query,data=UploadChunks(payload),timeout=60)
            if not r.ok or len(r.json())!=1:
                raise RuntimeError(f'Concurrent edit or write failure (HTTP {r.status_code}); no automatic overwrite retry.')
    r=requests.get(url,headers=headers,params=query,timeout=30)
    if not r.ok or len(r.json())!=1 or r.json()[0]['value']!=merged:
        raise RuntimeError('Supabase readback differs from merged bank; investigate before retrying.')
    ids={e['id'] for e in exams}
    untouched_before=[e for e in previous['exams'] if e.get('id') not in ids]
    untouched_after=[e for e in merged['exams'] if e.get('id') not in ids]
    if untouched_before!=untouched_after: raise RuntimeError('Unrelated exam preservation check failed.')
    report=dict(batch_id=BATCH,remote_key='data/li.json',readback_verified=True,
        grade_counts=dict(Counter(e.get('grade','unspecified') for e in merged['exams'])),
        preserved_existing_exams=len(untouched_before),added_batch_exams=20,
        bank_sha256=audit['bank_sha256'],backup_file=str(backup.relative_to(ROOT)))
    save(ROOT/'docs/pdf-exams-grade12-publish.json',report)
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true')
    mode.add_argument('--publish',action='store_true')
    parser.add_argument('--env-file',type=Path,default=ROOT.parent/'.env')
    parser.add_argument('--transport',choices=['requests','curl'],default='requests')
    args=parser.parse_args()
    if args.prepare: prepare()
    else: publish(args.env_file,args.transport)
