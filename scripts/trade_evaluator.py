"""
trade_evaluator.py — Evaluate a Huddlepuffers trade using FantasyCalc dynasty values
plus age/trend/positional context.

Usage (CLI):
    python3 trade_evaluator.py --send "Christian McCaffrey, 2026 1st" --get "Brock Bowers, 2027 2nd"

Usage (interactive — just run with no args):
    python3 trade_evaluator.py
    > SEND: Christian McCaffrey, 2026 1st
    > GET:  Brock Bowers, 2027 2nd

Pick formats accepted (case-insensitive, comma-separated):
    "2026 1st"            -> generic mid-1st
    "2026 Pick 1.06"      -> specific slot
    "26 mid 2"            -> shorthand: 2026 mid-2nd
    "2027 early 3"        -> 2027 Pick 3.03
    "2026 late 1"         -> 2026 Pick 1.10

Verdict thresholds (based on % difference favoring the side that GETS more):
    <  5%  : FAIR
    5-15%  : SLIGHT EDGE
   15-30%  : CLEAR WIN / LOSS
    > 30%  : STEAL / OVERPAY

Outputs:
  - Side-by-side breakdown to console
  - Verdict with context
"""

import sqlite3
import argparse
import re
from pathlib import Path
from difflib import get_close_matches

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "db" / "fantasy.sqlite"

# ---------- PICK PARSING ----------

ROUND_WORDS = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5",
               "1st": "1", "2nd": "2", "3rd": "3", "4th": "4", "5th": "5"}
SLOT_BY_TIER = {"early": 3, "mid": 6, "late": 10}  # which pick number to use


def normalize_pick(text):
    """
    Convert a user pick string into the FantasyCalc full_name format.
    Returns (lookup_name, fallback_name) — try lookup first, then fallback.
    """
    s = text.strip().lower()
    # Year shorthand: "26" -> "2026"
    s = re.sub(r"\b(2[5-9])\b", r"20\1", s)
    s = re.sub(r"\b(3[0-5])\b", r"20\1", s)

    # Pull year
    ym = re.search(r"\b(20\d{2})\b", s)
    if not ym:
        return text, text  # give up, let caller flag
    year = ym.group(1)

    # Specific slot: "1.06" or "round 1 pick 6"
    slot_m = re.search(r"\b([1-5])[.\s-]+(\d{1,2})\b", s)
    if slot_m:
        rd, pk = slot_m.group(1), int(slot_m.group(2))
        return f"{year} Pick {rd}.{pk:02d}", f"{year} {rd}{ordinal(int(rd))}"

    # Tier: "early/mid/late 1st" or "mid 2"
    tier_m = re.search(r"\b(early|mid|late)\b.*?\b([1-5])(st|nd|rd|th)?\b", s)
    if tier_m:
        tier, rd = tier_m.group(1), tier_m.group(2)
        pk = SLOT_BY_TIER[tier]
        return f"{year} Pick {rd}.{pk:02d}", f"{year} {rd}{ordinal(int(rd))}"
    tier_m2 = re.search(r"\b([1-5])(st|nd|rd|th)?\b.*?\b(early|mid|late)\b", s)
    if tier_m2:
        rd, tier = tier_m2.group(1), tier_m2.group(3)
        pk = SLOT_BY_TIER[tier]
        return f"{year} Pick {rd}.{pk:02d}", f"{year} {rd}{ordinal(int(rd))}"

    # Plain round: "2026 1st" or "2026 1"
    rd_m = re.search(r"\b([1-5])(st|nd|rd|th)?\b", s)
    if rd_m:
        rd = rd_m.group(1)
        return f"{year} {rd}{ordinal(int(rd))}", f"{year} Pick {rd}.06"

    return text, text


def ordinal(n):
    return {1: "st", 2: "nd", 3: "rd"}.get(n, "th")


# ---------- LOOKUP ----------

def lookup_asset(conn, raw, all_names):
    """
    Resolve one asset (player or pick) to a fantasycalc_values row.
    Returns dict with name/position/value/age/trend or None if unmatched.
    """
    raw = raw.strip()
    if not raw:
        return None

    # Pick?
    if re.search(r"\b20\d{2}\b|\b2[5-9]\b|\b3[0-5]\b", raw) or "pick" in raw.lower():
        primary, fallback = normalize_pick(raw)
        for candidate in (primary, fallback):
            row = conn.execute(
                "SELECT full_name, position, value, age, trend_30day, overall_rank "
                "FROM fantasycalc_values WHERE LOWER(full_name) = LOWER(?)",
                (candidate,)
            ).fetchone()
            if row:
                return _to_dict(row, source=f"pick (matched '{candidate}')")
        # Fuzzy
        match = get_close_matches(primary.lower(), [n.lower() for n in all_names], n=1, cutoff=0.6)
        if match:
            row = conn.execute(
                "SELECT full_name, position, value, age, trend_30day, overall_rank "
                "FROM fantasycalc_values WHERE LOWER(full_name) = ?", (match[0],)
            ).fetchone()
            if row:
                return _to_dict(row, source=f"pick (fuzzy '{row[0]}')")
        return {"name": raw, "position": "PICK", "value": 0, "age": None,
                "trend": None, "rank": None, "source": "NOT FOUND"}

    # Player — exact, then fuzzy
    row = conn.execute(
        "SELECT full_name, position, value, age, trend_30day, overall_rank "
        "FROM fantasycalc_values WHERE LOWER(full_name) = LOWER(?)", (raw,)
    ).fetchone()
    if row:
        return _to_dict(row, source="exact")

    match = get_close_matches(raw.lower(), [n.lower() for n in all_names], n=1, cutoff=0.7)
    if match:
        row = conn.execute(
            "SELECT full_name, position, value, age, trend_30day, overall_rank "
            "FROM fantasycalc_values WHERE LOWER(full_name) = ?", (match[0],)
        ).fetchone()
        if row:
            return _to_dict(row, source=f"fuzzy → '{row[0]}'")

    return {"name": raw, "position": "?", "value": 0, "age": None,
            "trend": None, "rank": None, "source": "NOT FOUND"}


def _to_dict(row, source):
    return {
        "name": row[0], "position": row[1], "value": row[2] or 0,
        "age": row[3], "trend": row[4], "rank": row[5], "source": source,
    }


# ---------- EVALUATION ----------

def verdict(send_total, get_total):
    if send_total == 0 and get_total == 0:
        return "NO VALUE — check inputs", 0
    bigger = max(send_total, get_total)
    diff_pct = abs(send_total - get_total) / bigger * 100
    you_win = get_total > send_total

    if diff_pct < 5:
        return "FAIR — equal value either way", diff_pct
    if diff_pct < 15:
        return ("SLIGHT EDGE — you" if you_win else "SLIGHT EDGE — them"), diff_pct
    if diff_pct < 30:
        return ("CLEAR WIN — accept" if you_win else "CLEAR LOSS — pass"), diff_pct
    return ("STEAL — accept now" if you_win else "OVERPAY — walk away"), diff_pct


def context_notes(side_assets, label):
    """Generate qualitative notes about a side of the trade."""
    notes = []
    players = [a for a in side_assets if a["position"] not in ("PICK", "?")]
    picks = [a for a in side_assets if a["position"] == "PICK"]

    # Age signals
    old = [a for a in players if a["age"] and a["age"] >= 29]
    young = [a for a in players if a["age"] and a["age"] <= 23]
    if old:
        notes.append(f"{label} includes aging asset(s): " + ", ".join(
            f"{a['name']} ({a['age']:.1f})" for a in old))
    if young:
        notes.append(f"{label} includes youth: " + ", ".join(
            f"{a['name']} ({a['age']:.1f})" for a in young))

    # Trend signals
    falling = [a for a in players if a["trend"] is not None and a["trend"] <= -200]
    rising = [a for a in players if a["trend"] is not None and a["trend"] >= 200]
    if falling:
        notes.append(f"{label} has falling value: " + ", ".join(
            f"{a['name']} ({a['trend']:+.0f})" for a in falling))
    if rising:
        notes.append(f"{label} has rising value: " + ", ".join(
            f"{a['name']} ({a['trend']:+.0f})" for a in rising))

    # Pick concentration
    if len(picks) >= 2:
        notes.append(f"{label} is pick-heavy ({len(picks)} picks) — projection risk")

    return notes


# ---------- DRIVER ----------

def parse_side(text, conn, all_names):
    items = [t.strip() for t in text.split(",") if t.strip()]
    return [lookup_asset(conn, x, all_names) for x in items]


def print_side(label, assets):
    print(f"\n  {label}")
    print(f"  {'-'*60}")
    for a in assets:
        age = f"{a['age']:.1f}" if a["age"] is not None else " — "
        trend = f"{a['trend']:+.0f}" if a["trend"] is not None else "  — "
        rank = f"#{int(a['rank'])}" if a["rank"] else "  — "
        print(f"  {a['name']:<28} {a['position']:<5} age={age:<4} val={a['value']:>5,}  rank={rank:<5} 30d={trend:<5}  [{a['source']}]")
    total = sum(a["value"] for a in assets)
    print(f"  {'':<28} {'':<5} {'':<8} {'TOTAL':<5} {total:>5,}")
    return total


def evaluate(send_text, get_text):
    conn = sqlite3.connect(DB_PATH)
    all_names = [r[0] for r in conn.execute("SELECT full_name FROM fantasycalc_values")]

    send = parse_side(send_text, conn, all_names)
    get_ = parse_side(get_text, conn, all_names)

    print("\n" + "="*70)
    print("  TRADE EVALUATION — Huddlepuffers (Dynasty, 1QB, 10-team, PPR)")
    print("="*70)
    send_total = print_side("YOU SEND", send)
    get_total  = print_side("YOU GET", get_)

    v, pct = verdict(send_total, get_total)
    print("\n" + "="*70)
    diff = get_total - send_total
    print(f"  NET: {diff:+,} ({pct:.1f}% delta)   →   {v}")
    print("="*70)

    print("\n  CONTEXT")
    for line in context_notes(send, "Send-side"):
        print(f"   • {line}")
    for line in context_notes(get_, "Get-side"):
        print(f"   • {line}")

    # Roster fit hint
    your_pos = {"QB": (7, "weak"), "RB": (2, "strong"), "WR": (5, "average"),
                "TE": (4, "average")}
    pos_traded_in = {a["position"] for a in get_ if a["position"] in your_pos}
    pos_traded_out = {a["position"] for a in send if a["position"] in your_pos}
    fit = []
    for p in pos_traded_in:
        rk, lbl = your_pos[p]
        fit.append(f"add at {p} (currently #{rk} / {lbl})")
    for p in pos_traded_out:
        rk, lbl = your_pos[p]
        fit.append(f"thin at {p} (currently #{rk} / {lbl})")
    if fit:
        print(f"   • Roster fit: {'; '.join(fit)}")

    # Starter-value gap reminder
    starters_added = sum(a["value"] for a in get_ if a["position"] != "PICK")
    starters_lost  = sum(a["value"] for a in send if a["position"] != "PICK")
    sv_change = starters_added - starters_lost
    if abs(sv_change) >= 1500:
        direction = "improves" if sv_change > 0 else "weakens"
        print(f"   • This {direction} your starter value by ~{abs(sv_change):,} "
              f"(reminder: you're #5 in starter value, #3 in total)")

    print()
    conn.close()


def interactive():
    print("Trade Evaluator — type SEND and GET sides separated by commas. Empty to exit.")
    while True:
        send = input("\nSEND > ").strip()
        if not send:
            return
        get_ = input("GET  > ").strip()
        if not get_:
            return
        evaluate(send, get_)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", help="Comma-separated assets you give up")
    ap.add_argument("--get", help="Comma-separated assets you receive")
    args = ap.parse_args()
    if args.send and args.get:
        evaluate(args.send, args.get)
    else:
        interactive()


if __name__ == "__main__":
    main()
