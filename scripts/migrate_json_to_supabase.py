import argparse
import json
import os
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def default_source_root():
    runtime_data = PROJECT_ROOT / "runtime-data"
    if runtime_data.exists():
        return runtime_data
    return PROJECT_ROOT


def supabase_headers(service_key):
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }


def upsert_json(supabase_url, service_key, table, key, value):
    response = requests.post(
        f"{supabase_url.rstrip('/')}/rest/v1/{table}",
        headers=supabase_headers(service_key),
        params={"on_conflict": "key"},
        json={"key": key, "value": value},
        timeout=30,
    )
    response.raise_for_status()


def iter_json_documents(source_root):
    data_dir = source_root / "data"
    if data_dir.exists():
        for path in sorted(data_dir.glob("*.json")):
            yield f"data/{path.name}", path

    for filename in ("questions.json", "scores.json"):
        path = source_root / filename
        if path.exists():
            yield filename, path


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Upload local JSON data files to the Supabase JSON store table."
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=default_source_root(),
        help="Folder containing data/*.json plus optional questions.json/scores.json.",
    )
    parser.add_argument(
        "--table",
        default=os.getenv("SUPABASE_JSON_TABLE", "app_json_store"),
        help="Supabase table name.",
    )
    args = parser.parse_args()

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not supabase_url or not service_key:
        raise SystemExit(
            "Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_KEY."
        )

    count = 0
    for key, path in iter_json_documents(args.source_root.resolve()):
        with path.open("r", encoding="utf-8") as f:
            value = json.load(f)
        upsert_json(supabase_url, service_key, args.table, key, value)
        count += 1
        print(f"Uploaded {key}")

    print(f"Done. Uploaded {count} JSON document(s) to {args.table}.")


if __name__ == "__main__":
    main()
