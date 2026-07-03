"""
Phases 2-5: Deep enrichment via MusicBrainz.
- Phase 2: Release groups, tags, ratings
- Phase 3: Language detection
- Phase 4: Track count estimation
- Phase 5: Size classification (MusicBrainz-based, rough)
"""

import musicbrainzngs
import time
from datetime import datetime
from collections import defaultdict


# ========================== PHASE 2: ENRICHMENT ==========================

def enrich_single(mb_id):
    """Fetch detailed data for one artist."""
    try:
        result = musicbrainzngs.get_artist_by_id(
            mb_id, includes=["release-groups", "tags", "ratings"]
        )
        artist = result.get('artist', {})

        release_groups = []
        for rg in artist.get('release-group-list', []):
            release_groups.append({
                'title': rg.get('title', ''),
                'type': rg.get('type', ''),
                'primary_type': rg.get('primary-type', ''),
                'first_release_date': rg.get('first-release-date', ''),
                'id': rg.get('id', ''),
            })

        tags = {t['name']: int(t.get('count', 0)) for t in artist.get('tag-list', [])}
        rating = artist.get('rating', {})

        return {
            'release_groups': release_groups,
            'detailed_tags': tags,
            'rating_value': float(rating.get('value', 0) or 0),
            'rating_count': int(rating.get('votes-count', 0) or 0),
        }
    except:
        return None


def enrich_all(artists):
    """Phase 2: Enrich all artists with release groups, tags, ratings."""
    print(f"\n📊 PHASE 2: Enrichment ({len(artists)} artists, ~{len(artists)*1.1/60:.0f} min)")
    print("-" * 55)

    total = len(artists)
    for i, (mb_id, data) in enumerate(artists.items()):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"   [{i+1}/{total}] Enriching...")

        enriched = enrich_single(mb_id)
        if enriched:
            data['release_groups'] = enriched['release_groups']
            data['detailed_tags'] = enriched['detailed_tags']
            data['rating_value'] = enriched['rating_value']
            data['rating_count'] = enriched['rating_count']

            albums = [rg for rg in enriched['release_groups'] if rg.get('primary_type') in ('Album', 'EP')]
            singles = [rg for rg in enriched['release_groups'] if rg.get('primary_type') == 'Single']
            data['album_count'] = len(albums)
            data['single_count'] = len(singles)
            data['total_releases'] = len(enriched['release_groups'])
            data['max_tag_votes'] = max(enriched['detailed_tags'].values()) if enriched['detailed_tags'] else 0
            data['total_tag_votes'] = sum(enriched['detailed_tags'].values())

            dates = [rg['first_release_date'] for rg in enriched['release_groups'] if rg.get('first_release_date')]
            data['latest_release_date'] = max(dates) if dates else ''
        else:
            for key in ['release_groups', 'detailed_tags', 'rating_value', 'rating_count',
                        'album_count', 'single_count', 'total_releases', 'max_tag_votes',
                        'total_tag_votes', 'latest_release_date']:
                data[key] = [] if key == 'release_groups' else ({} if key == 'detailed_tags' else (0 if 'count' in key or 'votes' in key or 'rating' in key or 'releases' in key else ''))

        time.sleep(1.1)

    print(f"   ✅ Enrichment complete")
    return artists


# ========================== PHASE 3: LANGUAGE ==========================

def check_language(artists):
    """Phase 3: Check release languages for English preference."""
    print(f"\n🗣️  PHASE 3: Language check ({len(artists)} artists, ~{len(artists)*1.1/60:.0f} min)")
    print("-" * 55)

    total = len(artists)
    for i, (mb_id, data) in enumerate(artists.items()):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"   [{i+1}/{total}] Checking languages...")

        try:
            result = musicbrainzngs.search_releases(arid=mb_id, limit=25)
            releases = result.get('release-list', [])

            lang_counts = defaultdict(int)
            release_countries = set()

            for r in releases:
                lang = r.get('text-representation', {}).get('language', '')
                country = r.get('country', '')
                if lang:
                    lang_counts[lang] += 1
                if country:
                    release_countries.add(country)

            total_with_lang = sum(lang_counts.values())
            eng_count = lang_counts.get('eng', 0)

            data['languages'] = dict(lang_counts)
            data['release_countries'] = list(release_countries)
            data['release_country_count'] = len(release_countries)
            data['english_ratio'] = eng_count / total_with_lang if total_with_lang > 0 else 0
            data['has_english'] = eng_count > 0
            data['primary_language'] = max(lang_counts, key=lang_counts.get) if lang_counts else 'unknown'

            time.sleep(1.1)

        except:
            data['languages'] = {}
            data['english_ratio'] = 0
            data['has_english'] = False
            data['primary_language'] = 'unknown'
            data['release_countries'] = []
            data['release_country_count'] = 0

    eng = sum(1 for d in artists.values() if d.get('has_english'))
    print(f"   ✅ {eng}/{total} have English releases")
    return artists


# ========================== PHASE 4: TRACK COUNT ==========================

def check_track_counts(artists):
    """Phase 4: Estimate track count from release groups."""
    print(f"\n🎶 PHASE 4: Track count estimation")
    print("-" * 55)

    for mb_id, data in artists.items():
        ep_count = 0
        album_only = 0
        for rg in data.get('release_groups', []):
            if rg.get('primary_type') == 'EP':
                ep_count += 1
            elif rg.get('primary_type') == 'Album':
                album_only += 1

        singles = data.get('single_count', 0)
        estimated = (album_only * 10) + (ep_count * 5) + singles
        data['estimated_tracks'] = estimated
        data['ep_count'] = ep_count
        data['album_only_count'] = album_only
        data['enough_tracks'] = estimated >= 8

    enough = sum(1 for d in artists.values() if d.get('enough_tracks'))
    print(f"   ✅ {enough}/{len(artists)} have enough tracks (≥8)")
    return artists


# ========================== PHASE 5: SIZE (MB-based rough) ==========================

def check_size_mb(artists):
    """Phase 5: Rough size classification from MusicBrainz data only."""
    print(f"\n📏 PHASE 5: Rough size classification (MusicBrainz)")
    print("-" * 55)

    for mb_id, data in artists.items():
        max_tv = data.get('max_tag_votes', 0)
        rc = data.get('rating_count', 0)
        tr = data.get('total_releases', 0)
        rcc = data.get('release_country_count', 0)

        size_score = min(max_tv, 50) + min(rc * 5, 25) + min(tr * 2, 30) + min(rcc * 3, 30)
        data['mb_size_score'] = size_score

    print(f"   ✅ Size scores computed (will be refined by Last.fm in rank.py)")
    return artists
