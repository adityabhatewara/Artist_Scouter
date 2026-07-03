"""
Output utilities — CSV export and terminal summary.
Used by both scout.py (raw output) and rank.py (final output).
"""

import csv
from collections import defaultdict


def export_raw_csv(artists, filename):
    """Export raw scouted data (from scout.py) before ranking."""
    sorted_a = sorted(artists.values(), key=lambda x: x.get('name', ''))

    fields = [
        'Artist Name', 'MusicBrainz ID', 'Country', 'Area', 'Type',
        'Genre Tags', 'Primary Language', 'English Ratio', 'Has English',
        'Estimated Tracks', 'Albums', 'EPs', 'Singles', 'Total Releases',
        'Latest Release Date', 'Active Since', 'Disbanded',
        'MB Size Score', 'Max Tag Votes', 'Rating Count', 'Release Countries',
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for a in sorted_a:
            w.writerow({
                'Artist Name': a.get('name', ''),
                'MusicBrainz ID': a.get('mb_id', ''),
                'Country': a.get('country', ''),
                'Area': a.get('area', ''),
                'Type': a.get('type', ''),
                'Genre Tags': ', '.join(a.get('tags', [])[:10]),
                'Primary Language': a.get('primary_language', ''),
                'English Ratio': f"{a.get('english_ratio', 0):.0%}",
                'Has English': 'Yes' if a.get('has_english') else 'No',
                'Estimated Tracks': a.get('estimated_tracks', 0),
                'Albums': a.get('album_only_count', 0),
                'EPs': a.get('ep_count', 0),
                'Singles': a.get('single_count', 0),
                'Total Releases': a.get('total_releases', 0),
                'Latest Release Date': a.get('latest_release_date', ''),
                'Active Since': a.get('begin_year', ''),
                'Disbanded': 'Yes' if a.get('ended') else 'No',
                'MB Size Score': a.get('mb_size_score', 0),
                'Max Tag Votes': a.get('max_tag_votes', 0),
                'Rating Count': a.get('rating_count', 0),
                'Release Countries': a.get('release_country_count', 0),
            })
    print(f"📁 Raw data exported: {filename} ({len(sorted_a)} artists)")


def export_ranked_csv(artists, filename):
    """Export final ranked data (from rank.py)."""
    sorted_a = sorted(artists, key=lambda x: x.get('wf_score', 0), reverse=True)

    fields = [
        'Rank', 'Artist Name', 'WF Score', 'Country', 'Type',
        'Genre Tags', 'Primary Language', 'English Ratio',
        'Last.fm Listeners', 'Last.fm Plays', 'Size Category',
        'Estimated Tracks', 'Albums', 'EPs', 'Singles',
        'Latest Release Date', 'Active Since',
        'Score: Popularity', 'Score: English', 'Score: Tracks',
        'Score: Active', 'Score: Genre', 'Score: Country',
        'MusicBrainz ID', 'Last.fm URL', 'Status',
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rank, a in enumerate(sorted_a, 1):
            bd = a.get('score_breakdown', {})
            w.writerow({
                'Rank': rank,
                'Artist Name': a.get('name', ''),
                'WF Score': a.get('wf_score', 0),
                'Country': a.get('country', ''),
                'Type': a.get('type', ''),
                'Genre Tags': ', '.join(a.get('tags', [])[:8]),
                'Primary Language': a.get('primary_language', ''),
                'English Ratio': f"{a.get('english_ratio', 0):.0%}",
                'Last.fm Listeners': a.get('lastfm_listeners', 0),
                'Last.fm Plays': a.get('lastfm_playcount', 0),
                'Size Category': a.get('size_category', ''),
                'Estimated Tracks': a.get('estimated_tracks', 0),
                'Albums': a.get('album_only_count', 0),
                'EPs': a.get('ep_count', 0),
                'Singles': a.get('single_count', 0),
                'Latest Release Date': a.get('latest_release_date', ''),
                'Active Since': a.get('begin_year', ''),
                'Score: Popularity': bd.get('popularity', ''),
                'Score: English': bd.get('english', ''),
                'Score: Tracks': bd.get('tracks', ''),
                'Score: Active': bd.get('active', ''),
                'Score: Genre': bd.get('genre', ''),
                'Score: Country': bd.get('country', ''),
                'MusicBrainz ID': a.get('mb_id', ''),
                'Last.fm URL': a.get('lastfm_url', ''),
                'Status': '',
            })
    print(f"📁 Final ranked list: {filename} ({len(sorted_a)} artists)")


def print_scout_summary(artists, country=None):
    """Print summary after scouting (scout.py)."""
    total = len(artists)
    vals = list(artists.values())
    eng = sum(1 for a in vals if a.get('has_english'))
    enough = sum(1 for a in vals if a.get('enough_tracks'))

    print("\n" + "=" * 60)
    print(f"  🎸 SCOUT SUMMARY — {country or 'Multiple countries'}")
    print(f"  Total: {total} | English: {eng} | Enough tracks: {enough}")
    print("=" * 60)

    # Genre distribution
    tag_dist = defaultdict(int)
    for a in vals:
        for t in a.get('tags', []):
            tag_dist[t] += 1
    print(f"\n  Top genres:")
    for tag, count in sorted(tag_dist.items(), key=lambda x: -x[1])[:10]:
        print(f"     {tag:25s} {count:4d}")
    print("=" * 60)


def print_rank_summary(artists, country=None):
    """Print summary after ranking (rank.py)."""
    print("\n" + "=" * 70)
    print(f"  🏆 FINAL RANKINGS — {country or 'Multiple countries'}")
    print(f"  Total ranked: {len(artists)}")
    print("=" * 70)

    # Size distribution
    size_dist = defaultdict(int)
    for a in artists:
        size_dist[a.get('size_category', 'unknown')] += 1
    print(f"\n  📏 Size distribution:")
    for cat in ['too_small', 'small', 'wf_sweet_spot', 'big', 'too_big']:
        c = size_dist.get(cat, 0)
        label = f"  ★ {cat}" if cat == 'wf_sweet_spot' else f"    {cat}"
        print(f"   {label:25s} {c:4d}")

    # Top 30
    print(f"\n  🏆 Top 30:")
    print(f"     {'#':>3}  {'Artist':28s} {'Score':>5}  {'Listeners':>10}  {'Size':>12} {'Eng':>4} {'Tags'}")
    print(f"     {'─'*3}  {'─'*28} {'─'*5}  {'─'*10}  {'─'*12} {'─'*4} {'─'*25}")
    for i, a in enumerate(artists[:30], 1):
        tags = ', '.join(a.get('tags', [])[:3])[:25]
        eng = '✅' if a.get('has_english') else '❌'
        listeners = a.get('lastfm_listeners', 0)
        size = a.get('size_category', '?')
        print(f"     {i:>3}  {a['name']:28s} {a.get('wf_score',0):>5}  {listeners:>10,}  {size:>12} {eng:>4} {tags}")

    print("=" * 70)
