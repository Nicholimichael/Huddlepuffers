# Huddlepuffers Weekly Review — 2026-04-22

## Headline: NFL Draft is tomorrow. Fix your refresh script. Sell Brian Robinson this week.

> **Executive summary** — Dead-quiet league activity, but the single most important offseason event in dynasty (the 2026 NFL Draft in Pittsburgh, April 23–25) starts in less than 24 hours. Your 49ers stash **Jordan James** is now the clear handcuff to CMC after Brian Robinson's move to ATL — a taxi-squad jackpot. **Christian McCaffrey is leaking value fast** (-343 over 30d) after Shanahan publicly said he wants him to play less. **Your roster has two sell-high windows right now (Brian Robinson, CMC) and one gift (Jordan James).** Also: the LaunchAgent refresh didn't run this morning — your Mac either wasn't awake or lost file-system permissions.

---

## ⚠️ Operational note — the automated refresh failed

The scheduled task `com.hossautomation.huddlepuffers-refresh` errored out ("Operation not permitted") on the last two Wednesday cycles. Today's digest was regenerated manually from the 2026-04-21 snapshot. Before next Wednesday:

1. Confirm Mac is awake at 7:00 AM Wednesday (wake schedule in `pmset`)
2. Re-grant Full Disk Access to `bash` / `launchd` in **System Settings → Privacy & Security → Full Disk Access**
3. Test with `launchctl kickstart -k gui/$(id -u)/com.hossautomation.huddlepuffers-refresh`
4. `nfl_data_py` isn't installed in the Cowork sandbox so the refresh won't work there either — the LaunchAgent is the only path to fresh NFL stats

---

## What actually changed this week

The FantasyCalc snapshot is one day old, so nothing moved week-over-week inside our warehouse. The real story is in the **30-day trend lines** and the **NFL free-agency dust** that has settled over the last 3 weeks:

- **Brian Robinson → Falcons** (late March) — signed a 1-yr cheap deal. He was on the 49ers last year, now handcuffs Bijan instead of CMC.
- **Travis Etienne → Saints** — but HC Kellen Moore says Alvin Kamara isn't going anywhere. Crowded.
- **Puka Nacua** back with Rams after rehab stint. Lawsuit still pending. Value -411 on the 30-day.
- **Ja'Marr Chase + Tee Higgins** both extended in Cincinnati. Higgins = $115M / 4yr. WR1/WR2 duo secured through Nick's competitive window.
- **Kyle Shanahan** explicitly said he wants "less wear and tear" for CMC in 2026. CMC value: -343 in 30 days.

---

## Top risers (league-wide 30-day) — why they moved

| Player | Trend | Why |
|---|---:|---|
| Kaytron Allen (RB, rookie) | +1,115 | Rising draft stock heading into Thursday — Penn State back, reported late-1st/early-2nd projection |
| Dontayvion Wicks (WR, GB) | +823 | Christian Watson ACL recovery + Reed uncertainty = clear WR2 opportunity in GB |
| Jordan James (RB, SF) ★ Nick's | +671 | **Brian Robinson walked to ATL; James is "front-runner" for CMC handcuff (Matt Barrows, The Athletic)** |
| Brian Robinson (RB, ATL) ★ Nick's | +642 | Signed with Falcons to back up Bijan — but replaces Tyler Allgeier who left for ARI |
| Harold Fannin (TE, CLE) | +357 | Rookie TE flash in Cleveland, David Njoku extension still unresolved |
| Ja'Marr Chase (WR, CIN) | +336 | Extension certainty + WR1 overall redraft consensus |
| Rashee Rice (WR, KC) | +327 | Suspension resolved, expected to be full-go for 2026 |
| Jeremiyah Love (RB, rookie) | +316 | Consensus 1.01 in dynasty rookie drafts (Notre Dame, Bijan-caliber profile) |
| Brock Bowers (TE, LV) | +311 | Bounceback candidate — only 680 yds in 2025 due to Week 1 knee injury; ADP says TE1 |

## Top fallers (league-wide 30-day) — why they moved

| Player | Trend | Why |
|---|---:|---|
| Jonah Coleman (RB, rookie) | -900 | Stock sliding in final pre-draft rankings |
| Makai Lemon (WR, rookie) | -738 | Was a "Big 3" WR at USC — now slipping on route-running concerns |
| Kenneth Walker (RB, KC) | -530 | Landed in KC backfield — committee with Hunt/Pacheco limits ceiling |
| Puka Nacua (WR, LAR) | -411 | Rehab stint + pending lawsuit from NYE incident |
| Jonathan Taylor (RB, IND) | -384 | Age-27 RB in run-first offense — dynasty window narrowing |
| **Christian McCaffrey** (RB, SF) ★ Nick's | **-343** | Shanahan: "less wear and tear"; 49ers expected to draft an RB |
| Bucky Irving (RB, TB) | -294 | Rachaad White resurgence + Egbuka targets eating RB passing work |
| Carnell Tate (WR, rookie) | -275 | Slight draft-stock dip but still likely top-3 rookie WR |

---

## 🎯 Action items for your roster

### SELL HIGH THIS WEEK (before NFL Draft noise buries the offer)

**1. Brian Robinson (RB, ATL) — Sell NOW.**
- Current value: 1,241 (+642 in 30d — peak post-FA bump already priced in)
- The reality: BRob is now a 27-year-old capped backup behind Bijan in a timeshare the Falcons explicitly called "balance." He'll likely revert to 600–800 yards with TD upside. Dynasty value bleeds from here.
- **Target trade partners:** rebuilders who need a cheap productive RB. Try **Romen Noodlez (R6, 2-12)** or **Team Basic AF (R8, 2-12)** — offer BRob + a 2027 2nd/3rd for their upcoming 2026 2nd or a young WR they've given up on.

**2. Christian McCaffrey (RB, SF) — Sell at whatever's left.**
- Current value: 4,204 (-343, and still falling)
- The age-30 RB with Shanahan publicly saying "less wear and tear" is a textbook sell signal. He'll probably finish as an RB1 for stretches, but his dynasty asset value in April 2027 is probably under 2,500.
- **Target:** a win-now team that missed in the playoffs. **Golden Receivers (R4, 10-4)** — they finished 3rd, were 5 points from the final, and could use a bellcow for one more run.
- **Asking price:** a 2026 1st + a young RB (e.g., Omarion Hampton) or a top-40 dynasty WR.

**3. DeVonta Smith (WR, PHI) — Consider selling.**
- +206 on the 30-day up to 3,299. He's 27, on a run-heavy Eagles team, and your WR room is already deep (Tee Higgins, DJ Moore, Egbuka, Jameson Williams, Worthy, Downs, McMillan, Aiyuk).
- If you can flip him for a **2026 top-5 rookie pick**, do it. He's peak ceiling right now.

### BUY LOW (if the owner is panicking)

**1. Puka Nacua (WR, LAR)** — -411 in 30 days. If anyone in the league is treating the lawsuit like a career-ender, he's a **buy-low all-star**. Still a top-5 dynasty WR talent at 25. Try **Winging It (R3, 7-7)** — they may be shopping impatiently.

**2. Kenneth Walker (RB, KC)** — -530. Goal-line package in a top offense is real; committee risk is overblown. Worth a look if anyone in the league is dumping.

### HOLD

- **Jordan James (RB, SF, taxi)** — Do NOT trade yet. He's the CMC handcuff heir apparent. If CMC gets injured, James could be a 1,000-yard back in the SF scheme with a massive dynasty value spike. He's on your taxi squad, which is perfect.
- **TreVeyon Henderson** — locked-in NE starter behind/ahead of Rhamondre; 2026 breakout candidate.
- **Emeka Egbuka** — TB WR2 role with Evans aging; hold through his sophomore leap.

### DROP CANDIDATES

- **Isaac Guerendo (RB, SF)** — 207 dynasty value. With James taking the CMC backup role, Guerendo is now #3 or #4 on the depth chart. Free your bench spot.
- **Jalen McMillan (WR, TB)** — 1,643 value. In a room with Evans, Godwin, and Egbuka. Ceiling is capped. If you need a taxi spot for a rookie after Thursday, he's the cut.

---

## 🏈 Rookie draft prep — this is the real game this week

**Your draft capital:**
- Your own 2026 1st (~pick 5–7 — 9-5 record, 4th seed)
- Your own 2027 1st
- **Team Basic AF's (R8) 2027 1st** — R8 finished 2-12, so if they repeat this could be top-3 in 2027
- You *lost* your 2026 2nd (to Golden Receivers) and 2026 3rd (to Team Basic AF)

**Targets at ~1.05–1.07:**
- If **Jeremiyah Love** slips (unlikely — he's consensus 1.01), trade up
- Likely targets: **Carnell Tate (WR, Ohio State)**, **Fernando Mendoza (QB, IND)**, **Sadiq (TE, freak)**, or a top 3 rookie RB (Kaytron Allen, Jam Miller)
- Be ready to trade DOWN from ~1.06 and accumulate picks if the player you want is already gone — this is a 3-deep RB class with a thin WR tier behind Tate.

**League rookie draft order (inverse 2025 standings, playoff-adjusted):**
1. Team Basic AF (R8) — 2-12 → **1.01 (Jeremiyah Love)**
2. Romen Noodlez (R6) — 2-12
3. Cow Tippers (R2) — 4-10
4. Speedway Jesus (R7) — 5-9
5. Winging It (R3) — 7-7
6. Tenacious D (R9) — 8-6
7. **High Settlers (Nick) — 9-5 → ~1.07**
8. Golden Receivers (R4) — 10-4
9. Lorde Commissioner (R1) — 11-3
10. Brady >Manning (R10) — 12-2 (champ)

*(Huddlepuffers may use a different tiebreaker — confirm in Sleeper settings — but that's the typical shape.)*

---

## 👀 League watch — owners to corner

- **Team Basic AF (R8)** — owns **1.01 (Love incoming)** and Nick's 2026 3rd. They're rebuilding; offer them **Brian Robinson + something** for the 1.01 if Love drops to a great landing spot (long shot, but ask). More realistically, trade for their 2027 1st before it recovers value from a strong rebuild year.
- **Golden Receivers (R4, 10-4)** — owns your 2026 2nd. They're a win-now team that just missed. **They are the #1 trade partner for CMC.** Pitch: CMC + your 1.07 for their Hampton/Cook-tier RB + your 2026 2nd back.
- **Brady >Manning (R10, champ)** — contending. They have no reason to sell. Skip them.
- **Lorde Commissioner (R1, 11-3)** — owns your 2025 3rd and 4th (already used). They're stacked and contending; only targetable if they're chasing a specific piece.
- **Romen Noodlez (R6)** — 2-12, full rebuild. Perfect recipient for your aging vets (CMC, Prescott, Kelce).

---

## 🔮 Next week to watch (draft-week list)

1. **Jeremiyah Love's landing spot** (Thursday night, 1st round) — if he goes to a premier RB situation (Broncos, Cowboys, Chargers), his dynasty value jumps another 10–15%. If he lands in a committee (PHI?), slight fade.
2. **Fernando Mendoza's draft slot** — the Heisman-winning QB. If he goes top-5, rookie QB value spikes across the board.
3. **49ers RB pick** — if SF takes a back Day 2 or earlier, Jordan James's "front-runner" label evaporates and his value cools. If SF doesn't, his value climbs another notch and you can actively entertain trading him.
4. **Patriots WR room** — if NE drafts a WR Day 1, that affects your TreVeyon Henderson (more passing concepts) and Rhamondre Stevenson (stays a pure runner). Watch the landing-spot dominoes.
5. **Rookie draft date & trade window** — confirm in Sleeper when the Huddlepuffers rookie draft is scheduled and when pre-draft pick trading closes. Get your trades in *before* the NFL Draft changes everyone's opinion.

---

*Generated 2026-04-22. Based on FantasyCalc snapshot 2026-04-21 + offseason news through April 22, 2026. League: The Huddlepuffers (league_id 1182393556535246848). Owner: Nmhochstedler (user_id 472596585608376320, team High Settlers, 9-5 in 2025).*

**Sources:**
- [2026 NFL Draft — Wikipedia](https://en.wikipedia.org/wiki/2026_NFL_draft)
- [2026 Dynasty Rookie Rankings — FantasyPros](https://www.fantasypros.com/nfl/rankings/dynasty-rookies-overall.php)
- [Jeremiyah Love 1.01 — SI](https://www.si.com/onsi/fantasy/nfl/2026-dynasty-rookie-mock-draft-round-1-jeremiyah-love-headlines-top-prospects)
- [49ers' Backfield Shake-Up Opens Door for Jordan James — Yahoo](https://sports.yahoo.com/articles/49ers-backfield-shake-opens-door-120037060.html)
- [Falcons sign Brian Robinson — Fantasy Index](https://fantasyindex.com/2026/03/24/around-the-nfl/falcons-sign-brian-robinson)
- [Puka Nacua returns to offseason program — NFL.com](https://www.nfl.com/news/puka-nacua-attends-first-day-rams-offseason-program-rehab-stint)
- [Tee Higgins contract details — SI Bengals](https://www.si.com/nfl/bengals/onsi/news/look-contract-details-for-tee-higgins-new-extension-with-cincinnati-bengals-01jpd7dxeqa2)
- [2026 Top 5 RBs — No McCaffrey — SI](https://www.si.com/onsi/fantasy/rankings/2026-fantasy-football-top-5-running-backs-bijan-robinson-but-no-christian-mccaffrey)
