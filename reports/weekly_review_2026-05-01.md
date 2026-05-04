# Huddlepuffers Weekly Review — 2026-05-01

## Headline: 48 hours of fresh FC data confirms — **DeVonta Smith trend30 jumped to +444 (peak sell window is TODAY), Puka Nacua's slide DECELERATED to -314 from -564 (buy window NARROWING), and Tucker Kraft's -98 trend30 is ACL noise, not a sell signal.** Plus: 124 days since the last league transaction.

> **Executive summary** — Two days after the 4/29 review, the post-draft FC re-price has produced more separation, not less. DeVonta Smith ripped through the sell ceiling (trend30 +391 → +444) — this is the **absolute top tick** of the offseason and you have one move-window before next Wednesday's re-pricing cycle. Puka Nacua's slide decelerated meaningfully (-564 → -314) and McVay confirmed he's a "full participant" at OTAs — buy window is **narrowing fast**, not widening. Tucker Kraft's -98 trend30 is the market mispricing ACL recovery for a player who'll be GB's #1 target after Doubs walked — **flip the 4/29 sell-or-hold flag to HOLD.** Jordan James shed another -85 in 2 days (trend30 -40, was +49); the Black narrative is fully baked and James is now a "survives as a 3rd-down back" bet, not "inherits CMC's workload." Brian Robinson trend30 turned negative (-2 → -49) — the plateau is over, the slide started; sell **this week** or accept the price has settled. League: 0 transactions, 124 days of silence — Nick remains the only owner watching the cycle.

---

## ⚠️ Operational note — refresh status (UNCHANGED FROM 4/29)

- **The macOS LaunchAgent did not fire today.** It's only scheduled for Wednesdays at 7:00 AM, so a 5/1 (Friday) absence is *expected* — but the underlying Full Disk Access permission issue from the 4/29 review **has not been verified fixed.** The next test fire is Wednesday 5/6.
- **What ran today inside Cowork sandbox (manual):**
  - ✓ `fetch_sleeper.py` — Sleeper rosters/transactions/users refreshed (db updated 19:08).
  - ✓ `fetch_fantasycalc.py` — fresh FC values pulled (CSV written 19:09, 463 rows).
  - ✗ `fetch_nfl_stats.py` — not run (offseason, no new game data).
  - ✗ `build_rankings.py` / `build_artifact_v2.py` — **failed again** with `disk I/O error` on the SQLite write step. Same journal-permission issue as 4/29.
  - ✓ `weekly_digest.py` — ran cleanly, but the diff is mechanically empty because rankings_data.json wasn't rebuilt today (composite dynasty_score values are still on the 4/28 baseline).
- **Bottom line:** FC values in this review are **fresh as of 5/1 19:09 UTC**. The platform HTML and composite dynasty_score are still 3 days stale. The deltas in this review are computed against 4/29 FC pulls (not the empty 5/1 digest).
- **Action for Nick — do this BEFORE Tuesday night 5/5 so the 5/6 LaunchAgent fire is clean:**
  1. System Settings → Privacy & Security → **Full Disk Access** → add `/bin/bash` and `launchd`
  2. Run the bootstrap commands in the 4/29 review (lines 14–17)
  3. Manually delete `db/fantasy.sqlite-journal` and `db/fantasy.sqlite-journal.bak` in Finder (the sandbox can't unlink them, which is what's tripping the rebuild)
  4. Verify with `launchctl kickstart -k gui/$(id -u)/com.hossautomation.huddlepuffers-refresh` and check `logs/refresh_2026-05-01_*.log` shows clean exit
  - If you don't have time before 5/6, the manual catch-up pattern continues to work — but the dashboard HTML drifts further out of sync each week.

---

## What changed in 48 hours (since the 4/29 review)

### 1) The 4/27 → 4/29 → 5/1 trendline confirms every directional call — and **widens the spreads**

| 4/27 thesis | 4/27 trend30 | 4/29 trend30 | **5/1 trend30** | Reading |
|---|---:|---:|---:|---|
| BRob "will plateau then slide" | +642 | -2 | **-49** | ✓ Plateau done. Slide started. **Urgency: HIGH** (downgraded from MAX, then re-confirmed). |
| JT "buy-low — workload locked" | -384 | +159 | **+299** | ✓ Bounce intensifying. **NOT a buy at this price.** |
| CMC "Black confirms sell" | -343 | -17 | **-5** | ✓ Slide stopped. Floor set. **Sell window narrowing — pitch by 5/8.** |
| Puka Nacua "still slipping — pounce" | -411 | -564 | **-314** | ⚠️ Slide decelerating. **Buy window NARROWING.** McVay confirmed full OTA participation. |
| Bowers "+311 trend keeps lifting" | +311 | +413 | **+202** | ✓ Still climbing but trend slowing. Premium TE1. Not on Nick's roster. |
| DeVonta Smith "Lemon priced in — sell" | +206 | +391 | **+444** | ✓ Sell window WIDER again. **This is the top tick. Today.** |
| Jordan James "Black hurts thesis" | +671 | +49 | **-40** | ✓ Narrative fully priced. -85 in 2 days. **Inflection: hold-vs-drop.** |
| Tucker Kraft (4/29 flag: "watch — sell or build around slide") | n/a | +36 | **-98** | ⚠️ Slide accelerated, but **fundamentals say buy/hold not sell** (see #3). |

The 4/27 → 5/1 pattern is the cleanest evidence yet that **Nick's read of the post-draft FC re-pricing cycle was right** — every directional call hit. The two pieces of *new* nuance from today:

- DeVonta Smith continues to climb when the assumption was the Lemon pick would clip the trend30. **It hasn't.** The Eagles' WR room (Smith #1, Lemon slot, Hollywood Brown / Moore / Wicks below) means Smith is locked in as the alpha, and the market is rewarding that clarity. **Sell today, before next Wednesday's re-price.**
- Puka's slide decelerating + McVay's "full participant" comment at OTAs ([NBC Sports](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/lawyer-puka-nacua-will-be-available-for-all-rams-2026-otas), [ESPN](https://www.espn.com/nfl/story/_/id/48553704/rams-sean-mcvay-puka-nacua-doing-really-well-otas)) is the catalyst that closes the buy window. The 4/29 thesis was "buy window OPEN and likely brief" — **the brief part is now real.** Get an offer to aigo100 by Sunday 5/3.

### 2) Your roster — 48-hour FC moves (vs 4/29 baseline)

| Player | Pos | Team | 4/29 | **5/1** | 2-day Δ | trend30 | Read |
|---|---|---|---:|---:|---:|---:|---|
| Travis Hunter | WR | JAX | 1,936 | **2,130** | **+194** | +15 | Big jump. Likely OTA buzz; check beat reporters. |
| Marvin Harrison Jr | WR | ARI | 3,469 | **3,561** | +92 | +133 | Slow steady up. Hold. |
| Tyrone Tracy | RB | NYG | 1,423 | **1,504** | +81 | +374 | Skattebo competition is priced; Tracy holding. |
| Keenan Allen | WR | FA | 193 | **261** | +68 | -4 | Bounce off floor. Still drop. |
| Hunter Henry | TE | NE | 852 | **910** | +58 | -74 | Roster fodder. |
| Ja'Tavion Sanders | TE | CAR | 395 | **452** | +57 | +26 | TE3 stash. |
| Chuba Hubbard | RB | CAR | 2,175 | **2,220** | +45 | +192 | Still rising. Hold or sell at 2300+. |
| Rachaad White | RB | WAS | 1,555 | **1,600** | +45 | +66 | Quiet stabilization. |
| DeVonta Smith | WR | PHI | 3,357 | **3,390** | +33 | **+444** | **SELL — peak.** |
| Bhayshul Tuten | RB | JAX | 2,550 | **2,545** | -5 | +127 | Held the +292 jump. Hold. |
| Brian Robinson | RB | ATL | 1,413 | **1,403** | -10 | **-49** | **SELL — slide started.** |
| Eli Raridon | TE | NE | 883 | **858** | -25 | **+869** | Trend30 still elite. Speculative add. |
| Tucker Kraft | TE | GB | 3,002 | **2,964** | -38 | -98 | Market mispricing ACL noise — **HOLD.** |
| Travis Etienne | RB | NO | 3,428 | **3,369** | -59 | +101 | Slow drift. Sell at price floor. |
| Christian McCaffrey | RB | SF | 4,451 | **4,373** | -78 | -5 | **SELL by 5/8** — floor priced. |
| Jordan James | RB | SF | 899 | **814** | -85 | -40 | Hold-vs-drop inflection. |
| Kyle Williams | WR | NE | 966 | **844** | -122 | -295 | Drop candidate. |
| George Pickens | WR | DAL | 4,567 | **4,343** | -224 | **-369** | Cratering. Owner is chochstedler. Watch for fire-sale offers. |

**One-line takeaways:**
- **Your two biggest sells (Smith, BRob) are diverging:** Smith is still climbing, BRob is now declining. Pitch Smith first (more upside left); pitch BRob second (price has settled).
- **Travis Hunter's +194 in 48 hours is the surprise mover on your bench.** No injury news, no depth chart move I can find — likely OTA hype/film clips from JAX. If he keeps climbing, he becomes a viable trade-out asset alongside Smith.
- **Tucker Kraft -38 today + -193 on 4/29 = -231 over 4 days.** The market is pricing ACL-recovery uncertainty. The fundamentals ([Zone Coverage](https://zonecoverage.com/2026/packers/green-bay-must-prioritize-extending-tucker-kraft/), [Cheesehead TV](https://cheeseheadtv.com/blog/the-time-for-the-green-bay-packers-to-sign-tucker-kraft-to-an-extension-is-now-401)) are: (a) Romeo Doubs left in FA — Kraft inherits ~83 vacated targets; (b) Packers' own front office is talking $15.5M/yr extension; (c) Kraft was on a 1,039-yard / 13-TD pace before the November ACL. **The 4/29 "trade him soon or build around the slide" flag should flip to HOLD.** This is a buy-low for someone, not a sell window for Nick.

### 3) Tucker Kraft — flipping the 4/29 sell flag

The 4/29 review flagged Kraft's -193 day as "either trade him soon or build around the slide." Today's added context changes that read:

- **Doubs walked.** Romeo Doubs's 83 targets in 2025 are vacant. Kraft was already GB's leading receiver before his ACL — he's the #1 target by default in 2026.
- **Packers are signaling extension.** Spotrac models a 4-year, $62M extension at ~$15.5M/yr. That's a top-3 TE deal — locking in Kraft as Jordan Love's #1 read for 4 more years.
- **Pre-injury 17-game pace was 1,039 / 13.** Top-3 TE production. Bowers and McBride are the only TEs operating at that ceiling.
- **What the market is pricing instead:** ACL recovery uncertainty + the late-round TE the Packers added ([SI](https://www.si.com/nfl/packers/onsi/these-tight-ends-might-not-be-on-packers-2026-nfl-draft-board)) being seen as a threat. Both are noise.

**Verdict: HOLD Kraft.** If he drops below 2,800 — **buy more of him from any owner who'll deal.** This is the offseason 2026 buy-low setup that fantasy managers will look back on in October.

### 4) Puka Nacua — buy window is NARROWING, not widening

The 4/29 thesis: "Buy window is OPEN and likely brief." Today's data: trend30 -314 (was -564) + McVay's "full participant" quote = **the deceleration started.** Once trend30 inflects positive (likely 5/3–5/8 once OTAs film hits Twitter), the pricing premium snaps back. Nacua's *football* picture is unchanged from 4/29 — healthy, in the building, no league discipline ([Pro Football Rumors](https://www.profootballrumors.com/2026/04/puka-nacua-a-full-participant-in-rams-offseason-program), [NFL.com](https://www.nfl.com/news/attorney-says-rams-wr-puka-nacua-in-rehab)). The lawsuit will be a slow-burn legal fight; the OTA narrative will overwhelm it once practice clips drop.

**Get an offer in front of aigo100 by Sunday 5/3.** Not Friday-after-work — *Sunday*, ahead of the Monday news cycle.

### 5) Jordan James — closer to the drop trigger

4/29: trend30 +49, val 899. Today: trend30 -40, val 814. The -85 in 2 days is the first time James has dropped this fast since the Kaelon Black pick. The narrative is now fully priced: ([NBC Sports Bay Area](https://www.nbcsportsbayarea.com/nfl/san-francisco-49ers/draft-pick-kaelon-black-indiana/1934030/), [Yahoo Sports](https://sports.yahoo.com/articles/49ers-select-indiana-rb-kaelon-195438637.html)) confirms Black is the rookie pick competing with James for the CMC backup role. **The drop trigger from 4/29 was "if FC reprices James DOWN below 700, switch to drop."** Today: 814. **One more bad week and he hits the trigger.** Hold through 49ers OTAs (late May), but **set a stop-loss at 700.**

### 6) League activity: 0 transactions, 124 days of silence

The 4/29 digest noted 122 days. Today: **124.** Last move was Lorde Commissioner's FA pickup on 2025-12-28. The league is in the deepest dormancy of any Huddlepuffers offseason on record (the 2024 offseason had 11 transactions in the same Apr 1–May 1 window).

**Why this matters for Nick's strategy:** Every other owner is letting Nick cherry-pick the FC pricing cycle without competition. The first owner to fire offers after the rookie draft will set the market — and the rookie draft start date is unconfirmed in Sleeper. **Nick should fire 3 offers by EOD Friday 5/2:** Smith, CMC, and Nacua-buy. None require counter-pings; all three should land in inboxes before the weekend.

---

## 🎯 Action items for Nick's roster — UPDATED from 4/29

### SELL HIGH — pitch THIS WEEK before the 5/6 FC re-price erodes the spread

**1. DeVonta Smith (WR, PHI) — urgency: MAXIMUM (held from 4/29)**
- val 3,390, trend30 **+444** (was +391 on 4/29). The market is still rewarding Smith despite Lemon. The Eagles signed Lemon to a 4-year, $20.8M deal ([Bleacher Report](https://bleacherreport.com/articles/25423542-makai-lemon-eagles-agree-rookie-contract-115m-signing-bonus-after-2026-nfl-draft)) — but the team's confirmed Smith stays as #1 with Lemon in the slot ([NBC Sports Philly](https://www.nbcsportsphiladelphia.com/nfl/philadelphia-eagles/devonta-smith-makai-lemon-eagles-wide-receiver-duo/730854/)).
- **Pitch (highest value):** Smith + late 2027 pick → 1.04–1.06 in a contender's 2026 rookie draft.
- **Pitch (broader):** Smith → 2026 1st (any non-bottom-3) + a young WR.
- **Send by EOD Friday 5/2** — three different owners, three different framings. Forshey11 / Brady>Manning / Golden Receivers.

**2. Christian McCaffrey (RB, SF) — urgency: HIGH (held from 4/29)**
- val 4,373, trend30 -5 (essentially flat). Floor is set. Every additional offseason day trims his value as he ages out.
- **Pitch:** CMC → Golden Receivers (R4, 10-4) for their 2026 2nd + a player. Their need for a bell-cow is unchanged. Send by 5/3.
- **Backup target:** Romen Noodlez (R6) full rebuild — they'll take CMC for a 2027 1st flier.

**3. Brian Robinson (RB, ATL) — urgency: HIGH (downgraded from MAX on 4/29, but slide is real)**
- val 1,403, trend30 **-49** (was -2). The plateau the 4/27 review predicted has hit and the slide started.
- **Pitch (best):** BRob + your 2027 2nd → Team Basic AF's (R8, 2-12) 2026 2nd round pick. They've ignored 4 months of DMs — try a fresh subject line and one-sentence pitch ("BRob + 2027 2nd for your 2026 2nd?").
- **Floor offer:** BRob straight-up for any 2026 2nd.
- **Hard deadline:** if no offer hits by 5/8, accept the price has settled and roster him as RB depth into the season.

**4. Travis Etienne (RB, NO) — urgency: MEDIUM (held from 4/29)**
- val 3,369, trend30 +101. Slow drift, no urgency. Pitch as a throw-in ahead of any larger trade.

### BUY LOW — windows narrowing fast

**1. Puka Nacua (WR, LAR) — urgency: MAXIMUM (UPGRADED from 4/29)**
- val 8,343, trend30 -314 (was -564). **The slide is decelerating.** McVay said full OTA participation; Snead said "doing really, really well." Once OTA practice clips hit Twitter (likely 5/26+), the pricing snaps back.
- **Pitch:** Your 2026 1st (your own ~1.07) + DeVonta Smith → Nacua. Send to aigo100 **by Sunday 5/3.**
- **Backup:** 1.07 + Tee Higgins → Nacua.
- **If aigo100 declines:** monitor for any league discipline announcement. If "matter under review" stays "under review" for another 30 days, the buy window quietly closes.

**2. Tucker Kraft (TE, GB) — NEW ADD (flipped from 4/29 sell flag)**
- val 2,964, trend30 -98. Market is mispricing ACL recovery + Doubs absence. **Acquire MORE Kraft if you can.**
- **Pitch:** any TE-needy team's 2026 3rd + a UDFA filler → Kraft from someone dropping him. (You already own him; this is a "buy more if anyone tries to sell" alert.)

**3. Christian Watson (WR, GB) — speculative (held from 4/29)**
- ACL recovery, GB WR room shaky. Cheap dart.

### MODIFIED HOLD

- **Jordan James (RB, SF)** — val 814, trend30 -40. **Hold through 49ers OTAs; stop-loss set at 700.** If James reps with the 1s on third down by mid-June, value spikes back; if Black is poaching short-yardage AND third-down, drop and free the roster spot.

### DROP CANDIDATES (unchanged from 4/29 unless noted)

- **Keenan Allen (WR, FA)** — val 261 (bounced from 193). Still no team. **Drop today.**
- **Isaac Guerendo (RB, SF)** — val 142 (was 207). 4th on SF depth chart. **Drop today.**
- **Davis Mills (QB, HOU)** — val 82. **Drop.**
- **Michael Mayer (TE, LV)** — val 621 (was 666). Bowers locked in as TE1. **Drop for any 2026 rookie TE2.**
- **Jalen McMillan (WR, TB)** — val 1,480 (was 1,643). Crowded TB room, bleeding -173 trend30. **Drop by 5/13** if no camp news lifts him.

### SPECULATIVE ADDS

- **Eli Raridon (TE, NE)** — val 858, trend30 **+869**. FA in your league. The trend30 is still the highest on the FC board. If you drop Mayer, replace him with Raridon.
- **Cam Skattebo (RB, NYG)** — val 3,331, trend30 +256. Owner Forshey11. Hold for now; he's their roster, not yours. But if Forshey11 starts shopping (he's a known active manager), Skattebo into your RB room as a CMC replacement is the move.

---

## 🏈 Rookie draft — your 1.07 plan (unchanged from 4/29)

The 2026 NFL Draft is fully complete. Plan stands:

**Top 5 board names that will be GONE before 1.07:**
- Jeremiyah Love (1.01), Carnell Tate (1.02–1.04), Jordyn Tyson (1.04–1.06), Makai Lemon (1.05–1.06), Ty Simpson (top of the board if superflex).

**Tier 2 names that should still be on the board at 1.07:**
- **Jadarian Price (RB, SEA, NFL #32)** — val 3,643 (+74 in 48 hours), trend30 **+865**. Strongest landing-spot value at your slot. Walker is gone to KC, Charbonnet still in ACL recovery — Price has the cleanest path of any non-top-5 rookie RB.
- **Cam Skattebo (RB, NYG)** — val 3,331, trend30 +256. NYG took him in 2026 NFL Draft. Devin Singletary is now 27 and contract-thin. Clean path, worse offense.
- **Kaytron Allen (RB)** — check landing spot; FC tagging may not have fully propagated.

**Recommendation (unchanged):**
1. **First:** Trade 1.07 for **2 picks in the 1.10–2.04 range.** Talent gap is real — better to take two darts.
2. **Second:** Take Jadarian Price at 1.07 if no good trade-down materializes.
3. **Third (superflex only):** Mendoza.

**Your draft capital (unchanged):**
- 2026 1st (your own ~1.07; 9-5, 4th seed)
- 2027 1st (your own)
- **Team Basic AF 2027 1st (theirs; 2-12 — likely 1.01–1.03)**
- You do NOT have 2026 2nd (Golden Receivers) or 2026 3rd (Team Basic AF) — top buy-back targets if you sell Smith/CMC/BRob.

---

## 👀 League watch — owners worth pinging this week

| Owner (Team) | Why now |
|---|---|
| **aigo100 (Puka owner)** | URGENT. Buy window narrowing as Nacua's OTA participation decelerates the slide. Send your Smith-for-Nacua pitch by Sunday 5/3. |
| **Team Basic AF (R8, 2-12)** | Holds your 2026 3rd; their 2027 1st is yours. Re-ping with BRob + 2027 2nd → 2026 2nd. **Fresh subject line.** Try email or text instead of Sleeper DM if you have his number. |
| **Golden Receivers (R4, 10-4)** | Holds your 2026 2nd. Top CMC sell target. Their rookie draft moves haven't started — you're early. Send the CMC pitch by Sunday 5/3. |
| **chochstedler (George Pickens owner)** | NEW — Pickens trend30 -369, dropped -224 in 48 hours. If chochstedler panic-sells, Pickens at 4,000 or below is a buy-low for a contender. Watch for offers. |
| **colsheske** | Hampton dropped -160 in 48 hours (post-draft hype fading slightly), JT bounced to +299 trend30 (he's now over-priced if you were targeting him). Re-ping if he lists JT or Olave for sale. |
| **Forshey11** | Champion runner-up, owns Cam Skattebo (+256 trend30). May test the market on Skattebo at the post-draft peak. Watch for Skattebo offers — Skattebo into your RB room = CMC replacement. |
| **Romen Noodlez (R6)** | Full rebuild. Plan B for CMC if Golden Receivers passes. |

**Single biggest league insight (unchanged from 4/29):** Nobody else has fired an offer in 124 days. The first to start sets the market. **Get 3 offers out by EOD Friday 5/2:** Smith pitch + CMC pitch + Nacua-buy pitch.

---

## 🔮 Next week to watch

1. **Wednesday May 6, 7:00 AM — next LaunchAgent fire.** This is the test. If Nick fixes Full Disk Access by Tuesday night, the 5/6 run will be the first clean automated refresh in 4+ weeks. **If still fails, time to escape the LaunchAgent and run via cron or a Python script triggered by Cowork directly.**
2. **FantasyCalc next re-pricing cycle — likely 5/3 to 5/6.** The post-draft re-price has landed; the next cycle reflects rookie draft activity and OTA reports. **Run a manual `fetch_fantasycalc.py` daily through 5/6** to catch trend30 inflections before competing managers do.
3. **Huddlepuffers rookie draft start date** — confirm in Sleeper. If it lands in the next 7–14 days, your trade window for picks closes when the draft goes live. **Lock down all pick trades BEFORE the draft starts.**
4. **Puka Nacua league discipline announcement** — if NFL moves "matter under review" → "discipline pending," value collapses and the buy-low window briefly slams shut. If no announcement by 5/26 (OTAs start), the football narrative officially overrides the legal one and the price snaps back.
5. **49ers OTAs (May 26)** — first signal on Jordan James vs. Kaelon Black snap-share. Hold James through this checkpoint; stop-loss at val 700.
6. **DeVonta Smith trend30 next reading (5/6)** — if Smith stays above +300, sell window still open. If it drops below +150 by 5/6, the Lemon-doesn't-matter premium has been cashed in. **Sell before that reading.**
7. **Travis Hunter +194 surprise mover** — track whether the 5/3–5/6 FC pull confirms the spike or it's a one-day anomaly. If the spike holds, Hunter joins Smith on the trade-out menu.
8. **Tucker Kraft trend30 inflection** — if the trend30 turns positive again by 5/13, the ACL noise has fully cleared and you've held through it correctly. If it keeps bleeding past -150, re-evaluate.

---

## Sources

- [Puka Nacua A 'Full Participant' In Rams' Offseason Program — Pro Football Rumors](https://www.profootballrumors.com/2026/04/puka-nacua-a-full-participant-in-rams-offseason-program)
- [Lawyer: Puka Nacua will be available for all Rams 2026 OTAs — NBC Sports](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/lawyer-puka-nacua-will-be-available-for-all-rams-2026-otas)
- [Rams' Sean McVay: Puka Nacua 'doing really well,' at OTAs — ESPN](https://www.espn.com/nfl/story/_/id/48553704/rams-sean-mcvay-puka-nacua-doing-really-well-otas)
- [Attorney says Rams WR Puka Nacua in rehab — NFL.com](https://www.nfl.com/news/attorney-says-rams-wr-puka-nacua-in-rehab)
- [49ers select RB Kaelon Black with the No. 90 Pick — 49ers.com](https://www.49ers.com/news/49ers-select-rb-kaelon-black-with-the-no-90-pick-in-the-2026-nfl-draft)
- [49ers select Indiana RB Kaelon Black with No. 90 — NBC Sports Bay Area](https://www.nbcsportsbayarea.com/nfl/san-francisco-49ers/draft-pick-kaelon-black-indiana/1934030/)
- [Why the 49ers bet on Kaelon Black — SF Standard](https://sfstandard.com/2026/04/25/49ers-nfl-draft-2026-kaelon-black-running-back-picks/)
- [Green Bay Must Prioritize Extending Tucker Kraft — Zone Coverage](https://zonecoverage.com/2026/packers/green-bay-must-prioritize-extending-tucker-kraft-this-offseason/)
- [The Time for Packers to Sign Tucker Kraft to an Extension Is Now — Cheesehead TV](https://cheeseheadtv.com/blog/the-time-for-the-green-bay-packers-to-sign-tucker-kraft-to-an-extension-is-now-401)
- [How DeVonta Smith and Makai Lemon are building a bond — NBC Sports Philly](https://www.nbcsportsphiladelphia.com/nfl/philadelphia-eagles/devonta-smith-makai-lemon-eagles-wide-receiver-duo/730854/)
- [Makai Lemon, Eagles Agree to Rookie Contract — Bleacher Report](https://bleacherreport.com/articles/25423542-makai-lemon-eagles-agree-rookie-contract-115m-signing-bonus-after-2026-nfl-draft)

---

*Generated 2026-05-01 by manual catch-up of the Cowork weekly-digest scheduled task. Based on FantasyCalc snapshot 2026-05-01 (fresh — 463 rows pulled at 19:09 UTC), Sleeper data 2026-05-01 (refreshed), composite dynasty_score values still on 2026-04-28 baseline due to ongoing SQLite journal-permission issue. League: The Huddlepuffers (league_id 1182393556535246848). Owner: nmhochstedler (user_id 472596585608376320, team High Settlers, 9-5 in 2025). Operational note: macOS LaunchAgent not yet verified fixed — Tuesday 5/5 night is the deadline before the 5/6 fire.*
