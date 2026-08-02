#!/usr/bin/env python3
"""
test_digest_fixtures.py — Regression fixtures for weekly_digest.py (v3/B5).

Two historical bugs this pins down forever:
  1. 2026-06-14: "Your roster" header hardcoded to the wrong owner (mmmatlock).
  2. 2026-06-14: "No new transactions" printed while trades existed.

Builds a throwaway sqlite DB + two fake snapshots in a temp dir, monkeypatches
weekly_digest's module paths at it, runs write_digest, and asserts on the output.
No network, no real data touched. Runs as a CI step (and locally: python3
scripts/test_digest_fixtures.py). Exit 0 = all assertions pass.
"""
import datetime as dt
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import config  # noqa: E402
import scripts.weekly_digest as wd  # noqa: E402  (works because ROOT on path)

LEAGUE = str(config.CURRENT_LEAGUE_ID)
ME = config.MY_USER_ID
NOW_MS = int(dt.datetime.now().timestamp() * 1000)


def fake_snapshot(dyn_a):
    return {
        "meta": {"league_id": LEAGUE, "my_user_id": ME,
                 "my_display_name": config.MY_DISPLAY_NAME,
                 "generated_at": "2026-08-01T00:00:00Z"},
        "players": [
            {"player_id": "1001", "full_name": "Test Playerman", "position": "RB",
             "owner_id": ME, "owner_name": config.MY_DISPLAY_NAME,
             "dynasty_score": dyn_a, "winnow_score": 50.0,
             "dynasty_overall_rank": 10},
            {"player_id": "1002", "full_name": "Other Guy", "position": "WR",
             "owner_id": "999", "owner_name": "someoneelse",
             "dynasty_score": 40.0, "winnow_score": 40.0,
             "dynasty_overall_rank": 20},
        ],
    }


def fake_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE transactions (type TEXT, status TEXT, created INT, "
                 "_league_id TEXT, draft_picks TEXT, adds_1001 INT, roster_ids TEXT)")
    conn.execute("INSERT INTO transactions VALUES ('trade','complete',?,?,"
                 "'[{\"season\":\"2028\",\"round\":1,\"owner_id\":2}]',5,'[2,5]')",
                 (NOW_MS, LEAGUE))
    conn.execute("INSERT INTO transactions VALUES ('waiver','complete',?,?,NULL,NULL,NULL)",
                 (NOW_MS, LEAGUE))
    # A trade from a DIFFERENT league in the window — must NOT be counted.
    conn.execute("INSERT INTO transactions VALUES ('trade','complete',?,'other_league',"
                 "NULL,NULL,NULL)", (NOW_MS,))
    conn.execute("CREATE TABLE rosters (roster_id INT, owner_id TEXT, _league_id TEXT)")
    conn.execute("INSERT INTO rosters VALUES (5, ?, ?)", (ME, LEAGUE))
    conn.execute("INSERT INTO rosters VALUES (2, '999', ?)", (LEAGUE,))
    conn.execute("CREATE TABLE users (user_id TEXT, display_name TEXT, _league_id TEXT)")
    conn.execute("INSERT INTO users VALUES (?, ?, ?)", (ME, config.MY_DISPLAY_NAME, LEAGUE))
    conn.execute("INSERT INTO users VALUES ('999', 'someoneelse', ?)", (LEAGUE,))
    conn.execute("CREATE TABLE players (player_id TEXT, full_name TEXT, position TEXT)")
    conn.execute("INSERT INTO players VALUES ('1001', 'Test Playerman', 'RB')")
    conn.commit()
    conn.close()


def main():
    failures = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        db = tmp / "test.sqlite"
        fake_db(db)
        # Point the module at the sandbox
        wd.DB = db
        wd.REPORTS = tmp / "reports"

        prev = fake_snapshot(50.0)
        curr = fake_snapshot(58.5)  # +8.5 — must appear as a my-roster mover
        out = wd.write_digest(prev, curr, ME)
        text = out.read_text()

        def check(cond, label):
            (print(f"  PASS  {label}") if cond else failures.append(label))
            if not cond:
                print(f"  FAIL  {label}")

        check(f"## Your roster ({config.MY_DISPLAY_NAME})" in text,
              "roster header uses my_display_name (bug #1)")
        check("mmmatlock" not in text.split("## Your roster")[1][:40],
              "roster header is not the hardcoded wrong owner")
        check("1 trade" in text and "1 waiver" in text,
              "transaction counts present and league-scoped (bug #2)")
        check("2 trades" not in text,
              "other-league trade excluded from counts")
        check("Test Playerman" in text, "trade line names the traded player")
        check("2028 R1 pick" in text, "trade line names the traded pick")
        check("+8.5" in text, "my-roster mover delta rendered")

    if failures:
        print(f"::error::[test_digest_fixtures] {len(failures)} assertion(s) failed: {failures}")
        return 1
    print("[test_digest_fixtures] all digest fixtures pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
