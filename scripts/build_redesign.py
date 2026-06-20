#!/usr/bin/env python3
"""
build_redesign.py — Inject fresh league data + AI labels into the redesigned
Huddlepuffers dashboard template, producing platform/index.html.

The redesign is ONE self-contained file: every view reads from a single embedded
object, window.__RANKINGS_DATA__. This script takes:
  - platform/rankings_data.json   (built by the existing data pipeline; same shape)
  - platform/ai_labels.json       (optional; the fun copy Claude writes each week)
and renders platform/index.html from platform/redesign_template.html.

AI labels are merged INTO the data object (team.power_nickname / team.power_blurb
and meta.state_of_league), which the dashboard reads natively — no window.claude
needed on the live site.

Usage:
  python3 scripts/build_redesign.py
  python3 scripts/build_redesign.py --data PATH --labels PATH --template PATH --out PATH --keep-generated-at
"""
import argparse, json, datetime, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM = os.path.join(os.path.dirname(HERE), "platform")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(PLATFORM, "rankings_data.json"))
    ap.add_argument("--labels", default=os.path.join(PLATFORM, "ai_labels.json"))
    ap.add_argument("--template", default=os.path.join(PLATFORM, "redesign_template.html"))
    ap.add_argument("--out", default=os.path.join(PLATFORM, "index.html"))
    ap.add_argument("--keep-generated-at", action="store_true",
                    help="keep meta.generated_at from the data file instead of bumping to now")
    args = ap.parse_args()

    with open(args.data, encoding="utf-8") as f:
        data = json.load(f)
    for k in ("meta", "teams", "players", "picks"):
        if k not in data:
            sys.exit(f"ERROR: {args.data} missing required key: {k}")

    # --- merge AI labels (the part Claude writes weekly), keyed by owner_name ---
    labels = {}
    if os.path.exists(args.labels):
        with open(args.labels, encoding="utf-8") as f:
            labels = json.load(f)
    team_labels = labels.get("teams", {})
    applied = 0
    for t in data["teams"]:
        L = team_labels.get(t.get("owner_name"))
        if L:
            if L.get("nickname"):
                t["power_nickname"] = L["nickname"]
            if L.get("blurb"):
                t["power_blurb"] = L["blurb"]
            applied += 1
    if labels.get("state_of_league"):
        data["meta"]["state_of_league"] = labels["state_of_league"]

    # --- timestamp: bump so movement arrows + label caches refresh (HANDOFF S3/S4) ---
    if not args.keep_generated_at:
        data["meta"]["generated_at"] = datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    gen = data["meta"]["generated_at"]

    # --- inject into the template (escape </ so no embedded </script> breaks parsing) ---
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()
    if "__HP_RANKINGS_DATA__" not in tpl or "__HP_DATA_VERSION__" not in tpl:
        sys.exit("ERROR: template missing injection placeholders")
    out = tpl.replace("__HP_RANKINGS_DATA__", blob).replace("__HP_DATA_VERSION__", gen)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"[build_redesign] wrote {args.out}")
    print(f"  teams={len(data['teams'])} players={len(data['players'])} "
          f"picks={len(data['picks'])} extras={'yes' if data.get('extras') else 'no'}")
    print(f"  labels applied to {applied}/{len(data['teams'])} teams; "
          f"state_of_league={'set' if data['meta'].get('state_of_league') else 'MISSING'}")
    print(f"  generated_at={gen}  size={len(out)/1024/1024:.2f} MB")


if __name__ == "__main__":
    main()
