"""
fetch_news.py — Pull NFL player news from ESPN's public news API.

ESPN exposes a free, key-less news endpoint that returns recent NFL story
headlines. Each story carries "categories", and athlete categories give us
the player name (+ ESPN athlete id), which lets us tie a headline back to a
specific player on a Huddlepuffers roster (matched downstream by name in
build_platform_v2.py, since rankings players are keyed by Sleeper id).

Outputs:
  - data/raw/espn_news.json   : raw API response (for reprocessing / debugging)
  - data/news.json            : cleaned article list consumed by build_platform_v2.py
  - data/csv/news.csv         : flattened article table (Excel-friendly)

Usage:
    python3 fetch_news.py
"""

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ---------- CONFIG ----------
LIMIT = 50   # how many recent stories to pull (ESPN caps this internally)
# ----------------------------

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CSV = ROOT / "data" / "csv"
NEWS_JSON = ROOT / "data" / "news.json"
for d in (RAW, CSV):
    d.mkdir(parents=True, exist_ok=True)

URL = (
    f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/news?limit={LIMIT}"
)


def get(url, retries=3):
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "HossAutomation-FantasyFootball/1.0"})
            with urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError) as e:
            if i == retries - 1:
                raise
            time.sleep(1.5 ** i)


def _athletes_from_categories(categories):
    """Pull (name, espn_id) pairs from a story's athlete categories."""
    out = []
    seen = set()
    for cat in categories or []:
        if cat.get("type") != "athlete":
            continue
        athlete = cat.get("athlete") or {}
        name = athlete.get("displayName") or athlete.get("description") or cat.get("description")
        if not name:
            continue
        espn_id = athlete.get("id") or cat.get("id")
        key = (name, espn_id)
        if key in seen:
            continue
        seen.add(key)
        out.append({"name": name, "espn_id": espn_id})
    return out


def main():
    print(f"Pulling ESPN NFL news (limit={LIMIT})")
    data = get(URL)
    articles_raw = data.get("articles", [])
    print(f"  {len(articles_raw)} stories returned")

    RAW.joinpath("espn_news.json").write_text(json.dumps(data, indent=2, default=str))

    articles = []
    for a in articles_raw:
        links = a.get("links") or {}
        web = (links.get("web") or {}).get("href")
        images = a.get("images") or []
        image = images[0].get("url") if images else None
        articles.append({
            "id": a.get("id") or web,
            "headline": a.get("headline"),
            "description": a.get("description"),
            "published": a.get("published"),
            "type": a.get("type"),
            "byline": a.get("byline"),
            "link": web,
            "image": image,
            "athletes": _athletes_from_categories(a.get("categories")),
        })

    payload = {
        "source": "ESPN",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles": articles,
    }
    NEWS_JSON.write_text(json.dumps(payload, indent=2, default=str))

    # Flattened CSV — one row per story, athletes joined for readability.
    with open(CSV / "news.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "headline", "published", "athletes", "link"])
        w.writeheader()
        for a in articles:
            w.writerow({
                "id": a["id"],
                "headline": a["headline"],
                "published": a["published"],
                "athletes": "; ".join(x["name"] for x in a["athletes"]),
                "link": a["link"],
            })

    tagged = sum(1 for a in articles if a["athletes"])
    print(f"  wrote {len(articles):,} stories ({tagged} with athlete tags) -> news.json + csv")


if __name__ == "__main__":
    main()
