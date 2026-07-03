#!/usr/bin/env python3
"""
=============================================================================
  SCOUT.PY — Script 1 of WF Auto-Scouter
  
  Discovers ~1000 artists from MusicBrainz, enriches with language/track data.
  Outputs a RAW CSV — no filtering, no ranking yet.
  
  Usage:
      python scout.py --country Finland                     # Quick (discovery only)
      python scout.py --country Finland --deep              # Full enrichment
      python scout.py --country Finland --deep --limit 1000 # More artists
      python scout.py --country Finland --deep --use-cache  # Reuse previous data
  
  Output: raw_<country>_<timestamp>.csv + cache JSON
  Then run rank.py on the output to get the final ranked list.
=============================================================================
"""

import os

import musicbrainzngs
import argparse
from datetime import datetime

from config import MB_APP_NAME, MB_APP_VERSION, MB_CONTACT, COUNTRY_TIERS
from discovery import discover
from enrichment import enrich_all, check_language, check_track_counts, check_size_mb
from cache import save_cache, load_cache
from output import export_raw_csv, print_scout_summary


def main():
    parser = argparse.ArgumentParser(description="WF Scout — Discover artists from MusicBrainz")
    parser.add_argument('--country', type=str, default="Finland")
    parser.add_argument('--genre', type=str, default=None, help='Focus on one genre')
    parser.add_argument('--limit', type=int, default=1000, help='Target artist count (default: 1000)')
    parser.add_argument('--deep', action='store_true', help='Full enrichment (language, tracks, size)')
    parser.add_argument('--use-cache', action='store_true', help='Load from cache if available')
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    # Setup MusicBrainz
    musicbrainzngs.set_useragent(MB_APP_NAME, MB_APP_VERSION, MB_CONTACT)

    countries = COUNTRY_TIERS["Tier 1"] if args.country.lower() == "all" else [args.country]
    genres = [args.genre] if args.genre else None

    if not args.output:
        tag = countries[0].lower().replace(' ', '_') if len(countries) == 1 else "multi"
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'Results', 'raw'), exist_ok=True)
        args.output = os.path.join(os.path.dirname(__file__), '..', 'Results', 'raw', f"raw_{tag}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv")

    mode = "DEEP" if args.deep else "QUICK"

    print("=" * 60)
    print("  🎸 WF SCOUT — Artist Discovery")
    print("  Saarang 2027 | Script 1 of 2")
    print("=" * 60)
    print(f"  Mode: {mode} | Countries: {', '.join(countries)}")
    print(f"  Genre: {args.genre or 'All'} | Limit: {args.limit}")
    if args.deep:
        est = (args.limit * 3.3) / 60
        print(f"  ⏱️  Estimated time: ~{est:.0f} minutes")

    # Try cache first
    all_artists = None
    if args.use_cache:
        all_artists = load_cache(args.output)

    # Phase 1: Discovery
    if not all_artists:
        all_artists = {}
        for c in countries:
            all_artists.update(discover(c, genres=genres, total_limit=args.limit))

    if not all_artists:
        print("\n❌ No artists found.")
        return

    # Phases 2-5: Deep enrichment
    if args.deep and not args.use_cache:
        all_artists = enrich_all(all_artists)         # Phase 2: Release groups, tags
        all_artists = check_language(all_artists)      # Phase 3: Language
        all_artists = check_track_counts(all_artists)  # Phase 4: Track count
        all_artists = check_size_mb(all_artists)       # Phase 5: Rough size
        save_cache(all_artists, args.output)

    # Output
    target = countries[0] if len(countries) == 1 else None
    print_scout_summary(all_artists, country=target)
    export_raw_csv(all_artists, args.output)

    print(f"\n✅ Scouting complete!")
    print(f"   Next step: python rank.py --input {args.output}")


if __name__ == "__main__":
    main()
