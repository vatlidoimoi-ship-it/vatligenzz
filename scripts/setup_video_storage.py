"""Create the private Supabase bucket without changing existing access policy."""
import os
from pathlib import Path
import sys
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from migrate_json_to_supabase import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / '.env')
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
base = os.environ['SUPABASE_URL'].rstrip('/')
key = os.environ['SUPABASE_SERVICE_ROLE_KEY']
headers = {'apikey': key, 'Authorization': 'Bearer ' + key}
bucket = os.getenv('VIDEO_STORAGE_BUCKET', 'teacher-videos')
response = requests.get(base + '/storage/v1/bucket/' + bucket, headers=headers, timeout=30)
if response.ok:
    if response.json().get('public'):
        raise SystemExit('Existing video bucket is public; refusing to use it.')
    print('Private video bucket already exists.')
elif response.status_code in {400, 404}:
    response = requests.post(base + '/storage/v1/bucket', headers=headers, timeout=30,
        json={'id': bucket, 'name': bucket, 'public': False,
              'file_size_limit': 52428800, 'allowed_mime_types': ['video/mp4']})
    if not response.ok:
        raise SystemExit(f'Bucket creation failed: HTTP {response.status_code}')
    print('Created private teacher-videos bucket (50 MiB per video).')
else:
    raise SystemExit(f'Bucket check failed: HTTP {response.status_code}')
