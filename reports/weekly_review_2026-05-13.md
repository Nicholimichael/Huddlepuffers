# Huddlepuffers Weekly Review — 2026-05-13

_Layered analysis on top of `weekly_digest_2026-05-13.md`. Window: **2026-05-04 → 2026-05-13** (9 days, offseason)._

> ⚠️ **Two operational issues to flag up top:**
> 1. **The launchd auto-refresh is still broken** — `com.hossautomation.huddlepuffers-refresh` has been erroring with `Operation not permitted` since at least May 1. Fix the macOS Full Disk Access permission for `/bin/bash` (System Settings → Privacy & Security) so the Wed 7am job stops being a manual run.
> 2. **This scheduled run could not deploy the site.** The Cowork sandbox runs Linux/FUSE — the SQLite warehouse throws `disk I/O error` mid-write over FUSE, and the Netlify CLI isn't authenticated in the sandbox. DB integrity verified intact afterwards (quick_check = ok). **Live site at https://huddlepuffers.hossautomation.com still shows the May 4 build.** To deploy, run from your Mac terminal:
> ```bash
> bash "/Users/Consulting/Documents/Claude/Projects/Fantasy Football/scripts/refresh_platform.sh"
> ```

---

## TL;DR — What changed this week

**Quiet on the transaction wire, loud on the value board.** The market re-priced the elite WR room hard (Jefferson, Chase, Higgins, Tyler Warren all -300+) while a single news event — **David Njoku signing with the Chargers on May 11 (+317, biggest riser in the league)** — moved one TE more than any other player. You were **the only owner in the green this week (+312)** because your roster skews young/rookie-capital and you don't own the bleeding WR1s; the rest of the league lost ground, with colsheske (-1,734) and Swerve33 (-1,324) leading the bloodbath.

---

## Why the top movers moved

### Risers — the *why*

| Player | Δ | The why (May 2026 context) |
|---|---:|---|
| **David Njoku (TE, Forshey11)** | **+317** | Signed 1-yr/$8M with the **Chargers on May 11**. New team needs TE production behind a thin WR room — instant TE1 ceiling if Gadsden doesn't take the job. |
| Jaxon Smith-Njigba (aigo100) | +271 | WR market shifting to "post-elite next tier" — JSN moved into the consensus top-3 WR slot as Chase/Jefferson softened. |
| Puka Nacua (isaacimel) | +223 | Same dynamic as JSN — established WR2 elites holding while the very top depreciates. |
| Breece Hall (chochstedler) | +218 | Jets offseason buzz + RB market re-correcting upward; he's now the only proven workhorse on a depth chart that lost camp competition. |
| **Trevor Lawrence (thedukestill)** | **+216** | Finished 5th in 2025 MVP balloting, healthy entering OTAs, "next step" buzz from Liam Coen. |
| **TreVeyon Henderson (Nmhochstedler — YOU)** | **+159** | Standard rookie-class appreciation curve — second-year-RB hype starts now and runs through training camp. |
| Travis Hunter (mmmatlock) | +158 | Jags **confirmed two-way role for 2026** but with uptick in CB snaps. Knee surgery recovery on track for OTAs. Market priced in "he plays Year 2." |
| **Jordan Love (Nmhochstedler — YOU)** | **+151** | Quiet Packers OTA buzz + the QB tier behind the top 6 is thin, so Love appreciates as a stable QB1. |

### Fallers — the *why*

| Player | Δ | The why (May 2026 context) |
|---|---:|---|
| Justin Jefferson (isaacimel) | **-388** | 2025 WR25 finish (1,048 yards, 2 TDs) on bad QB play. Now Kyler Murray is the Vikings starter — market is *underpricing the rebound*. **Strong buy-low signal.** |
| Ja'Marr Chase (colsheske) | -339 | Bengals contract overhang + the entire elite-WR tier is being repriced; nothing player-specific has broken. |
| **Tee Higgins (Nmhochstedler — YOU)** | **-312** | His 4yr/$115M deal is signed and the $40.9M guarantee already locked, so this isn't contract risk — it's WR-tier compression. **Hold.** Burrow's back, contract is done, market is mispricing him. |
| Tyler Warren (thedukestill) | -312 | Made the **2026 Pro Bowl as a rookie** (76/817/4) — and *still* dropped 312. Read this as market correction: post-rookie hype was priced too high, now it's settling into the TE4-behind-McBride/Bowers/Loveland tier. |
| Omarion Hampton (colsheske) | -302 | Rookie RB hype-curve compression — typical for non-elite first-round RBs once draft capital is priced in. |
| Drake Maye (colsheske) | -262 | Patriots reset chatter + nothing concrete on the roster building around him this offseason. |

---

## Action items for your roster (Nmhochstedler / High Settlers)

### 1. Buy low: **Justin Jefferson** (isaacimel) — TOP priority
The math is too obvious to ignore: Jefferson dropped 388 spots because he was a WR25 in 2025 with bad QB play. **Kyler Murray is now his QB.** This is the exact "down a year, primed to rebound" buy window dynasty owners pray for. isaacimel got hammered this week (-1,090 total) and is sitting on Jefferson and Michael Wilson — they might be open to consolidating. **Offer:** Tee Higgins + Travis Etienne + a 2027 2nd. Higgins covers their WR1 hole, Etienne is your weakest RB asset, the pick is the sweetener. If you can land Jefferson at this trough, it's the move of the year.

### 2. Sell high: **Jordan Love** (+151)
Love is at a local max — quiet offseason hype with no actual football evidence yet. You also have Jalen Hurts and Dak Prescott on the roster (3 QB1s is one too many for a 1QB league). **Test the market** with thedukestill (Trevor Lawrence is their only QB after Lawrence — wait, double-check — they could want depth) or Forshey11 (just spent capital on Njoku, may want QB stability). Ask for a top-50 rookie pick or a rising rookie WR.

### 3. Drops already executed — keep going
You dropped **Pat Freiermuth and Malik Willis** this week (no transaction logged — Sleeper's offseason endpoint isn't populating 2026-season activity yet, but the roster delta confirms it: 36 → 34 players). Both correct. You still have **Jordan James, Isaac Guerendo, and Jalen McMillan** on the roster bleeding modest value — consider whether any of them is taking a spot a deeper waiver dart should have.

### 4. Don't panic on Tee Higgins
He's the worst Δ on your roster (-312) but the *narrative* is positive: signed long-term, Burrow's healthy, top-three WR talent on a top-five offense. Holding through the offseason rebound is correct unless someone offers a clear win (2 first-rounders or an established WR1 swap). The contract guarantee trigger already passed in mid-March, so the floor is set.

### 5. Hot waiver pickups (offseason context)
- **Late-round rookies who haven't moved yet** — anyone in your `players` table with rookie status (yrs=0) and FantasyCalc rank > 200 who's getting OTA chatter is worth a roster spot. Check the rookies module on the dashboard after you redeploy.
- **Backup RBs to injury-prone starters** — offseason is when contingency capital is cheapest.

---

## League watch — who else moved that you should care about

| Owner | Δ Total Value | What they're doing |
|---|---:|---|
| **colsheske (Lorde Commissioner)** | **-1,734** | The worst week in the league. Owns Chase (-339), Hampton (-302), Pierce (-271), J. Taylor (-266), Maye (-262), Thornton (-268). Pure top-of-roster bleed. **Trade target — they're hurting and may want to consolidate.** Probably hard to pry Chase loose but easier to grab pick capital. |
| **Swerve33 (Romen Noodlez)** | -1,324 | Owns Emanuel Wilson (-266). May be looking to move depth pieces. |
| **isaacimel (Brady > Manning)** | -1,090 | Owns Jefferson + Puka + Michael Wilson. The Jefferson buy-low target. |
| **aigo100 (Tenacious D)** | -1,143 | Owns JSN (+271). The +271 is masked by other losses — could be a window to ask about JSN if they think this is the peak. |
| **thedukestill (Winging It)** | -782 | Owns Trevor Lawrence (+216) and Tyler Warren (-312). Mixed — could be a Tyler-Warren-buy candidate if they're discouraged. |
| **mmmatlock (Cow Tippers)** | -330 | Owns Travis Hunter (+158). Commissioner. Hunter is at "two-way confirmed" peak — sell-high candidate, but mmmatlock is unlikely to move him. |

**Your closest trade partner historically:** chochstedler (Golden Receivers). They own Breece Hall (+218) and Tony Pollard (+177) — they had a positive RB week. If you want to make a play, *this is when you ask about Breece*: their week was mediocre overall (-588) but their RBs were the highlight. Could be a "consolidate from depth" pitch — your Etienne + Stevenson + pick for their Breece.

---

## Next week to watch (5 things)

1. **2026 NFL Schedule release — May 14 (tomorrow).** Strength-of-schedule fairness across your roster will move values fast. Watch the Bengals (Higgins), Patriots (TreVeyon Henderson), Packers (Love), and Eagles (Hurts, DeVonta Smith) for soft/hard early-season splits.
2. **Jaguars OTAs continue May 26 / 28-29.** Trevor Lawrence + Travis Hunter snap-share signals will dictate whether the +216 / +158 holds.
3. **Chargers TE depth chart sorting** — Njoku vs. Oronde Gadsden. If Njoku locks the starting job, his +317 is just the beginning. If Gadsden wins the camp battle, expect a sharp giveback.
4. **Vikings OTA reports on Kyler Murray–Justin Jefferson chemistry.** Any positive snap from Eagan, MN and Jefferson rebounds fast. **This is your buy-low window closing.**
5. **Bengals contract guarantee trigger date already passed (5 days into 2026 league year, mid-March 2026).** Tee Higgins' $40.9M is locked. If his price stays depressed into June, that's an arbitrage signal — buy more if anyone in the league panic-sells.

---

## Source notes

- Auto-digest: `reports/weekly_digest_2026-05-13.md` (generated 01:32 UTC against May 4 snapshot + fresh FantasyCalc pull)
- Warehouse: `db/fantasy.sqlite` — integrity verified, quick_check = ok
- Snapshots compared: `data/snapshots/rankings_2026-05-04.json` vs the live FantasyCalc/Sleeper state captured at digest time

**Live site is still showing the May 4 build.** Run the refresh script from your Mac to update.

### News sources cited

- [Bengals agree to terms with WRs Ja'Marr Chase, Tee Higgins on four-year contract extensions](https://www.nfl.com/news/bengals-agree-to-terms-with-wrs-ja-marr-chase-tee-higgins-on-four-year-contract-extensions)
- [David Njoku Signs With The Chargers: The Dynasty Fantasy Football Impact (DLF, May 11 2026)](https://dynastyleaguefootball.com/2026/05/11/david-njoku-signs-with-the-chargers-the-dynasty-fantasy-football-impact/)
- [Justin Jefferson Poised to Re-Emerge as an Elite Dynasty Wide Receiver in 2026 (Fantasy Footballers)](https://www.thefantasyfootballers.com/news/214932/justin-jefferson-justin-jefferson-poised-to-re-emerge-as-an-elite-dynasty-wide-receiver-in-2026/)
- [QB Trevor Lawrence on Phase 1 of Jaguars 2026 Offseason Program](https://www.jaguars.com/news/k000609-trevor-lawrence-further-ahead-entering-2026-offseason-program)
- [Jaguars still plan on Travis Hunter being a two-way player in 2026 (ESPN)](https://www.espn.com/nfl/story/_/id/47610252/jaguars-plan-travis-hunter-being-two-way-player-2026)
- [Tyler Warren 2026 Dynasty Outlook: Year 2 Pro Bowl Path (BrainyBallers)](https://brainyballers.com/tyler-warren-2026-dynasty-outlook/)
- [Colts TE Tyler Warren named to 2026 Pro Bowl](https://www.colts.com/news/colts-tight-end-tyler-warren-2026-pro-bowl-rookie-nfl-brock-bowers)
- [Tee Higgins NFL Contracts & Salaries — Spotrac](https://www.spotrac.com/nfl/player/_/id/47628/tee-higgins)
