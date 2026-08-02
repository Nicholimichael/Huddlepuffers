#!/usr/bin/env python3
"""
generate_labels.py — Write the weekly "fun copy" (platform/ai_labels.json) for the
Huddlepuffers redesign by asking Claude to riff on that week's real numbers.

Reads platform/rankings_data.json (the freshly-built league data), sends the
standings + last week's copy to the Anthropic Messages API, and writes nicknames,
team blurbs, and a state-of-the-league paragraph in the exact shape that
build_redesign.py expects.

Safe by design:
  * If ANTHROPIC_API_KEY is NOT set, this is a NO-OP — it leaves the existing
    platform/ai_labels.json untouched and exits 0. The weekly workflow therefore
    ships the current (frozen) copy until you opt in by adding the key.
  * If the API call fails, times out, or returns unparseable JSON, it WARNS and
    keeps the existing labels rather than shipping broken copy. Never exits non-zero
    for a copy problem — a bad fun-copy week must not fail the whole refresh.

Stdlib only (urllib) — no new dependencies, matching the fetch_* scripts.

Usage:
  python3 scripts/generate_labels.py                 # regenerate (needs ANTHROPIC_API_KEY)
  python3 scripts/generate_labels.py --dry-run       # build + print the prompt, no API call
  python3 scripts/generate_labels.py --model claude-haiku-4-5   # cheaper model
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.join(os.path.dirname(HERE), "platform")
DATA_PATH = os.path.join(PLATFORM, "rankings_data.json")
LABELS_PATH = os.path.join(PLATFORM, "ai_labels.json")

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = os.environ.get("HP_LABELS_MODEL", "claude-opus-4-8")

SYSTEM_PROMPT = """\
You write the weekly personality copy for a buddy fantasy-football dynasty league
dashboard called the Huddlepuffers. The audience is the 10 league members — it's a
group chat, not ESPN.

Voice: punchy, funny, a little roast-y but affectionate. Ground EVERY line in the
team's actual numbers (record, points for/against, roster value). No clichés, no
hedging, no generic filler.

Return ONLY a JSON object — no markdown, no commentary — in EXACTLY this shape:

{
  "generated_for_snapshot": "YYYY-MM-DD",
  "state_of_league": "2-4 sentences on the league's overall shape this week, naming real teams and real numbers.",
  "teams": {
    "<owner_name>": {
      "nickname_friendly": "ALL-CAPS, <=3 WORDS",
      "blurb_friendly": "one punchy sentence grounded in their numbers",
      "nickname_spicy": "ALL-CAPS, <=3 WORDS",
      "blurb_spicy": "one punchy sentence grounded in their numbers"
    }
  }
}

Rules:
- Include EVERY owner_name present in the standings I give you — no more, no fewer.
- Write BOTH tone sets for every team. The dashboard has a Friendly/Spicy toggle:
  * friendly = hype and affectionate — celebrate what's working, soften what isn't.
  * spicy = roast-y and pointed — same numbers, no mercy (still league-banter, not cruel).
- Nicknames are ALL CAPS, at most 3 words, and the two tones' nicknames should differ.
- Blurbs are a single sentence each.
- Use the previous week's copy only for continuity of voice; do not just repeat it —
  reflect where teams actually are now.
"""


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_context(data, prior_labels):
    """Compact, model-friendly digest of the week from rankings_data.json."""
    meta = data.get("meta", {})
    fields = (
        "owner_name", "wins", "losses", "fpts", "fpts_against", "ppts",
        "dynasty_total", "winnow_total", "starters_dynasty", "starters_winnow",
        "roster_size", "is_me",
    )
    standings = [{k: t.get(k) for k in fields} for t in data.get("teams", [])]
    # Natural standings order: most wins, then most points.
    standings.sort(key=lambda x: (-(x.get("wins") or 0), -(x.get("fpts") or 0)))
    return {
        "season": meta.get("season"),
        "latest_nfl_week": meta.get("latest_nfl_week"),
        "owner_of_dashboard": meta.get("my_display_name"),
        "standings": standings,
        "previous_copy": prior_labels or {},
    }


def call_claude(api_key, model, context, max_tokens=4000):
    user_msg = (
        "Here are this week's Huddlepuffers numbers (standings sorted best-to-worst) "
        "and last week's copy for voice continuity. Write this week's copy.\n\n"
        + json.dumps(context, ensure_ascii=False)
    )
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user_msg}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.load(r)
    return "".join(block.get("text", "") for block in resp.get("content", []))


def extract_json(text):
    """Pull the JSON object out of a model reply, tolerating ``` fences / stray prose."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    start, end = t.find("{"), t.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in model reply")
    return json.loads(t[start:end + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=DATA_PATH)
    ap.add_argument("--labels", default=LABELS_PATH)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--max-tokens", type=int, default=4000)
    ap.add_argument("--dry-run", action="store_true",
                    help="build + print the context the model would receive, then exit (no API call)")
    args = ap.parse_args()

    data = load_json(args.data)
    if not data:
        print(f"[generate_labels] no data at {args.data}; keeping existing labels.")
        return 0
    prior = load_json(args.labels, default={})
    context = build_context(data, prior)

    if args.dry_run:
        print("[generate_labels] DRY RUN — context that would be sent:")
        print(json.dumps(context, indent=2, ensure_ascii=False))
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[generate_labels] ANTHROPIC_API_KEY not set — NO-OP, keeping existing "
              f"{os.path.basename(args.labels)} (frozen copy).")
        return 0

    try:
        reply = call_claude(api_key, args.model, context, args.max_tokens)
        labels = extract_json(reply)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError, KeyError) as e:
        print(f"::warning::[generate_labels] copy generation failed ({type(e).__name__}: {e}); "
              "keeping existing labels.")
        return 0

    if "teams" not in labels or "state_of_league" not in labels:
        print("::warning::[generate_labels] model reply missing required keys; keeping existing labels.")
        return 0

    # Backfill the legacy single-set fields (nickname/blurb) from the spicy set so
    # older templates / consumers keep working; warn if a team is missing a tone.
    for owner, L in labels["teams"].items():
        if L.get("nickname_spicy") and not L.get("nickname"):
            L["nickname"] = L["nickname_spicy"]
        if L.get("blurb_spicy") and not L.get("blurb"):
            L["blurb"] = L["blurb_spicy"]
        missing = [k for k in ("nickname_friendly", "blurb_friendly",
                               "nickname_spicy", "blurb_spicy") if not L.get(k)]
        if missing:
            print(f"::warning::[generate_labels] {owner} missing tone fields: {missing} "
                  "(toggle will fall back to the legacy set for them).")

    labels.setdefault(
        "generated_for_snapshot",
        (data.get("meta", {}).get("generated_at", "") or "")[:10]
        or datetime.date.today().isoformat(),
    )
    labels["_comment"] = ("AI personality copy for the Huddlepuffers redesign, "
                          "auto-generated weekly by scripts/generate_labels.py from that "
                          "week's numbers. Hand-edit freely; the next run will overwrite.")
    with open(args.labels, "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2, ensure_ascii=False)
        f.write("\n")

    applied = len(labels.get("teams", {}))
    print(f"[generate_labels] wrote {args.labels} — {applied} team labels, "
          f"model={args.model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
