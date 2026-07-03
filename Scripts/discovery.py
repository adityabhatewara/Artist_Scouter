"""
Phase 1: Artist Discovery via MusicBrainz.
Searches by country + genre with even distribution across all genres.
"""

import musicbrainzngs
import time
from collections import defaultdict
from config import COUNTRY_TO_MB, MB_TO_COUNTRY, GENRE_TAGS


def mb_search(country_code, tag=None, limit=100):
    """Search MusicBrainz for artists from a country, optionally by genre tag."""
    artists = []
    offset = 0
    while offset < limit:
        try:
            fetch = min(100, limit - offset)
            query = f'country:{country_code} AND tag:"{tag}"' if tag else f'country:{country_code}'
            result = musicbrainzngs.search_artists(query=query, limit=fetch, offset=offset)
            batch = result.get('artist-list', [])
            if not batch:
                break
            for a in batch:
                artists.append({
                    'name': a.get('name', ''),
                    'mb_id': a.get('id', ''),
                    'mb_score': int(a.get('ext:score', 0)),
                    'country_code': a.get('country', ''),
                    'country': MB_TO_COUNTRY.get(a.get('country', ''), a.get('country', '')),
                    'area': a.get('area', {}).get('name', ''),
                    'type': a.get('type', ''),
                    'tags': [t['name'] for t in a.get('tag-list', [])],
                    'tag_votes': {t['name']: int(t.get('count', 0)) for t in a.get('tag-list', [])},
                    'begin_year': (a.get('life-span', {}).get('begin', '') or '')[:4],
                    'ended': a.get('life-span', {}).get('ended', 'false') == 'true',
                    'disambiguation': a.get('disambiguation', ''),
                })
            offset += len(batch)
            time.sleep(1.1)
            if len(batch) < fetch:
                break
        except Exception as e:
            print(f"     ⚠️  MB error: {e}")
            time.sleep(2)
            break
    return artists


def discover(country_name, genres=None, total_limit=1000, per_genre_limit=None):
    """
    Discover artists from a country with EVEN genre distribution.
    
    Instead of a global pool that gets eaten by the first few genres,
    allocates a fixed quota per genre so all genres get fair representation.
    """
    code = COUNTRY_TO_MB.get(country_name)
    if not code:
        print(f"  ❌ Unknown country: {country_name}")
        return {}

    search_genres = genres if genres else GENRE_TAGS
    
    # Calculate per-genre limit for even distribution
    # Reserve 100 for the broad search, split the rest evenly
    broad_limit = min(100, total_limit // 5)
    remaining = total_limit - broad_limit
    if not per_genre_limit:
        per_genre_limit = max(10, remaining // len(search_genres))

    all_artists = {}

    print(f"\n🌍 DISCOVERY: {country_name} ({code})")
    print(f"   Total limit: {total_limit} | Per genre: {per_genre_limit} | Genres: {len(search_genres)}")
    print("-" * 55)

    # Broad search first (catches popular artists regardless of genre tags)
    print(f"   [broad] No genre filter (limit: {broad_limit})...")
    for a in mb_search(code, tag=None, limit=broad_limit):
        if a['mb_id'] not in all_artists and not a['ended']:
            all_artists[a['mb_id']] = a
    print(f"     → {len(all_artists)} unique")

    # Genre-specific searches with even distribution
    genre_counts = {}
    for i, genre in enumerate(search_genres):
        results = mb_search(code, tag=genre, limit=per_genre_limit)
        new = 0
        for a in results:
            if a['mb_id'] not in all_artists and not a['ended']:
                all_artists[a['mb_id']] = a
                new += 1
        genre_counts[genre] = new
        if new > 0:
            print(f"   [{i+1}/{len(search_genres)}] '{genre}' +{new} (total: {len(all_artists)})")

    # Summary of genre distribution
    print(f"\n   📊 Genre distribution:")
    for genre, count in sorted(genre_counts.items(), key=lambda x: -x[1])[:10]:
        if count > 0:
            print(f"      {genre:25s} +{count}")

    print(f"\n   ✅ {len(all_artists)} active artists discovered from {country_name}")
    return all_artists
