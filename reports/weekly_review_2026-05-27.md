# Huddlepuffers Weekly Review — 2026-05-27

_Layered narrative on top of `weekly_digest_2026-05-27.md`._

## Executive summary (what changed this week)

Quietest league week of the offseason — **zero transactions league-wide since 5/20**, and no trade chatter to react to. The action was all in the market: Josh Jacobs was charged in a domestic violence case (price down −370, −11%), Najee Harris's free-agency tour drove a +109% bounce off the floor, and Bears TE Colston Loveland keeps climbing on Year-2 hype after Chicago traded DJ Moore. **Your roster ticked up +578 (+0.87%) to 67,124** — McCaffrey and Jeanty did the work, DeVonta Smith and Jalen McMillan softened. Headline for the week: **sell-high window cracking open on McCaffrey; do nothing rash on DeVonta yet.**

> ⚠ Operational note: `refresh_platform.sh` still cannot run end-to-end from Cowork — sandbox blocks the macOS paths and the SQLite I/O error from 5/20 is still parked in `db/`. The live site at huddlepuffers.hossautomation.com is actually showing the **5/13 build** — the 5/20 attempt died at the SQLite step before Netlify was ever called, so the dashboard hasn't refreshed in 14 days. The path-resolution fix has now been applied to `scripts/refresh_platform.sh` (see "Operational" section). You just need to run it once from Terminal with the journal cleanup.

---

## Risers — why they moved

| Player | Δ | Why |
|---|---:|---|
| **Colston Loveland (TE, CHI)** | +392 | Year-2 hype is now consensus. Bears traded DJ Moore earlier this offseason, target tree narrows, and analysts are openly calling him a high-end TE1 for 2026. Comments coming out of his post-concussion recovery have been bullish. |
| **Tetairoa McMillan (WR, CAR)** | +312 | 2025 OROY (70/1,014/7) — but tempered by **foot soreness at OTAs** this week. Coaches "not concerned," resting him preemptively. Market is paying for the OROY tag despite the minor flag. |
| **Christian McCaffrey (RB, SF)** | +258 | All-RB1 in 2025 (413 touches, 2,100+ yards), and Shanahan publicly said he wants to give CMC more breathers in 2026. Market is paying for the resume, even though he turns 30 in June. **This is the textbook sell-high window.** |
| **Najee Harris (RB, FA)** | +247 (+109%) | Pure landing-spot speculation. Agent says he's "running with ease" on the Alter-G five months post-Achilles surgery. He's already visited SEA and LV. The +109% is off a floor of $230 — he's still RB275, not a real asset until he signs. |
| **Justin Jefferson (WR, MIN)** | +233 | No fresh news — looks like a quiet market correction back toward consensus WR1/WR2 status. |
| **De'Von Achane (RB, MIA)** | +225 | Same — minor positive drift, no specific catalyst this week. |
| **Tyler Warren (TE, ?)** | +210 | Rookie TE2 of the 2025 draft class continuing his post-draft rise. |
| **Mike Evans (WR, TB)** | +208 (+10.5%) | Bounce back from a sell-off; still aging but cleared off the bottom. |
| **Bijan / Hampton / Jeanty** | +198 / +197 / +192 | RB1, RB14, RB6 — all top-15 dynasty RBs ticked up together. Looks like a small RB-tier-wide rerating, not specific to any of them. |
| **Cade Otton (TE, TB)** | +190 (+23%) | Late-round TE deep-leaguer move; no specific news, probably a one-pundit ranking shift filtered through. |

## Fallers — why they moved

| Player | Δ | Why |
|---|---:|---|
| **Josh Jacobs (RB, GB)** | −370 | **Material news**: charged in a domestic-violence case. Packers said they'll let the legal process play out before acting. Cap implications, suspension risk, contract pressure ($11.5M in '26, $13.5M in '27) — all open. Real-money downside. |
| **Brock Bowers (TE, LV)** | −366 | Confusing one. Public narrative is bullish — Kubiak called him "a football robot from heaven," Kirk Cousins said "best TE in football," Seth Rollins on GMFB predicted 100 catches. The −5% looks like FC reweighting after his late-2025 bump rather than a new negative. Don't read this as a sell signal. |
| **Jaxon Smith-Njigba (WR, SEA)** | −266 | No bad news — small drift from WR4. Probably positional volatility, not signal. |
| **Tre Tucker (WR, LV)** | −244 (−23%) | Kubiak/Cousins arrival means more targets get vacuumed back to Bowers and the WR1 — Tucker is the squeeze play. |
| **Tez Johnson (WR, TB)** | −208 | Deep-roster rookie, OTA reports unfavorable. |
| **Jahmyr Gibbs (RB, DET)** | −204 | RB2 overall ticked down −1.9% — noise, not signal. |
| **Justin Fields (QB, NYJ)** | −200 (−30%) | Continued QB2/streamer-only positioning. Market giving up on him as a starter. |
| **Zach Charbonnet** | −191 | Backup behind Walker, no path. |
| **Audric Estime** | −168 (−72%) | Off the depth chart, training-camp body. |
| **Travis Hunter (WR/CB, JAX)** | −166 | Two-way usage uncertainty resurfacing. The "fantasy ceiling" debate is back. |
| **Terrance Ferguson** | −154 | Rookie TE drift downward. |

---

## Action items — your roster

### Sell-high candidates

1. **Christian McCaffrey** (RB, SF, +258 this week, 4,775 value, RB22) — **strongest sell-high candidate on your roster.** Turns 30 in June, coming off 413 touches, and the market just paid you another +5.7%. The Shanahan "more breathers" quote is doing real work in the price. Target return: a 2027 1st + a young RB3 piece, or a young WR2 + late pick. Don't dump for less. Pair offer to **isaacimel** (he just made Najee Harris a +109% bet — he's reaching for RB volume) or **Forshey11** (Conner just lost −159, his RB depth is thin).
2. **Travis Kelce** (TE, KC, +92) — same age logic. If Freiermuth's +178 is real (and Kraft is still your starter at 3,145), Kelce becomes a tradeable depth piece. Probably only worth a late pick or a buy-low WR.

### Hold

- **Ashton Jeanty** — RB6 overall, +192 this week, no reason to move. Cornerstone.
- **Pat Freiermuth** (+178) and **Tucker Kraft** (−46 but still 3,145, your TE1) — TE room is fine.
- **DJ Moore** (+44) and **Josh Downs** (+55) — both quietly up; nothing to do.

### Watch (don't act yet)

- **DeVonta Smith** (−102, the −102 follows last week's +193 — wash over two weeks). Not a sell signal yet, but if it drops another week without a positive catalyst, start exploring offers. Eagles WR room is fine; this looks like noise.
- **Jalen McMillan** (−112) — Bucs WR depth chart unsettled. If Evans' +208 means TB is back to a top-two target tree (Evans + Egbuka), McMillan's role shrinks. Currently 1,279 value — probably worth a low-end WR4-tier flier offer to clear the roster spot for someone else's Jordan James-shaped lottery ticket.
- **Brian Robinson** (−42, 1,360) and **Jaylen Warren** (+42, 2,018) — both backups whose value depends on incumbent injury. Hold.

### Drop / cut bait

- Nothing screams cut this week. Your bottom-of-roster (Guerendo, Mayer, Willis) all moved in normal noise ranges. Save drops for after the rookie draft when you'll need slots.

### Hot waiver/buy-low targets (league-wide market)

- **Najee Harris** (isaacimel) — if he signs somewhere with a path (Raiders looks most likely given recent visit), the +109% this week is just the start. **Don't try to acquire from isaacimel** — he's not selling something he just bought into. Watch for the next FC update after a signing.
- **Mike Evans** (+208, colsheske) — buy-low window may already have closed.
- **Josh Jacobs** (thedukestill) — **morally and operationally fraught.** DV charge is serious. Even if dynasty value rebounds on a legal outcome, you do not want this player on your roster and Nick has been clear about clean roster construction. Pass.

---

## League watch — what other owners did

No transactions this week, so the "watch" is value movement, not moves:

- **colsheske** (your biggest division rival on the value board): Bijan +198, Hampton +197, Mike Evans +208 — three top-15 RB/WR assets up. But **Bowers −366** is the offsetting story. Net still up. He is still the team to beat.
- **chochstedler**: **Loveland +392** is the headline. He sits on the best young TE in dynasty right now (debatable vs. Bowers, but trending). Justin Fields −200 doesn't matter — depth piece.
- **thedukestill**: **Jacobs −370** is the bad news, partially offset by Tyler Warren +210 and Cade Otton +190 (TE-heavy roster construction continuing). Vulnerable at RB. Worth pinging him next week to see if he's panicking — could be a window to pry a TE.
- **isaacimel**: **Najee Harris +247 (+109%)** and **JJ +233** are big, but offset by Tre Tucker −244 and Estime −168. Net positive but he's exposed at WR depth.
- **mmmatlock**: Hunter −166, Charbonnet −191, Ferguson −154 — rough week, no big gainer to balance it. He may be soft. Worth checking back in two weeks.
- **Swerve33**: McMillan +312 is the win.
- **aigo100**, **SpeedwayJesus**, **Forshey11**: quiet on both sides.

---

## Next week to watch

1. **Najee Harris signing.** If he lands in LV behind a thin RB room, he's a real piece. If SEA, behind Walker/Charbonnet, lottery ticket. The signing news drives the next move in his value — and possibly Charbonnet's.
2. **Josh Jacobs legal update.** Any movement (suspension, dropped charges, plea) will reprice him hard either direction.
3. **Tetairoa McMillan foot.** "Soreness, not concerned" today can become "PUP candidate" tomorrow. If the next OTA report reuses the word "soreness," start treating it as a yellow flag.
4. **Tucker Kraft (TE, GB) Jacobs fallout.** If GB shifts target distribution because of the Jacobs uncertainty, Kraft (your TE1) sees more red-zone work. Watch the next FC update.
5. **Bears OTA reports / DJ Moore replacement.** Loveland's +392 partly assumes target consolidation. If Chicago signs/trades for a veteran WR, some of that comes back.

---

## Operational — getting the live site current

The refresh script has been broken for two consecutive weeks from Cowork. You have two paths:

**The portable-path patch has already been applied** to `scripts/refresh_platform.sh` (lines 14–22). It now derives `PROJECT_ROOT` from its own location, so it runs identically on Mac, Cowork, and launchd — verified resolving correctly to both `/Users/Consulting/Documents/Claude/Projects/Fantasy Football` (Mac) and `/sessions/.../mnt/Fantasy Football` (sandbox).

**You still need to run it once from Terminal on the Mac** to clear the SQLite corruption and push the deploy. The Cowork sandbox can't write to the SQLite DB (TCC permission issue is separate from the path issue), so the actual data refresh has to happen on the Mac:

```bash
cd "/Users/Consulting/Documents/Claude/Projects/Fantasy Football"
rm -f db/fantasy.sqlite-journal db/fantasy.sqlite.fresh db/_test_write.txt db/_writetest db/fantasy.sqlite-journal.stale-*
bash scripts/refresh_platform.sh
```

The `rm` line clears the leftover SQLite journal from the 5/20 corruption. After that, every future weekly run should "just work" — including from Cowork, with the caveat that Cowork still can't deploy (no Netlify CLI auth there). The clean flow going forward is: Cowork generates the digest + narrative; Mac runs the refresh to update the live site.

**Until that one-time Mac run happens, the dashboard at huddlepuffers.hossautomation.com remains on the 5/13 build (14 days stale).**

---

## Sources

- [Colston Loveland — fantasy outlook 2026 (Bear Goggles On)](https://beargoggleson.com/chicago-bears-fantasy-analyst-has-understandably-cautious-view-of-colston-loveland-for-2026)
- [Najee Harris — dynasty value re-establishment (Rotoballer)](https://www.rotoballer.com/player-news/can-najee-harris-re-establish-some-dynasty-value-in-2026/1857774)
- [Najee Harris — Chargers / Seahawks / Raiders visits (FantasyPros)](https://www.fantasypros.com/nfl/players/najee-harris.php)
- [Josh Jacobs — DV charge and contract impact (A to Z Sports)](https://atozsports.com/nfl/green-bay-packers-news/josh-jacobs-arrest/)
- [Josh Jacobs — dynasty value at peak? (Rotoballer)](https://www.rotoballer.com/player-news/is-josh-jacobs-at-the-peak-of-his-dynasty-value/1863600)
- [Brock Bowers — "robot from heaven" Klint Kubiak quote (Review Journal)](https://www.reviewjournal.com/sports/raiders/raiders-robot-from-heaven-brock-bowers-maxx-crosby-excite-klint-kubiak-3826972/)
- [Brock Bowers — strong outlook under Kubiak (Heavy)](https://heavy.com/sports/nfl/las-vegas-raiders/brock-bowers-strong-outlook-klint-kubiak/)
- [Tetairoa McMillan — foot soreness at OTAs (Panthers.com)](https://www.panthers.com/news/three-takeaways-from-friday-including-dave-canales-hoping-tetairoa-mcmillan-can-play)
- [Christian McCaffrey — sell-high case (Yahoo Sports)](https://sports.yahoo.com/fantasy/article/fantasy-football-dynasty-sells-it-might-be-time-to-cut-patrick-mahomes-christian-mccaffrey-loose-174629264.html)
- [Christian McCaffrey — reality check on selling (DLF)](https://dynastyleaguefootball.com/2026/04/16/dynasty-trades-reality-check-christian-mccaffrey/)
