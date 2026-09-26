import argparse
import os
import sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).with_name('.env'))

SITE_URL = 'https://rebjorn-wiki.com'
LISTING_URL = f'{SITE_URL}/dqmj2/monsters?lang=en'
DEFAULT_BUCKET = 'monster-thumbnails'
LOCAL_DIR = Path(__file__).with_name('monster-thumbnails')
LOCAL_DIR.mkdir(exist_ok=True)

url = os.getenv('VITE_SUPABASE_URL')
service_key = (
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    or os.getenv('SUPABASE_SERVICE_KEY')
    or os.getenv('VITE_SUPABASE_ANON_KEY')
    or os.getenv('VITE_SUPABASE_PUBLISHABLE_KEY')
)

if not url or not service_key:
    raise RuntimeError(
        'Missing Supabase credentials in backend/supabase/.env. '
        'Add VITE_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (recommended) or another valid key.'
    )

supabase = create_client(url, service_key)


def list_monster_slugs() -> list[str]:
    """Return ordered monster slugs from the Rebjorn list page."""
    html = fetch_text(LISTING_URL)
    soup = BeautifulSoup(html, 'html.parser')

    slugs = []
    seen = set()
    for row in soup.select('tr.clickable-row[data-href]'):
        href = row.get('data-href', '')
        if not href.startswith('/dqmj2/monsters/'):
            continue
        slug = href.rstrip('/').split('/')[-1]
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)

    return slugs


def slug_to_monster_id(slug: str) -> int | None:
    """Map the monster slug to the monster_id used in the Supabase dqmj2_monsters table."""
    slugs = list_monster_slugs()
    for idx, candidate in enumerate(slugs, start=1):
        if candidate == slug:
            return idx
    return None


def fetch_text(url: str) -> str:
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8', 'replace')


def fetch_image_bytes(image_url: str) -> bytes:
    req = Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urlopen(req, timeout=30) as response:
        return response.read()


def find_full_icon_url(monster_page_url: str) -> str:
    html = fetch_text(monster_page_url)
    soup = BeautifulSoup(html, 'html.parser')

    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src') or ''
        if 'full_icons' in src.lower():
            return urljoin(SITE_URL, src)

    for img in soup.select('img'):
        src = img.get('src') or img.get('data-src') or ''
        if 'monster' in src.lower() and ('png' in src.lower() or 'jpg' in src.lower() or 'webp' in src.lower()):
            return urljoin(SITE_URL, src)

    raise RuntimeError(f'No monster image found for {monster_page_url}')


def ensure_bucket(bucket_name: str):
    storage = supabase.storage
    try:
        buckets = storage.list_buckets()
        existing = [bucket.name for bucket in buckets if getattr(bucket, 'name', None)]
        if bucket_name not in existing:
            storage.create_bucket(bucket_name, {'public': True})
            print(f'Created bucket: {bucket_name}')
    except Exception as exc:
        print(f'Bucket check/create warning: {exc}')


def upload_file(bucket_name: str, file_path: Path, supabase_path: str):
    with file_path.open('rb') as f:
        data = f.read()

    storage = supabase.storage.from_(bucket_name)
    result = storage.upload(supabase_path, data, {'content-type': 'image/png', 'upsert': 'true'})
    print(f'Uploaded {file_path.name} -> {supabase_path}: {result}')


def parse_args():
    parser = argparse.ArgumentParser(description='Bulk-download monster thumbnails from Rebjorn and upload them to Supabase Storage.')
    parser.add_argument('--bucket', default=DEFAULT_BUCKET, help='Supabase Storage bucket name to upload into.')
    parser.add_argument('--dry-run', action='store_true', help='Fetch and save files locally without uploading to Supabase.')
    parser.add_argument('--limit', type=int, default=0, help='Optional cap on the number of monsters to process (0 = all).')
    parser.add_argument('--start', type=int, default=1, help='Monster ID to start at (1-based).')
    return parser.parse_args()


def main():
    args = parse_args()
    slug_candidates = list_monster_slugs()

    if args.limit > 0:
        slug_candidates = slug_candidates[:args.limit]

    if not args.dry_run:
        ensure_bucket(args.bucket)

    uploaded = 0
    for slug in slug_candidates:
        monster_id = slug_to_monster_id(slug)
        if monster_id is None:
            print(f'Skipping {slug}: no monster id match')
            continue

        if monster_id < args.start:
            continue

        monster_page_url = f'{SITE_URL}/dqmj2/monsters/{slug}'
        image_url = find_full_icon_url(monster_page_url)
        file_name = f'monster-{monster_id:03d}.png'
        file_path = LOCAL_DIR / file_name

        try:
            blob = fetch_image_bytes(image_url)
            file_path.write_bytes(blob)
            print(f'Fetched {slug} -> {file_path.name}')

            if not args.dry_run:
                upload_file(args.bucket, file_path, file_name)
            uploaded += 1
        except Exception as exc:
            print(f'Failed {slug} ({monster_id}): {exc}')

    print(f'Finished. Processed {uploaded} thumbnails. Dry run: {args.dry_run}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped by user.')
        sys.exit(1)
