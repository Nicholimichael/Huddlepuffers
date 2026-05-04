# Huddlepuffers Weekly Review — 2026-04-27

## Headline: 49ers DID take an RB — Kaelon Black at #90. Jordan James thesis weakens but doesn't break (Black is 2-down only). FC has not re-priced yet, so trade-window urgency is now MAXIMUM before the next re-pricing cycle.

> **Executive summary** — Three days have passed since the 4/24 review. The 2026 NFL Draft completed Saturday night (4/25). The single most important Nick-roster outcome: **the 49ers spent pick #90 on Indiana RB Kaelon Black** — a 25-year-old, 2-down-only runner (4 receptions in 2025). That partially undermines the "Jordan James as CMC heir" thesis from Friday's review, BUT Black profiles as a thumper/short-yardage complement, not a passing-down handcuff, so James's third-down-back path is still intact. Meanwhile, **FantasyCalc has not yet re-priced** — Jordan James still shows val 1,136 / +671, Brian Robinson still shows val 1,241 / +642, Puka Nacua still -411. **Your sell-high window on BRob/DeVonta/CMC is still open, and tighter than Friday's window because the news is now fully baked but the price hasn't moved yet.** Fire offers today.

---

## ⚠️ Operational note — refresh status

- **The macOS LaunchAgent is still broken.** `logs/launchd_err.log` shows the last two `launchctl` invocations both failed with `/bin/bash: ... refresh_platform.sh: Operation not permitted`. The last successful Wednesday refresh was either manual or never happened.
- **Today (Monday April 27) is NOT a scheduled run day.** Wednesdays at 7:00 AM is the schedule. The next scheduled fire is **Wednesday April 29 at 7:00 AM** — and unless the Full Disk Access fix gets done before then, that run will fail too.
- **Today's data refresh:** I ran `fetch_fantasycalc.py` (456 rows pulled), `fetch_sleeper.py`, `build_rankings.py`, `build_platform_v2.py`, and `weekly_digest.py` from inside the Cowork sandbox. The mechanical digest at `weekly_digest_2026-04-27.md` shows all-zero week-over-week deltas because **FantasyCalc itself hasn't re-priced post-draft yet** — values are byte-for-byte identical to the 4/24 snapshot. This is FantasyCalc's lag, not a script bug.
- **Action for Nick (do this BEFORE Wednesday 4/29):**
  1. System Settings → Privacy & Security → Full Disk Access → add `/bin/bash` and `launchd`
  2. `launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist`
  3. `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hossautomation.huddlepuffers-refresh.plist`
  4. `launchctl kickstart -k gui/$(id -u)/com.hossautomation.huddlepuffers-refresh` to force-fire and verify a fresh `logs/refresh_2026-04-27_*.log` lands.

---

## What actually changed this week

### 1) The 49ers DID draft a running back — and it's not who anyone expected

**Kaelon Black, RB, Indiana — Round 3, pick #90.** Trade swap from Miami (the 49ers received #90 + #133 from Miami in the Round 1 trade-down — see 4/24 review). Black went from being a Day 3 / UDFA name in most analyst boards to a Round 3 pick to one of the league's premier rushing schemes.

Why this matters for Nick:
- **Profile:** 25 years old in October, posted 186-1040-10 (5.6 YPC) at Indiana in 2025 in a 1B role behind Roman Hemby, **only 4 receptions** on 6 targets. He is a downhill, two-down thumper.
- **Role projection:** This is NOT a pass-down handcuff to McCaffrey. Most likely usage: short-yardage / goal-line / cold-weather games. Closer to a Tyler Allgeier-to-Bijan analogue than a CMC heir.
- **Implication for Jordan James:** The "James inherits CMC's full workload when CMC retires" narrative weakens. The "James is the third-down/passing-game back" narrative survives — and arguably gets cleaner now that the 49ers have drafted a complement, not a replacement.
- **Implication for CMC:** Marginally negative. The 49ers did not draft an *heir*, but they did draft *insurance* — confirming they are publicly preparing for life beyond CMC even if not this season. The -343 30-day FC trend should continue trickling, not collapse.
- **Implication for Isaac Guerendo:** **Drop candidate confirmed.** Guerendo (val 207) is now fourth on the depth chart behind CMC, Black, and James. Cut him to make room for any UDFA dart throw.

### 2) Falcons did NOT add a Round 1–3 RB — Brian Robinson's role is fully locked in

The Falcons' RB room going into 2026: **Bijan Robinson (RB1, fifth-year option exercised) + Brian Robinson Jr. (FA signing, March 2026) + nobody else of consequence.** No Round 1, 2, or 3 RB drafted. This is the **best case** for BRob's near-term touch share — he's the confirmed complement to Bijan, replacing Tyler Allgeier's role.

What this does to BRob's value:
- His +642 30-day FC bump is now **locked in** — there's no incremental positive news coming. The Falcons' draft stayed quiet at RB.
- The "sell high" thesis from Friday is **stronger** today. Once FC re-prices to reflect the completed draft + the locked-in Falcons RB room, BRob's value will likely tick up another 100–200 points and then plateau. **Anyone who's going to pay a premium for BRob will pay it in the next 5–10 days.**

### 3) Eagles drafted Makai Lemon at #20 (recap from 4/24) — DeVonta Smith sell case is now baked

No new news here, but the FC market still hasn't reacted. Smith remains val 3,299 / +206 30-day. Once Lemon's name shows up alongside Smith's on every Eagles depth-chart article for the next month, Smith's price slides. **The window to extract Smith's pre-Lemon value closes when FC re-prices.**

### 4) FantasyCalc has NOT re-priced post-draft

This is the operative fact for every action item below. As of today's pull:
- Jordan James: val **1,136**, trend30 **+671**
- Brian Robinson: val **1,241**, trend30 **+642**
- Brock Bowers: val **6,764**, trend30 **+311**
- DeVonta Smith: val **3,299**, trend30 **+206**
- Ashton Jeanty: val **7,681**, trend30 **+175**
- Christian McCaffrey: val **4,204**, trend30 **−343**
- Jonathan Taylor: val **5,444**, trend30 **−384**
- Puka Nacua: val **8,648**, trend30 **−411**

Every single one of those is byte-identical to Friday's snapshot. **FantasyCalc's next re-pricing cycle is your countdown clock.** Industry pattern: post-NFL-Draft re-prices typically land 3–7 days after draft completion (so anywhere from today through Saturday May 2).

### 5) League activity: still bone dry — 121 days since the last transaction

Last league transaction: **2025-12-28** (Lorde Commissioner FA pickup). That's **121 days** without a single move in the league. Zero trades, zero adds, zero drops. Nobody has reacted to Round 1, Round 2, Round 3, or any of it. **You are competing with sleeping owners. Be the only one who's awake.**

---

## 🎯 Action items for Nick's roster (revised from 4/24)

### SELL HIGH — fire offers TODAY, before FC re-prices

**1. Brian Robinson (RB, ATL) — urgency: MAXIMUM (was HIGH on 4/24)**
- The Falcons did not add a RB in Rounds 1–3. BRob's role is now permanent and his FC value will plateau (or tick up slightly) before sliding once the offseason narrative shifts to camp battles.
- **Pitch:** BRob + Nick's 2027 2nd → Team Basic AF's (R8, 2-12) 2026 2nd or their 2027 1st.
- **Fallback target:** Romen Noodlez (R6) — full rebuild, will pay near-term value for picks.
- **Floor offer:** Straight-up BRob for any 2026 2nd round pick.

**2. DeVonta Smith (WR, PHI) — urgency: MAXIMUM (was HIGH on 4/24)**
- Eagles took Lemon at #20. Once FC re-prices, Smith's +206 likely flips to flat or negative within a week.
- **Pitch:** Smith + a late 2027 pick → a 2026 1st (top-5 rookie spot) from a rebuilder.
- **Your WR depth covers the loss:** Tee Higgins, DJ Moore, Egbuka, Jameson Williams, Worthy, Downs, Aiyuk, McMillan, Parker Washington — you've got 9 startable WRs.

**3. Christian McCaffrey (RB, SF) — urgency: HIGH (was CONDITIONAL on 4/24)**
- The 49ers drafting Black at #90 confirms they're preparing for life after CMC. The -343 30-day trend will continue.
- **Pitch:** CMC → Golden Receivers (R4, 10-4) for their 2026 2nd + a player. Golden Receivers missed the championship by 5 points — they need a bellcow for one more run.
- **Window:** This window closes the moment Golden Receivers themselves draft an RB at 2.02 or 2.03 in the rookie draft.

**4. Travis Etienne (RB, NO) — NEW SELL CANDIDATE**
- val 3,294, trend30 -147. Now in NO with Kellen Moore offense, behind Olave at WR. The Saints did not draft any premier WR in Rounds 1–3 (they took Tyson at #8, but Tyson is Yr1-limited per Friday's review). The Saints' offense will lean run-first — but Etienne is 27 and not the bell-cow. **Sell while the "new offense" buzz still has legs.**
- **Pitch:** Etienne + a late pick → any contender's 2026 3rd or two 2027 mid-rounders.

### MODIFIED HOLD — Jordan James (was HOLD on 4/24)

- **Hold for now, but lower conviction.** Black at #90 is a downgrade to the James thesis but not a death blow. Black is a 2-down-only player. James still has the passing-down path.
- **Watch:** OTAs (late May / early June) for first reports on the SF backfield pecking order. If James is repping with the 1s on third down by mid-June, value spikes back. If Black is poaching all carries inside the 10, value slides.
- **If FC reprices James DOWN by more than 200 points in the next cycle, switch to SELL.**

### BUY LOW — windows narrowing

**1. Puka Nacua (WR, LAR)** — still val 8,648, trend30 -411. Rams took QB Ty Simpson at #13 (no WR threat to Nacua). The lawsuit is still the only headwind. If a tilted owner is dumping, **pounce now** — Nacua is a top-3 dynasty WR at 25.

**2. Jonathan Taylor (RB, IND)** — val 5,444, trend30 -384. Colts did not draft a RB. Henderson-to-NE took some of the rookie-class pressure off. JT has at minimum 2026 + 2027 of bell-cow workload locked in.

**3. Christian Watson (WR, GB)** — not on roster. Watson returning from ACL, Dontayvion Wicks +823 30d (#2 riser in the entire FC database), GB WR room unsettled. Cheap dart throw.

### DROP CANDIDATES (make room for rookies + UDFAs)

- **Isaac Guerendo (RB, SF)** — val 207. Now 4th on the SF depth chart behind CMC/Black/James. **Drop today** if you need a spot for a Day 3 rookie or UDFA stash.
- **Jalen McMillan (WR, TB)** — val 1,643. Crowded TB room (Evans, Egbuka, Godwin if re-signed).
- **Michael Mayer (TE, LV)** — val 666, trend30 -48. With Bowers locked in as TE1 in LV, Mayer has no path. Drop for a TE2 dart.

---

## 🏈 Rookie draft — your 1.07 plan after the FULL draft

Reconfirmed from 4/24: **Jeremiyah Love, Carnell Tate, Jordyn Tyson, Makai Lemon, Ty Simpson are all gone before 1.07.** Now we know the rest of the field:

**Tier 2 names that should still be on the board at 1.07:**
- **Jadarian Price (RB, SEA, #32)** — Now confirmed as the SEA lead-back-in-waiting (Charbonnet ACL recovery, Walker now in KC). **Price is the strongest landing-spot value at your slot.** FC: val 2,856, trend30 +65 (will move much higher post-FC re-price).
- **Kaytron Allen (RB, ?)** — FC val 1,530, trend30 **+1,115** (top riser in the entire database). Landing spot will determine everything; if he went to a clean room (KC, MIA, IND late picks), he's a steal at 1.07.
- **Fernando Mendoza (QB, LV, #1)** — if Huddlepuffers is superflex, Mendoza at 1.07 is theft. **Confirm league settings before the draft.**

**Recommendation:**
1. **First-choice:** Trade 1.07 for **2 picks in the 1.10–2.04 range** (e.g., 1.07 → someone's 1.11 + 2.05). The talent gap from the top tier to the next is real; better to take two darts at a flatter tier.
2. **Second choice:** Take Jadarian Price at 1.07. Best floor + landing spot in the available pool.
3. **Third choice:** If superflex, take Mendoza.

**Draft capital reminder (unchanged):**
- 2026 1st: ~1.07 (your own; 9-5, 4th seed)
- 2027 1st: yours
- **Team Basic AF's 2027 1st: yours (they went 2-12 — could be 1.01–1.03)**
- You do NOT have 2026 2nd (held by Golden Receivers) or 2026 3rd (held by Team Basic AF) — these are YOUR top buy-back targets if you sell BRob/DeVonta/CMC

---

## 👀 League watch — 121 days since the last move

| Owner (Team) | Why they matter to you |
|---|---|
| **Team Basic AF (R8, 2-12)** | Holds your 2026 3rd. Their 2027 1st is yours. **Best trade partner all offseason.** Push BRob + your 2027 2nd for their 2026 2nd. Send the offer today. |
| **Golden Receivers (R4, 10-4)** | Holds your 2026 2nd. The CMC sell target. Watch their rookie-draft moves — if they take an RB at 2.02 or 2.03, your CMC window closes. |
| **Romen Noodlez (R6)** | Full rebuild. Good dumping ground for aging vets (CMC, Prescott, Kelce, BRob). |
| **Brady >Manning (R10, champ)** | Last year's champ. No reason to move. Skip. |
| **colsheske** | Holds Omarion Hampton (RB) and Kayshon Boutte (WR) — see prior 4/22 trade scenarios doc. He's been silent for 4 months too. Re-ping him. |
| **aigo100** | Owns CeeDee Lamb, Bucky Irving — three top-25 dynasty assets. Best contender to pitch CMC to if Golden Receivers passes. |

**Single biggest league insight:** Nobody else has fired an offer in 4 months. The first owner to start trading after the rookie draft will set the market. **Be that owner. Get 3–4 offers out in the next 48 hours.**

---

## 🔮 Next week to watch

1. **Wednesday April 29, 7:00 AM — LaunchAgent fire.** If the Full Disk Access fix is in, today's `weekly_review_2026-04-27.md` is the last review I had to fake-refresh manually. If the fix isn't in, you'll get a third consecutive miss and we're patching live again next week.
2. **FantasyCalc post-draft re-pricing window — Tuesday 4/28 through Saturday 5/2.** The single biggest mechanical event of the offseason. Re-run `fetch_fantasycalc.py` and `weekly_digest.py` daily this week if possible to catch the moment.
3. **Huddlepuffers rookie draft start date** — confirm in Sleeper. If it's the next 7–10 days, your trade window for picks closes when the draft goes live. **Lock down all pick trades BEFORE the draft starts.**
4. **49ers OTAs (late May)** — first real signal on Jordan James vs. Kaelon Black snap-share split. Until then, hold.
5. **Puka Nacua lawsuit news** — any resolution slams the buy-low window shut.

---

## Sources

- [49ers select Kaelon Black at #90 — 49ers.com](https://www.49ers.com/news/49ers-select-rb-kaelon-black-with-the-no-90-pick-in-the-2026-nfl-draft)
- [What 49ers' Kaelon Black pick means for CMC — Yahoo Sports](https://ca.sports.yahoo.com/news/49ers-pick-indiana-rb-kaelon-025644019.html)
- [Why the 49ers bet on Kaelon Black — SF Standard](https://sfstandard.com/2026/04/25/49ers-nfl-draft-2026-kaelon-black-running-back-picks/)
- [49ers RB Depth Chart after Black pick — Pro Football Network](https://www.profootballnetwork.com/49ers-rb-depth-chart-kaelon-black-draft/)
- [Dynasty Rookie Draft Advice: Kaelon Black — FantasyPros](https://www.fantasypros.com/2026/04/dynasty-rookie-draft-advice-kaelon-black-2026-fantasy-football/)
- [Bijan Robinson + Brian Robinson Jr. balance the Falcons' backfield — Atlanta Falcons](https://www.atlantafalcons.com/news/bijan-robinson-brian-robinson-jr-falcons-backfield)
- [Falcons exercise Bijan Robinson's 5th-year option — Washington Post](https://www.washingtonpost.com/sports/nfl/2026/04/10/falcons-bijan-robinson-contract/59ef09fe-3531-11f1-b85b-2cd751275c1d_story.html)
- [2026 NFL Draft Day 2 Winners & Losers — FantasyPros](https://www.fantasypros.com/2026/04/2026-nfl-draft-day-2-winners-losers-fantasy-football/)
- [NFL Draft 2026 Rookie Winners and Losers Rounds 2-3 — SI](https://www.si.com/fantasy/nfl-draft-2026-rookie-winners-losers-rounds-2-3)
- [Fantasy Football Winners and Losers Day 2 — PFF](https://www.pff.com/news/fantasy-football-winners-and-losers-from-day-2-of-the-2026-nfl-draft)

---

*Generated 2026-04-27 by the Cowork scheduled weekly-digest task. Based on FantasyCalc snapshot 2026-04-27 (still pre-FC-re-price), Sleeper data 2026-04-27, and 2026 NFL Draft news through 4/26. League: The Huddlepuffers (league_id 1182393556535246848). Owner: Nmhochstedler (user_id 472596585608376320, team High Settlers, 9-5 in 2025). Operational note: macOS LaunchAgent failed last cycle — Full Disk Access fix required before Wednesday 4/29.*
