# WF Artist-Scouter v3
### WorldFest Artist Discovery Tool — Saarang 2027

Two-script pipeline: **scout** → **rank**

## Quick Start


# Step 1:
```bash
pip install -r requirements.txt

# Step 2: 
In the file config.py, update the countries and the genres.

# Step 3:
## Getting API Keys

**Last.fm (recommended, free):**
1. Go to https://www.last.fm/api/account/create
2. Fill in app name (anything) and description
3. You get an API key instantly
4. Paste it in `config.py` or pass with `--lastfm-key`

Application name	Professional Shows World Fest Artist Scouter
API key	6824d78ab26c9cc54c8f0f10af9ad5f7
Shared secret	920358ab57d544b3f9d7e5c70b51f46c
Registered to	adityabhatewara
# use your own apis 



# Step 4:
## Script 1: scout.py

Discovers artists from MusicBrainz with even genre distribution.

```bash
python scout.py --country Finland                      # Quick mode (~1 min)
python scout.py --country Finland --deep               # Full enrichment (~15 min)
python scout.py --country Finland --deep --limit 1000  # More artists
python scout.py --country Finland --genre metal        # Focus one genre
python scout.py --country all --deep                   # All Tier 1 countries
python scout.py --country Finland --deep --use-cache   # Reuse cached data
```

Output: `raw_<country>_<timestamp>.csv`

## Script 2: rank.py

Filters, adds Last.fm popularity, scores, and ranks.

```bash
python rank.py --input raw_finland.csv --lastfm-key 6824d78ab26c9cc54c8f0f10af9ad5f7   # With Last.fm
python rank.py --input raw_finland.csv --skip-lastfm           			       # Without Last.fm
python rank.py --input raw_finland.csv --country Finland        		       # Country-specific scoring
```

Output: `ranked_<country>_<timestamp>.csv`

## File Structure

```
wf_scouter/
├── scout.py          # Script 1: Discovery + Enrichment
├── rank.py           # Script 2: Filter + Last.fm + Score
├── config.py         # All constants and API keys
├── discovery.py      # MusicBrainz search with genre distribution
├── enrichment.py     # Language, track count, size checks
├── output.py         # CSV export and summaries
├── cache.py          # Cache save/load
├── requirements.txt
└── README.md
```

## Scoring (rank.py)

| Criterion | Max | What it measures |
|-----------|-----|------------------|
| Popularity | 25 | Last.fm listeners in WF range (5K-50K) |
| English | 20 | % of releases in English |
| Tracks | 15 | Enough songs for a 40-50 min set |
| Active | 15 | Released music recently |
| Genre | 15 | Has WF-relevant genre tags |
| Country | 10 | Matches target country |

## Size Categories (Last.fm)

| Category | Listeners | WF Fit |
|----------|-----------|--------|
| too_small | <500 | Probably too obscure |
| small | 500-5K | Viable but risky |
| **wf_sweet_spot** | **5K-50K** | **Perfect for WF** |
| big | 50K-500K | Might expect payment |
| too_big | >500K | Definitely too big |

Built for Saarang 2027 Professional Shows.
