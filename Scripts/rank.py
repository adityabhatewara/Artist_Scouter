#!/usr/bin/env python3
"""
=============================================================================
  RANK.PY — Script 2 of WF Auto-Scouter
  
  Takes the raw CSV from scout.py, adds Last.fm popularity data,
  filters out unsuitable artists, scores and ranks the rest.
  
  Usage:
      python rank.py --input raw_finland_20260410.csv
      python rank.py --input raw_finland_20260410.csv --lastfm-key YOUR_KEY
      python rank.py --input raw_finland_20260410.csv --skip-lastfm
      python rank.py --input raw_finland_20260410.csv --min-listeners 1000 --max-listeners 100000
  
  Get a free Last.fm API key: https://www.last.fm/api/account/create
  
  Output: ranked_<country>_<timestamp>.csv
=============================================================================
"""

import csv
import os
import time
import argparse
import json
import requests
from datetime import datetime
from collections import defaultdict

from config import (
    LASTFM_API_KEY, ALL_TARGET_COUNTRIES, WF_RELEVANT_GENRE_KEYWORDS,
    LASTFM_LISTENERS_TOO_BIG, LASTFM_LISTENERS_BIG,
    LASTFM_LISTENERS_MEDIUM_HIGH, LASTFM_LISTENERS_MEDIUM_LOW,
    LASTFM_LISTENERS_SMALL, LASTFM_LISTENERS_TOO_SMALL,
    MIN_TRACKS_FOR_SET, MAX_YEARS_SINCE_RELEASE,
)
from output import export_ranked_csv, print_rank_summary


# ========================== LOAD RAW CSV ==========================

def load_raw_csv(filename):
    """Load the raw CSV from scout.py into a list of dicts."""
    artists = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['estimated_tracks'] = int(row.get('Estimated Tracks', 0) or 0)
            row['album_only_count'] = int(row.get('Albums', 0) or 0)
            row['ep_count'] = int(row.get('EPs', 0) or 0)
            row['single_count'] = int(row.get('Singles', 0) or 0)
            row['total_releases'] = int(row.get('Total Releases', 0) or 0)
            row['mb_size_score'] = int(row.get('MB Size Score', 0) or 0)
            row['max_tag_votes'] = int(row.get('Max Tag Votes', 0) or 0)
            row['rating_count'] = int(row.get('Rating Count', 0) or 0)
            row['release_country_count'] = int(row.get('Release Countries', 0) or 0)

            # Parse english ratio
            er = row.get('English Ratio', '0%').replace('%', '')
            row['english_ratio'] = int(er) / 100 if er.isdigit() else 0

            # Normalize fields
            row['name'] = row.get('Artist Name', '')
            row['mb_id'] = row.get('MusicBrainz ID', '')
            row['country'] = row.get('Country', '')
            row['area'] = row.get('Area', '')
            row['type'] = row.get('Type', '')
            row['tags'] = [t.strip() for t in row.get('Genre Tags', '').split(',') if t.strip()]
            row['primary_language'] = row.get('Primary Language', 'unknown')
            row['has_english'] = row.get('Has English', 'No') == 'Yes'
            row['latest_release_date'] = row.get('Latest Release Date', '')
            row['begin_year'] = row.get('Active Since', '')
            row['ended'] = row.get('Disbanded', 'No') == 'Yes'
            row['enough_tracks'] = row['estimated_tracks'] >= MIN_TRACKS_FOR_SET

            artists.append(row)

    print(f"📂 Loaded {len(artists)} artists from {filename}")
    return artists


# ========================== FILTER ==========================

def filter_artists(artists):
    """Remove artists that are definitely not WF-viable."""
    print(f"\n🔍 FILTERING...")
    print("-" * 55)

    before = len(artists)
    filtered = []

    disbanded = 0
    no_english = 0
    too_few_tracks = 0
    no_recent = 0

    for a in artists:
        # Remove disbanded
        if a.get('ended'):
            disbanded += 1
            continue

        # Remove no English (keep unknowns)
        if a.get('primary_language') not in ('eng', 'unknown', '') and not a.get('has_english'):
            no_english += 1
            continue

        # Remove too few tracks (keep if we don't have data)
        if a.get('estimated_tracks', 0) > 0 and a['estimated_tracks'] < MIN_TRACKS_FOR_SET:
            too_few_tracks += 1
            continue

        # Remove no recent releases (keep if no data)
        rd = a.get('latest_release_date', '')
        if rd and len(rd) >= 4:
            try:
                diff = datetime.now().year - int(rd[:4])
                if diff > MAX_YEARS_SINCE_RELEASE:
                    no_recent += 1
                    continue
            except:
                pass

        filtered.append(a)

    print(f"   Removed: {disbanded} disbanded, {no_english} no English, {too_few_tracks} too few tracks, {no_recent} inactive")
    print(f"   Remaining: {len(filtered)}/{before}")
    return filtered


# ========================== LAST.FM POPULARITY ==========================

def fetch_lastfm_data(artist_name, api_key):
    """Fetch listener count and play count from Last.fm."""
    try:
        url = "http://ws.audioscrobbler.com/2.0/"
        params = {
            "method": "artist.getinfo",
            "artist": artist_name,
            "api_key": api_key,
            "format": "json",
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if 'artist' in data:
            artist = data['artist']
            stats = artist.get('stats', {})
            return {
                'lastfm_listeners': int(stats.get('listeners', 0)),
                'lastfm_playcount': int(stats.get('playcount', 0)),
                'lastfm_url': artist.get('url', ''),
                'lastfm_tags': [t['name'] for t in artist.get('tags', {}).get('tag', [])],
            }
    except:
        pass
    return None


def add_lastfm_popularity(artists, api_key):
    """Fetch Last.fm data for all artists."""
    print(f"\n📻 LAST.FM: Fetching popularity data ({len(artists)} artists)")
    print(f"   Rate: ~5 req/sec (much faster than MusicBrainz)")
    print("-" * 55)

    found = 0
    total = len(artists)

    for i, a in enumerate(artists):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"   [{i+1}/{total}] {found} found on Last.fm...")

        result = fetch_lastfm_data(a['name'], api_key)
        if result and result['lastfm_listeners'] > 0:
            a.update(result)
            found += 1
        else:
            a['lastfm_listeners'] = 0
            a['lastfm_playcount'] = 0
            a['lastfm_url'] = ''
            a['lastfm_tags'] = []

        time.sleep(0.2)  # Last.fm allows ~5 req/sec

    print(f"   ✅ {found}/{total} found on Last.fm")
    return artists


def classify_size(artists):
    """Classify artist size based on Last.fm listeners."""
    print(f"\n📏 SIZE CLASSIFICATION (Last.fm-based)")
    print("-" * 55)

    counts = defaultdict(int)

    for a in artists:
        listeners = a.get('lastfm_listeners', 0)

        if listeners >= LASTFM_LISTENERS_TOO_BIG:
            a['size_category'] = 'too_big'
        elif listeners >= LASTFM_LISTENERS_BIG:
            a['size_category'] = 'big'
        elif listeners >= LASTFM_LISTENERS_MEDIUM_LOW:
            a['size_category'] = 'wf_sweet_spot'
        elif listeners >= LASTFM_LISTENERS_SMALL:
            a['size_category'] = 'small'
        elif listeners > 0:
            a['size_category'] = 'too_small'
        else:
            # No Last.fm data — fall back to MB size score
            mb_ss = a.get('mb_size_score', 0)
            if mb_ss > 60:
                a['size_category'] = 'big'
            elif mb_ss > 20:
                a['size_category'] = 'wf_sweet_spot'
            else:
                a['size_category'] = 'small'

        counts[a['size_category']] += 1

    for cat in ['too_small', 'small', 'wf_sweet_spot', 'big', 'too_big']:
        label = f"★ {cat}" if cat == 'wf_sweet_spot' else f"  {cat}"
        print(f"   {label:25s} {counts.get(cat, 0):4d}")

    return artists


# ========================== SCORING ==========================

def score_artists(artists, target_country=None):
    """
    Final WF scoring (0-100).
    
    Popularity sweet spot:   25 pts   (Last.fm listeners in WF range)
    English language:        20 pts   (English releases)
    Track count:             15 pts   (enough for a set)
    Active & recent:         15 pts   (recent releases)
    Genre relevance:         15 pts   (WF-relevant genres)
    Country match:           10 pts   (from target country)
    """
    for a in artists:
        score = 0
        bd = {}

        # --- Popularity sweet spot (0-25) ---
        cat = a.get('size_category', 'small')
        if cat == 'wf_sweet_spot':
            s = 25
        elif cat == 'small':
            s = 15
        elif cat == 'big':
            s = 8
        elif cat == 'too_small':
            s = 5
        else:  # too_big
            s = 2
        score += s; bd['popularity'] = s

        # --- English (0-20) ---
        er = a.get('english_ratio', 0)
        has_eng = a.get('has_english', False)
        if er >= 0.7:
            s = 20
        elif er >= 0.3:
            s = 15
        elif has_eng:
            s = 10
        elif a.get('primary_language', '') in ('unknown', ''):
            s = 8
        else:
            s = 2
        score += s; bd['english'] = s

        # --- Track count (0-15) ---
        et = a.get('estimated_tracks', 0)
        if et >= 15:
            s = 15
        elif et >= 10:
            s = 12
        elif et >= 8:
            s = 10
        elif et >= 5:
            s = 5
        else:
            s = 1
        score += s; bd['tracks'] = s

        # --- Active & recent (0-15) ---
        rd = a.get('latest_release_date', '')
        if rd and len(rd) >= 4:
            try:
                diff = datetime.now().year - int(rd[:4])
                s = 15 if diff <= 1 else (12 if diff <= 2 else (8 if diff <= 3 else 4))
            except:
                s = 5
        else:
            s = 3
        score += s; bd['active'] = s

        # --- Genre relevance (0-15) ---
        all_tags = a.get('tags', []) + a.get('lastfm_tags', [])
        wf_tags = [t for t in all_tags if any(g in t.lower() for g in WF_RELEVANT_GENRE_KEYWORDS)]
        s = 15 if len(wf_tags) >= 4 else (12 if len(wf_tags) >= 2 else (8 if len(wf_tags) >= 1 else (3 if all_tags else 1)))
        score += s; bd['genre'] = s

        # --- Country match (0-10) ---
        if target_country:
            s = 10 if a.get('country') == target_country else (5 if a.get('country') in ALL_TARGET_COUNTRIES else 2)
        else:
            s = 8 if a.get('country') in ALL_TARGET_COUNTRIES else 3
        score += s; bd['country'] = s

        a['wf_score'] = score
        a['score_breakdown'] = bd

    # Sort by score
    artists.sort(key=lambda x: x.get('wf_score', 0), reverse=True)
    return artists


# ========================== MAIN ==========================

def main():
    parser = argparse.ArgumentParser(description="WF Rank — Filter, rank, and score scouted artists")
    parser.add_argument('--input', type=str, required=True, help='Raw CSV from scout.py')
    parser.add_argument('--lastfm-key', type=str, default=None, help='Last.fm API key')
    parser.add_argument('--skip-lastfm', action='store_true', help='Skip Last.fm (use MB data only)')
    parser.add_argument('--min-listeners', type=int, default=None, help='Override min listener threshold')
    parser.add_argument('--max-listeners', type=int, default=None, help='Override max listener threshold')
    parser.add_argument('--country', type=str, default=None, help='Target country for scoring')
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    # Determine Last.fm API key
    api_key = args.lastfm_key or LASTFM_API_KEY
    use_lastfm = bool(api_key) and not args.skip_lastfm

    if not args.output:
        ranked_name = os.path.basename(args.input).replace('raw_', 'ranked_')
        if ranked_name == os.path.basename(args.input):
            ranked_name = f"ranked_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'Results'), exist_ok=True)
        args.output = os.path.join(os.path.dirname(__file__), '..', 'Results', ranked_name)

    print("=" * 60)
    print("  🏆 WF RANK — Filter & Score Artists")
    print("  Saarang 2027 | Script 2 of 2")
    print("=" * 60)
    print(f"  Input: {args.input}")
    print(f"  Last.fm: {'Yes' if use_lastfm else 'No (using MB data only)'}")
    if not use_lastfm and not args.skip_lastfm:
        print(f"  💡 Tip: Get a free Last.fm key for MUCH better popularity data:")
        print(f"     https://www.last.fm/api/account/create")
        print(f"     Then run: python rank.py --input {args.input} --lastfm-key YOUR_KEY")

    # Load raw data
    artists = load_raw_csv(args.input)

    # Filter
    artists = filter_artists(artists)

    # Last.fm popularity
    if use_lastfm:
        artists = add_lastfm_popularity(artists, api_key)
    
    # Classify size
    artists = classify_size(artists)

    # Score
    artists = score_artists(artists, target_country=args.country)

    # Output
    print_rank_summary(artists, country=args.country)
    export_ranked_csv(artists, args.output)

    print(f"\n✅ Done! Open {args.output} in Sheets/Excel.")
    print(f"   Top picks: Filter by Size = 'wf_sweet_spot' and sort by WF Score.")


if __name__ == "__main__":
    main()
