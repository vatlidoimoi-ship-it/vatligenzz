import json
import os
import shutil
import threading
import copy
import time
from pathlib import Path

import requests
from flask import g, has_request_context, request
from .http_client import http_session


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DATA_DIR = BASE_DIR / "data"
STATIC_FORUM_UPLOAD_DIR = BASE_DIR / "static" / "uploads" / "forum"

DATA_BACKEND = os.getenv("DATA_BACKEND", "file").lower()
PERSISTENT_DIR = os.getenv("PERSISTENT_DIR")
SUPABASE_BACKEND = DATA_BACKEND == "supabase"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
    or os.getenv("SUPABASE_KEY")
)
SUPABASE_JSON_TABLE = os.getenv("SUPABASE_JSON_TABLE", "app_json_store")

RUNNING_ON_RENDER = any(
    os.getenv(name)
    for name in (
        "RENDER",
        "RENDER_EXTERNAL_URL",
        "RENDER_SERVICE_ID",
        "RENDER_INSTANCE_ID",
    )
)

if RUNNING_ON_RENDER and not PERSISTENT_DIR and not SUPABASE_BACKEND:
    raise RuntimeError(
        "Persistent storage is required on Render to prevent user data loss. "
        "Set PERSISTENT_DIR for a Render Persistent Disk or set DATA_BACKEND=supabase "
        "with SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
    )

if SUPABASE_BACKEND and (not SUPABASE_URL or not SUPABASE_KEY):
    raise RuntimeError(
        "DATA_BACKEND=supabase requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
        "(or SUPABASE_ANON_KEY/SUPABASE_KEY if your table policies allow server writes)."
    )

if SUPABASE_BACKEND and not PERSISTENT_DIR:
    _remote_cache_root = Path(
        os.getenv("REMOTE_DATA_CACHE_DIR") or BASE_DIR / ".runtime_data"
    ).resolve()
    DATA_DIR = Path(os.getenv("DATA_DIR", _remote_cache_root / "data")).resolve()
    STATE_DIR = Path(os.getenv("STATE_DIR", _remote_cache_root)).resolve()
    FORUM_UPLOAD_DIR = Path(
        os.getenv("FORUM_UPLOAD_DIR", _remote_cache_root / "uploads" / "forum")
    ).resolve()
elif PERSISTENT_DIR:
    _persistent_root = Path(PERSISTENT_DIR).resolve()
    DATA_DIR = Path(os.getenv("DATA_DIR", _persistent_root / "data")).resolve()
    STATE_DIR = Path(os.getenv("STATE_DIR", _persistent_root)).resolve()
    FORUM_UPLOAD_DIR = Path(
        os.getenv("FORUM_UPLOAD_DIR", _persistent_root / "uploads" / "forum")
    ).resolve()
else:
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data")).resolve()
    STATE_DIR = Path(os.getenv("STATE_DIR", BASE_DIR)).resolve()
    FORUM_UPLOAD_DIR = Path(
        os.getenv("FORUM_UPLOAD_DIR", BASE_DIR / "static" / "uploads" / "forum")
    ).resolve()

FORUM_UPLOAD_URL_PREFIX = "/uploads/forum"
_json_locks = {}
_json_locks_guard = threading.Lock()
_catalog_cache = {}
_catalog_cache_lock = threading.Lock()
# Only reference catalogs may be briefly shared across GET requests. User roles,
# balances, messages and results are always refreshed for each request.
_CATALOG_KEYS = {'data/documents.json', 'data/courses.json',
                 'data/li.json', 'data/career_assessments.json'}
_CATALOG_TTL = 30

def _request_reads():
    if not has_request_context():
        return None
    if not hasattr(g, '_supabase_reads'):
        g._supabase_reads = {}
    return g._supabase_reads


def _supabase_headers(prefer=None):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _supabase_table_url():
    return f"{SUPABASE_URL}/rest/v1/{SUPABASE_JSON_TABLE}"


def _supabase_key_for(local_path):
    local_path = Path(local_path).resolve()
    for base, prefix in (
        (DATA_DIR, "data"),
        (REPO_DATA_DIR, "data"),
        (STATE_DIR, ""),
        (BASE_DIR, ""),
    ):
        try:
            relative = local_path.relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
        return f"{prefix}/{relative}" if prefix else relative
    return None


def _supabase_get_json(remote_key):
    reads = _request_reads()
    if reads is not None and remote_key in reads:
        return copy.deepcopy(reads[remote_key])
    shared = has_request_context() and request.method in {'GET', 'HEAD'} and remote_key in _CATALOG_KEYS
    if shared:
        with _catalog_cache_lock:
            cached = _catalog_cache.get(remote_key)
        if cached is not None and time.monotonic() < cached[0]:
            reads[remote_key] = copy.deepcopy(cached[1])
            return copy.deepcopy(cached[1])
    response = http_session().get(
        _supabase_table_url(),
        headers=_supabase_headers(),
        params={"key": f"eq.{remote_key}", "select": "value"},
        timeout=20,
    )
    response.raise_for_status()
    rows = response.json()
    value = rows[0].get('value') if rows else None
    if reads is not None:
        reads[remote_key] = copy.deepcopy(value)
    if shared:
        with _catalog_cache_lock:
            _catalog_cache[remote_key] = (time.monotonic() + _CATALOG_TTL, copy.deepcopy(value))
    return value


def _supabase_upsert_json(remote_key, value):
    response = http_session().post(
        _supabase_table_url(),
        headers=_supabase_headers("resolution=merge-duplicates,return=minimal"),
        params={"on_conflict": "key"},
        json={"key": remote_key, "value": value},
        timeout=30,
    )
    response.raise_for_status()
    with _catalog_cache_lock:
        _catalog_cache.pop(remote_key, None)
    reads = _request_reads()
    if reads is not None:
        reads[remote_key] = copy.deepcopy(value)


def _write_local_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    with _lock_for(path):
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)


def ensure_file_from_remote(local_path, remote_path=None):
    if SUPABASE_BACKEND:
        local_path = Path(local_path)
        if local_path.suffix.lower() != ".json":
            return False
        remote_path = remote_path or _supabase_key_for(local_path)
        if not remote_path:
            return False
        value = _supabase_get_json(remote_path)
        if value is None:
            return False
        _write_local_json(local_path, value)
        return True

    return False


def sync_file_to_remote(local_path, remote_path=None):
    if SUPABASE_BACKEND:
        local_path = Path(local_path)
        if local_path.suffix.lower() != ".json" or not local_path.exists():
            return
        remote_path = remote_path or _supabase_key_for(local_path)
        if not remote_path:
            return
        with open(local_path, "r", encoding="utf-8-sig") as f:
            _supabase_upsert_json(remote_path, json.load(f))
        return

    return


def ensure_forum_upload_available(filename):
    safe_filename = Path(filename).name
    target = FORUM_UPLOAD_DIR / safe_filename
    if target.exists():
        return True
    if ensure_file_from_remote(target):
        return True

    seed = STATIC_FORUM_UPLOAD_DIR / safe_filename
    if seed.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(seed, target)
        sync_file_to_remote(target)
        return True
    return False


def _lock_for(path):
    key = str(Path(path).resolve())
    with _json_locks_guard:
        if key not in _json_locks:
            _json_locks[key] = threading.Lock()
        return _json_locks[key]


def read_json(path, default=None):
    if SUPABASE_BACKEND:
        remote_path = _supabase_key_for(path)
        if remote_path:
            value = _supabase_get_json(remote_path)
            if value is not None:
                return value

    try:
        with _lock_for(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return [] if default is None else default


def write_json(path, value):
    _write_local_json(path, value)
    sync_file_to_remote(path)


def _copy_seed(seed_path, target_path):
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seed_path, target_path)
    sync_file_to_remote(target_path)


def writable_data_file(filename, default=None):
    target = DATA_DIR / filename
    if SUPABASE_BACKEND and ensure_file_from_remote(target):
        return str(target)
    if SUPABASE_BACKEND and target.exists():
        sync_file_to_remote(target)
        return str(target)
    if not target.exists():
        seed = REPO_DATA_DIR / filename
        if seed.exists():
            _copy_seed(seed, target)
        else:
            write_json(target, [] if default is None else default)
    return str(target)


def readable_data_file(filename):
    target = DATA_DIR / filename
    if SUPABASE_BACKEND and ensure_file_from_remote(target):
        return str(target)
    if target.exists():
        return str(target)
    return str(REPO_DATA_DIR / filename)


def writable_state_file(filename, default=None):
    target = STATE_DIR / filename
    if SUPABASE_BACKEND and ensure_file_from_remote(target):
        return str(target)
    if SUPABASE_BACKEND and target.exists():
        sync_file_to_remote(target)
        return str(target)
    if not target.exists():
        seed = BASE_DIR / filename
        if seed.exists():
            _copy_seed(seed, target)
        else:
            write_json(target, [] if default is None else default)
    return str(target)


def forum_upload_path(filename):
    FORUM_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return FORUM_UPLOAD_DIR / filename


def forum_upload_url(filename):
    return f"{FORUM_UPLOAD_URL_PREFIX}/{filename}"


def attachment_storage_path(attachment):
    storage_path = attachment.get("storage_path")
    if storage_path:
        return Path(storage_path)

    path = attachment.get("path", "")
    if path.startswith(FORUM_UPLOAD_URL_PREFIX + "/"):
        return FORUM_UPLOAD_DIR / Path(path).name

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return BASE_DIR / candidate
