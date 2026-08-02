#!/usr/bin/env python3
"""
smoke_test.py — Post-deploy verification of the LIVE site (v3/B2).

Runs after the Netlify deploy step. Fetches the production URL and asserts:
  1. the page parses and contains the embedded data object
  2. meta.league_id matches config (we deployed the right league)
  3. meta.generated_at is fresh (this deploy, not a stale CDN copy)
  4. every team carries both tone sets (the toggle is alive)

The deploy has already happened when this runs — a failure here trips the
workflow's failure-alert issue so a bad publish is loud, not silent.

Exit 0 = live site verified. Exit 1 = live site is wrong/stale.
"""
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402

URL = "https://huddlepuffers.hossautomation.com/"
MAX_AGE_MIN = 20
TONE_FIELDS = ("power_nickname_friendly", "power_blurb_friendly",
               "power_nickname_spicy", "power_blurb_spicy")


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "huddlepuffers-smoke"})
    html = urllib.request.urlopen(req, timeout=45).read().decode()

    m = re.search(r"window\.__RANKINGS_DATA__\s*=\s*", html)
    if not m:
        print("::error::[smoke_test] live page has no __RANKINGS_DATA__ marker")
        return 1
    i = html.index("{", m.end())
    depth = 0
    for j in range(i, len(html)):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                break
    data = json.loads(html[i:j + 1].replace("<\\/", "</"))
    meta = data["meta"]

    ok = True
    if str(meta.get("league_id")) != str(config.CURRENT_LEAGUE_ID):
        print(f"::error::[smoke_test] LIVE site serves league {meta.get('league_id')}, "
              f"config says {config.CURRENT_LEAGUE_ID}")
        ok = False

    gen = meta.get("generated_at", "")
    try:
        gen_dt = dt.datetime.fromisoformat(gen.replace("Z", "+00:00"))
        age_min = (dt.datetime.now(dt.timezone.utc) - gen_dt).total_seconds() / 60
        if age_min > MAX_AGE_MIN:
            print(f"::error::[smoke_test] live generated_at is {age_min:.0f} min old "
                  f"(> {MAX_AGE_MIN}) — deploy did not take or CDN is stale")
            ok = False
        else:
            print(f"[smoke_test] live data is {age_min:.1f} min old")
    except ValueError:
        print(f"::error::[smoke_test] unparseable generated_at: {gen!r}")
        ok = False

    toneless = [t.get("owner_name") for t in data.get("teams", [])
                if not all(t.get(f) for f in TONE_FIELDS)]
    if toneless:
        print(f"::error::[smoke_test] teams missing tone fields on LIVE site "
              f"(toggle broken): {toneless}")
        ok = False

    if ok:
        print(f"[smoke_test] OK — live site serves league {meta.get('league_id')}, "
              f"{len(data.get('teams', []))} teams, both tone sets present")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
