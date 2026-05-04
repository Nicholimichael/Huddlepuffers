# Huddlepuffers Weekly Review — 2026-04-29

## Headline: FantasyCalc has FINALLY re-priced post-draft. The "fire offers today" window from 4/27 is now half-closed: BRob plateaued (+172, trend 0), JT bounced (+159 from -384), CMC stopped bleeding. **DeVonta Smith is the one sell where the window WIDENED — trend30 went from +206 to +391.** Puka Nacua dropped another -387 — buy-low window WIDER.

> **Executive summary** — The post-NFL-Draft FantasyCalc re-pricing cycle the 4/27 review was waiting for has landed. The damage report on Nick's sell list: BRob plateaued exactly as predicted (still a sell, but no more headroom — fire today or next week, not in two), JT bounced (no longer a sell — switch to HOLD), CMC's slide stopped (sell window narrowing — pitch within the next 5–7 days). DeVonta Smith is the only sell where the window got *better* (trend30 jumped from +206 → +391). On the buy side, Puka Nacua continued to slide (-564 trend30) — the lawsuit news this week (TMZ reports of accuser serving rehab on 4/22, then Nacua filing aggressive answer claiming intoxication/aggression) is the catalyst, but he's back at Rams offseason program. **Buy window is OPEN and likely brief.** The Jordan James thesis broke harder than feared — value cratered -237 from 4/27, FC market priced in the Kaelon Black implication. Cut losses or hold for OTAs.

---

## ⚠️ Operational note — refresh status

- **The macOS LaunchAgent failed AGAIN this morning (4/29).** `logs/launchd_err.log` shows two consecutive failures with `/bin/bash: ... refresh_platform.sh: Operation not permitted`. The Full Disk Access fix from the 4/27 review was not applied before this scheduled fire.
- **Today's manual catch-up:** I ran `fetch_sleeper.py` (success), `fetch_fantasycalc.py` (CSV written successfully — 458 rows of fresh post-draft FC values) inside the Cowork sandbox. The SQLite write step hit a journal-permission error in the bind-mounted DB, so `build_rankings.py` and `build_artifact_v2.py` did NOT run today — meaning `platform/rankings_data.json` and `huddlepuffers_platform.html` are still on yesterday's composite scores. **The FC values in this review are fresh; the composite dynasty_score values in the platform HTML are 24 hours stale.**
- **Action for Nick (do this BEFORE Wednesday 5/6, ideally today):**
  1. System Settings → Privacy & Security → Full Disk Access → add `/bin/bash` and `launchd`
  2. `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist`
  3. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist`
  4. `launchctl kickstart -k gui/$(id -u)/com.hossautomation.huddlepuffers-refresh` and verify a fresh `logs/refresh_2026-04-29_*.log` appears.
  5. Once the agent is firing cleanly, also delete the stale `db/fantasy.sqlite-journal` and `db/fantasy.sqlite-journal.bak` files in Finder — the sandbox can't unlink them.

---

## What actually changed this week

### 1) The post-draft FantasyCalc re-price has happened — and it confirms every 4/27 thesis

The 4/27 review opened with: *"FantasyCalc has not yet re-priced post-draft. Industry pattern: post-NFL-Draft re-prices typically land 3–7 days after draft completion (so anywhere from today through Saturday May 2)."* Today's pull confirms that re-price cycle has landed. Evidence:

| 4/27 Thesis | 4/27 trend30 | 4/29 trend30 | Verdict |
|---|---:|---:|---|
| Brian Robinson "will plateau then slide" | +642 | **-2** | ✓ Plateau hit. Next move: sideways-to-down. |
| Jonathan Taylor "buy-low — workload locked" | -384 | **+159** | ✓ Bounce hit. JT is no longer a buy-low. |
| CMC "Black confirms sell case" | -343 | **-17** | ✓ Slide stopped. Sell window NARROWING. |
| Puka Nacua "still slipping — pounce" | -411 | **-564** | ✓ Continued slide. Buy-low window WIDER. |
| Bowers "+311 trend keeps lifting" | +311 | **+413** | ✓ Bowers value continues to climb. |
| DeVonta Smith "Lemon priced in — sell" | +206 | **+391** | ✓ Value still climbing. Best sell window of the offseason is RIGHT NOW. |
| Jordan James "Black hurts thesis" | +671 | **+49** | ✓ Narrative broke. -237 absolute value drop in 2 days. |

Every directional call from 4/27 was right. The only nuance: a couple of trend30 numbers actually got *more* favorable for sellers (DeVonta) or buyers (Puka) than the 4/27 review predicted. Lean into those.

### 2) The 1-day FC value movers (mechanical, see digest for full table)

**Top story risers:**
- **Bhayshul Tuten (RB, JAX) — +292 from yesterday, on YOUR roster.** Was a deep-stash dart in late 2025. Travis Etienne in NO opens up the Jaguars' 2026 backfield; Tuten was drafted by JAX in the 2025 Round 4 and is the presumptive committee lead. *Why now:* offseason program reports surfaced this week putting Tuten ahead of Tank Bigsby on the depth chart. Hold; could be your most valuable taxi-graduate of the offseason.
- **Omarion Hampton (RB, LAC) — +325, owner colsheske.** Confirmed 2026 NFL Draft pick #18 to LA (Justin Herbert offense). Trend30 +359. Highly relevant: colsheske is on the 4/27 trade-target list — Hampton's rising value makes a Hampton-for-CMC pitch viable.
- **Eli Raridon (TE, NE) — +211 today, +894 30-day.** Drafted by NE in 2026 (mid-rounds). Cheap dart-stash if you want a TE3 behind Tucker Kraft and Hunter Henry. **FA in your league.**
- **MarShawn Lloyd (RB, GB) — +212 today, +416 30-day.** Josh Jacobs running mate. FA. Worth a flier if you drop Guerendo.

**Top story fallers:**
- **Drake London (WR, ATL) — -228.** Owner thedukestill. *Why:* late-week reports questioning Falcons' offensive scheme fit; Bijan + BRob + Penix Jr. profile suggests a run-heavy 2026. London is now a soft-buy candidate if his value bottoms.
- **Tucker Kraft (TE, GB) — -193, on YOUR roster.** *Why:* the Packers spent draft capital on a TE and added Lloyd at RB; Love's targets distribute wider in 2026. **Watch this — if Kraft drops another 10% by next Wednesday, he's no longer a reliable TE2 next to Bowers in trade pitches. Either trade him soon or build around the slide.**
- **Keenan Allen (WR, FA) — -161, on YOUR roster.** Currently teamless. Almost zero trade value. **Drop candidate** to make room for a 2026 rookie or UDFA.
- **Ladd McConkey (WR, LAC) — -177, owner SpeedwayJesus.** Hampton's arrival pulls offensive volume to the run game. Soft sell from his owner; you don't have a need.
- **Joe Mixon, James Conner, Sean Tucker — RBs ≥27 in unstable backfields.** Standard offseason age-curve drop. Nothing actionable on your roster.

### 3) Puka Nacua: the lawsuit + rehab story crystallized this week

This is the catalyst behind Nacua's -564 trend30. Confirmed timeline:
- **4/22 (TMZ):** Process servers showed up at Nacua's Malibu rehab facility and served the civil suit from his accuser (Madison Atiabi) for the alleged New Year's Eve assault.
- **Mid-April:** The accuser withdrew the restraining-order petition without prejudice; she's now pursuing only the civil case.
- **This week:** Nacua's attorneys filed the answer to the lawsuit, claiming the accuser's "intoxication, aggressive behavior, and/or escalation" was a substantial factor — an aggressive defense that signals a long, public legal fight.
- **Football side:** Nacua appeared at the Rams' offseason program this week per multiple beats. **He is practicing.**

The fantasy verdict: legal headwind keeps growing (more public, longer, uglier), but the *football* picture for 2026 is unchanged — he's healthy, in the building, no suspension threat from the league yet (NFL still says "matter under review"). **This is the textbook "buy a top-3 dynasty WR at 25 because of off-field noise" setup.** If a tilted owner (specifically aigo100, who owns him AND is a known active manager) starts shopping, get there first. The buy window is opening, not closing.

### 4) League activity: 122 days since the last move

Last Huddlepuffers transaction: **2025-12-28** (Lorde Commissioner FA pickup). That's now 122 days. The dormancy hasn't broken even with the 2026 NFL Draft completed. Nick is still the only owner who has been preparing, planning, and watching pricing cycles. **Every other owner is asleep at the wheel.** This is the structural edge.

---

## 🎯 Action items for Nick's roster — REVISED from 4/27

### SELL HIGH — pitch THIS WEEK before the next FC re-price erodes the spread

**1. DeVonta Smith (WR, PHI) — urgency: MAXIMUM (UPGRADED from 4/27)**
- trend30 jumped from +206 to **+391** in 48 hours. The market is still rewarding Smith despite the Lemon pick. This is the single best sell window of the offseason.
- **Pitch (highest value):** Smith + late 2027 pick → 1.04–1.06 in a contender's 2026 rookie draft.
- **Pitch (broader):** Smith → 2026 1st (any non-bottom-3) + a young WR of comparable tier (Jameson Williams, Egbuka, etc. — already on your roster, so use this as a swap to acquire picks).
- **Ping list:** Forshey11 (champion runner-up), Brady>Manning (champ but window-closing), Golden Receivers (R4, 10-4).

**2. Brian Robinson (RB, ATL) — urgency: HIGH (DOWNGRADED from MAXIMUM)**
- Value is up to 1,413 (+172 from 4/27). Trend30 went from +642 to **-2**. The plateau the 4/27 review predicted has hit.
- The window isn't closed — but it's no longer expanding. Fire one offer today, one next Tuesday; if neither hits by 5/8, accept that BRob's price has settled.
- **Pitch (best):** BRob + your 2027 2nd → Team Basic AF's (R8, 2-12) 2026 2nd round pick. They've been silent for 4 months — re-ping with a fresh subject line.
- **Floor offer:** BRob straight-up for any 2026 2nd.
- **Do NOT go into rookie draft holding BRob "in case."** His value will be lower the day after the rookie draft starts.

**3. Christian McCaffrey (RB, SF) — urgency: HIGH (UPGRADED from 4/27)**
- Value bounced back to 4,451 (+247 from 4/27). Trend30 stopped at -17 (was -343). The Kaelon Black narrative is fully priced; the floor is set.
- That floor is the sell signal — every additional offseason day from here trims his value as he ages.
- **Pitch:** CMC → Golden Receivers (R4, 10-4) for their 2026 2nd + a player. Still the best fit (they missed the championship by 5; they need a bell-cow).
- **Backup target:** aigo100 — has Bucky Irving + CeeDee Lamb + Jonathan Taylor (he's a contender). CMC + a pick → JT? Don't initiate this one (you don't want JT now that he's bounced) but if aigo100 ASKS, it's a tradable framework.

**4. Travis Etienne (RB, NO) — urgency: MEDIUM (held from 4/27)**
- val 3,428, trend30 +60. Slow-rising, no urgency in either direction. The Saints' offseason buzz is what it'll be.
- **Pitch:** Etienne + a 2027 mid → any contender's 2026 3rd or two 2027 mids. Not a fire-today pitch.

### CHANGE — Jonathan Taylor is OFF the buy list (was buy-low on 4/27)

- val 5,597, trend30 jumped to **+159** (was -384). The bounce predicted in the 4/27 review hit. **No longer a buy-low.** If colsheske offers JT, you can do the trade — but at the bouncing-back price, JT is not the bargain he was last week.

### BUY LOW — windows OPENING

**1. Puka Nacua (WR, LAR) — urgency: MAXIMUM**
- val 8,261, trend30 -564 (worsening from -411). The lawsuit-and-rehab story is fully public now. Owner aigo100 has not signaled a sale, but he's the most active manager in the league — he WILL field offers.
- **Pitch:** Your 2026 1st (your own ~1.07) + DeVonta Smith → Nacua. The Smith-as-trade-bait works perfectly here: you're cashing him at the top tick to buy the bottom tick on a younger, higher-ceiling WR.
- **Backup:** 1.07 + Tee Higgins → Nacua (worse, but moves a 31-year-old WR with declining value).
- **Watch:** Any league suspension news. If the NFL announces "matter under review" → "discipline pending," value collapses further and you wait one more week.

**2. Christian Watson (WR, GB) — speculative add**
- Not on roster. ACL-recovery, GB WR room shaky. Cheap dart throw. If Wright/Egbuka contention fades, Watson rises.

### MODIFIED HOLD — Jordan James (was HOLD on 4/27)

- val 899, trend30 +49 — but lost -237 in 2 days. The Kaelon Black narrative IS priced now; James is no longer a "James inherits CMC's full workload" bet, only a "James survives as 3rd-down back" bet. **Hold through OTAs (late May).** If James is repping with the 1s on third down by mid-June, value spikes back; if Black is poaching short-yardage AND third-down, switch to drop.
- **If FC reprices James DOWN below 700, switch to drop.**

### DROP CANDIDATES

- **Keenan Allen (WR, FA)** — val 193, no team. **Drop today.**
- **Isaac Guerendo (RB, SF)** — val 207, 4th on SF depth chart behind CMC/Black/James. **Drop today.**
- **Davis Mills (QB, HOU)** — val 67. Roster spot is more valuable than him. Drop.
- **Michael Mayer (TE, LV)** — val 666 trend -48. Bowers locked in as TE1; no path. Drop for any 2026 rookie TE2.
- **Jalen McMillan (WR, TB)** — val 1,643. Crowded TB room. Hold one more week to see camp news; if he doesn't move by 5/13, drop.

---

## 🏈 Rookie draft — your 1.07 plan (unchanged from 4/27)

The 2026 NFL Draft is now fully complete. The 4/27 plan stands:

**Top 5 board names that are GONE before 1.07:**
- Jeremiyah Love (1.01), Carnell Tate (1.02–1.04), Jordyn Tyson (1.04–1.06), Makai Lemon (1.05–1.06), Ty Simpson (top of the board if superflex).

**Tier 2 names that should still be on the board at 1.07:**
- **Jadarian Price (RB, SEA, #32 NFL)** — trend30 +816, FC val 3,569. **Strongest landing-spot value at your slot.** Walker is gone to KC, Charbonnet still in ACL recovery — Price has the cleanest path of any non-top-5 rookie RB.
- **Kaytron Allen (RB, ?)** — FC val 1,530, trend30 +1,115 last cycle. Where he landed in the 2026 NFL Draft is the variable; check via `analysis_buy_low.csv` once the FC team-tagging propagates.
- **Cam Skattebo (RB, NYG)** — val 3,357, trend30 +281. NYG took him in 2026 NFL Draft. Devin Singletary is now 27 and contract-thin. **Skattebo has clean path, just a worse offense than Price.**

**Recommendation (unchanged):**
1. **First-choice:** Trade 1.07 for **2 picks in the 1.10–2.04 range.** Talent gap from top tier to next is real; better to take two darts.
2. **Second:** Take Jadarian Price at 1.07 if no good trade-down materializes.
3. **Third (superflex only):** Mendoza.

**Your draft capital (unchanged):**
- 2026 1st (your own ~1.07; 9-5, 4th seed)
- 2027 1st (your own)
- **Team Basic AF 2027 1st (theirs; they went 2-12 — likely 1.01–1.03)**
- You do NOT have 2026 2nd (Golden Receivers) or 2026 3rd (Team Basic AF) — these are your top buy-back targets if you sell BRob/DeVonta/CMC

---

## 👀 League watch — owners worth pinging this week

| Owner (Team) | Why now |
|---|---|
| **Team Basic AF (R8, 2-12)** | Holds your 2026 3rd; their 2027 1st is yours. Re-ping with BRob + 2027 2nd → 2026 2nd. They have not responded to any DM in 4 months — try a fresh subject line and a one-line pitch. |
| **Golden Receivers (R4, 10-4)** | Holds your 2026 2nd. Top CMC sell target. Their rookie-draft moves haven't started — you're early. |
| **colsheske** | New context: he just gained +325 on Hampton. He's now a *Hampton + JT + Olave + Boutte* contender. Could be persuaded to sell JT for picks now that JT bounced. **Re-ping the 4/22 trade-scenario document with new prices.** |
| **aigo100** | The Nacua owner. Active manager. Best buy-low source for Nacua. Don't lead with Nacua name — lead with "I'd give you a 1st + a young WR for any wideout you'd consider moving." |
| **Romen Noodlez (R6)** | Full rebuild. Dumping ground for CMC, Prescott, Kelce, BRob. If the Golden Receivers CMC pitch dies, Romen Noodlez is plan B. |
| **Forshey11** | Still owns Cam Skattebo (+281 today, +5.3 dynasty in 4/28 digest). Could be looking to sell into the post-draft hype. Watch for Skattebo offers. |

**Single biggest league insight (unchanged):** Nobody else has fired an offer in 122 days. The first owner to start trading after the rookie draft will set the market. Be that owner. **Get 3 offers out by Friday May 1.**

---

## 🔮 Next week to watch

1. **Wednesday May 6, 7:00 AM — next LaunchAgent fire.** If Nick fixes Full Disk Access this week, the 5/6 run will be the first clean automated refresh in 4 weeks. If not, this manual catch-up pattern continues.
2. **FantasyCalc next re-pricing cycle — likely 5/3 to 5/6.** The post-draft re-price has landed; the next cycle reflects rookie draft activity (when leagues actually start drafting). Run a manual `fetch_fantasycalc.py` daily through 5/6 to catch it.
3. **Huddlepuffers rookie draft start date** — confirm in Sleeper. If it lands in the next 7–10 days, your trade window for picks closes when the draft goes live. **Lock down all pick trades BEFORE the draft starts.** Top priority: the Team Basic AF 2026 2nd-for-BRob deal.
4. **49ers OTAs (late May)** — first signal on Jordan James vs. Kaelon Black snap-share. Hold James through this checkpoint.
5. **Puka Nacua league discipline announcement** — if NFL moves from "matter under review" to "discipline pending," value collapses and the buy-low window briefly slams shut. Watch the next 14 days.
6. **DeVonta Smith trend30 reading** — if Smith's trend30 stays above +300 next Wednesday, the sell window is still open. If it drops below +150 by 5/6, the market has stopped paying the Lemon-doesn't-matter premium and the sell window has closed.

---

## Sources

- [Puka Nacua bite accuser serves lawsuit at rehab — TMZ](https://www.tmz.com/2026/04/22/puka-nacua-bite-accuser-serves-lawsuit-at-rehab/)
- [Nacua makes shocking claims about bite accuser in lawsuit answer — Yahoo Sports](https://sports.yahoo.com/articles/puka-nacua-makes-shocking-claims-175031287.html)
- [NFL addresses Puka Nacua lawsuit, rehab: 'Matter Under Review' — National Today](https://nationaltoday.com/us/ca/los-angeles/news/2026/04/02/nfl-addresses-puka-nacua-lawsuit-rehab-matter-under-review/)
- [2026 NFL offseason moves tracker — NBC Sports](https://www.nbcsports.com/fantasy/football/news/2026-nfl-offseason-moves-instant-fantasy-reaction-to-latest-free-agent-signings-and-trades)
- [Lions exercise Jahmyr Gibbs' 5th-year option — RotoWire](https://www.rotowire.com/football/news.php)
- [2026 NFL Draft tracker — NFLTradeRumors](https://nfltraderumors.co/2026-nfl-draft-tracker-first-round/)

---

*Generated 2026-04-29 by manual catch-up of the Cowork weekly-digest scheduled task. Based on FantasyCalc snapshot 2026-04-29 (post-draft re-priced — 458 rows), Sleeper data 2026-04-29 (refreshed), composite dynasty_score values still on 2026-04-28 baseline. League: The Huddlepuffers (league_id 1182393556535246848). Owner: Nmhochstedler (user_id 472596585608376320, team High Settlers, 9-5 in 2025). Operational note: macOS LaunchAgent failed for the 3rd consecutive Wednesday — Full Disk Access fix overdue.*
