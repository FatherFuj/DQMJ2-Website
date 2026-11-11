import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


SITE_URL = 'https://rebjorn-wiki.com'
LISTING_URL = f'{SITE_URL}/dqmj2/monsters?lang=en'
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parents[2]
    / 'vite'
    / 'src'
    / 'lib'
    / 'dqmj2-monster-details.json'
)
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; DQMJ2Bestiary/1.0)'}


def fetch_page(session: requests.Session, url: str) -> BeautifulSoup:
    for attempt in range(5):
        response = session.get(url, headers=HEADERS, timeout=30)
        if response.status_code not in (429, 500, 502, 503, 504):
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        if attempt == 4:
            response.raise_for_status()

        retry_after = response.headers.get('Retry-After')
        wait_seconds = min(int(retry_after), 60) if retry_after and retry_after.isdigit() else 2 ** attempt
        print(f'Source returned HTTP {response.status_code}; retrying in {wait_seconds}s.')
        time.sleep(wait_seconds)

    raise RuntimeError(f'Could not fetch source page: {url}')


def parse_monster_listing(soup: BeautifulSoup) -> list[dict]:
    monsters = []
    seen_ids = set()

    for row in soup.select('tr.clickable-row[data-href]'):
        href = row.get('data-href', '')
        if not href.startswith('/dqmj2/monsters/'):
            continue

        cells = row.select('td')
        try:
            monster_id = int(cells[0].get_text(strip=True))
        except (IndexError, ValueError) as error:
            raise ValueError(f'Could not read monster ID from listing row: {row}') from error

        name = row.get('data-monster-name', '').split(' ', 1)[0]
        name_cell = cells[2] if len(cells) > 2 else None
        if name_cell:
            name = name_cell.get_text(' ', strip=True)
        if not name:
            raise ValueError(f'Could not read monster name for ID {monster_id}')
        if monster_id in seen_ids:
            continue

        seen_ids.add(monster_id)
        monsters.append({
            'monster_id': monster_id,
            'name_en': name,
            'slug': href.rstrip('/').split('/')[-1],
            'source_url': urljoin(SITE_URL, href),
            'scoutable': row.get('data-scoutable') == '1',
            'normal_synthesis': row.get('data-normal-synthesis') == '1',
            'special_synthesis': row.get('data-special-synthesis') == '1',
        })

    if not monsters:
        raise ValueError('The source monster listing did not contain any monster rows')

    return monsters


def parse_scout_locations(soup: BeautifulSoup) -> list[str]:
    habitats = soup.select_one('section.habitats')
    if habitats is None:
        return []

    locations = []
    for card in habitats.select('.habitats-grid article'):
        name = card.select_one('.habitat-name')
        if name is None:
            continue

        location = name.get_text(' ', strip=True)
        conditions = [
            condition.get_text(' ', strip=True)
            for condition in card.select('.conditions .chip')
            if condition.get_text(strip=True)
        ]
        if not conditions:
            fallback = card.select_one('.muted')
            if fallback:
                conditions = [fallback.get_text(' ', strip=True)]

        locations.append(f'{location} ({", ".join(conditions)})' if conditions else location)

    return locations


def parse_detail(monster: dict, soup: BeautifulSoup) -> dict:
    title = soup.select_one('.monster-title h1')
    if title and title.get_text(' ', strip=True) != monster['name_en']:
        raise ValueError(
            f"Monster page mismatch for ID {monster['monster_id']}: "
            f"expected {monster['name_en']!r}, got {title.get_text(' ', strip=True)!r}"
        )

    detail = {
        'monster_id': monster['monster_id'],
        'name_en': monster['name_en'],
        'slug': monster['slug'],
        'source_url': f"{monster['source_url']}?lang=en",
        'scoutable': monster['scoutable'],
        'normal_synthesis': monster['normal_synthesis'],
        'special_synthesis': monster['special_synthesis'],
        'scout_locations': parse_scout_locations(soup),
    }

    # Keep these keys when the source adds the sections in the future.
    for field in ('innate_skill', 'traits', 'primary_synthesis'):
        values = parse_labeled_values(soup, field.replace('_', ' '))
        if values:
            detail[field] = values

    return detail


def parse_labeled_values(soup: BeautifulSoup, label: str) -> list[str]:
    expected = label.casefold().strip()

    for heading in soup.select('h2, h3, dt, th, .section-title'):
        if heading.get_text(' ', strip=True).casefold().rstrip(':') != expected:
            continue

        container = heading.find_parent(['section', 'tr', 'dl']) or heading.parent
        if container is None:
            continue
        value_nodes = container.select('li, td, dd, .value, .trait, .skill')
        values = [
            node.get_text(' ', strip=True)
            for node in value_nodes
            if node is not heading and node.get_text(strip=True)
        ]
        if values:
            return values

        sibling = heading.find_next_sibling()
        if sibling and sibling.get_text(strip=True):
            return [sibling.get_text(' ', strip=True)]

    return []


def save_output(output_path: Path, output: dict):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    os.replace(temporary_path, output_path)


def import_monster_details(
    output_path: Path,
    limit: int = 0,
    delay: float = 0.3,
    refresh: bool = False,
) -> dict:
    cached_records = {}
    if output_path.exists() and not refresh:
        cached_records = json.loads(output_path.read_text(encoding='utf-8')).get('records', {})

    with requests.Session() as session:
        monsters = parse_monster_listing(fetch_page(session, LISTING_URL))
        if limit:
            monsters = monsters[:limit]

        records = {}
        for index, monster in enumerate(monsters):
            cached = cached_records.get(str(monster['monster_id']))
            if cached and cached.get('slug') == monster['slug']:
                records[str(monster['monster_id'])] = cached
                continue

            url = f"{monster['source_url']}?lang=en"
            page = fetch_page(session, url)
            detail = parse_detail(monster, page)
            records[str(monster['monster_id'])] = detail
            save_output(output_path, {
                'source': LISTING_URL,
                'record_count': len(records),
                'records': records,
            })
            print(f"Parsed {monster['monster_id']}: {monster['name_en']}")
            if index + 1 < len(monsters) and delay > 0:
                time.sleep(delay)

    output = {
        'source': LISTING_URL,
        'record_count': len(records),
        'records': records,
    }
    save_output(output_path, output)
    return output


def main():
    parser = argparse.ArgumentParser(
        description='Parse DQMJ2 monster scout locations and synthesis flags from Rebjørn Wiki.'
    )
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--limit', type=int, default=0, help='Optional cap for testing.')
    parser.add_argument('--delay', type=float, default=0.3, help='Seconds between detail-page requests.')
    parser.add_argument('--refresh', action='store_true', help='Fetch records again instead of reusing saved entries.')
    args = parser.parse_args()

    if args.limit < 0:
        parser.error('--limit must be zero or a positive integer')
    if args.delay < 0:
        parser.error('--delay must be zero or a positive number')

    result = import_monster_details(args.output, args.limit, args.delay, args.refresh)
    print(f"Saved {result['record_count']} monster records to {args.output}")


if __name__ == '__main__':
    main()
