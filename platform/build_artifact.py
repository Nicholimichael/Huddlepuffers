"""Build the Huddlepuffers interactive platform artifact HTML."""
import json, textwrap

with open("/sessions/quirky-lucid-cannon/mnt/outputs/rankings_data.compact.json") as f:
    DATA_JSON = f.read()

HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Huddlepuffers Dynasty Platform</title>
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

  .tabs { display: flex; gap: 2px; background: var(--card); border: 1px solid var(--line);
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

  /* Trade tab contender/rebuild */
  .posture { display: inline-flex; align-items: center; gap: 8px; }

  .rank-badge { display: inline-block; font-weight: 700; color: var(--ink-2); min-width: 24px; }
</style>
</head>
<body>
<div class="app">
  <header>
    <div>
      <h1 id="title">The Huddlepuffers — Dynasty Platform</h1>
      <div class="meta" id="subtitle"></div>
    </div>
    <div class="meta" id="refresh-meta"></div>
  </header>

  <nav class="tabs" id="tabs">
    <button data-tab="overview" class="active">Overview</button>
    <button data-tab="rankings">Rankings</button>
    <button data-tab="trade">Trade Calculator</button>
    <button data-tab="myteam">My Team</button>
    <button data-tab="about">Methodology</button>
  </nav>

  <!-- OVERVIEW -->
  <section id="tab-overview" class="tab-panel">
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
        a 2025 championship, Rebuild if you're trading for future picks and youth.
      </div>
    </div>
  </section>

  <!-- MY TEAM -->
  <section id="tab-myteam" class="tab-panel hidden">
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
      </div>
      <h3 style="margin-top:16px">Data sources & freshness</h3>
      <div class="methodology" id="sources"></div>
      <h3 style="margin-top:16px">Caveats</h3>
      <div class="methodology">
        IDP players (DL/LB/DB) don't appear in FantasyCalc and have no offensive fantasy points in our stat feed,
        so their scores default to 50/50. Rankings for offensive players (QB/RB/WR/TE) are the meaningful ones.
        Kickers are included but are effectively replaceable — treat their scores as directional only.
      </div>
    </div>
  </section>
</div>

<script id="data-blob" type="application/json">__DATA_PLACEHOLDER__</script>
<script>
(function(){
  const DATA = JSON.parse(document.getElementById('data-blob').textContent);
  const ME = DATA.meta.my_user_id;
  const PLAYERS = DATA.players;
  const PICKS = DATA.picks;
  const TEAMS = DATA.teams;
  const FMT = new Intl.NumberFormat('en-US');

  // --- Header meta ---
  document.getElementById('title').textContent = DATA.meta.league_name + ' — Dynasty Platform';
  const me = TEAMS.find(t => t.owner_id === ME);
  document.getElementById('subtitle').textContent =
    (me ? `${me.owner_name} · ${me.wins}-${me.losses}` : '') +
    `  ·  ${DATA.meta.season} season  ·  NFL stats through ${DATA.meta.latest_nfl_season} Week ${DATA.meta.latest_nfl_week}`;
  document.getElementById('refresh-meta').textContent =
    'Refreshed ' + new Date(DATA.meta.generated_at).toLocaleString() +
    '  ·  ' + PLAYERS.length + ' players · ' + PICKS.length + ' picks';

  // --- Tabs ---
  const tabButtons = document.querySelectorAll('#tabs button');
  tabButtons.forEach(b => b.addEventListener('click', () => {
    tabButtons.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
    document.getElementById('tab-' + b.dataset.tab).classList.remove('hidden');
  }));

  // --- Overview ---
  if (me) {
    document.getElementById('o-record').textContent = `${me.wins}-${me.losses}`;
    document.getElementById('o-record-sub').textContent =
      `PF ${Math.round(me.fpts)}  ·  PA ${Math.round(me.fpts_against)}`;

    const dynSorted = [...TEAMS].sort((a,b) => (b.dynasty_total||0) - (a.dynasty_total||0));
    const winSorted = [...TEAMS].sort((a,b) => (b.starters_winnow||0) - (a.starters_winnow||0));
    const dynRank = dynSorted.findIndex(t => t.owner_id === ME) + 1;
    const winRank = winSorted.findIndex(t => t.owner_id === ME) + 1;
    const startRank = [...TEAMS].sort((a,b)=>(b.starters_winnow||0)-(a.starters_winnow||0)).findIndex(t=>t.owner_id===ME)+1;

    document.getElementById('o-dyn').textContent = FMT.format(Math.round(me.dynasty_total||0));
    document.getElementById('o-dyn-rank').textContent = `#${dynRank} of ${TEAMS.length} league-wide`;
    document.getElementById('o-win').textContent = FMT.format(Math.round(me.winnow_total||0));
    document.getElementById('o-win-rank').textContent = `full roster`;
    document.getElementById('o-starters').textContent = FMT.format(Math.round(me.starters_winnow||0));
    document.getElementById('o-starters-rank').textContent = `#${startRank} of ${TEAMS.length}`;

    // Standings tables
    const dynTbody = document.querySelector('#t-dyn-standings tbody');
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

  // --- Rankings table ---
  const POS_ORDER = ['ALL','QB','RB','WR','TE','K','DEF','DL','LB','DB','PICK'];
  const posSet = new Set(PLAYERS.map(p => p.position).filter(Boolean));
  // include PICK as synthetic filter
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

  // Owners dropdown
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
    // Add delta
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

  // Rankings events
  document.querySelectorAll('#rank-view-toggle button').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('#rank-view-toggle button').forEach(x => x.classList.remove('active'));
      b.classList.add('active');
      state.view = b.dataset.view;
      // reset default sort for the view
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

  // --- Trade Calculator ---
  const sideA = []; const sideB = [];
  let posture = 'balanced';
  const POSTURE_WEIGHTS = { balanced: [0.5, 0.5], contender: [0.25, 0.75], rebuild: [0.8, 0.2] };
  // [dynasty_weight, winnow_weight]

  function allAssets() {
    // players (with trade values) + picks
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
    const delta = b.blended - a.blended;   // from my perspective (receiving - sending)
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
    // add delta
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

  // --- Methodology text ---
  document.getElementById('methodology').innerHTML =
    `<p><strong>Dynasty Score</strong> — ${DATA.meta.ranking_methodology.dynasty}</p>` +
    `<p><strong>Win-Now Score</strong> — ${DATA.meta.ranking_methodology.winnow}</p>`;
  document.getElementById('sources').innerHTML =
    `NFL stats through the <strong>${DATA.meta.latest_nfl_season} season, Week ${DATA.meta.latest_nfl_week}</strong>.
     Sleeper league + roster data from <code>${DATA.meta.league_name}</code> (id <code>${DATA.meta.league_id}</code>).
     Trade values from <strong>FantasyCalc</strong>.
     Re-run <code>scripts/refresh.sh</code> in your Fantasy Football folder and rebuild this artifact to refresh.`;
})();
</script>
</body>
</html>
"""

# Browser JSON.parse rejects bare NaN/Infinity (Python's json.dumps emits them).
# Sanitize the embedded data blob so the page actually renders in a browser.
DATA_JSON_SAFE = (
    DATA_JSON
    .replace("NaN", "null")
    .replace("-Infinity", "null")
    .replace("Infinity", "null")
)

with open("/sessions/quirky-lucid-cannon/mnt/outputs/huddlepuffers_platform.html", "w") as f:
    f.write(HTML.replace("__DATA_PLACEHOLDER__", DATA_JSON_SAFE))

print("wrote /sessions/quirky-lucid-cannon/mnt/outputs/huddlepuffers_platform.html")
import os
print("size:", os.path.getsize("/sessions/quirky-lucid-cannon/mnt/outputs/huddlepuffers_platform.html"), "bytes")
