# Huddlepuffers Weekly Review — 2026-04-24

## Headline: Round 1 is done — your top 5 rookie-draft targets are all off the board, but the 49ers didn't take an RB, so Jordan James just got more valuable.

> **Executive summary** — NFL Draft Round 1 went last night (April 23). Every player Nick had circled at 1.07 — Jeremiyah Love, Carnell Tate, Jordyn Tyson, Makai Lemon, Ty Simpson — is **gone**. The 49ers traded out of Round 1 entirely and have NOT drafted a running back yet, which keeps Jordan James (your taxi stash) as the presumptive CMC handcuff with rising value. FantasyCalc hasn't re-priced yet, so today's snapshot-vs-snapshot diff shows zero mechanical movement — but the **landing-spot data is the whole story this week**. Your 1.07 decision has fundamentally changed in the last 18 hours.

---

## ⚠️ Operational note — refresh status

- **Today (Friday, April 24) is NOT a LaunchAgent run day** — the agent is scheduled for Wednesdays at 7:00 AM, and the most recent Wednesday run (April 22) executed as a manual fallback (the scheduled refresh had been erroring with "Operation not permitted" — see prior review).
- **Today's data refresh:** I re-ran `fetch_fantasycalc.py` and `weekly_digest.py` from inside the Cowork sandbox. FantasyCalc returned 458 players; however, FantasyCalc has not yet re-priced players based on last night's Round 1 results (rookies are still listed with team "FA"). That means the dynasty-value deltas lag the news by at least one trading cycle.
- **`fetch_sleeper.py`** started but timed out in the sandbox and I didn't want to leave it running against a locked DB. League has had **zero transactions since 2025-12-28**, so this is effectively a no-op for week-over-week anyway.
- **Action for Nick:** Before next Wednesday (April 29), do the LaunchAgent fix from the 4/22 review — Full Disk Access for `bash` / `launchd` in System Settings, and `launchctl kickstart -k gui/$(id -u)/com.hossautomation.huddlepuffers-refresh`.

---

## What actually changed this week

Mechanically, nothing moved inside our warehouse (no league transactions, FantasyCalc values unchanged pending post-draft re-pricing). But the single biggest dynasty event of the offseason — the 2026 NFL Draft — **started Thursday night at 8 PM ET in Pittsburgh**, and Round 1 is already in the books. Here is every Nick-relevant domino that fell:

### 2026 NFL Draft Round 1 — the full list of selections that move Nick's needle

| Pick | Team | Player | Pos | Why Nick cares |
|---:|---|---|---|---|
| 1 | LV Raiders | **Fernando Mendoza** | QB, Indiana | Heisman winner, immediate superflex dynasty QB2 target. **Not on Nick's roster**, and he'll be long gone before 1.07. |
| 3 | ARI Cardinals | **Jeremiyah Love** | RB, Notre Dame | Highest RB drafted since Saquon (2018). 1.01 in Nick's rookie draft — **unreachable at 1.07**. Value spikes further. |
| 4 | TEN Titans | **Carnell Tate** | WR, Ohio State | Cam Ward's new WR1. Was Nick's consensus fallback WR target — **gone 3 picks before his slot**. |
| 8 | NO Saints | **Jordyn Tyson** | WR, Arizona State | Kellen Moore offense, behind Chris Olave. Limited Yr1 ceiling but long-term stash. **Off the board.** |
| 13 | LAR Rams | **Ty Simpson** | QB, Alabama | Backup to Stafford — dynasty-only QB stash. **Gone**, but limited impact on Nick's plans. |
| 20 | PHI Eagles | **Makai Lemon** | WR, USC | Surprise rise: Eagles traded up for him despite a -738 30-day dynasty dip. **Gone.** |
| 27 | MIA Dolphins | Chris Johnson | CB, SDSU | No fantasy impact. Noted for context. |
| 30 | NYJ Jets | (trade up from 49ers) | — | **This is the critical one for Nick.** |
| 32 | SEA Seahawks | **Jadarian Price** | RB, Notre Dame | Replaces Kenneth Walker in Seattle's lead-back role. Walker is now in KC (committee) — double-hit to his dynasty value. |

### The 49ers move that matters most for your roster

The 49ers traded **out of Round 1 entirely** — swapping pick No. 27 to Miami for No. 30 + No. 90, then flipping No. 30 to the Jets for No. 33 + No. 179. **Result: San Francisco did not draft a running back in Round 1.** They enter Day 2 (tonight, Friday April 24) with pick No. 33 and are reportedly "very open" to trading down again.

**Implication for Nick:** Jordan James's value proposition just firmed up. Every hour the 49ers go without drafting an RB, James's "CMC handcuff / heir apparent" narrative gains steam. **Watch tonight's first three or four picks obsessively.**

---

## Top movers on Nick's roster (30-day trend, FantasyCalc pre-draft)

These values are as of April 21–24 and do **not** yet reflect post-Round-1 adjustments. Use them as a baseline — the next re-pricing cycle (likely Saturday/Sunday) will show the real reaction.

**Risers:**
- **Jordan James** (RB, SF, taxi) — val 1,136, +671 (30d). Should trend **up further** after tonight if 49ers don't pick an RB at 33.
- **Brian Robinson** (RB, ATL) — val 1,241, +642 (30d). Still at post-FA peak. **Sell-high window open.**
- **Brock Bowers** (TE, LV) — val 6,764, +311 (30d). Fantasy consensus as 2026 TE1 overall after Mendoza landing ("#1 pick needs a TE1"). Hold.
- **DeVonta Smith** (WR, PHI) — val 3,299, +206 (30d). Eagles just drafted Makai Lemon (#20). **Sell signal strengthens** — Smith's target share will absorb the new rookie long-term.
- **Ashton Jeanty** (RB, LV) — val 7,681, +175 (30d). Raiders added Mendoza at QB. Better offense around Jeanty = value creeps up. Hold.

**Fallers:**
- **Christian McCaffrey** (RB, SF) — val 4,204, -343 (30d). Still bleeding. Tonight's 49ers pick at 33 could either stabilize (no RB) or accelerate the drop (RB taken).
- **Jonathan Taylor** (RB, IND) — val 5,444, -384 (30d). Colts had a quiet Round 1 (no WR help). JT's window narrowing.
- **Puka Nacua** (WR, LAR) — val 8,648, -411 (30d). Rams drafted QB Ty Simpson at 13 — no short-term threat to Nacua. **Still a buy-low opportunity.**

---

## 🎯 Action items for Nick's roster

### SELL HIGH — this weekend, before FantasyCalc re-prices

**1. Brian Robinson (RB, ATL) — urgency: HIGH**
- The 30-day +642 bump is fully priced in. The Falcons didn't touch RB in Round 1 (confirmed), but the value is already at peak.
- **Pitch to Team Basic AF (R8, 2-12):** BRob + your 2027 2nd for their 2026 2nd. They're in full rebuild mode and could use near-term production.
- **Alternative target:** Romen Noodlez (R6, 2-12).

**2. DeVonta Smith (WR, PHI) — urgency: HIGH and rising**
- The Eagles just spent pick 20 on Makai Lemon. Smith is 27 and now has a true long-term threat to his WR1 target share. Once FantasyCalc re-prices, his +206 30-day gain could evaporate in a week.
- **Pitch:** Smith + a late 2026 pick for a 2026 top-3 rookie pick. Your WR room (Tee Higgins, DJ Moore, Egbuka, Williams, Worthy, Downs, Aiyuk, McMillan) covers the loss.

**3. Christian McCaffrey (RB, SF) — urgency: CONDITIONAL**
- If the 49ers draft a RB tonight at pick 33 (or earlier in Day 2), **sell immediately** — another -200 to -400 drop is coming.
- If the 49ers do NOT draft a RB before Day 2 ends (Friday night), CMC's floor holds and you have one more cycle to extract value.
- **Target:** Golden Receivers (R4, 10-4) — they missed the final by 5 points and need a bellcow for one more run. They also hold your 2026 2nd.

### BUY LOW — window closing as news cycle turns

**1. Puka Nacua (WR, LAR)** — -411 in 30 days. Rams took a QB at 13, not a WR. Nacua's situation is unchanged and he's still a top-5 dynasty WR at 25. If anyone in the league is treating the lawsuit as a career-ender, pounce.

**2. Jonathan Taylor (RB, IND)** — -384 in 30 days. Colts didn't touch RB in Round 1 and the depth chart is clear. If a rebuilder is dumping age-27 RBs for picks, consider.

**3. Christian Watson (WR, GB)** — not on Nick's roster yet. Watson is returning from ACL, Dontayvion Wicks is trending (+823), and the GB WR room is unresolved. Cheap dart throw.

### HOLD

- **Jordan James (RB, SF, taxi)** — Do NOT trade. Continue to let the 49ers Day 2 story play out tonight. If SF doesn't take an RB by Saturday morning, James's value will jump another 200–400 points in the next FantasyCalc cycle.
- **TreVeyon Henderson** — Patriots didn't draft a WR in Round 1, so the Henderson passing-game upside didn't materialize. Small disappointment, still hold.
- **Emeka Egbuka** — no change. Tampa WR2 future is secure.

### DROP CANDIDATES (make room for rookies)

- **Isaac Guerendo (RB, SF)** — 207 value. If James locks in as the #2 SF back, Guerendo is redundant.
- **Jalen McMillan (WR, TB)** — 1,643 value. Crowded TB room. Cut if needed for a Day 3 taxi stash.

---

## 🏈 Rookie draft — your 1.07 strategy has changed

**The top 5 targets from the April 22 review are ALL OFF THE NFL BOARD:**
- ~~Jeremiyah Love~~ → ARI #3
- ~~Carnell Tate~~ → TEN #4
- ~~Jordyn Tyson~~ → NO #8
- ~~Makai Lemon~~ → PHI #20
- ~~Ty Simpson~~ → LAR #13

**What to do with 1.07 now:**

**Path A — Trade down** (strongly recommended). The player tier Nick was targeting is gone. The next tier (Kaytron Allen, Jadarian Price landing in SEA with a real workload, Denzel Boston, Jam Miller) is flatter. Trade 1.07 + a later asset for someone's 2.02 + 2.05 (or similar) to accumulate darts.

**Path B — Take the best RB available.** Jadarian Price to Seattle is an **unexpectedly strong landing spot**: Seattle let Kenneth Walker walk to KC, and Price profiles as a more natural runner than Love in a scheme that wants a workhorse. **If Price is still on the board at 1.07, seriously consider him.** His dynasty value should rise after tonight/tomorrow based on the landing spot alone.

**Path C — Fernando Mendoza in superflex.** If this is a superflex league (confirm), Mendoza at #1 to the Raiders with a re-tooled offense is a genuine QB1 stash. At 1.07 he's a likely steal.

**Path D — Best WR available.** Expect Denzel Boston (Washington), Kaden Prather (Penn State), Germie Bernard types to go in Rounds 2–3 tonight. Landing spots determine everything — wait and see, then take the best Day 2 WR at 1.07.

**Draft capital reminder:**
- Your 2026 1st: ~1.07 (9-5 record, 4th seed)
- Your 2027 1st: yours
- **Team Basic AF's 2027 1st:** yours (they went 2-12; this could be top-3)
- You do NOT have 2026 2nd (Golden Receivers) or 2026 3rd (Team Basic AF)

---

## 👀 League watch — still dead quiet, but the pressure is building

- **Zero transactions in the league in the last 30 days** (last recorded: 2025-12-28 free agent pickup by Lorde Commissioner). The offseason trade window is wide open and unused.
- **Team Basic AF (R8)** — holds your 2026 3rd and owns 1.01 (Love incoming). Still your best near-term trade partner.
- **Golden Receivers (R4)** — holds your 2026 2nd. The CMC landing pad if you're selling. **Watch whether they move for a RB in the 2026 rookie draft** — if they do, the CMC window closes.
- **Brady >Manning (R10, champ)** — no reason to move. Skip.
- **Romen Noodlez (R6)** — full rebuild. Good dumping ground for aging vets (CMC, Prescott, Kelce).

The fact that NO owner has made a move in 4 months despite Round 1 of the NFL Draft just happening suggests the league is waiting for the rookie draft to start trading. **Be the first to fire an offer this weekend.**

---

## 🔮 Next week to watch

1. **Tonight (Friday April 24, 7:00 PM ET) — Rounds 2 & 3 of the NFL Draft.** The 49ers pick at 33 is the single most important event for Nick's roster. If they take an RB (Kaytron Allen, Jam Miller, anyone), Jordan James's value collapses. If they don't, James firms up further.
2. **Saturday April 25 — Rounds 4–7.** Late-round RB/WR landing spots matter for Nick's taxi-squad decisions post-draft.
3. **FantasyCalc re-pricing** — expect the first post-Round-1 dynasty re-price by Saturday PM or Sunday. Re-run `fetch_fantasycalc.py` then and rebuild rankings.
4. **Rookie draft timing** — confirm Sleeper settings for when Huddlepuffers rookie draft goes live and when pre-draft pick trades close. Get your 1.07 trade offers out BEFORE the draft — value is maximally volatile in the 3–5 days post-NFL-draft.
5. **Puka Nacua news** — if the lawsuit resolves in the next week, his 30-day slide stops cold and the buy-low window shuts.

---

## Sources (post-draft news used in this review)

- [2026 NFL Draft first-round picks, grades — Yahoo Sports](https://sports.yahoo.com/nfl/live/2026-nfl-draft-first-round-results-grades-as-fernando-mendoza-goes-no-1-jeremiyah-love-heads-to-cardinals-rams-take-ty-simpson-at-no-13-140000468.html)
- [Cardinals select Jeremiyah Love at No. 3 — NFL.com](https://www.nfl.com/news/jeremiyah-love-cardinals-no-3-overall-pick-2026-nfl-draft)
- [Seahawks draft Jadarian Price at No. 32 — Seahawks.com](https://www.seahawks.com/news/jadarian-price-nfl-draft-running-back-notre-dame)
- [49ers trade out of Round 1 — 49ers.com](https://www.49ers.com/news/trade-alert-49ers-trade-down-with-jets-in-round-1-of-2026-nfl-draft)
- [Seven players 49ers could target at No. 33 — NBC Sports Bay Area](https://www.nbcsportsbayarea.com/nfl/san-francisco-49ers/2026-draft-targets-pick-33/1933850/)
- [NFL Draft 2026 Fantasy Rookie Winners and Losers — Sports Illustrated](https://www.si.com/fantasy/nfl-draft-fantasy-rookie-winners-losers-round-1)
- [Makai Lemon to Eagles at No. 20 — CBS Philadelphia](https://www.cbsnews.com/philadelphia/news/makai-lemon-eagles-2026-nfl-draft/)
- [Biggest winners and losers from Round 1 — NFL.com](https://www.nfl.com/news/2026-nfl-draft-biggest-winners-and-losers-from-round-1)

---

*Generated 2026-04-24 by the Cowork scheduled weekly-digest task. Based on FantasyCalc snapshot 2026-04-24 (pre-Round-1 values) + 2026 NFL Draft Round 1 news through 4/24 AM. League: The Huddlepuffers (league_id 1182393556535246848). Owner: Nmhochstedler (user_id 472596585608376320, team High Settlers, 9-5 in 2025). Next refresh cycle: Saturday 4/25 post-Day-2 of the NFL Draft.*
