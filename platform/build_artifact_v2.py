"""Build the Huddlepuffers Dynasty Platform — v2 with Trends / Construction / Picks tabs.

Reads platform/rankings_data.json (augmented by build_platform_v2.py) and emits
huddlepuffers_platform.html into the same directory.

The JSON is NOT embedded inline — the HTML fetches rankings_data.json at runtime
(using the meta.generated_at timestamp as a cache-buster). This keeps the HTML
shell small (~125 KB) so the browser can cache it independently of the data.
"""
import json
import os
import re
import sys

# ---- Path flexibility (sandbox VM vs local) ----
# Always anchor to the directory this script lives in — works in any season.
PLATFORM_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PLATFORM_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import config

DATA_PATH = os.path.join(PLATFORM_DIR, "rankings_data.json")
OUT_PATH  = os.path.join(PLATFORM_DIR, "huddlepuffers_platform.html")

# Read the JSON for two reasons:
#   1) Grab generated_at for cache-busting in the HTML
#   2) Sanitize bare NaN / Infinity tokens before the browser fetches it.
#      Python's json module emits these for float('nan') / float('inf'), but
#      JSON.parse() in the browser rejects them — they're not valid JSON.
#      We rewrite the file in place with NaN/Infinity replaced by null.
with open(DATA_PATH) as f:
    _raw_json = f.read()

_data_meta = json.loads(_raw_json).get("meta", {})
DATA_VERSION = _data_meta.get("generated_at", "")

_sanitized = re.sub(r'\bNaN\b', 'null', _raw_json)
_sanitized = re.sub(r'-?\bInfinity\b', 'null', _sanitized)
if _sanitized != _raw_json:
    with open(DATA_PATH, "w") as f:
        f.write(_sanitized)
    print(f"sanitized rankings_data.json (NaN/Infinity → null)")

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Huddlepuffers Dynasty Platform</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.5.0/dist/chart.umd.js" integrity="sha384-iU8HYtnGQ8Cy4zl7gbNMOhsDTTKX02BTXptVP/vqAWIaTfM7isw76iyZCsjL2eVi" crossorigin="anonymous"></script>
<style>
  :root {
    color-scheme: light;
    --bg: #f6f7fb;
    --card: #ffffff;
    --ink: #0f172a;
    --ink-2: #475569;
    --ink-3: #94a3b8;
    --line: #e2e8f0;
    --line-2: #cbd5e1;
    --accent: #2563eb;
    --accent-2: #1d4ed8;
    --accent-soft: #dbeafe;
    --good: #16a34a;
    --good-soft: #dcfce7;
    --bad: #dc2626;
    --bad-soft: #fee2e2;
    --warn: #b45309;
    --warn-soft: #fef3c7;
    --me: #7c3aed;
    --me-soft: #ede9fe;
    --qb: #ef4444; --rb: #22c55e; --wr: #3b82f6; --te: #f59e0b;
    --k: #6b7280; --def: #0ea5e9; --idp: #8b5cf6; --pick: #a855f7;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    font-size: 14px; line-height: 1.45; }
  a { color: var(--accent); text-decoration: none; }
  .app { max-width: 1400px; margin: 0 auto; padding: 20px 24px 40px; }
  header { display: flex; align-items: baseline; justify-content: space-between; flex-wrap: wrap;
    gap: 8px; margin-bottom: 18px; }
  header h1 { font-size: 22px; margin: 0; letter-spacing: -0.01em; }
  header .meta { color: var(--ink-2); font-size: 12px; }

  .tabs { display: flex; flex-wrap: wrap; gap: 2px; background: var(--card); border: 1px solid var(--line);
    border-radius: 10px; padding: 4px; width: fit-content; margin-bottom: 16px; }
  .tabs button { appearance: none; border: 0; background: transparent; color: var(--ink-2);
    font-weight: 600; font-size: 13px; padding: 8px 14px; border-radius: 7px; cursor: pointer; }
  .tabs button.active { background: var(--accent); color: #fff; }
  .tabs button:hover:not(.active) { background: var(--bg); color: var(--ink); }

  .card { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 18px; margin-bottom: 14px; }
  .card h2 { margin: 0 0 12px; font-size: 15px; font-weight: 600; }
  .card h3 { margin: 0 0 8px; font-size: 13px; font-weight: 600; color: var(--ink-2); }

  .grid { display: grid; gap: 14px; }
  .grid-2 { grid-template-columns: 1fr 1fr; }
  .grid-3 { grid-template-columns: repeat(3, 1fr); }
  .grid-4 { grid-template-columns: repeat(4, 1fr); }
  @media (max-width: 900px) { .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; } }

  .stat { display: flex; flex-direction: column; gap: 2px; }
  .stat .label { font-size: 11px; color: var(--ink-3); text-transform: uppercase;
    letter-spacing: 0.06em; }
  .stat .value { font-size: 22px; font-weight: 600; color: var(--ink); }
  .stat .sub { font-size: 11px; color: var(--ink-2); }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 8px 10px; font-size: 11px; font-weight: 600; color: var(--ink-3);
    text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--line);
    background: var(--bg); position: sticky; top: 0; cursor: pointer; user-select: none;
    white-space: nowrap; }
  th .arrow { opacity: 0.4; font-size: 10px; }
  th.sorted .arrow { opacity: 1; color: var(--accent); }
  td { padding: 7px 10px; border-bottom: 1px solid var(--line); vertical-align: middle; }
  tr.me-row { background: var(--me-soft); }
  tr:hover { background: #f8fafc; }
  tr.me-row:hover { background: #ddd6fe; }

  .chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 999px;
    font-size: 11px; font-weight: 600; }
  .pos { color: #fff; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: 700;
    width: 34px; display: inline-block; text-align: center; letter-spacing: 0.03em; }
  .pos-QB { background: var(--qb); }
  .pos-RB { background: var(--rb); }
  .pos-WR { background: var(--wr); }
  .pos-TE { background: var(--te); }
  .pos-K  { background: var(--k); }
  .pos-DEF{ background: var(--def); }
  .pos-DL,.pos-DE,.pos-DT { background: #6366f1; }
  .pos-LB { background: #8b5cf6; }
  .pos-DB,.pos-CB,.pos-S,.pos-SS,.pos-FS { background: #a855f7; }
  .pos-PICK { background: var(--pick); }

  .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }
  .controls input[type=text], .controls select {
    font: inherit; padding: 7px 10px; border: 1px solid var(--line-2); border-radius: 8px;
    background: #fff; color: var(--ink); outline: none; }
  .controls input[type=text]:focus, .controls select:focus { border-color: var(--accent); }
  .controls input[type=text] { min-width: 220px; }
  .toggle { display: inline-flex; background: var(--bg); border: 1px solid var(--line); border-radius: 8px;
    padding: 2px; }
  .toggle button { appearance: none; border: 0; background: transparent; font: inherit; padding: 6px 12px;
    border-radius: 6px; color: var(--ink-2); cursor: pointer; font-weight: 600; font-size: 12px; }
  .toggle button.active { background: var(--accent); color: #fff; }
  .filter-chips { display: flex; gap: 4px; flex-wrap: wrap; }
  .filter-chips button { appearance: none; border: 1px solid var(--line-2); background: #fff;
    padding: 5px 10px; border-radius: 999px; font: inherit; font-size: 11px; font-weight: 600;
    color: var(--ink-2); cursor: pointer; letter-spacing: 0.04em; }
  .filter-chips button.active { background: var(--ink); color: #fff; border-color: var(--ink); }
  .checkbox-wrap { display: inline-flex; gap: 6px; align-items: center; font-size: 12px;
    color: var(--ink-2); cursor: pointer; user-select: none; }

  .score-bar { position: relative; height: 6px; width: 80px; background: var(--line); border-radius: 3px;
    display: inline-block; vertical-align: middle; margin-left: 8px; }
  .score-bar > span { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; background: var(--accent); }
  .score-bar.warm > span { background: var(--good); }
  .score-bar.cool > span { background: var(--me); }
  .score-bar.wide { width: 100%; display: block; margin: 4px 0; }

  .trade-sides { display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: stretch; }
  @media (max-width: 900px) { .trade-sides { grid-template-columns: 1fr; } }
  .trade-side { background: var(--bg); border: 1px solid var(--line); border-radius: 10px; padding: 12px;
    min-height: 180px; }
  .trade-side.mine { border-color: var(--me); background: var(--me-soft); }
  .trade-side .side-header { display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 8px; }
  .trade-side .side-header h3 { margin: 0; }
  .trade-side .side-total { font-weight: 700; font-size: 15px; }
  .asset-list { display: flex; flex-direction: column; gap: 4px; margin: 8px 0; }
  .asset { display: flex; align-items: center; justify-content: space-between; gap: 6px;
    background: #fff; border: 1px solid var(--line); padding: 6px 8px; border-radius: 8px; font-size: 12px; }
  .asset .rm { appearance: none; border: 0; background: transparent; color: var(--bad); cursor: pointer;
    font-size: 16px; line-height: 1; padding: 0 4px; }
  .asset .asset-val { color: var(--ink-2); font-size: 11px; white-space: nowrap; }
  .trade-add { display: flex; gap: 6px; position: relative; }
  .trade-add input { flex: 1; padding: 7px 10px; border: 1px solid var(--line-2); border-radius: 8px;
    font: inherit; background: #fff; }
  .autocomplete { position: absolute; top: 38px; left: 0; right: 0; background: #fff; border: 1px solid var(--line-2);
    border-radius: 8px; max-height: 260px; overflow-y: auto; z-index: 5; display: none;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
  .autocomplete.open { display: block; }
  .autocomplete .ac-item { padding: 7px 10px; cursor: pointer; display: flex; justify-content: space-between;
    align-items: center; gap: 8px; font-size: 12px; border-bottom: 1px solid var(--line); }
  .autocomplete .ac-item:hover, .autocomplete .ac-item.highlight { background: var(--accent-soft); }
  .trade-arrow { font-size: 24px; color: var(--ink-3); align-self: center; }
  .trade-verdict { margin-top: 14px; padding: 12px 14px; border-radius: 10px; font-weight: 600;
    display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  .trade-verdict.win { background: var(--good-soft); color: var(--good); }
  .trade-verdict.loss { background: var(--bad-soft); color: var(--bad); }
  .trade-verdict.even { background: var(--warn-soft); color: var(--warn); }

  .trend-up { color: var(--good); }
  .trend-dn { color: var(--bad); }

  .muted { color: var(--ink-3); }
  .small { font-size: 11px; }

  .team-card { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 12px;
    display: flex; flex-direction: column; gap: 4px; }
  .team-card.me { border-color: var(--me); background: var(--me-soft); }
  .team-card .row { display: flex; justify-content: space-between; align-items: baseline; }
  .team-card .name { font-weight: 600; }
  .team-card .rec { color: var(--ink-2); font-size: 12px; }

  .methodology { font-size: 11px; color: var(--ink-2); line-height: 1.55; }
  .methodology code { background: var(--bg); padding: 1px 4px; border-radius: 4px; font-size: 10px; }

  .table-wrap { max-height: 65vh; overflow-y: auto; border: 1px solid var(--line); border-radius: 10px; }
  .hidden { display: none !important; }

  .starter-badge { display: inline-block; width: 8px; height: 8px; border-radius: 2px; background: var(--accent);
    margin-right: 4px; vertical-align: middle; }
  .taxi-badge    { background: var(--warn); }
  .reserve-badge { background: var(--bad); }

  .legend { display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: var(--ink-2);
    margin-top: 6px; }

  .posture { display: inline-flex; align-items: center; gap: 8px; }
  .rank-badge { display: inline-block; font-weight: 700; color: var(--ink-2); min-width: 24px; }

  /* === v2 additions === */

  /* Posture pill */
  .posture-pill { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 11px;
    font-weight: 700; letter-spacing: 0.03em; text-transform: uppercase; }
  .p-super     { background: #fef3c7; color: #92400e; }
  .p-contender { background: #dcfce7; color: #14532d; }
  .p-rebuilder { background: #ede9fe; color: #5b21b6; }
  .p-young     { background: #dbeafe; color: #1e3a8a; }
  .p-balanced  { background: #e2e8f0; color: #334155; }
  .p-stuck     { background: #fee2e2; color: #991b1b; }

  /* Construction per-team card */
  .construction-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  @media (max-width: 900px) { .construction-grid { grid-template-columns: 1fr; } }
  .team-construction { background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 14px; }
  .team-construction.me { border-color: var(--me); background: var(--me-soft); box-shadow: 0 0 0 2px var(--me-soft); }
  .team-construction .tc-head { display: flex; justify-content: space-between; align-items: baseline;
    margin-bottom: 8px; gap: 8px; flex-wrap: wrap; }
  .team-construction .tc-head .tc-name { font-weight: 700; font-size: 15px; }
  .team-construction .tc-head .tc-rec  { color: var(--ink-2); font-size: 12px; }
  .team-construction .tc-bars { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 8px 0; }
  .bar-cell { background: var(--bg); border-radius: 6px; padding: 8px 10px; }
  .bar-cell .bc-label { font-size: 10px; color: var(--ink-3); text-transform: uppercase;
    letter-spacing: 0.06em; font-weight: 600; }
  .bar-cell .bc-val   { font-size: 18px; font-weight: 700; }
  .bar-cell .bc-bar   { height: 5px; background: var(--line); border-radius: 3px; margin-top: 4px;
    position: relative; overflow: hidden; }
  .bar-cell .bc-bar > span { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; }
  .bar-cell.winnow .bc-bar > span   { background: var(--accent); }
  .bar-cell.rebuild .bc-bar > span  { background: var(--me); }
  .team-construction .pos-strengths { display: flex; gap: 6px; flex-wrap: wrap; font-size: 11px; }
  .team-construction .pos-strengths .tag { background: var(--good-soft); color: var(--good);
    padding: 2px 8px; border-radius: 999px; font-weight: 700; }
  .team-construction .pos-strengths .tag.weak { background: var(--bad-soft); color: var(--bad); }
  .team-construction .rec-box { font-size: 12px; color: var(--ink-2); background: var(--bg);
    border-radius: 6px; padding: 8px 10px; margin-top: 8px; line-height: 1.4; }

  /* Risers/fallers leaderboards */
  .rf-side { background: var(--card); border: 1px solid var(--line); border-radius: 10px;
    padding: 12px; }
  .rf-side h3 { margin: 0 0 8px; font-size: 13px; }
  .rf-row { display: flex; justify-content: space-between; align-items: center; gap: 6px;
    padding: 5px 0; border-bottom: 1px dashed var(--line); font-size: 12px; }
  .rf-row:last-child { border-bottom: 0; }
  .rf-row .rf-name { font-weight: 600; }
  .rf-row .rf-val { font-weight: 700; font-variant-numeric: tabular-nums; }

  /* Team / player news (My Team tab) */
  .news-item { padding: 10px 0; border-bottom: 1px dashed var(--line); }
  .news-item:last-child { border-bottom: 0; }
  .news-head { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }
  .news-item a.news-title { font-weight: 600; color: var(--ink); text-decoration: none; font-size: 14px; }
  .news-item a.news-title:hover { color: var(--accent); text-decoration: underline; }
  .news-item .news-desc { font-size: 12px; color: var(--ink-2); margin: 4px 0 6px; }
  .news-item .news-when { font-size: 11px; color: var(--ink-2); white-space: nowrap; }
  .news-players { display: flex; flex-wrap: wrap; gap: 4px; }
  .news-chip { font-size: 11px; padding: 1px 7px; border-radius: 999px; background: var(--bg);
    border: 1px solid var(--line); color: var(--ink-2); }
  .news-chip .pos { font-weight: 700; margin-right: 3px; }

  /* Trend chart wrapper */
  #trend-chart-wrap { position: relative; height: 320px; }

  /* Draft pick matrix */
  .picks-matrix { font-size: 12px; }
  .picks-matrix td, .picks-matrix th { padding: 6px 8px; }
  .picks-matrix .pick-cell { display: inline-flex; align-items: center; gap: 4px; padding: 2px 6px;
    border-radius: 4px; font-size: 11px; font-weight: 600; }
  .picks-matrix .pick-own  { background: var(--good-soft); color: var(--good); }
  .picks-matrix .pick-sent { background: var(--bad-soft); color: var(--bad); text-decoration: line-through; }
  .picks-matrix .pick-acq  { background: var(--accent-soft); color: var(--accent); }
  .picks-matrix .pick-none { color: var(--ink-3); }

  /* Rank superscript on NFL teams cells */
  .ranked-cell { position: relative; display: inline-block; min-width: 38px; text-align: right; }
  .ranked-cell .rank-sup { position: relative; top: -6px; left: 2px; font-size: 9px;
    font-weight: 700; color: var(--ink-3); padding: 1px 3px; border-radius: 3px; }
  .rank-top      { color: var(--good); background: var(--good-soft); }
  .rank-bottom   { color: var(--bad);  background: var(--bad-soft); }

  /* Sparkline cell (Snap & Opp tab) */
  .sparkline { display: inline-block; height: 18px; width: 80px; }
  .sparkline polyline { fill: none; stroke: var(--accent); stroke-width: 1.6; }
  .sparkline circle { fill: var(--accent); }

  /* Rookie / context cards */
  .pill { display: inline-block; padding: 1px 6px; border-radius: 9999px; font-size: 10px;
    font-weight: 700; background: var(--accent-soft); color: var(--accent); }
  .pill-mine { background: var(--good-soft); color: var(--good); }
  .pill-fa   { background: #f1f5f9; color: var(--ink-3); }

  /* Delta arrows */
  .delta-up { color: var(--good); }
  .delta-dn { color: var(--bad); }

  /* Injury banner on Overview */
  .injury-banner { display: flex; align-items: center; gap: 12px; padding: 10px 14px;
    border: 1px solid #fca5a5; background: #fef2f2; color: #991b1b;
    border-radius: 8px; margin-bottom: 12px; font-size: 13px; font-weight: 600; }
  .injury-banner.is-clean { border-color: #86efac; background: #f0fdf4; color: #166534; }
  .injury-banner button.injury-link { margin-left: auto; appearance: none; border: 0;
    background: transparent; color: inherit; font: inherit; cursor: pointer;
    text-decoration: underline; }

  /* Severity pills (Injury Wire) */
  .sev-5 { background: #fee2e2; color: #991b1b; }
  .sev-4 { background: #fed7aa; color: #9a3412; }
  .sev-3 { background: #fef9c3; color: #854d0e; }
  .sev-2 { background: #e0e7ff; color: #3730a3; }
  .sev-1 { background: #f1f5f9; color: var(--ink-3); }

  /* SoS heat tint on numeric cells */
  .sos-easy   { background: #dcfce7; color: #166534; font-weight: 700; }
  .sos-soft   { background: #f0fdf4; color: #166534; }
  .sos-mid    { background: transparent; }
  .sos-tough  { background: #fef3c7; color: #92400e; }
  .sos-brutal { background: #fee2e2; color: #991b1b; font-weight: 700; }

  .team-pill { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px;
    font-weight: 600; background: var(--bg); border: 1px solid var(--line); white-space: nowrap; }
  .team-pill.me { background: var(--me-soft); border-color: var(--me); color: var(--me); }

  /* Global team selector ("logged in as") */
  .team-selector-wrap { display: inline-flex; align-items: center; gap: 8px;
    background: var(--me-soft); border: 1px solid var(--me); padding: 6px 10px;
    border-radius: 999px; font-size: 12px; color: var(--me); font-weight: 600; }
  .team-selector-wrap label { cursor: pointer; letter-spacing: 0.04em;
    text-transform: uppercase; font-size: 10px; }
  .team-selector-wrap select { appearance: none; -webkit-appearance: none;
    background: #fff; border: 1px solid var(--me); color: var(--ink);
    font: inherit; font-weight: 700; padding: 4px 26px 4px 10px; border-radius: 999px;
    cursor: pointer; outline: none;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'><path d='M1 1l4 4 4-4' stroke='%237c3aed' stroke-width='1.5' fill='none' stroke-linecap='round'/></svg>");
    background-repeat: no-repeat; background-position: right 10px center; }
  .team-selector-wrap select:focus { box-shadow: 0 0 0 2px var(--me-soft); }
</style>
</head>
<body>
<div class="app">
  <header>
    <div>
      <h1 id="title">The Huddlepuffers — Dynasty Platform</h1>
      <div class="meta" id="subtitle"></div>
    </div>
    <div class="team-selector-wrap" title="Switch which team's view you're seeing">
      <label for="team-selector">Viewing as</label>
      <select id="team-selector"></select>
    </div>
    <div class="meta" id="refresh-meta"></div>
  </header>

  <nav class="tabs" id="tabs">
    <button data-tab="overview" class="active">Overview</button>
    <button data-tab="rankings">Rankings</button>
    <button data-tab="trends">Trends</button>
    <button data-tab="construction">Construction</button>
    <button data-tab="picks">Draft Picks</button>
    <button data-tab="trade">Trade Calc</button>
    <button data-tab="myteam">My Team</button>
    <button data-tab="rookies">Rookies</button>
    <button data-tab="nflteams">NFL Teams</button>
    <button data-tab="snaps">Snap & Opp</button>
    <button data-tab="injuries">Injuries</button>
    <button data-tab="sos">SoS</button>
    <button data-tab="about">Methodology</button>
  </nav>

  <!-- OVERVIEW -->
  <section id="tab-overview" class="tab-panel">
    <div id="o-injury-banner" class="injury-banner hidden">
      <span id="o-injury-text">—</span>
      <button class="injury-link" data-jump="injuries">Open Injury Wire →</button>
    </div>
    <div class="grid grid-4">
      <div class="card stat"><span class="label">My Record</span><span class="value" id="o-record">—</span>
        <span class="sub" id="o-record-sub"></span></div>
      <div class="card stat"><span class="label">My Dynasty Total</span><span class="value" id="o-dyn">—</span>
        <span class="sub" id="o-dyn-rank"></span></div>
      <div class="card stat"><span class="label">My Win-Now Total</span><span class="value" id="o-win">—</span>
        <span class="sub" id="o-win-rank"></span></div>
      <div class="card stat"><span class="label">My Starters Win-Now</span><span class="value" id="o-starters">—</span>
        <span class="sub" id="o-starters-rank"></span></div>
    </div>

    <div class="grid grid-2">
      <div class="card">
        <h2>League — Dynasty Totals (roster-wide)</h2>
        <div class="table-wrap">
          <table id="t-dyn-standings"><thead><tr>
            <th>Rank</th><th>Team</th><th>Record</th><th>Dynasty Total</th><th>Starters Dyn</th>
          </tr></thead><tbody></tbody></table>
        </div>
      </div>
      <div class="card">
        <h2>League — Win-Now Totals (starters)</h2>
        <div class="table-wrap">
          <table id="t-win-standings"><thead><tr>
            <th>Rank</th><th>Team</th><th>Record</th><th>Starters Win-Now</th><th>Full Roster</th>
          </tr></thead><tbody></tbody></table>
        </div>
      </div>
    </div>
  </section>

  <!-- RANKINGS -->
  <section id="tab-rankings" class="tab-panel hidden">
    <div class="card">
      <div class="controls">
        <div class="toggle" id="rank-view-toggle">
          <button class="active" data-view="dynasty">Dynasty</button>
          <button data-view="winnow">Win Now</button>
          <button data-view="split">Split (both)</button>
        </div>
        <input type="text" id="rank-search" placeholder="Search player, team…"/>
        <select id="rank-owner">
          <option value="">All owners</option>
        </select>
        <div class="filter-chips" id="rank-pos-chips"></div>
        <label class="checkbox-wrap"><input type="checkbox" id="rank-starters-only"/> Starters only</label>
        <label class="checkbox-wrap"><input type="checkbox" id="rank-mine-only"/> My players only</label>
        <label class="checkbox-wrap"><input type="checkbox" id="rank-fa-only"/> Free agents only</label>
      </div>
      <div class="table-wrap">
        <table id="t-rankings"><thead id="th-rankings"></thead><tbody></tbody></table>
      </div>
      <div class="legend">
        <span><span class="starter-badge"></span> Starter</span>
        <span><span class="starter-badge taxi-badge"></span> Taxi</span>
        <span><span class="starter-badge reserve-badge"></span> Reserve/IR</span>
        <span id="rank-count"></span>
      </div>
    </div>
  </section>

  <!-- TRENDS -->
  <section id="tab-trends" class="tab-panel hidden">
    <div class="card">
      <h2>Value trend chart</h2>
      <div class="controls">
        <input type="text" id="trend-search" placeholder="Add a player to chart (e.g. Jonathan Taylor)…" autocomplete="off"/>
        <div class="autocomplete" id="trend-ac"></div>
        <button id="trend-clear" style="padding:6px 12px;border:1px solid var(--line-2);background:#fff;border-radius:8px;cursor:pointer;font:inherit">Clear</button>
        <span class="muted small" id="trend-meta"></span>
      </div>
      <div id="trend-chart-wrap"><canvas id="trend-chart"></canvas></div>
      <div class="small muted" style="margin-top:8px">
        Chart tracks FantasyCalc dynasty value over time, based on rankings snapshots taken after each platform refresh.
        More data points = smoother curves. Check back weekly.
      </div>
    </div>

    <div class="grid grid-2">
      <div class="rf-side">
        <h3>📈 Top Risers (30-day)</h3>
        <div id="risers-list"></div>
      </div>
      <div class="rf-side">
        <h3>📉 Top Fallers (30-day)</h3>
        <div id="fallers-list"></div>
      </div>
    </div>

    <div class="card" style="margin-top:14px">
      <h2>My team — hottest / coldest assets (30-day)</h2>
      <div class="grid grid-2">
        <div>
          <h3 class="trend-up">My Risers</h3>
          <div id="my-risers"></div>
        </div>
        <div>
          <h3 class="trend-dn">My Fallers</h3>
          <div id="my-fallers"></div>
        </div>
      </div>
    </div>
  </section>

  <!-- CONSTRUCTION -->
  <section id="tab-construction" class="tab-panel hidden">
    <div class="card">
      <h2>Roster Construction — league posture map</h2>
      <div class="small muted" style="margin-bottom:10px">
        Each team is scored on two axes: a <strong>Win-Now Index</strong> (percentile of starting lineup Win-Now
        points) and a <strong>Rebuild Index</strong> (percentile of dynasty value in players 24 and younger). Posture
        is classified from those two scores plus full-roster depth.
      </div>
      <div class="construction-grid" id="construction-grid"></div>
    </div>

    <div class="card">
      <h2>Positional strength matrix</h2>
      <div class="small muted" style="margin-bottom:8px">
        League rank (1 = best) of each team's starter-weighted Win-Now points at each offensive position.
        Green = top-3 at that position, red = bottom-3.
      </div>
      <div class="table-wrap">
        <table id="t-pos-matrix"><thead></thead><tbody></tbody></table>
      </div>
    </div>
  </section>

  <!-- DRAFT PICKS -->
  <section id="tab-picks" class="tab-panel hidden">
    <div class="card">
      <h2>Future rookie draft pick ownership</h2>
      <div class="controls">
        <div class="toggle" id="picks-season-toggle"></div>
        <select id="picks-owner">
          <option value="">All owners</option>
        </select>
        <label class="checkbox-wrap"><input type="checkbox" id="picks-traded-only"/> Traded picks only</label>
      </div>
      <div class="small muted" style="margin-bottom:8px">
        Rows = original owner. Columns = round. Cell shows the current owner of that pick. Green = still owned,
        red = sent away, blue = acquired. Pick values are <em>estimated</em> from FantasyCalc median pick prices
        (not slot-specific since early-season ordering isn't set yet).
      </div>
      <div class="table-wrap">
        <table id="t-picks-matrix" class="picks-matrix"><thead></thead><tbody></tbody></table>
      </div>
    </div>

    <div class="card">
      <h2>Pick stock ranking</h2>
      <div class="small muted" style="margin-bottom:8px">
        Total count and estimated trade value of picks each team currently owns across all future seasons.
      </div>
      <div class="table-wrap">
        <table id="t-pick-stock"><thead><tr>
          <th>Rank</th><th>Team</th><th>Record</th><th>Total Picks</th><th>Est. Value</th><th>Season Breakdown</th>
        </tr></thead><tbody></tbody></table>
      </div>
    </div>
  </section>

  <!-- TRADE CALC -->
  <section id="tab-trade" class="tab-panel hidden">
    <div class="card">
      <div class="controls">
        <span class="posture"><strong>My team posture:</strong>
          <div class="toggle" id="posture-toggle">
            <button data-p="balanced" class="active">Balanced (50/50)</button>
            <button data-p="contender">Contender (25/75 Win Now)</button>
            <button data-p="rebuild">Rebuild (80/20 Dynasty)</button>
          </div>
        </span>
        <button id="clear-trade" style="margin-left:auto;padding:6px 12px;border:1px solid var(--line-2);background:#fff;border-radius:8px;cursor:pointer;font:inherit">Clear</button>
      </div>

      <div class="trade-sides">
        <div class="trade-side mine">
          <div class="side-header"><h3>I send (my side)</h3><span class="side-total" id="a-total">0</span></div>
          <div class="asset-list" id="a-list"></div>
          <div class="trade-add">
            <input type="text" id="a-add" placeholder="Add player or pick…" autocomplete="off"/>
            <div class="autocomplete" id="a-ac"></div>
          </div>
          <div class="small muted" style="margin-top:8px">
            Dynasty: <span id="a-dyn">0</span> · Win-Now: <span id="a-win">0</span>
          </div>
        </div>
        <div class="trade-arrow">⇄</div>
        <div class="trade-side">
          <div class="side-header"><h3>I receive</h3><span class="side-total" id="b-total">0</span></div>
          <div class="asset-list" id="b-list"></div>
          <div class="trade-add">
            <input type="text" id="b-add" placeholder="Add player or pick…" autocomplete="off"/>
            <div class="autocomplete" id="b-ac"></div>
          </div>
          <div class="small muted" style="margin-top:8px">
            Dynasty: <span id="b-dyn">0</span> · Win-Now: <span id="b-win">0</span>
          </div>
        </div>
      </div>

      <div class="trade-verdict even" id="verdict">
        <span id="verdict-text">Add players or picks to both sides to evaluate.</span>
        <span id="verdict-delta"></span>
      </div>

      <div class="small muted" style="margin-top:10px">
        Values use FantasyCalc dynasty & redraft values (updated from the last refresh). The posture toggle
        re-weights both sides of the deal from <em>your</em> perspective — use Contender if you're pushing for
        a __SEASON__ championship, Rebuild if you're trading for future picks and youth.
      </div>
    </div>
  </section>

  <!-- MY TEAM -->
  <section id="tab-myteam" class="tab-panel hidden">
    <div class="card" id="myteam-news-card">
      <h2>📰 Team / Player News <span class="muted small" id="myteam-news-meta"></span></h2>
      <div id="myteam-news"></div>
    </div>
    <div class="card">
      <div class="controls">
        <div class="toggle" id="myteam-view">
          <button class="active" data-view="dynasty">Sort by Dynasty</button>
          <button data-view="winnow">Sort by Win Now</button>
          <button data-view="gap">Sort by Delta (Win-Now − Dynasty)</button>
        </div>
      </div>
      <div class="grid grid-3">
        <div id="myteam-starters"></div>
        <div id="myteam-bench"></div>
        <div id="myteam-taxiIR"></div>
      </div>
    </div>
  </section>

  <!-- ROOKIES -->
  <section id="tab-rookies" class="tab-panel hidden">
    <div class="card">
      <h2>__NEXT_DRAFT__ Rookies & Recent Draftees</h2>
      <div class="small muted" style="margin-bottom:8px">
        <strong>Incoming class</strong> = players with 0 NFL years experience (__NEXT_DRAFT__ NFL draft class — pre-rookie-draft, almost all FA).
        <strong>2nd-year</strong> = last year's dynasty rookie draftees, currently rostered.
        Values are FantasyCalc dynasty.
      </div>
      <div class="controls">
        <div class="toggle" id="rookie-toggle">
          <button class="active" data-view="incoming">Incoming (yrs 0)</button>
          <button data-view="second_year">2nd-year (yrs 1)</button>
          <button data-view="picks">__NEXT_DRAFT__ Pick Values</button>
        </div>
        <input type="text" id="rookie-search" placeholder="Search…"/>
        <div class="filter-chips" id="rookie-pos-chips"></div>
      </div>
      <div class="table-wrap">
        <table id="t-rookies"><thead id="th-rookies"></thead><tbody></tbody></table>
      </div>
    </div>

    <div class="card" style="margin-top:14px">
      <h2>Rookie Capital by Owner</h2>
      <div class="small muted" style="margin-bottom:8px">
        Combines dynasty value of rostered 2nd-year players (last dynasty rookie draft class) plus
        the FantasyCalc dynasty value of __NEXT_DRAFT__ rookie picks each owner currently holds.
      </div>
      <div class="table-wrap">
        <table id="t-rookie-capital"><thead><tr>
          <th>Owner</th><th>2nd-yr Players</th><th>Young Value</th>
          <th>__NEXT_DRAFT__ Picks</th><th>Pick Value</th><th>Total Capital</th>
        </tr></thead><tbody></tbody></table>
      </div>
    </div>
  </section>

  <!-- NFL TEAMS -->
  <section id="tab-nflteams" class="tab-panel hidden">
    <div class="card">
      <h2 id="nflteams-h">NFL Team Offensive Context — <span id="nflteams-season">—</span> regular season</h2>
      <div class="small muted" style="margin-bottom:8px">
        Per-game volume + scoring rates, ranked 1–32. Use this to read how an offense supports its
        skill players (e.g., a top-5 pass volume team is good news for a borderline WR2).
        Click a column to sort.
      </div>
      <div class="controls">
        <input type="text" id="nflteams-search" placeholder="Search team…"/>
      </div>
      <div class="table-wrap">
        <table id="t-nflteams"><thead><tr>
          <th data-sort="team">Team</th>
          <th data-sort="games" class="num">G</th>
          <th data-sort="plays_per_game" class="num">Plays/G</th>
          <th data-sort="pass_per_game" class="num">Pass Att/G</th>
          <th data-sort="rush_per_game" class="num">Rush Att/G</th>
          <th data-sort="pass_pct" class="num">Pass%</th>
          <th data-sort="pass_yards_pg" class="num">Pass Yds/G</th>
          <th data-sort="rush_yards_pg" class="num">Rush Yds/G</th>
          <th data-sort="total_tds_pg" class="num">TD/G</th>
          <th data-sort="fpts_ppr_pg" class="num">PPR/G</th>
          <th>Tags</th>
        </tr></thead><tbody></tbody></table>
      </div>
      <div class="small muted" style="margin-top:8px">
        Numbers in superscript on each cell = league rank (1 = best).
      </div>
    </div>
  </section>

  <!-- SNAPS & OPPORTUNITY -->
  <section id="tab-snaps" class="tab-panel hidden">
    <div class="card">
      <h2>Snap Share & Opportunity</h2>
      <div class="small muted" style="margin-bottom:8px">
        Last <span id="snaps-recent">8</span> games of <span id="snaps-snapseason">—</span> snap%
        for every offensive player rostered in the league. The <strong>Δ4v4</strong> column compares the most recent
        4 games to the prior 4 — a strong positive number means workload is trending up.
      </div>
      <div class="controls">
        <select id="snaps-owner"><option value="">All owners</option></select>
        <div class="filter-chips" id="snaps-pos-chips"></div>
        <label class="checkbox-wrap"><input type="checkbox" id="snaps-mine-only"/> My players only</label>
        <input type="text" id="snaps-search" placeholder="Search player…"/>
      </div>
      <div class="table-wrap">
        <table id="t-snaps"><thead><tr>
          <th>Player</th><th>Pos</th><th>Team</th><th>Owner</th>
          <th class="num">Snap Avg %</th>
          <th class="num">Δ4v4</th>
          <th class="num">Slope</th>
          <th class="num">Tgt/G</th>
          <th class="num">Car/G</th>
          <th>Trend</th>
        </tr></thead><tbody></tbody></table>
      </div>
      <div class="small muted" style="margin-top:8px">
        Snap data from the <span id="snaps-snapseason-2">—</span> NFL season; targets/carries from
        the most recent fully-loaded weekly stats season (<span id="snaps-statseason">—</span>).
        The trend chip is a sparkline of snap% across the displayed window.
      </div>
    </div>
  </section>

  <!-- INJURIES -->
  <section id="tab-injuries" class="tab-panel hidden">
    <div class="card">
      <h2>Injury Wire</h2>
      <div class="small muted" style="margin-bottom:8px">
        Pulled directly from Sleeper's player file <code>injury_status</code>. In the offseason this list
        will be sparse — most carry-over designations are PUP/IR/Sus from the prior season. During the
        regular season this becomes the league-wide injury report, sorted by severity.
      </div>
      <div class="controls">
        <select id="inj-owner"><option value="">All owners</option></select>
        <div class="filter-chips" id="inj-status-chips"></div>
        <label class="checkbox-wrap"><input type="checkbox" id="inj-mine-only"/> My players only</label>
        <label class="checkbox-wrap"><input type="checkbox" id="inj-rostered-only" checked/> Rostered only</label>
      </div>
      <div class="table-wrap">
        <table id="t-injuries"><thead><tr>
          <th>Player</th><th>Pos</th><th>NFL Team</th><th>Owner</th>
          <th>Status</th><th>Severity</th><th class="num">FC Dyn</th>
        </tr></thead><tbody></tbody></table>
      </div>
      <div id="inj-empty" class="small muted hidden" style="padding:14px 0">
        No active injury designations on rostered players right now. Check back when training camp opens.
      </div>
    </div>

    <div class="card" style="margin-top:14px">
      <h2>Owner Injury Counts</h2>
      <div class="table-wrap">
        <table id="t-injury-counts"><thead><tr>
          <th>Owner</th><th class="num">Total</th><th class="num">Starters Out</th><th class="num">High-Value (≥3000 dyn)</th>
        </tr></thead><tbody></tbody></table>
      </div>
    </div>
  </section>

  <!-- STRENGTH OF SCHEDULE -->
  <section id="tab-sos" class="tab-panel hidden">
    <div class="card">
      <h2>__NEXT_DRAFT__ Strength of Schedule (proxy)</h2>
      <div class="small muted" style="margin-bottom:8px">
        <strong>How this works:</strong> defense-vs-position points-per-game allowed in <strong>__DVP_SEASON__</strong>
        rank each NFL team 1–32 per position (1 = toughest D). Each NFL team's __SEASON__ schedule is then averaged
        through that rank, giving an opponent-strength proxy per position.
        <em>The __NEXT_DRAFT__ NFL schedule typically releases mid-May; this view will auto-update once it's available.</em>
        <br>Higher avg-rank ⇒ <span class="delta-up">easier schedule</span>.
        Lower avg-rank ⇒ <span class="delta-dn">tougher schedule</span>.
      </div>
      <div class="controls">
        <div class="toggle" id="sos-view">
          <button class="active" data-view="rosters">Huddlepuffers Rosters</button>
          <button data-view="teams">All NFL Teams</button>
          <button data-view="dvp">DvP — __DVP_SEASON__ Defense Rankings</button>
        </div>
        <select id="sos-pos">
          <option value="ALL">All positions</option>
          <option value="QB">QB</option>
          <option value="RB">RB</option>
          <option value="WR">WR</option>
          <option value="TE">TE</option>
        </select>
      </div>
      <div class="table-wrap">
        <table id="t-sos"><thead id="th-sos"></thead><tbody></tbody></table>
      </div>
    </div>
  </section>

  <!-- ABOUT -->
  <section id="tab-about" class="tab-panel hidden">
    <div class="card">
      <h2>Ranking Methodology</h2>
      <div class="methodology" id="methodology"></div>
      <h3 style="margin-top:16px">Columns explained</h3>
      <div class="methodology">
        <strong>Dynasty Score</strong> — 0–100 score per position. Higher = more valuable long-term asset.<br>
        <strong>Win-Now Score</strong> — 0–100 score per position. Higher = more likely to score points <em>this year</em>.<br>
        <strong>Δ (Win-Now − Dynasty)</strong> — positive values are "sell-high" candidates (aging vets producing now);
        negative values are "buy-low" candidates (young players not yet producing).<br>
        <strong>Recent PPG</strong> — average PPR fantasy points over the last 8 games of the most recent NFL season.<br>
        <strong>Snap %</strong> — offensive snap share over the last 8 games.<br>
        <strong>Target Share</strong> — % of team targets over the last 8 games.<br>
        <strong>Trade Values</strong> — raw FantasyCalc dynasty/redraft values, used by the trade calculator.<br>
        <strong>30d trend</strong> — FantasyCalc's 30-day value change.<br>
        <strong>Win-Now Index / Rebuild Index</strong> — per-team percentile scores used on the Construction tab.
      </div>
      <h3 style="margin-top:16px">Data sources & freshness</h3>
      <div class="methodology" id="sources"></div>
      <h3 style="margin-top:16px">Caveats</h3>
      <div class="methodology">
        IDP players (DL/LB/DB) don't appear in FantasyCalc and have no offensive fantasy points in our stat feed,
        so their scores default to 50/50. Rankings for offensive players (QB/RB/WR/TE) are the meaningful ones.
        Kickers are included but are effectively replaceable — treat their scores as directional only.
        Trend chart data accumulates each refresh; with only a handful of snapshots, early curves will look flat.
        Future-pick values are estimated from round medians, not slot-specific projections.
      </div>
    </div>
  </section>
</div>

<div id="hp-loading" style="position:fixed;top:0;left:0;right:0;bottom:0;display:flex;align-items:center;justify-content:center;background:#f6f7fb;z-index:9999;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;flex-direction:column;gap:12px;">
  <div style="font-size:14px;color:#475569;font-weight:600;">Loading Huddlepuffers dashboard…</div>
  <div id="hp-loading-detail" style="font-size:11px;color:#94a3b8;">Fetching latest rankings</div>
</div>
<script>window.__DATA_VERSION__ = "__DATA_VERSION_PLACEHOLDER__";</script>
<script>
(async function(){
  // Fetch rankings_data.json at runtime instead of embedding it inline.
  // Cache-buster: ?v=<generated_at> — browser re-downloads only when the
  // build emits a new timestamp, otherwise serves from cache.
  const v = window.__DATA_VERSION__ ? "?v=" + encodeURIComponent(window.__DATA_VERSION__) : "";
  let DATA;
  try {
    const resp = await fetch("rankings_data.json" + v);
    if (!resp.ok) throw new Error("HTTP " + resp.status + " loading rankings_data.json");
    DATA = await resp.json();
  } catch (err) {
    const loader = document.getElementById("hp-loading");
    if (loader) {
      loader.innerHTML = '<div style="text-align:center;font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;color:#dc2626;max-width:500px;padding:24px;">' +
        '<h2 style="margin:0 0 8px;font-size:18px;">Failed to load dashboard data</h2>' +
        '<p style="margin:0 0 8px;font-size:13px;color:#475569;">' + String(err).replace(/[<>&]/g, c => ({"<":"&lt;",">":"&gt;","&":"&amp;"}[c])) + '</p>' +
        '<p style="margin:0;font-size:12px;color:#94a3b8;">Try a hard refresh (Cmd+Shift+R / Ctrl+Shift+R).</p>' +
      '</div>';
    }
    return;
  }
  // Hide the loading overlay once data is in hand and rendering can proceed.
  const _loader = document.getElementById("hp-loading");
  if (_loader) _loader.remove();

  const PLAYERS = DATA.players;
  const PICKS = DATA.picks;
  const TEAMS = DATA.teams;
  const EXTRAS = DATA.extras || {};
  const FMT = new Intl.NumberFormat('en-US');

  // ============================================================
  //   "Logged-in" team identity — runtime, not baked
  // ============================================================
  const STORAGE_KEY = 'huddlepuffers_roster_id';
  const DEFAULT_ROSTER_ID = 5; // Nick (the dashboard owner) — fallback only

  function readSavedRosterId() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const n = raw == null ? null : parseInt(raw, 10);
      if (Number.isFinite(n) && TEAMS.some(t => t.roster_id === n)) return n;
    } catch (e) { /* localStorage may be blocked — fall through to default */ }
    return DEFAULT_ROSTER_ID;
  }

  // Mutable so they can be re-derived when the user switches teams.
  let MY_ROSTER_ID = readSavedRosterId();
  let me = TEAMS.find(t => t.roster_id === MY_ROSTER_ID) || TEAMS[0];
  let ME = me ? me.owner_id : DATA.meta.my_user_id;

  function isMe(rosterId) { return rosterId === MY_ROSTER_ID; }

  // Render functions register here so the team-switcher can re-run them all.
  const RENDERERS = [];
  function registerRenderer(fn) { RENDERERS.push(fn); }

  // --- Header meta ---
  document.getElementById('title').textContent = DATA.meta.league_name + ' — Dynasty Platform';
  function renderHeaderSubtitle() {
    document.getElementById('subtitle').textContent =
      (me ? `${me.owner_name} · ${me.wins}-${me.losses}` : '') +
      `  ·  ${DATA.meta.season} season  ·  NFL stats through ${DATA.meta.latest_nfl_season} Week ${DATA.meta.latest_nfl_week}`;
  }
  renderHeaderSubtitle();
  document.getElementById('refresh-meta').textContent =
    'Refreshed ' + new Date(DATA.meta.generated_at).toLocaleString() +
    '  ·  ' + PLAYERS.length + ' players · ' + PICKS.length + ' picks';

  // --- Team selector dropdown ---
  (function initTeamSelector(){
    const sel = document.getElementById('team-selector');
    const sorted = [...TEAMS].sort((a, b) =>
      (a.owner_name || '').localeCompare(b.owner_name || ''));
    sorted.forEach(t => {
      const opt = document.createElement('option');
      opt.value = String(t.roster_id);
      opt.textContent = t.owner_name || `Team ${t.roster_id}`;
      if (t.roster_id === MY_ROSTER_ID) opt.selected = true;
      sel.appendChild(opt);
    });
    sel.addEventListener('change', e => {
      const newId = parseInt(e.target.value, 10);
      if (!Number.isFinite(newId)) return;
      MY_ROSTER_ID = newId;
      me = TEAMS.find(t => t.roster_id === MY_ROSTER_ID) || TEAMS[0];
      ME = me ? me.owner_id : ME;
      try { localStorage.setItem(STORAGE_KEY, String(MY_ROSTER_ID)); } catch (_) {}
      renderHeaderSubtitle();
      RENDERERS.forEach(fn => { try { fn(); } catch (err) { console.error(err); } });
    });
  })();

  // --- Tabs ---
  const tabButtons = document.querySelectorAll('#tabs button');
  tabButtons.forEach(b => b.addEventListener('click', () => {
    tabButtons.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.getElementById('tab-' + b.dataset.tab).classList.remove('hidden');
    // Chart.js sometimes needs a resize when its container becomes visible
    if (b.dataset.tab === 'trends' && window._trendChart) window._trendChart.resize();
  }));

  // --- Overview ---
  function renderOverview() {
    if (!me) return;
    document.getElementById('o-record').textContent = `${me.wins}-${me.losses}`;
    document.getElementById('o-record-sub').textContent =
      `PF ${Math.round(me.fpts)}  ·  PA ${Math.round(me.fpts_against)}`;

    const dynSorted = [...TEAMS].sort((a,b) => (b.dynasty_total||0) - (a.dynasty_total||0));
    const winSorted = [...TEAMS].sort((a,b) => (b.starters_winnow||0) - (a.starters_winnow||0));
    const dynRank = dynSorted.findIndex(t => t.owner_id === ME) + 1;
    const startRank = [...TEAMS].sort((a,b)=>(b.starters_winnow||0)-(a.starters_winnow||0)).findIndex(t=>t.owner_id===ME)+1;

    document.getElementById('o-dyn').textContent = FMT.format(Math.round(me.dynasty_total||0));
    document.getElementById('o-dyn-rank').textContent = `#${dynRank} of ${TEAMS.length} league-wide`;
    document.getElementById('o-win').textContent = FMT.format(Math.round(me.winnow_total||0));
    document.getElementById('o-win-rank').textContent = `full roster`;
    document.getElementById('o-starters').textContent = FMT.format(Math.round(me.starters_winnow||0));
    document.getElementById('o-starters-rank').textContent = `#${startRank} of ${TEAMS.length}`;

    const dynTbody = document.querySelector('#t-dyn-standings tbody');
    dynTbody.innerHTML = '';
    dynSorted.forEach((t, i) => {
      const tr = document.createElement('tr');
      if (t.owner_id === ME) tr.classList.add('me-row');
      tr.innerHTML = `<td><span class="rank-badge">${i+1}</span></td>
        <td><strong>${t.owner_name||'?'}</strong></td>
        <td class="muted">${t.wins}-${t.losses}</td>
        <td><strong>${FMT.format(Math.round(t.dynasty_total||0))}</strong></td>
        <td class="muted">${FMT.format(Math.round(t.starters_dynasty||0))}</td>`;
      dynTbody.appendChild(tr);
    });
    const winTbody = document.querySelector('#t-win-standings tbody');
    winTbody.innerHTML = '';
    winSorted.forEach((t, i) => {
      const tr = document.createElement('tr');
      if (t.owner_id === ME) tr.classList.add('me-row');
      tr.innerHTML = `<td><span class="rank-badge">${i+1}</span></td>
        <td><strong>${t.owner_name||'?'}</strong></td>
        <td class="muted">${t.wins}-${t.losses}</td>
        <td><strong>${FMT.format(Math.round(t.starters_winnow||0))}</strong></td>
        <td class="muted">${FMT.format(Math.round(t.winnow_total||0))}</td>`;
      winTbody.appendChild(tr);
    });
  }
  renderOverview();
  registerRenderer(renderOverview);

  // --- Rankings table ---
  const POS_ORDER = ['ALL','QB','RB','WR','TE','K','DEF','DL','LB','DB','PICK'];
  const posSet = new Set(PLAYERS.map(p => p.position).filter(Boolean));
  const availablePos = POS_ORDER.filter(p => p === 'ALL' || posSet.has(p) || p === 'PICK');
  const chipEl = document.getElementById('rank-pos-chips');
  availablePos.forEach(p => {
    const b = document.createElement('button');
    b.textContent = p;
    b.dataset.pos = p;
    if (p === 'ALL') b.classList.add('active');
    b.addEventListener('click', () => {
      chipEl.querySelectorAll('button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      state.pos = p;
      renderRankings();
    });
    chipEl.appendChild(b);
  });

  const ownerSel = document.getElementById('rank-owner');
  const owners = [...new Set(PLAYERS.filter(p=>p.owner_name).map(p => p.owner_name))].sort();
  owners.forEach(o => {
    const opt = document.createElement('option'); opt.value = o; opt.textContent = o;
    ownerSel.appendChild(opt);
  });

  const state = {
    view: 'dynasty', pos: 'ALL', search: '', owner: '',
    startersOnly: false, mineOnly: false, faOnly: false,
    sortCol: 'dynasty_score', sortDir: 'desc'
  };

  const COLS_DYN = [
    {k:'dynasty_overall_rank', t:'Rk', w:40, fmt:(v)=>v?`<span class="rank-badge">${v}</span>`:''},
    {k:'full_name', t:'Player', w:160, fmt:(v,r)=>playerCell(r)},
    {k:'position', t:'Pos', w:50, fmt:(v,r)=>`<span class="pos pos-${v}">${v}</span>${posRankTag(r,'dyn')}`},
    {k:'team', t:'Tm', w:40, fmt:(v)=>v||'<span class="muted">—</span>'},
    {k:'age', t:'Age', w:40, fmt:(v)=>v!=null?v:''},
    {k:'dynasty_score', t:'Dynasty', w:120, fmt:(v)=>scoreBar(v,'warm')},
    {k:'winnow_score', t:'Win Now', w:120, fmt:(v)=>scoreBar(v,'')},
    {k:'delta', t:'Δ', w:50, fmt:(v)=>deltaFmt(v)},
    {k:'trend_30day', t:'30d', w:55, fmt:(v)=>trendFmt(v)},
    {k:'recent_ppg', t:'Last-8 PPG', w:85, fmt:(v)=>v?v.toFixed(1):'<span class="muted">—</span>'},
    {k:'owner_name', t:'Owner', w:110, fmt:(v,r)=>ownerFmt(r)},
  ];
  const COLS_WIN = [
    {k:'winnow_overall_rank', t:'Rk', w:40, fmt:(v)=>v?`<span class="rank-badge">${v}</span>`:''},
    {k:'full_name', t:'Player', w:160, fmt:(v,r)=>playerCell(r)},
    {k:'position', t:'Pos', w:50, fmt:(v,r)=>`<span class="pos pos-${v}">${v}</span>${posRankTag(r,'win')}`},
    {k:'team', t:'Tm', w:40, fmt:(v)=>v||'<span class="muted">—</span>'},
    {k:'age', t:'Age', w:40, fmt:(v)=>v!=null?v:''},
    {k:'winnow_score', t:'Win Now', w:120, fmt:(v)=>scoreBar(v,'')},
    {k:'dynasty_score', t:'Dynasty', w:120, fmt:(v)=>scoreBar(v,'warm')},
    {k:'recent_ppg', t:'Last-8 PPG', w:85, fmt:(v)=>v?v.toFixed(1):'<span class="muted">—</span>'},
    {k:'recent_off_snap_pct', t:'Snap%', w:60, fmt:(v)=>v?(v*100).toFixed(0)+'%':'<span class="muted">—</span>'},
    {k:'recent_tgt_share', t:'Tgt%', w:55, fmt:(v)=>v?(v*100).toFixed(0)+'%':'<span class="muted">—</span>'},
    {k:'trend_30day', t:'30d', w:55, fmt:(v)=>trendFmt(v)},
    {k:'owner_name', t:'Owner', w:110, fmt:(v,r)=>ownerFmt(r)},
  ];
  const COLS_SPLIT = [
    {k:'full_name', t:'Player', w:160, fmt:(v,r)=>playerCell(r)},
    {k:'position', t:'Pos', w:50, fmt:(v)=>`<span class="pos pos-${v}">${v}</span>`},
    {k:'team', t:'Tm', w:40, fmt:(v)=>v||'<span class="muted">—</span>'},
    {k:'age', t:'Age', w:40, fmt:(v)=>v!=null?v:''},
    {k:'dynasty_score', t:'Dynasty', w:120, fmt:(v)=>scoreBar(v,'warm')},
    {k:'dynasty_pos_rank', t:'Dyn #', w:55, fmt:(v)=>v?`<span class="rank-badge">${v}</span>`:''},
    {k:'winnow_score', t:'Win Now', w:120, fmt:(v)=>scoreBar(v,'')},
    {k:'winnow_pos_rank', t:'Win #', w:55, fmt:(v)=>v?`<span class="rank-badge">${v}</span>`:''},
    {k:'delta', t:'Δ', w:50, fmt:(v)=>deltaFmt(v)},
    {k:'owner_name', t:'Owner', w:110, fmt:(v,r)=>ownerFmt(r)},
  ];

  function scoreBar(v, cls) {
    if (v == null) return '<span class="muted">—</span>';
    return `<span>${v.toFixed(1)}</span><span class="score-bar ${cls}"><span style="width:${Math.max(0,Math.min(100,v))}%"></span></span>`;
  }
  function deltaFmt(v) {
    if (v == null || isNaN(v)) return '';
    const cls = v > 4 ? 'trend-up' : v < -4 ? 'trend-dn' : 'muted';
    const sign = v > 0 ? '+' : '';
    return `<span class="${cls}">${sign}${v.toFixed(1)}</span>`;
  }
  function trendFmt(v) {
    if (v == null || isNaN(v) || v === 0) return '<span class="muted">—</span>';
    const cls = v > 0 ? 'trend-up' : 'trend-dn';
    const sign = v > 0 ? '+' : '';
    return `<span class="${cls}">${sign}${FMT.format(Math.round(v))}</span>`;
  }
  function playerCell(r) {
    const badges = [];
    if (r.is_starter) badges.push('<span class="starter-badge" title="Starter"></span>');
    if (r.is_taxi) badges.push('<span class="starter-badge taxi-badge" title="Taxi"></span>');
    if (r.is_reserve) badges.push('<span class="starter-badge reserve-badge" title="Reserve/IR"></span>');
    return `${badges.join('')}<strong>${r.full_name||'?'}</strong>`;
  }
  function ownerFmt(r) {
    if (!r.owner_name) return '<span class="muted">FA</span>';
    if (r.owner_id === ME) return `<strong style="color:var(--me)">${r.owner_name}</strong>`;
    return r.owner_name;
  }
  function posRankTag(r, kind) {
    const k = kind === 'dyn' ? 'dynasty_pos_rank' : 'winnow_pos_rank';
    return r[k] ? `<span class="muted small" style="margin-left:4px">#${r[k]}</span>` : '';
  }

  function cols() {
    if (state.view === 'dynasty') return COLS_DYN;
    if (state.view === 'winnow') return COLS_WIN;
    return COLS_SPLIT;
  }

  function renderHeaderRow() {
    const tr = document.createElement('tr');
    cols().forEach(c => {
      const th = document.createElement('th');
      th.style.width = c.w + 'px';
      th.innerHTML = `${c.t} <span class="arrow">${state.sortCol === c.k ? (state.sortDir==='asc'?'▲':'▼') : '▾'}</span>`;
      if (state.sortCol === c.k) th.classList.add('sorted');
      th.addEventListener('click', () => {
        if (state.sortCol === c.k) state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
        else { state.sortCol = c.k; state.sortDir = 'desc'; }
        renderRankings();
      });
      tr.appendChild(th);
    });
    const thead = document.getElementById('th-rankings');
    thead.innerHTML = ''; thead.appendChild(tr);
  }

  function renderRankings() {
    renderHeaderRow();
    let rows = PLAYERS.slice();
    rows.forEach(r => { r.delta = (r.winnow_score != null && r.dynasty_score != null) ? +(r.winnow_score - r.dynasty_score).toFixed(1) : null; });

    if (state.pos === 'PICK') rows = PICKS.map(p => ({...p, dynasty_score: null, winnow_score: null}));
    else if (state.pos !== 'ALL') rows = rows.filter(r => r.position === state.pos);
    if (state.search) {
      const s = state.search.toLowerCase();
      rows = rows.filter(r => (r.full_name||'').toLowerCase().includes(s) || (r.team||'').toLowerCase().includes(s));
    }
    if (state.owner) rows = rows.filter(r => r.owner_name === state.owner);
    if (state.mineOnly) rows = rows.filter(r => r.owner_id === ME);
    if (state.startersOnly) rows = rows.filter(r => r.is_starter);
    if (state.faOnly) rows = rows.filter(r => !r.rostered);

    rows.sort((a,b) => {
      const av = a[state.sortCol], bv = b[state.sortCol];
      if (av == null && bv == null) return 0;
      if (av == null) return 1; if (bv == null) return -1;
      if (typeof av === 'string') {
        const cmp = av.localeCompare(bv);
        return state.sortDir === 'asc' ? cmp : -cmp;
      }
      return state.sortDir === 'asc' ? av - bv : bv - av;
    });

    const tbody = document.querySelector('#t-rankings tbody');
    tbody.innerHTML = '';
    const frag = document.createDocumentFragment();
    rows.forEach(r => {
      const tr = document.createElement('tr');
      if (r.owner_id === ME) tr.classList.add('me-row');
      cols().forEach(c => {
        const td = document.createElement('td');
        td.innerHTML = c.fmt(r[c.k], r);
        tr.appendChild(td);
      });
      frag.appendChild(tr);
    });
    tbody.appendChild(frag);
    document.getElementById('rank-count').textContent = `${rows.length} shown`;
  }

  document.querySelectorAll('#rank-view-toggle button').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('#rank-view-toggle button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      state.view = b.dataset.view;
      state.sortCol = state.view === 'winnow' ? 'winnow_score' : 'dynasty_score';
      state.sortDir = 'desc';
      renderRankings();
    });
  });
  document.getElementById('rank-search').addEventListener('input', e => { state.search = e.target.value; renderRankings(); });
  document.getElementById('rank-owner').addEventListener('change', e => { state.owner = e.target.value; renderRankings(); });
  document.getElementById('rank-starters-only').addEventListener('change', e => { state.startersOnly = e.target.checked; renderRankings(); });
  document.getElementById('rank-mine-only').addEventListener('change', e => { state.mineOnly = e.target.checked; renderRankings(); });
  document.getElementById('rank-fa-only').addEventListener('change', e => { state.faOnly = e.target.checked; renderRankings(); });
  renderRankings();
  registerRenderer(renderRankings);

  // ============================================================
  //   TRENDS TAB
  // ============================================================
  // history shape: { snapshot_dates: [...], by_player: { pid: [ {date, dyn, red, ...}, ... ] } }
  const HISTORY_RAW = EXTRAS.history || {};
  const HISTORY = HISTORY_RAW.by_player || {};
  const RF = EXTRAS.risers_fallers || {risers:[], fallers:[]};

  // Build a pid→{name,position} lookup from players+picks since history doesn't carry names
  const NAME_LOOKUP = {};
  PLAYERS.forEach(p => { NAME_LOOKUP[p.player_id] = {name: p.full_name, position: p.position}; });
  PICKS.forEach(p =>   { NAME_LOOKUP[p.player_id] = {name: p.full_name, position: 'PICK'}; });

  function histName(pid)  { return (NAME_LOOKUP[pid]||{}).name || `Player ${pid}`; }
  function histPos(pid)   { return (NAME_LOOKUP[pid]||{}).position || '—'; }
  function histPoints(pid){ return Array.isArray(HISTORY[pid]) ? HISTORY[pid] : []; }

  const ALL_DATES = (() => {
    if (Array.isArray(HISTORY_RAW.snapshot_dates) && HISTORY_RAW.snapshot_dates.length)
      return [...HISTORY_RAW.snapshot_dates].sort();
    const s = new Set();
    for (const pid in HISTORY) for (const pt of histPoints(pid)) s.add(pt.date);
    return [...s].sort();
  })();

  const COLORS = ['#2563eb', '#dc2626', '#16a34a', '#f59e0b', '#7c3aed',
                  '#0ea5e9', '#db2777', '#65a30d', '#ea580c', '#0891b2'];
  let trendSeries = []; // {pid, name, data: [{x:date, y:value}]}
  let trendChart = null;

  function initTrendChart() {
    const ctx = document.getElementById('trend-chart').getContext('2d');
    trendChart = new Chart(ctx, {
      type: 'line',
      data: { labels: ALL_DATES, datasets: [] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'nearest', axis: 'x', intersect: false },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10 } },
          tooltip: { callbacks: {
            label: ctx => `${ctx.dataset.label}: ${FMT.format(Math.round(ctx.parsed.y))}`
          }}
        },
        scales: {
          x: { title: { display: false }, grid: { color: 'rgba(0,0,0,0.04)' } },
          y: { beginAtZero: false, title: { display: true, text: 'FantasyCalc Dynasty Value' },
               grid: { color: 'rgba(0,0,0,0.06)' } }
        }
      }
    });
    window._trendChart = trendChart;
  }

  function addTrendSeries(pid) {
    const pts = histPoints(pid);
    if (!pts.length) return;
    if (trendSeries.find(s => s.pid === pid)) return;
    const pointMap = Object.fromEntries(pts.map(p => [p.date, p.dyn]));
    const series = {
      pid, name: histName(pid),
      data: ALL_DATES.map(d => pointMap[d] ?? null)
    };
    trendSeries.push(series);
    trendChart.data.datasets = trendSeries.map((s, i) => ({
      label: s.name,
      data: s.data,
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: COLORS[i % COLORS.length] + '20',
      borderWidth: 2,
      tension: 0.25,
      pointRadius: 3,
      spanGaps: true
    }));
    trendChart.update();
    renderTrendMeta();
  }

  function removeTrendSeries(pid) {
    trendSeries = trendSeries.filter(s => s.pid !== pid);
    trendChart.data.datasets = trendSeries.map((s, i) => ({
      label: s.name,
      data: s.data,
      borderColor: COLORS[i % COLORS.length],
      backgroundColor: COLORS[i % COLORS.length] + '20',
      borderWidth: 2, tension: 0.25, pointRadius: 3, spanGaps: true
    }));
    trendChart.update();
    renderTrendMeta();
  }

  function renderTrendMeta() {
    const n = trendSeries.length;
    const tracked = Object.keys(HISTORY).length;
    document.getElementById('trend-meta').textContent =
      n === 0 ? `${tracked} players tracked · ${ALL_DATES.length} snapshot${ALL_DATES.length===1?'':'s'} (grows each refresh)`
              : `${n} player${n===1?'':'s'} charted · click legend to toggle`;
  }

  // Trend autocomplete
  (function(){
    const input = document.getElementById('trend-search');
    const ac = document.getElementById('trend-ac');
    let hl = -1;
    function render(matches) {
      ac.innerHTML = '';
      matches.forEach((m, i) => {
        const d = document.createElement('div');
        d.className = 'ac-item' + (i === hl ? ' highlight' : '');
        d.innerHTML = `<span><span class="pos pos-${m.position}">${m.position}</span> <strong>${m.name}</strong></span>
                       <span class="muted small">${FMT.format(Math.round(m.dyn||0))}</span>`;
        d.addEventListener('mousedown', (e) => { e.preventDefault(); addTrendSeries(m.pid); input.value=''; ac.classList.remove('open'); });
        ac.appendChild(d);
      });
      ac.classList.toggle('open', matches.length > 0);
    }
    input.addEventListener('input', () => {
      hl = -1;
      const q = input.value.trim().toLowerCase();
      if (!q) { ac.classList.remove('open'); return; }
      const matches = [];
      for (const pid in HISTORY) {
        const nm = histName(pid);
        if ((nm||'').toLowerCase().includes(q)) {
          const pts = histPoints(pid);
          matches.push({pid, name: nm, position: histPos(pid),
                       dyn: pts.length ? pts[pts.length-1].dyn : 0});
        }
        if (matches.length >= 14) break;
      }
      render(matches);
    });
    input.addEventListener('blur', () => setTimeout(() => ac.classList.remove('open'), 150));
    document.getElementById('trend-clear').addEventListener('click', () => {
      trendSeries = [];
      trendChart.data.datasets = [];
      trendChart.update();
      renderTrendMeta();
    });
  })();

  // Leaderboards
  function renderRfList(listEl, rows, direction) {
    listEl.innerHTML = '';
    if (!rows || !rows.length) { listEl.innerHTML = '<div class="muted small">No data.</div>'; return; }
    rows.forEach((p, i) => {
      const cls = direction === 'up' ? 'trend-up' : 'trend-dn';
      const sign = (p.trend_30day||0) > 0 ? '+' : '';
      const ownerTag = p.owner_name
        ? `<span class="muted small">· ${p.owner_name}</span>`
        : `<span class="muted small">· FA</span>`;
        const d = document.createElement('div');
      d.className = 'rf-row';
      d.innerHTML = `<span><span class="rank-badge">${i+1}</span>
        <span class="pos pos-${p.position||'K'}">${p.position||'—'}</span>
        <span class="rf-name">${p.full_name}</span>
        ${ownerTag}</span>
        <span class="rf-val ${cls}">${sign}${FMT.format(Math.round(p.trend_30day||0))}</span>`;
      d.style.cursor = 'pointer';
      d.title = 'Click to add to trend chart';
      d.addEventListener('click', () => {
        if (HISTORY[p.player_id]) {
          addTrendSeries(p.player_id);
          // jump the user back to chart
          window.scrollTo({top: document.getElementById('tab-trends').offsetTop, behavior: 'smooth'});
        }
      });
      listEl.appendChild(d);
    });
  }

  initTrendChart();
  renderRfList(document.getElementById('risers-list'), RF.risers, 'up');
  renderRfList(document.getElementById('fallers-list'), RF.fallers, 'dn');

  // My team movers
  function renderMyMovers() {
    const myRise = PLAYERS.filter(p => p.owner_id === ME && p.trend_30day && p.trend_30day > 0)
      .sort((a,b) => (b.trend_30day||0) - (a.trend_30day||0)).slice(0, 8);
    const myFall = PLAYERS.filter(p => p.owner_id === ME && p.trend_30day && p.trend_30day < 0)
      .sort((a,b) => (a.trend_30day||0) - (b.trend_30day||0)).slice(0, 8);
    renderRfList(document.getElementById('my-risers'), myRise, 'up');
    renderRfList(document.getElementById('my-fallers'), myFall, 'dn');
  }
  renderMyMovers();
  registerRenderer(renderMyMovers);
  renderTrendMeta();

  // ============================================================
  //   CONSTRUCTION TAB
  // ============================================================
  const CONSTR = EXTRAS.construction || [];

  function postureClass(p) {
    const m = {'Super-Team':'p-super', 'Contender':'p-contender', 'Rebuilder':'p-rebuilder',
               'Young & Building':'p-young', 'Balanced':'p-balanced',
               'Stuck in the Middle':'p-stuck'};
    return m[p] || 'p-balanced';
  }

  function renderConstruction() {
    const grid = document.getElementById('construction-grid');
    grid.innerHTML = '';
    // sort: me first, then by win_now_index desc
    const sorted = [...CONSTR].sort((a,b) => {
      const am = isMe(a.roster_id), bm = isMe(b.roster_id);
      if (am !== bm) return am ? -1 : 1;
      return (b.win_now_index||0) - (a.win_now_index||0);
    });
    sorted.forEach(t => {
      const mine = isMe(t.roster_id);
      const el = document.createElement('div');
      el.className = 'team-construction' + (mine ? ' me' : '');
      const strengths = (t.strengths||[]).map(p => `<span class="tag">${p}</span>`).join('');
      const weakness = (t.weaknesses||[]).map(p => `<span class="tag weak">${p}</span>`).join('');
      const wn = Math.max(0, Math.min(100, t.win_now_index||0));
      const rb = Math.max(0, Math.min(100, t.rebuild_index||0));
      el.innerHTML = `
        <div class="tc-head">
          <div>
            <div class="tc-name">${t.owner_name||'?'}${mine?' (you)':''}</div>
            <div class="tc-rec">${t.wins}-${t.losses} · avg starter age ${t.avg_starter_age?.toFixed(1)||'—'}</div>
          </div>
          <span class="posture-pill ${postureClass(t.posture)}">${t.posture}</span>
        </div>
        <div class="tc-bars">
          <div class="bar-cell winnow">
            <div class="bc-label">Win-Now Index</div>
            <div class="bc-val">${(t.win_now_index||0).toFixed(0)}</div>
            <div class="bc-bar"><span style="width:${wn}%"></span></div>
          </div>
          <div class="bar-cell rebuild">
            <div class="bc-label">Rebuild Index</div>
            <div class="bc-val">${(t.rebuild_index||0).toFixed(0)}</div>
            <div class="bc-bar"><span style="width:${rb}%"></span></div>
          </div>
        </div>
        <div class="pos-strengths">
          ${strengths || '<span class="muted small">No standout strengths</span>'}
          ${weakness}
        </div>
        <div class="rec-box"><strong>Recommendation:</strong> ${t.recommendation||''}</div>
      `;
      grid.appendChild(el);
    });
  }
  renderConstruction();
  registerRenderer(renderConstruction);

  // Positional strength matrix
  function renderPosMatrix() {
    const POSITIONS = ['QB','RB','WR','TE'];
    // For each position, rank teams by starter_winnow
    const posRanksByTeam = {};
    POSITIONS.forEach(pos => {
      const ordered = [...CONSTR].map(t => ({
        rid: t.roster_id,
        val: (t.pos_totals?.[pos]?.starter_winnow) || 0
      })).sort((a,b) => b.val - a.val);
      ordered.forEach((row, i) => {
        posRanksByTeam[row.rid] = posRanksByTeam[row.rid] || {};
        posRanksByTeam[row.rid][pos] = { rank: i+1, val: row.val };
      });
    });

    const thead = document.querySelector('#t-pos-matrix thead');
    const tbody = document.querySelector('#t-pos-matrix tbody');
    thead.innerHTML = '<tr><th>Team</th><th>Record</th>' +
      POSITIONS.map(p => `<th>${p}</th>`).join('') + '<th>Avg Rank</th></tr>';

    const rows = [...CONSTR].map(t => {
      const ranks = POSITIONS.map(p => (posRanksByTeam[t.roster_id]?.[p]?.rank || 10));
      const avg = ranks.reduce((a,b) => a+b, 0) / ranks.length;
      return { t, ranks, avg };
    }).sort((a,b) => a.avg - b.avg);

    tbody.innerHTML = '';
    rows.forEach(({t, ranks, avg}) => {
      const tr = document.createElement('tr');
      if (isMe(t.roster_id)) tr.classList.add('me-row');
      const cells = ranks.map((r, i) => {
        const pos = POSITIONS[i];
        const val = posRanksByTeam[t.roster_id]?.[pos]?.val || 0;
        let color = 'var(--ink)'; let bg = 'transparent';
        if (r <= 3) { color = 'var(--good)'; bg = 'var(--good-soft)'; }
        else if (r >= 8) { color = 'var(--bad)'; bg = 'var(--bad-soft)'; }
        return `<td style="background:${bg};color:${color};font-weight:600;text-align:center">
          #${r}<span class="muted small" style="margin-left:4px">(${val.toFixed(0)})</span>
        </td>`;
      }).join('');
      tr.innerHTML = `<td><strong>${t.owner_name}</strong></td>
        <td class="muted">${t.wins}-${t.losses}</td>
        ${cells}
        <td style="text-align:center"><strong>${avg.toFixed(1)}</strong></td>`;
      tbody.appendChild(tr);
    });
  }
  renderPosMatrix();
  registerRenderer(renderPosMatrix);

  // ============================================================
  //   DRAFT PICKS TAB
  // ============================================================
  const FP = EXTRAS.future_picks || {matrix:[], totals:[], seasons:[]};
  const FP_ROSTERS = FP.matrix || [];
  const FP_SEASONS = FP.seasons || [__NEXT_DRAFT__, __NEXT_DRAFT_PLUS_1__, __NEXT_DRAFT_PLUS_2__];
  const FP_TOTALS = FP.totals || [];

  // Build season toggle
  (function(){
    const tg = document.getElementById('picks-season-toggle');
    const allBtn = document.createElement('button');
    allBtn.textContent = 'All';
    allBtn.dataset.s = 'all';
    allBtn.classList.add('active');
    tg.appendChild(allBtn);
    FP_SEASONS.forEach(s => {
      const b = document.createElement('button');
      b.textContent = s;
      b.dataset.s = String(s);
      tg.appendChild(b);
    });
    tg.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
      tg.querySelectorAll('button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      pickFilter.season = b.dataset.s;
      renderPicksMatrix();
    }));
  })();

  // Owner filter for picks tab
  (function(){
    const sel = document.getElementById('picks-owner');
    FP_ROSTERS.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.roster_id; opt.textContent = t.owner_name;
      sel.appendChild(opt);
    });
    sel.addEventListener('change', e => {
      pickFilter.owner = e.target.value;
      renderPicksMatrix();
    });
  })();

  document.getElementById('picks-traded-only').addEventListener('change', e => {
    pickFilter.tradedOnly = e.target.checked;
    renderPicksMatrix();
  });

  const pickFilter = { season: 'all', owner: '', tradedOnly: false };

  function renderPicksMatrix() {
    const thead = document.querySelector('#t-picks-matrix thead');
    const tbody = document.querySelector('#t-picks-matrix tbody');
    const rounds = [1,2,3,4,5];
    const seasonsShown = pickFilter.season === 'all' ? FP_SEASONS : [parseInt(pickFilter.season, 10)];

    // Header: Original Owner | for each season: R1..R5
    let thhtml = '<tr><th rowspan="2">Original Owner</th>';
    seasonsShown.forEach(s => {
      thhtml += `<th colspan="${rounds.length}" style="text-align:center">${s}</th>`;
    });
    thhtml += '</tr><tr>';
    seasonsShown.forEach(s => rounds.forEach(r => thhtml += `<th style="text-align:center">R${r}</th>`));
    thhtml += '</tr>';
    thead.innerHTML = thhtml;

    // Flatten all picks into map: original_rid -> season -> round -> pick
    const byOrig = {};
    FP_ROSTERS.forEach(team => {
      team.picks.forEach(p => {
        byOrig[p.original_roster_id] = byOrig[p.original_roster_id] || {};
        byOrig[p.original_roster_id][p.season] = byOrig[p.original_roster_id][p.season] || {};
        byOrig[p.original_roster_id][p.season][p.round] = p;
      });
    });

    tbody.innerHTML = '';
    [...FP_ROSTERS].sort((a,b) => a.roster_id - b.roster_id).forEach(team => {
      // if owner filter set, only include picks currently owned by that roster
      // (we still show the original-owner row, but we'll highlight)
      const tr = document.createElement('tr');
      const teamMine = isMe(team.roster_id);
      let rowHtml = `<td><span class="team-pill ${teamMine?'me':''}">${team.owner_name}</span>
        <span class="muted small">${team.wins!=null?` ${team.wins}-${team.losses}`:''}</span></td>`;
      let rowHasAny = false;
      seasonsShown.forEach(s => {
        rounds.forEach(r => {
          const p = byOrig[team.roster_id]?.[s]?.[r];
          if (!p) { rowHtml += `<td class="pick-none muted" style="text-align:center">—</td>`; return; }
          // Filters
          if (pickFilter.tradedOnly && !p.is_traded) {
            rowHtml += `<td class="pick-none muted" style="text-align:center">—</td>`; return;
          }
          if (pickFilter.owner && String(p.current_roster_id) !== String(pickFilter.owner)) {
            rowHtml += `<td class="pick-none muted" style="text-align:center">—</td>`; return;
          }
          let cls = 'pick-own';
          let label = p.current_owner_name || '?';
          if (p.is_traded) {
            if (p.current_roster_id === team.roster_id) {
              cls = 'pick-acq'; label = '→ ' + label;
            } else {
              cls = 'pick-sent'; label = label;
            }
          }
          rowHtml += `<td style="text-align:center" title="Est. value ${FMT.format(p.estimated_value)}">
            <span class="pick-cell ${cls}">${label}</span>
          </td>`;
          rowHasAny = true;
        });
      });
      tr.innerHTML = rowHtml;
      if (teamMine) tr.classList.add('me-row');
      tbody.appendChild(tr);
    });
  }
  renderPicksMatrix();
  registerRenderer(renderPicksMatrix);

  // Pick stock leaderboard
  function renderPickStock() {
    const tbody = document.querySelector('#t-pick-stock tbody');
    tbody.innerHTML = '';
    const sorted = [...FP_TOTALS].sort((a,b) => (b.total_value||0) - (a.total_value||0));
    sorted.forEach((t, i) => {
      const byYear = { };
      FP_ROSTERS.find(r => r.roster_id === t.roster_id).picks.forEach(p => {
        byYear[p.season] = (byYear[p.season]||0) + 1;
      });
      const brk = Object.keys(byYear).sort().map(y => `<span class="muted small">${y}: ${byYear[y]}</span>`).join(' · ');
      const tr = document.createElement('tr');
      if (isMe(t.roster_id)) tr.classList.add('me-row');
      tr.innerHTML = `<td><span class="rank-badge">${i+1}</span></td>
        <td><strong>${t.owner_name}</strong></td>
        <td class="muted">${t.wins!=null?`${t.wins}-${t.losses}`:''}</td>
        <td><strong>${t.total_picks}</strong></td>
        <td><strong>${FMT.format(t.total_value)}</strong></td>
        <td>${brk}</td>`;
      tbody.appendChild(tr);
    });
  }
  renderPickStock();
  registerRenderer(renderPickStock);

  // ============================================================
  //   TRADE CALC
  // ============================================================
  const sideA = []; const sideB = [];
  let posture = 'balanced';
  const POSTURE_WEIGHTS = { balanced: [0.5, 0.5], contender: [0.25, 0.75], rebuild: [0.8, 0.2] };

  function allAssets() {
    const pick = PICKS.map(p => ({
      id: p.player_id, name: p.full_name, position: 'PICK',
      dyn: p.trade_dyn_value || 0, red: p.trade_red_value || 0,
      meta: ''
    }));
    const ply = PLAYERS.map(p => ({
      id: p.player_id, name: p.full_name, position: p.position,
      team: p.team, age: p.age, owner: p.owner_name,
      dyn: p.trade_dyn_value || 0, red: p.trade_red_value || 0,
      meta: `${p.position}${p.team?' · '+p.team:''}${p.age?' · '+p.age+'yo':''}${p.owner_name?' · '+p.owner_name:''}`
    }));
    return pick.concat(ply);
  }
  const ALL_ASSETS = allAssets();

  function setupAutocomplete(inputId, acId, side) {
    const input = document.getElementById(inputId);
    const ac = document.getElementById(acId);
    let hl = -1;
    function render(matches) {
      ac.innerHTML = '';
      matches.forEach((m, i) => {
        const d = document.createElement('div');
        d.className = 'ac-item' + (i === hl ? ' highlight' : '');
        d.innerHTML = `<span><span class="pos pos-${m.position}">${m.position}</span> <strong>${m.name}</strong> <span class="muted small">${m.meta||''}</span></span><span class="muted small">${FMT.format(Math.round(m.dyn))} / ${FMT.format(Math.round(m.red))}</span>`;
        d.addEventListener('mousedown', (e) => { e.preventDefault(); add(m); });
        ac.appendChild(d);
      });
      ac.classList.toggle('open', matches.length > 0);
    }
    function add(m) {
      side.push(m);
      input.value = '';
      ac.classList.remove('open');
      renderTrade();
    }
    input.addEventListener('input', () => {
      hl = -1;
      const q = input.value.trim().toLowerCase();
      if (!q) { ac.classList.remove('open'); return; }
      const matches = ALL_ASSETS.filter(a =>
        a.name.toLowerCase().includes(q) || (a.team||'').toLowerCase()===q
      ).slice(0, 14);
      render(matches);
    });
    input.addEventListener('keydown', e => {
      if (!ac.classList.contains('open')) return;
      const items = ac.querySelectorAll('.ac-item');
      if (e.key === 'ArrowDown') { hl = Math.min(items.length-1, hl+1); e.preventDefault(); }
      else if (e.key === 'ArrowUp') { hl = Math.max(0, hl-1); e.preventDefault(); }
      else if (e.key === 'Enter') {
        const q = input.value.trim().toLowerCase();
        const matches = ALL_ASSETS.filter(a => a.name.toLowerCase().includes(q)).slice(0, 14);
        if (matches.length) { add(matches[hl >= 0 ? hl : 0]); e.preventDefault(); return; }
      }
      items.forEach((it,i)=> it.classList.toggle('highlight', i===hl));
    });
    input.addEventListener('blur', () => setTimeout(() => ac.classList.remove('open'), 150));
  }
  setupAutocomplete('a-add','a-ac', sideA);
  setupAutocomplete('b-add','b-ac', sideB);

  function renderSide(side, listEl, sumEl, dynEl, winEl) {
    listEl.innerHTML = '';
    let dyn = 0, win = 0;
    side.forEach((m, i) => {
      dyn += m.dyn; win += m.red;
      const d = document.createElement('div');
      d.className = 'asset';
      d.innerHTML = `<span><span class="pos pos-${m.position}">${m.position}</span> <strong>${m.name}</strong>${m.team?` <span class="muted small">${m.team}</span>`:''}</span>
        <span class="asset-val">${FMT.format(Math.round(m.dyn))} dyn · ${FMT.format(Math.round(m.red))} win</span>
        <button class="rm" title="Remove">×</button>`;
      d.querySelector('.rm').addEventListener('click', () => { side.splice(i,1); renderTrade(); });
      listEl.appendChild(d);
    });
    const [wd, wr] = POSTURE_WEIGHTS[posture];
    const blended = dyn * wd + win * wr;
    sumEl.textContent = FMT.format(Math.round(blended));
    dynEl.textContent = FMT.format(Math.round(dyn));
    winEl.textContent = FMT.format(Math.round(win));
    return { dyn, win, blended };
  }

  function renderTrade() {
    const a = renderSide(sideA, document.getElementById('a-list'), document.getElementById('a-total'),
      document.getElementById('a-dyn'), document.getElementById('a-win'));
    const b = renderSide(sideB, document.getElementById('b-list'), document.getElementById('b-total'),
      document.getElementById('b-dyn'), document.getElementById('b-win'));
    const v = document.getElementById('verdict');
    const vt = document.getElementById('verdict-text');
    const vd = document.getElementById('verdict-delta');
    if (sideA.length === 0 && sideB.length === 0) {
      v.className = 'trade-verdict even';
      vt.textContent = 'Add players or picks to both sides to evaluate.';
      vd.textContent = '';
      return;
    }
    if (sideA.length === 0 || sideB.length === 0) {
      v.className = 'trade-verdict even';
      vt.textContent = 'Add at least one asset to each side.';
      vd.textContent = '';
      return;
    }
    const delta = b.blended - a.blended;
    const pct = a.blended > 0 ? (delta / a.blended * 100) : 0;
    const dynDelta = b.dyn - a.dyn;
    const winDelta = b.win - a.win;
    let cls, label;
    if (delta > Math.max(300, a.blended * 0.08)) { cls = 'win'; label = 'You win this trade'; }
    else if (delta < -Math.max(300, a.blended * 0.08)) { cls = 'loss'; label = 'You lose this trade'; }
    else { cls = 'even'; label = 'Fair trade (within 8%)'; }
    v.className = 'trade-verdict ' + cls;
    vt.innerHTML = `${label} — <span class="muted">${posture === 'balanced' ? '50/50 blended' : posture==='contender' ? 'contender weighting' : 'rebuild weighting'}</span>`;
    const sign = delta > 0 ? '+' : '';
    vd.innerHTML = `<span>${sign}${FMT.format(Math.round(delta))} blended (${pct.toFixed(1)}%)</span>
      <span class="muted small" style="margin-left:12px">Dyn ${dynDelta>=0?'+':''}${FMT.format(Math.round(dynDelta))} · Win ${winDelta>=0?'+':''}${FMT.format(Math.round(winDelta))}</span>`;
  }

  document.querySelectorAll('#posture-toggle button').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('#posture-toggle button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      posture = b.dataset.p;
      renderTrade();
    });
  });
  document.getElementById('clear-trade').addEventListener('click', () => {
    sideA.length = 0; sideB.length = 0; renderTrade();
  });
  renderTrade();

  // --- My Team ---
  let myTeamView = 'dynasty';
  function renderMyTeam() {
    const mine = PLAYERS.filter(p => p.owner_id === ME);
    mine.forEach(p => p.delta = (p.winnow_score != null && p.dynasty_score != null) ? p.winnow_score - p.dynasty_score : null);
    const sortKey = myTeamView === 'dynasty' ? 'dynasty_score' : myTeamView === 'winnow' ? 'winnow_score' : 'delta';
    mine.sort((a,b) => (b[sortKey]||0) - (a[sortKey]||0));
    const starters = mine.filter(p => p.is_starter);
    const bench = mine.filter(p => !p.is_starter && !p.is_taxi && !p.is_reserve);
    const taxi = mine.filter(p => p.is_taxi || p.is_reserve);
    function group(title, list) {
      let html = `<div class="card"><h2>${title} <span class="muted small">(${list.length})</span></h2>`;
      if (!list.length) { html += '<div class="muted small">None</div></div>'; return html; }
      html += '<table><thead><tr><th>Player</th><th>Pos</th><th>Age</th><th>Dyn</th><th>Win</th><th>Δ</th></tr></thead><tbody>';
      list.forEach(p => {
        html += `<tr>
          <td><strong>${p.full_name}</strong><br><span class="muted small">${p.team||'—'}</span></td>
          <td><span class="pos pos-${p.position}">${p.position}</span></td>
          <td>${p.age||''}</td>
          <td>${(p.dynasty_score||0).toFixed(1)}</td>
          <td>${(p.winnow_score||0).toFixed(1)}</td>
          <td>${deltaFmt(p.delta)}</td>
        </tr>`;
      });
      html += '</tbody></table></div>';
      return html;
    }
    document.getElementById('myteam-starters').innerHTML = group('Starters', starters);
    document.getElementById('myteam-bench').innerHTML = group('Bench', bench);
    document.getElementById('myteam-taxiIR').innerHTML = group('Taxi / IR', taxi);
  }
  document.querySelectorAll('#myteam-view button').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('#myteam-view button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      myTeamView = b.dataset.view;
      renderMyTeam();
    });
  });
  renderMyTeam();
  registerRenderer(renderMyTeam);

  // ── Team / Player News (ESPN) ───────────────────────────────────────────
  const NEWS = EXTRAS.news || {available:false, items:[]};
  function escNews(s) {
    return String(s == null ? '' : s).replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]));
  }
  function newsWhen(iso) {
    if (!iso) return '';
    const d = new Date(iso), now = new Date(), mins = Math.round((now - d) / 60000);
    if (isNaN(mins)) return '';
    if (mins < 60) return mins <= 1 ? 'just now' : mins + 'm ago';
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.round(hrs / 24);
    if (days < 7) return days + 'd ago';
    return d.toLocaleDateString();
  }
  function renderTeamNews() {
    const wrap = document.getElementById('myteam-news');
    const meta = document.getElementById('myteam-news-meta');
    if (!wrap) return;
    if (!NEWS.available) {
      wrap.innerHTML = '<div class="muted small">No news feed yet — run scripts/fetch_news.py during the next refresh.</div>';
      if (meta) meta.textContent = '';
      return;
    }
    // Only stories that touch a player on the selected team.
    const mine = (NEWS.items || []).filter(it => (it.owner_ids || []).includes(ME));
    if (meta) meta.textContent = NEWS.source ? '· via ' + NEWS.source : '';
    if (!mine.length) {
      wrap.innerHTML = '<div class="muted small">No recent news for your roster. Check back after the next data refresh.</div>';
      return;
    }
    wrap.innerHTML = mine.slice(0, 25).map(it => {
      const chips = (it.players || [])
        .filter(p => p.owner_id === ME)
        .map(p => `<span class="news-chip"><span class="pos pos-${escNews(p.position)}">${escNews(p.position)}</span>${escNews(p.full_name)}</span>`)
        .join('');
      const title = it.link
        ? `<a class="news-title" href="${escNews(it.link)}" target="_blank" rel="noopener">${escNews(it.headline)}</a>`
        : `<span class="news-title">${escNews(it.headline)}</span>`;
      return `<div class="news-item">
        <div class="news-head">${title}<span class="news-when">${escNews(newsWhen(it.published))}</span></div>
        ${it.description ? `<div class="news-desc">${escNews(it.description)}</div>` : ''}
        <div class="news-players">${chips}</div>
      </div>`;
    }).join('');
  }
  renderTeamNews();
  registerRenderer(renderTeamNews);

  // --- Methodology ---
  document.getElementById('methodology').innerHTML =
    `<p><strong>Dynasty Score</strong> — ${DATA.meta.ranking_methodology.dynasty}</p>` +
    `<p><strong>Win-Now Score</strong> — ${DATA.meta.ranking_methodology.winnow}</p>`;
  document.getElementById('sources').innerHTML =
    `NFL stats through the <strong>${DATA.meta.latest_nfl_season} season, Week ${DATA.meta.latest_nfl_week}</strong>.
     Sleeper league + roster data from <code>${DATA.meta.league_name}</code> (id <code>${DATA.meta.league_id}</code>).
     Trade values from <strong>FantasyCalc</strong>.
     Re-run <code>scripts/refresh_platform.sh</code> in your Fantasy Football folder to refresh all data and rebuild this dashboard.`;

  // ────────────────────────────────────────────────────────────────────
  // ROOKIES TAB
  // ────────────────────────────────────────────────────────────────────
  (function initRookies(){
    const R = (EXTRAS.rookies) || {};
    if (!R.incoming_class) return;

    let view = "incoming"; // incoming | second_year | picks
    let posFilter = new Set();
    const POS = ["QB","RB","WR","TE"];

    const chips = document.getElementById("rookie-pos-chips");
    POS.forEach(p => {
      const b = document.createElement("button");
      b.textContent = p; b.dataset.pos = p;
      b.addEventListener("click", () => {
        if (posFilter.has(p)) { posFilter.delete(p); b.classList.remove("active"); }
        else { posFilter.add(p); b.classList.add("active"); }
        renderRookies();
      });
      chips.appendChild(b);
    });

    document.querySelectorAll("#rookie-toggle button").forEach(b => {
      b.addEventListener("click", () => {
        document.querySelectorAll("#rookie-toggle button").forEach(x=>x.classList.remove("active"));
        b.classList.add("active");
        view = b.dataset.view;
        renderRookies();
      });
    });
    document.getElementById("rookie-search").addEventListener("input", renderRookies);

    function renderRookies(){
      const q = (document.getElementById("rookie-search").value || "").toLowerCase().trim();
      const thead = document.getElementById("th-rookies");
      const tbody = document.querySelector("#t-rookies tbody");

      if (view === "picks") {
        thead.innerHTML = "<tr><th>Pick</th><th class='num'>FC Dynasty Value</th><th class='num'>Overall Rank</th></tr>";
        const rows = (R.top_picks || []).filter(p => !q || (p.label||"").toLowerCase().includes(q));
        tbody.innerHTML = rows.map(p =>
          `<tr><td>${p.label}</td><td class='num'>${p.fc_dyn != null ? FMT.format(p.fc_dyn) : "—"}</td>` +
          `<td class='num'>${p.overall_rank != null ? Math.round(p.overall_rank) : "—"}</td></tr>`
        ).join("");
        return;
      }

      const src = view === "incoming" ? R.incoming_class : R.second_year;
      thead.innerHTML = "<tr>" +
        "<th>Player</th><th>Pos</th><th>NFL Team</th><th class='num'>Age</th>" +
        "<th>Owner</th><th class='num'>FC Dyn</th><th class='num'>FC Rk</th>" +
        "<th class='num'>30d Δ</th></tr>";

      const filtered = (src || []).filter(r => {
        if (posFilter.size && !posFilter.has(r.position)) return false;
        if (q && !(r.full_name||"").toLowerCase().includes(q)
              && !(r.team||"").toLowerCase().includes(q)
              && !(r.owner_name||"").toLowerCase().includes(q)) return false;
        return true;
      });

      tbody.innerHTML = filtered.map(r => {
        const ownerCls = r.owner_name === "FA" ? "pill-fa"
                       : (r.owner_id === ME ? "pill-mine" : "pill");
        const trend = r.trend_30d == null ? "—"
                    : (r.trend_30d > 0 ? `<span class='delta-up'>+${Math.round(r.trend_30d)}</span>`
                                       : `<span class='delta-dn'>${Math.round(r.trend_30d)}</span>`);
        return `<tr>
          <td>${r.full_name || "—"}${r.is_taxi ? " <span class='pill'>TAXI</span>" : ""}</td>
          <td>${r.position || "—"}</td>
          <td>${r.team || "—"}</td>
          <td class='num'>${r.age != null ? r.age.toFixed(0) : "—"}</td>
          <td><span class='pill ${ownerCls}'>${r.owner_name}</span></td>
          <td class='num'>${r.fc_dyn != null ? FMT.format(r.fc_dyn) : "—"}</td>
          <td class='num'>${r.fc_dyn_rank != null ? Math.round(r.fc_dyn_rank) : "—"}</td>
          <td class='num'>${trend}</td>
        </tr>`;
      }).join("");
    }

    // Owner capital table — re-renderable so the highlighted "you" row updates on team switch
    function renderRookieCapital() {
      const ct = document.querySelector("#t-rookie-capital tbody");
      if (!ct) return;
      const myName = (TEAMS.find(t=>t.owner_id===ME)||{}).owner_name;
      ct.innerHTML = (R.owner_capital || []).map(o => {
        const cls = o.owner_name === myName ? " style='background:var(--good-soft)'" : "";
        return `<tr${cls}><td>${o.owner_name}</td>` +
          `<td class='num'>${o.young_players}</td>` +
          `<td class='num'>${FMT.format(o.young_value)}</td>` +
          `<td class='num'>${o.picks_2026}</td>` +
          `<td class='num'>${FMT.format(o.pick_value)}</td>` +
          `<td class='num'><strong>${FMT.format(o.total_value)}</strong></td></tr>`;
      }).join("");
    }
    renderRookieCapital();
    registerRenderer(renderRookieCapital);

    renderRookies();
    registerRenderer(renderRookies);
  })();

  // ────────────────────────────────────────────────────────────────────
  // NFL TEAMS TAB
  // ────────────────────────────────────────────────────────────────────
  (function initNflTeams(){
    const TC = EXTRAS.team_context;
    if (!TC || !TC.available) return;

    document.getElementById("nflteams-season").textContent = TC.season;

    let sortKey = "fpts_ppr_pg";
    let sortDir = -1;
    let q = "";

    document.getElementById("nflteams-search").addEventListener("input", e => {
      q = e.target.value.toLowerCase().trim();
      render();
    });

    document.querySelectorAll("#t-nflteams thead th[data-sort]").forEach(th => {
      th.style.cursor = "pointer";
      th.addEventListener("click", () => {
        const k = th.dataset.sort;
        if (k === sortKey) sortDir *= -1;
        else { sortKey = k; sortDir = (k === "team") ? 1 : -1; }
        render();
      });
    });

    function rankBadge(rank, total) {
      if (rank == null) return "";
      let cls = "";
      if (rank <= 5) cls = "rank-top";
      else if (rank >= total - 4) cls = "rank-bottom";
      return `<span class='rank-sup ${cls}'>#${rank}</span>`;
    }
    function rankedCell(val, rank, total, isInt) {
      const v = isInt ? Math.round(val) : val;
      return `<span class='ranked-cell'>${v}${rankBadge(rank, total)}</span>`;
    }

    function render(){
      const teams = (TC.teams || []).filter(t => !q || (t.team || "").toLowerCase().includes(q));
      teams.sort((a,b) => {
        const A = a[sortKey], B = b[sortKey];
        if (A == null && B == null) return 0;
        if (A == null) return 1;
        if (B == null) return -1;
        if (A === B) return 0;
        return (A > B ? 1 : -1) * sortDir;
      });
      const total = (TC.teams || []).length;
      const tbody = document.querySelector("#t-nflteams tbody");
      tbody.innerHTML = teams.map(t => `<tr>
        <td><strong>${t.team}</strong></td>
        <td class='num'>${t.games}</td>
        <td class='num'>${rankedCell(t.plays_per_game, t.plays_per_game_rank, total)}</td>
        <td class='num'>${rankedCell(t.pass_per_game,  t.pass_per_game_rank,  total)}</td>
        <td class='num'>${rankedCell(t.rush_per_game,  t.rush_per_game_rank,  total)}</td>
        <td class='num'>${t.pass_pct.toFixed(1)}%</td>
        <td class='num'>${rankedCell(t.pass_yards_pg,  t.pass_yards_pg_rank,  total)}</td>
        <td class='num'>${rankedCell(t.rush_yards_pg,  t.rush_yards_pg_rank,  total)}</td>
        <td class='num'>${rankedCell(t.total_tds_pg,   t.total_tds_pg_rank,   total)}</td>
        <td class='num'>${rankedCell(t.fpts_ppr_pg,    t.fpts_ppr_pg_rank,    total)}</td>
        <td class='small muted'>${t.context_tag}</td>
      </tr>`).join("");
    }
    render();
  })();

  // ────────────────────────────────────────────────────────────────────
  // SNAP & OPP TAB
  // ────────────────────────────────────────────────────────────────────
  (function initSnaps(){
    const S = EXTRAS.snap_opportunity;
    if (!S || !S.available) return;

    document.getElementById("snaps-recent").textContent = S.recent_games;
    document.getElementById("snaps-snapseason").textContent = S.snap_season;
    document.getElementById("snaps-snapseason-2").textContent = S.snap_season;
    document.getElementById("snaps-statseason").textContent = S.stat_season || "—";

    const ownerSel = document.getElementById("snaps-owner");
    const owners = Array.from(new Set((S.players || []).map(p => p.owner_name).filter(Boolean))).sort();
    owners.forEach(o => {
      const opt = document.createElement("option"); opt.value = o; opt.textContent = o;
      ownerSel.appendChild(opt);
    });

    const POS = ["QB","RB","WR","TE"];
    const posFilter = new Set();
    const chips = document.getElementById("snaps-pos-chips");
    POS.forEach(p => {
      const b = document.createElement("button");
      b.textContent = p; b.dataset.pos = p;
      b.addEventListener("click", () => {
        if (posFilter.has(p)) { posFilter.delete(p); b.classList.remove("active"); }
        else { posFilter.add(p); b.classList.add("active"); }
        render();
      });
      chips.appendChild(b);
    });

    document.getElementById("snaps-search").addEventListener("input", render);
    document.getElementById("snaps-mine-only").addEventListener("change", render);
    ownerSel.addEventListener("change", render);

    function sparkline(series) {
      if (!series || series.length === 0) return "";
      const pts = series.map(s => s.snap_pct);
      const w = 80, h = 18, pad = 2;
      const max = Math.max(...pts, 1);
      const min = Math.min(...pts, 0);
      const span = Math.max(max - min, 1);
      const xs = (i) => pad + i * ((w - pad*2) / Math.max(pts.length - 1, 1));
      const ys = (v) => (h - pad) - ((v - min) / span) * (h - pad*2);
      const poly = pts.map((v,i) => `${xs(i).toFixed(1)},${ys(v).toFixed(1)}`).join(" ");
      const last = pts.length - 1;
      return `<svg class='sparkline' viewBox='0 0 ${w} ${h}'>
        <polyline points='${poly}'/>
        <circle cx='${xs(last).toFixed(1)}' cy='${ys(pts[last]).toFixed(1)}' r='1.7'/>
      </svg>`;
    }

    function render(){
      const q = (document.getElementById("snaps-search").value || "").toLowerCase().trim();
      const ownerVal = ownerSel.value;
      const mineOnly = document.getElementById("snaps-mine-only").checked;
      const myName = (TEAMS.find(t => t.owner_id === ME) || {}).owner_name;

      const rows = (S.players || []).filter(p => {
        if (mineOnly && p.owner_name !== myName) return false;
        if (ownerVal && p.owner_name !== ownerVal) return false;
        if (posFilter.size && !posFilter.has(p.position)) return false;
        if (q && !(p.full_name||"").toLowerCase().includes(q)) return false;
        return true;
      });

      const tbody = document.querySelector("#t-snaps tbody");
      tbody.innerHTML = rows.map(p => {
        const dCls = p.snap_delta_4v4 == null ? "" :
          p.snap_delta_4v4 > 0 ? "delta-up" : (p.snap_delta_4v4 < 0 ? "delta-dn" : "");
        const sCls = p.snap_slope == null ? "" :
          p.snap_slope > 0 ? "delta-up" : (p.snap_slope < 0 ? "delta-dn" : "");
        return `<tr>
          <td>${p.full_name}</td>
          <td>${p.position || ""}</td>
          <td>${p.team || ""}</td>
          <td>${p.owner_name || ""}</td>
          <td class='num'>${p.snap_avg_pct != null ? p.snap_avg_pct.toFixed(1) + "%" : "—"}</td>
          <td class='num ${dCls}'>${p.snap_delta_4v4 != null ? (p.snap_delta_4v4 > 0 ? "+":"") + p.snap_delta_4v4.toFixed(1) : "—"}</td>
          <td class='num ${sCls}'>${p.snap_slope != null ? (p.snap_slope > 0 ? "+":"") + p.snap_slope.toFixed(2) : "—"}</td>
          <td class='num'>${p.tgt_avg != null ? p.tgt_avg.toFixed(1) : "—"}</td>
          <td class='num'>${p.car_avg != null ? p.car_avg.toFixed(1) : "—"}</td>
          <td>${sparkline(p.snap_series)}</td>
        </tr>`;
      }).join("");
    }
    render();
    registerRenderer(render);
  })();

  // ────────────────────────────────────────────────────────────────────
  // INJURY BANNER on Overview + INJURIES TAB
  // ────────────────────────────────────────────────────────────────────
  (function initInjuries(){
    const I = EXTRAS.injury_wire;
    if (!I || !I.available) return;

    // Banner — re-renderable so it updates when the user switches teams
    function renderInjuryBanner() {
      const myName = (TEAMS.find(t => t.owner_id === ME) || {}).owner_name;
      const myCounts = (I.owner_counts || {})[myName] || {total:0, starters:0, high_value:0};
      const banner = document.getElementById("o-injury-banner");
      const text   = document.getElementById("o-injury-text");
      if (!banner || !text) return;
      banner.classList.remove("hidden", "is-clean");
      if (myCounts.total === 0 && I.rostered_total === 0) {
        banner.classList.add("is-clean");
        text.innerHTML = "🟢 <strong>No active injury designations</strong> league-wide. Quiet offseason.";
      } else if (myCounts.total === 0) {
        banner.classList.add("is-clean");
        text.innerHTML = `🟢 <strong>None of your players carry an active injury designation.</strong> ${I.rostered_total} player(s) league-wide do.`;
      } else {
        let parts = [`⚠️ <strong>${myCounts.total} of your players have an active injury status</strong>`];
        if (myCounts.starters)   parts.push(`(${myCounts.starters} starter${myCounts.starters>1?'s':''})`);
        if (myCounts.high_value) parts.push(`· ${myCounts.high_value} high-value asset${myCounts.high_value>1?'s':''}`);
        text.innerHTML = parts.join(" ");
      }
    }
    renderInjuryBanner();
    registerRenderer(renderInjuryBanner);

    document.querySelectorAll('[data-jump]').forEach(b => b.addEventListener('click', () => {
      const t = b.dataset.jump;
      document.querySelector(`#tabs button[data-tab="${t}"]`)?.click();
    }));

    // Tab content
    const ownerSel = document.getElementById("inj-owner");
    const owners = Array.from(new Set((I.injuries || []).map(x => x.owner_name).filter(o => o && o !== "FA"))).sort();
    owners.forEach(o => {
      const opt = document.createElement("option"); opt.value = o; opt.textContent = o;
      ownerSel.appendChild(opt);
    });

    const STATUSES = ["Out","IR","PUP","Sus","Doubtful","COV","Questionable"];
    const statusFilter = new Set();
    const chips = document.getElementById("inj-status-chips");
    STATUSES.forEach(s => {
      const b = document.createElement("button");
      b.textContent = s; b.dataset.s = s;
      b.addEventListener("click", () => {
        if (statusFilter.has(s)) { statusFilter.delete(s); b.classList.remove("active"); }
        else { statusFilter.add(s); b.classList.add("active"); }
        renderInjuries();
      });
      chips.appendChild(b);
    });

    document.getElementById("inj-mine-only").addEventListener("change", renderInjuries);
    document.getElementById("inj-rostered-only").addEventListener("change", renderInjuries);
    ownerSel.addEventListener("change", renderInjuries);

    function renderInjuries(){
      const ownerVal = ownerSel.value;
      const mine = document.getElementById("inj-mine-only").checked;
      const rosOnly = document.getElementById("inj-rostered-only").checked;
      const myName = (TEAMS.find(t => t.owner_id === ME) || {}).owner_name;

      const rows = (I.injuries || []).filter(x => {
        if (rosOnly && !x.rostered) return false;
        if (mine && x.owner_name !== myName) return false;
        if (ownerVal && x.owner_name !== ownerVal) return false;
        if (statusFilter.size && !statusFilter.has(x.injury_status)) return false;
        return true;
      });

      const tbody = document.querySelector("#t-injuries tbody");
      const empty = document.getElementById("inj-empty");
      if (rows.length === 0) {
        tbody.innerHTML = "";
        empty.classList.remove("hidden");
      } else {
        empty.classList.add("hidden");
        tbody.innerHTML = rows.map(x => {
          const ownerCls = x.owner_name === "FA" ? "pill-fa" : (x.owner_id === ME ? "pill-mine" : "pill");
          return `<tr>
            <td>${x.full_name}${x.is_starter ? " <span class='pill'>STARTER</span>" : ""}</td>
            <td>${x.position||""}</td>
            <td>${x.team||""}</td>
            <td><span class='pill ${ownerCls}'>${x.owner_name||"FA"}</span></td>
            <td><span class='pill sev-${x.severity}'>${x.injury_status}</span></td>
            <td class='small muted'>${x.severity}/5</td>
            <td class='num'>${x.fc_dyn != null ? FMT.format(x.fc_dyn) : "—"}</td>
          </tr>`;
        }).join("");
      }

      // Owner counts table
      const ct = document.querySelector("#t-injury-counts tbody");
      const counts = I.owner_counts || {};
      const arr = Object.entries(counts).map(([owner, c]) => ({owner, ...c}))
        .sort((a,b) => b.total - a.total);
      if (arr.length === 0) {
        ct.innerHTML = "<tr><td colspan='4' class='small muted'>No owners affected.</td></tr>";
      } else {
        ct.innerHTML = arr.map(c => {
          const cls = c.owner === myName ? " style='background:var(--good-soft)'" : "";
          return `<tr${cls}><td>${c.owner}</td><td class='num'>${c.total}</td>` +
            `<td class='num'>${c.starters}</td><td class='num'>${c.high_value}</td></tr>`;
        }).join("");
      }
    }
    renderInjuries();
    registerRenderer(renderInjuries);
  })();

  // ────────────────────────────────────────────────────────────────────
  // STRENGTH OF SCHEDULE TAB
  // ────────────────────────────────────────────────────────────────────
  (function initSos(){
    const S = EXTRAS.sos;
    if (!S || !S.available) return;

    let view = "rosters";
    let pos = "ALL";

    document.querySelectorAll("#sos-view button").forEach(b => {
      b.addEventListener("click", () => {
        document.querySelectorAll("#sos-view button").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        view = b.dataset.view;
        render();
      });
    });
    document.getElementById("sos-pos").addEventListener("change", e => {
      pos = e.target.value; render();
    });

    function tintCell(rank, totalRange) {
      // For schedule difficulty: 1..32, 1=easiest in our ordering (we set easiest as rank 1)
      // Wait — actually for the ROSTER and TEAM views: 1 = easiest schedule (best for fantasy).
      //        For DvP view: 1 = toughest defense (worst for fantasy).
      if (rank == null) return "sos-mid";
      if (totalRange === "easyTop") {
        if (rank <= 6) return "sos-easy";
        if (rank <= 12) return "sos-soft";
        if (rank >= 27) return "sos-brutal";
        if (rank >= 21) return "sos-tough";
      } else {
        // DvP: low rank = tough D = bad for offense
        if (rank <= 6) return "sos-brutal";
        if (rank <= 12) return "sos-tough";
        if (rank >= 27) return "sos-easy";
        if (rank >= 21) return "sos-soft";
      }
      return "sos-mid";
    }

    function render(){
      const thead = document.getElementById("th-sos");
      const tbody = document.querySelector("#t-sos tbody");

      if (view === "dvp") {
        // __DVP_SEASON__ DvP rankings
        const positions = pos === "ALL" ? S.positions : [pos];
        thead.innerHTML = "<tr><th>Defense</th>" +
          positions.map(p => `<th class='num'>${p} Pts/G</th><th class='num'>${p} Rank</th>`).join("") + "</tr>";
        // Build a team-keyed map for each position
        const byTeam = {};
        S.positions.forEach(p => {
          (S.dvp[p] || []).forEach(r => {
            byTeam[r.team] = byTeam[r.team] || { team: r.team };
            byTeam[r.team][`${p}_ppr`]  = r.ppr_per_game;
            byTeam[r.team][`${p}_rank`] = r.rank;
          });
        });
        const rows = Object.values(byTeam).sort((a,b) => a.team.localeCompare(b.team));
        tbody.innerHTML = rows.map(r => `<tr>
          <td><strong>${r.team}</strong></td>
          ${positions.map(p => `<td class='num'>${r[`${p}_ppr`] != null ? r[`${p}_ppr`].toFixed(1) : "—"}</td>` +
            `<td class='num ${tintCell(r[`${p}_rank`],"toughTop")}'>${r[`${p}_rank`] != null ? "#" + r[`${p}_rank`] : "—"}</td>`).join("")}
        </tr>`).join("");
        return;
      }

      if (view === "teams") {
        const positions = pos === "ALL" ? S.positions : [pos];
        thead.innerHTML = "<tr><th>NFL Team</th><th class='num'>Games</th>" +
          positions.map(p => `<th class='num'>${p} Avg Opp Rank</th><th class='num'>${p} SoS Rank</th>`).join("") + "</tr>";
        const rows = [...S.team_sos];
        if (pos !== "ALL") {
          rows.sort((a,b) => (b[`sos_${pos}_avg_rank`] || 0) - (a[`sos_${pos}_avg_rank`] || 0));
        } else {
          rows.sort((a,b) => a.team.localeCompare(b.team));
        }
        tbody.innerHTML = rows.map(t => `<tr>
          <td><strong>${t.team}</strong></td>
          <td class='num'>${t.games}</td>
          ${positions.map(p => `<td class='num'>${t[`sos_${p}_avg_rank`] != null ? t[`sos_${p}_avg_rank`].toFixed(1) : "—"}</td>` +
            `<td class='num ${tintCell(t[`sos_${p}_rank`],"easyTop")}'>${t[`sos_${p}_rank`] != null ? "#" + t[`sos_${p}_rank`] : "—"}</td>`).join("")}
        </tr>`).join("");
        return;
      }

      // rosters view
      const positions = pos === "ALL" ? S.positions : [pos];
      thead.innerHTML = "<tr><th>Owner</th>" +
        positions.map(p => `<th class='num'>${p} Avg Rank</th><th class='num'>${p} N</th>`).join("") +
        (pos === "ALL" ? "<th class='num'>Overall Avg Rank</th>" : "") + "</tr>";
      const rows = [...S.roster_sos];
      // sort by overall when ALL, else by selected pos
      if (pos === "ALL") rows.sort((a,b) => (b.overall_avg_rank || 0) - (a.overall_avg_rank || 0));
      else rows.sort((a,b) => (b[`${pos}_avg_rank`] || 0) - (a[`${pos}_avg_rank`] || 0));

      const myName = (TEAMS.find(t => t.owner_id === ME) || {}).owner_name;
      tbody.innerHTML = rows.map(r => {
        const cls = r.owner_name === myName ? " style='background:var(--good-soft)'" : "";
        return `<tr${cls}>
          <td>${r.owner_name}</td>
          ${positions.map(p => `<td class='num'>${r[`${p}_avg_rank`] != null ? r[`${p}_avg_rank`].toFixed(1) : "—"}</td>` +
            `<td class='num small muted'>${r[`${p}_n`] || 0}</td>`).join("")}
          ${pos === "ALL" ? `<td class='num'><strong>${r.overall_avg_rank != null ? r.overall_avg_rank.toFixed(1) : "—"}</strong></td>` : ""}
        </tr>`;
      }).join("");
    }
    render();
    registerRenderer(render);
  })();
})();
</script>
</body>
</html>
"""

# Inject the cache-buster version (just the generated_at timestamp — ~30 bytes,
# vs. ~2 MB of inlined JSON we used to embed here). The browser will fetch the
# full rankings_data.json at runtime via fetch().
PLACEHOLDER = "__DATA_VERSION_PLACEHOLDER__"
idx = HTML.find(PLACEHOLDER)
if idx < 0:
    raise SystemExit("placeholder not found in template")
# Escape the version string so it can't break out of the JS string literal.
safe_version = DATA_VERSION.replace("\\", "\\\\").replace('"', '\\"')
OUT = HTML[:idx] + safe_version + HTML[idx + len(PLACEHOLDER):]

# Inject season-derived year labels from config — keeps year strings out of
# the HTML template so a season rollover only requires editing config.py.
SEASON_TOKENS = {
    "__SEASON__":            str(config.CURRENT_SEASON),
    "__NEXT_DRAFT__":        str(config.NEXT_DRAFT_SEASON),
    "__NEXT_DRAFT_PLUS_1__": str(config.NEXT_DRAFT_SEASON + 1),
    "__NEXT_DRAFT_PLUS_2__": str(config.NEXT_DRAFT_SEASON + 2),
    "__DVP_SEASON__":        str(config.LAST_COMPLETE_SEASON),
}
for token, value in SEASON_TOKENS.items():
    if token not in OUT:
        raise SystemExit(f"season token {token} not found in template")
    OUT = OUT.replace(token, value)

with open(OUT_PATH, "w") as f:
    f.write(OUT)

print(f"wrote {OUT_PATH}")
print(f"size: {len(OUT):,} bytes (data version: {DATA_VERSION or 'unset'})")

print(f"wrote {OUT_PATH}")
print(f"size: {os.path.getsize(OUT_PATH):,} bytes")
