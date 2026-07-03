"""
Cache utilities — save/load intermediate results to avoid re-fetching.
"""

import json
import os


def save_cache(artists, output_file):
    """Save results to JSON cache."""
    cache_file = output_file.replace('.csv', '_cache.json')
    serializable = {}
    for k, v in artists.items():
        sv = {sk: sv for sk, sv in v.items() if sk not in ('release_groups', 'score_breakdown')}
        serializable[k] = sv
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"💾 Cache saved: {cache_file}")
    return cache_file


def load_cache(output_file):
    """Load cached results if available."""
    cache_file = output_file.replace('.csv', '_cache.json')
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"💾 Loaded {len(data)} artists from cache: {cache_file}")
        return data
    return None
