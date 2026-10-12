"""Import the five supplied documents without replacing existing catalog entries.

Default: local data/documents.json. Use --configured-store in the deployment
environment to merge into its configured Supabase or persistent-file catalog.
The static/documents/datatm files must be deployed along with that catalog.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ('1. CHUYÊN ĐỀ 1 - DAO ĐỘNG - GV.docx', 'vat-li-11-dao-dong-gv.docx', '11',
     'Chuyên đề 1: Dao động – Bản giáo viên', 'Dao động',
     'Lý thuyết, phương pháp giải và bài tập về dao động điều hòa, vận tốc, gia tốc, năng lượng, dao động tắt dần và cộng hưởng. File Word, bản giáo viên.'),
    ('2. CHUYÊN ĐỀ 2 - SÓNG - GV.docx', 'vat-li-11-song-gv.docx', '11',
     'Chuyên đề 2: Sóng – Bản giáo viên', 'Sóng',
     'Ôn tập dao động; lý thuyết và bài tập về sóng cơ, sóng điện từ, giao thoa và sóng dừng. File Word, bản giáo viên.'),
    ('3. CHUYÊN ĐỀ 3 - ĐIỆN TRƯỜNG - GV.docx', 'vat-li-11-dien-truong-gv.docx', '11',
     'Chuyên đề 3: Điện trường – Bản giáo viên', 'Điện trường',
     'Ôn tập dao động và sóng; lực tương tác điện, điện trường, thế năng điện, điện thế và tụ điện. Có lý thuyết, bài tập và hướng dẫn giải. File Word, bản giáo viên.'),
    ('4. CHUYÊN ĐỀ 4 - DÒNG ĐIỆN. MẠCH ĐIỆN - GV.docx', 'vat-li-11-dong-dien-mach-dien-gv.docx', '11',
     'Chuyên đề 4: Dòng điện – Mạch điện – Bản giáo viên', 'Dòng điện và mạch điện',
     'Ôn tập điện trường; cường độ dòng điện, điện trở, định luật Ôm, nguồn điện, năng lượng và công suất điện. File Word, bản giáo viên.'),
    ('VẬT LÍ 12 CTM - GHÉP HỌC KÌ 2.pdf', 'vat-li-12-hoc-ki-2.pdf', '12',
     'Vật lí 12 chương trình mới – Học kì 2', 'Từ trường và vật lí hạt nhân',
     'Tài liệu của Vũ Đông Dương, năm học 2025–2026, gồm 190 trang. Từ trường, cảm ứng điện từ, dòng điện xoay chiều, vật lí hạt nhân và phóng xạ; lý thuyết, tự luận, trắc nghiệm 4 lựa chọn, đúng/sai và trả lời ngắn. File PDF.'),
]


def digest(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configured-store', action='store_true')
    args = parser.parse_args()
    target = ROOT / 'data/documents.json'
    if args.configured_store:
        sys.path.insert(0, str(ROOT))
        from migrate_json_to_supabase import load_dotenv
        load_dotenv(ROOT / '.env')
        from utils.storage import read_json, write_json, writable_data_file
        target = Path(writable_data_file('documents.json', []))
        catalog = read_json(target, [])
        save = lambda rows: write_json(target, rows)
    else:
        catalog = json.loads(target.read_text(encoding='utf-8-sig')) if target.exists() else []
        def save(rows):
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            temporary.replace(target)
    if not isinstance(catalog, list):
        raise ValueError('Document catalog must be a list; no changes made.')
    destination = ROOT / 'static/documents/datatm'
    # Check all sources before modifying anything. Deployed builds may contain
    # only the copies under static, so either location is accepted.
    sources = []
    for original, name, *_ in FILES:
        source = ROOT / 'datatm' / original
        if not source.exists():
            source = destination / name
        if not source.is_file():
            raise FileNotFoundError(source)
        sources.append(source)
    destination.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone(timedelta(hours=7))).isoformat()
    added = 0
    for index, ((original, name, grade, title, topic, description), source) in enumerate(zip(FILES, sources), 1):
        asset = destination / name
        checksum = digest(source)
        if asset.exists() and digest(asset) != checksum:
            raise ValueError(f'Destination differs from source: {asset}')
        if not asset.exists():
            shutil.copy2(source, asset)
        if digest(asset) != checksum:
            raise ValueError(f'Copy verification failed: {asset}')
        url = f'/static/documents/datatm/{name}'
        doc_id = f'doc_datatm_{index:02}'
        if any(doc.get('id') == doc_id or doc.get('url') == url for doc in catalog):
            continue
        catalog.append(dict(id=doc_id, title=title, grade=grade, doc_type='document',
                            link_type='file', url=url, description=description, topic=topic,
                            teacher_id=None, created_at=now, file_name=original,
                            file_size=asset.stat().st_size, file_format=asset.suffix[1:].upper(),
                            sha256=checksum))
        added += 1
    if added:
        save(catalog)
    print(f'Added {added} documents; catalog has {len(catalog)} entries. Files verified by SHA-256.')
    print('Store: ' + ('configured deployment store' if args.configured_store else 'local data/documents.json'))


if __name__ == '__main__':
    main()
