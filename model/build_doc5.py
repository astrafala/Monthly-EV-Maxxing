"""Version 5 of the document: the version 4 build plus Part 3 (firm reliability, added firms, revised per-person plan)."""
import re, json, collections, pathlib
import numpy as np

src4 = open("build_doc4.py").read()
cut = src4.index("doc = head + key_results() + p1 + body + appx_body + APPX_D + appx_end")
exec(src4[:cut])          # everything version 4 builds: helpers, data, chapters 1-32 with their numbers

F5 = json.load(open("final_v5.json"))
LOCK5 = json.load(open("lockstep_portfolio_v5.json"))
DISC = json.load(open("discount_v5.json"))
INSTR5 = json.load(open("instr_v5.json"))

def lock5(p, data="synth"):
    rs = [r for r in LOCK5 if r["p"] == p and r["data"].startswith(data)]
    M = np.array([r["monthly"] for r in rs]); C = M.cumsum(1)
    br = collections.Counter()
    for r in rs:
        for f, v in r["breaches"].items(): br[f] += v
    br = {f: v / len(rs) / 12 for f, v in br.items()}
    tr = np.array([r["trough"] for r in rs])
    ref = {sc: np.array([r["refusal"][sc] for r in rs]) for sc in ("tiered", "harsh")}
    return dict(n=len(rs), steady=float(M[:, 2:].mean()), year=float(M.mean()),
                ahead={h: float(np.mean(C[:, h - 1] > 0)) for h in (1, 2, 3, 6, 12)},
                low50=float(np.median(tr)), low05=float(np.percentile(tr, 5)), breaches=br, maxbr=max(br.values()),
                orders=float(np.mean([r["orders_per_trading_day"] for r in rs])),
                tiered=float(ref["tiered"][:, 2:].mean()), harsh=float(ref["harsh"][:, 2:].mean()),
                tiered_year=float(ref["tiered"].mean()), harsh_year=float(ref["harsh"].mean()))

P_A = "Tier A (5 firms, 11 accounts)"
P_AB = "Tier A + B (7 firms, 17 accounts)"
P_ABD = "Tier A + B + one account at each tier-D firm (13 firms, 23 accounts)"
P_ABDS = "The same + The5ers small accounts (13 firms, 33 accounts)"
P_ALL = "All tiers at full caps (13 firms, 31 accounts)"
P_FUT = "Tier A + B + futures (9 firms, 42 accounts)"
P_V4ONE = "Version 4 one per firm (11 firms)"
P_V4FULL = "Version 4 full caps (11 firms, 25 accounts)"
P_V4ONEC = "Version 4 one per firm, rules corrected (11 firms)"
P_V4FULLC = "Version 4 full caps, rules corrected (11 firms, 25 accounts)"
P5 = [P_A, P_AB, P_ABD, P_ABDS, P_ALL, P_FUT, P_V4ONE, P_V4FULL, P_V4ONEC, P_V4FULLC]
L5 = {p: lock5(p) for p in P5}
L5R = {p: lock5(p, "real") for p in P5}
LAB5 = {P_A: "Tier A: FTMO 4, FundingPips 4, The5ers, FXIFY, FundedNext (11 accounts)",
        P_AB: "Tier A + B: adds Fintokei 4 and Hola Prime 2 (17)",
        P_ABD: "<strong>Tier A + B + one account at each tier-D firm (23)</strong>",
        P_ABDS: "The same + The5ers small accounts (33)",
        P_ALL: "All tiers at full caps (31)",
        P_FUT: "Tier A + B + futures: Topstep 5, Apex 20 (42)",
        P_V4ONE: "Version 4 default: one account at each of 11 firms",
        P_V4FULL: "Version 4 full caps (25)",
        P_V4ONEC: "&hellip; the same 11 accounts, rules corrected (Chapter 34)",
        P_V4FULLC: "&hellip; the same 25 accounts, rules corrected"}
REC = P_ABD

# ------------------------------------------------------------------ chapter 33
REL = [  # firm, TrustPilot on 4 Oct 2026, reviews, share of 1-star, PropFirmMap grade, tier
    ("FTMO", "4.8", "53,729", "3%", "A+", "A"),
    ("The5ers", "4.7", "39,102", "3%", "A+", "A"),
    ("FundingPips", "4.5", "69,773", "&ndash;", "A+", "A"),
    ("FundedNext", "4.5", "80,781", "7%", "A+", "A"),
    ("FXIFY", "4.3", "6,373", "&ndash;", "A+", "A"),
    ("Topstep (futures)", "3.6", "14,881", "&ndash;", "A", "A"),
    ("Hola Prime (new)", "4.5", "3,882", "&ndash;", "B+", "B"),
    ("Fintokei (new)", "4.3", "1,387", "&ndash;", "B+", "B"),
    ("Apex (futures)", "4.2", "21,157", "&ndash;", "B+", "B"),
    ("Alpha Capital", "withheld", "21,822", "7%", "D", "D"),
    ("Maven", "withheld", "5,207", "9%", "D", "D"),
    ("BrightFunded", "withheld", "572", "20%", "D", "D"),
    ("Blue Guardian", "withheld (since Aug 2025)", "2,091", "23%", "D", "D"),
    ("FunderPro", "withheld", "1,559", "35%", "D", "D"),
    ("Goat Funded Trader (GFT)", "withheld", "4,342", "40%", "D", "D"),
]
def rel_table():
    rows = [[f"<strong>{a}</strong>", b, c, d, e, f"<strong>{t}</strong>"] for a, b, c, d, e, t in REL]
    return table(["Firm", "TrustPilot score", "Reviews", "One-star share", "PropFirmMap grade", "Tier"], rows, num_from=2, w0="30%") + \
        note('Read on trustpilot.com and propfirmmap.com on 4 October 2026. "Withheld": the page says "This company\'s rating is unavailable due to a breach of our guidelines" and "We\'ve removed a number of fake reviews for this company". One-star shares were recorded for the flagged firms and for three of the others.')

def v4_refusal_table():
    rows = []
    for p in (P_V4ONE, P_V4ONEC, P_V4FULL, P_V4FULLC):
        x = L5[p]
        rows.append([LAB5[p], usd(r100(x["steady"])), f'{usd(r100(x["tiered"]))} ({(x["tiered"]/x["steady"]-1)*100:+.0f}%)',
                     f'{usd(r100(x["harsh"]))} ({(x["harsh"]/x["steady"]-1)*100:+.0f}%)'])
    return table(["Version 4 plan", "Steady month, every payout paid", "Tiered refusals", "Harsh refusals"], rows, w0="40%") + \
        note("Lockstep engine, 200 simulated years per plan on 8 zero-edge paths; each simulated year replayed 10 times with random refusals. Steady month = average of months 3&ndash;12.")

# ------------------------------------------------------------------ chapter 34: rules re-checked
V4 = json.load(open("final_v32.json"))
CORR = [  # programme as modelled in version 4, version 4 key, version 5 key, what changed
    ("FXIFY", "FXIFY Two-Phase", "FXIFY Two Phase Classic (100%, 30 days)",
     "Version 4 used 10% / 5% with a 5% daily loss, no minimum days and $480. FXIFY's static two-phase is now Two Phase Classic: 5% then 10%, 4% daily loss, 10% static, 4 trading days, $549, and on funded accounts no day may exceed 25% of the profit paid out (measured against the account's best day ever). Paid 100% every 30 days (or 80% every 14). Two Phase Standard trails its 10% floor up to break-even; 2 Phase Pro (4% / 8%, 8% static) has no refund and is worth less."),
    ("FundingPips Flex", "FundingPips 2-Step Flex (95%)", "FundingPips 2-Step Flex (85%) v5",
     "Flex does not refund the fee. Since 26 August 2026 the 95% option needs 3 profitable days (+0.5%) in each evaluation phase as well as in each reward cycle; the 85% option needs one trading day. The 85% option is now the better one."),
    ("FundedNext Stellar 2-Step", "FundedNext Stellar 2-Step", "FundedNext Stellar 2-Step v5",
     "For accounts bought from 12 January 2026 the 15% challenge reward is paid only once the account qualifies for Scale-Up, not with the first reward; rewards follow a 21-day cycle."),
    ("GFT 2-Step Standard", "GFT 2-Step Standard", "GFT 2-Step Standard v5",
     "Targets are 8% / 5% (not 10% / 5%), with 3 trading days per phase; the first payout needs 3% profit and the first two are capped at 6%."),
    ("FunderPro Classic", "FunderPro Classic", "FunderPro Classic v5", "The second phase needs 5%, not 8%."),
    ("BrightFunded 2-Step Classic", "BrightFunded 2-Step Classic", "BrightFunded 2-Step Classic v5",
     "The fee is refunded only if the paid refund add-on was bought; without it there is no refund."),
    ("Blue Guardian 2-Step", "Blue Guardian 2-Step", "Blue Guardian 2-Step v5",
     "List price $579 (often half price with a code), 3 profitable days per phase instead of 3 trading days, fee refunded after the fourth payout."),
]
UNCH = ["FTMO 2-Step", "The5ers High Stakes", "Alpha Capital Pro 10%", "Maven 2-Step"]
def corr_table():
    rows = []
    for lab, k4, k5, what in CORR:
        a = V4[k4]["synth"]["EV_month"] if k4 in V4 else None
        if k4 == "FundedNext Stellar 2-Step": a = 4316.0             # version 4's gold figure (Chapter 20.2)
        b = F5[k5 + (" XAUUSD" if k5 == "FundedNext Stellar 2-Step v5" else "")]["synth"]["EV_month"]
        rows.append([f"<strong>{lab}</strong>", what, usd(r100(a)), f"<strong>{usd(r100(b))}</strong>", f"{(b/a-1)*100:+.0f}%"])
    for k in UNCH:
        rows.append([f"<strong>{sh(k)}</strong>", "Re-checked: unchanged.", usd(r100(V4[k]["synth"]["EV_month"])), usd(r100(F5[k]["synth"]["EV_month"])), "&ndash;"])
    return table(["Programme", "What the firm's own pages say now (4 October 2026)", "Version 4", "Version 5", "Change"], rows, cls="small", num_from=2, w0="15%") + \
        note("EV per month per 100K account, the plan, synthetic paths (24,000 attempts each). FundedNext on gold in both versions.")

# ------------------------------------------------------------------ chapter 35
CHECKED = [
    ("Fintokei ProTrader", "B", "8% / 6%; 5% daily loss from start-of-day equity; 10% static; 3 profitable days per phase; open risk per trade &le; 3%; weekends allowed; 80%; payout every 14 days with at least 3% profit and every position closed; fee returned with the first payout; up to &euro;500,000 per person; copying your own trades allowed", "added: 4 &times; 100K, Nasdaq"),
    ("Hola Prime 2-Step Prime", "B", "8% / 5%; 5% daily loss from the previous close; 10% static; 3 trading days per phase; funded: stop on every trade, risk &le; 2%, 80% every 14 days with 3 profitable days, best day &le; 40% of the payout; fee returned 25% with each of the first four payouts; $500,000 per person; copying only between your own Hola Prime accounts (one master, one copier); <em>copying from other prop firms prohibited</em>", "added: 2 &times; 100K on USDJPY, independent of the Nasdaq accounts"),
    ("The5ers High Stakes, small sizes", "A", "Next to the 100K account a person may hold 1 &times; 25K, 3 &times; 10K, 3 &times; 5K and 3 &times; 2.5K High Stakes accounts ($176, $69, $35, $19), copying allowed", "optional: +10 accounts"),
    ("Topstep 50K (futures)", "A", "$49 a month + $149 activation; $3,000 target; $2,000 end-of-day trailing; best day &le; 55% of the target; funded: 5 winning days of $150+, &le; 50% of the balance and &le; $2,000 per request, 90%; up to 5 funded accounts", "optional futures layer: 5"),
    ("Apex 4.0 50K EOD (futures)", "B", "$550 list, public 80&ndash;90% codes (about $55) + $99 activation on passing; 30-day evaluations; $2,000 end-of-day trailing; flat by 4:59 pm ET; 100% for at most 6 payouts; 50% consistency; up to 20 funded accounts, copying between your own allowed", "optional futures layer: 20, only at 80&ndash;90% off"),
    ("OANDA Prop Trader", "&ndash;", "Closed: FTMO bought OANDA (completed December 2025) and moved the prop business into FTMO by 31 March 2026", "&ndash;"),
    ("Blueberry Funded", "D", "TrustPilot rating withheld; funded loss per trade capped at 1.5%", "not added"),
    ("ThinkCapital", "D", "TrustPilot rating withheld (broker-owned)", "not added"),
    ("E8 Markets", "D", "TrustPilot rating withheld; mostly one-step products with trailing or 3% limits", "not added"),
    ("Funded Trading Plus", "D", "TrustPilot rating withheld; its help pages contradict each other on copying", "not added"),
    ("FTUK", "&ndash;", "Two-Step pays only from the third funded level (two more 8% steps first)", "not added"),
    ("The Trading Pit, AquaFunded, Audacity Capital", "D", "TrustPilot ratings withheld", "not added"),
]
def checked_table():
    rows = [[f"<strong>{a}</strong>", t, b, c] for a, t, b, c in CHECKED]
    return table(["Firm or programme", "Tier", "What was found (4 October 2026)", "Decision"], rows, cls="small", num_from=9, w0="17%")

NEW = [("Fintokei ProTrader", "Fintokei ProTrader", "Nasdaq"),
       ("Hola Prime 2-Step Prime (bi-weekly 80%) USDJPY", "Hola Prime 2-Step Prime, bi-weekly 80%", "USDJPY"),
       ("Hola Prime 2-Step Prime (monthly 95%) USDJPY", "Hola Prime 2-Step Prime, monthly 95%", "USDJPY"),
       ("Hola Prime 2-Step Prime (bi-weekly 80%) US100", "&hellip; the same on the Nasdaq (not used: copying rule)", "Nasdaq"),
       ("FundedNext Stellar 2-Step USDJPY", "FundedNext Stellar 2-Step (version 4: gold)", "USDJPY"),
       ("The5ers High Stakes 25K", "The5ers High Stakes 25K", "Nasdaq"), ("The5ers High Stakes 10K", "The5ers High Stakes 10K", "Nasdaq"),
       ("The5ers High Stakes 5K", "The5ers High Stakes 5K", "Nasdaq"), ("The5ers High Stakes 2.5K", "The5ers High Stakes 2.5K", "Nasdaq"),
       ("Topstep 50K", "Topstep 50K (futures)", "micro Nasdaq"),
       ("Apex 50K EOD (90% off: $55 + $99 activation)", "Apex 50K EOD at 90% off ($55 + $99)", "micro Nasdaq"),
       ("Apex 50K EOD (80% off: $110 + $99 activation)", "Apex 50K EOD at 80% off ($110 + $99)", "micro Nasdaq")]
def rs_(x):
    return r100(x) if abs(x) >= 1000 else int(round(x / 10.0)) * 10
def new_table():
    rows = []
    for key, lab, mk in NEW:
        r = F5[key]; s = r["synth"]; rl = r["real"]
        rows.append([lab, mk, (usd(r["fee"]) + (" a month" if r["monthly"] else "")) + (f' + {usd(r["activation"])}' if r["activation"] else ""),
                     pct(s["P"]), usd(rs_(s["Vf"])), usd(s["EV"]), f'<strong>{usd(rs_(s["EV_month"]))}</strong> &plusmn;{s["EV_month_CI"]:.0f}',
                     usd(rs_(rl["EV_month"])) if rl else "&ndash;"])
    return table(["Programme", "Market", "Fee", "Pass both", "Paid per funded account", "EV per attempt", "EV per month per account", "Real path"], rows, cls="small", num_from=2, w0="27%") + \
        note("The plan of Part 2 (stop 0.75 hourly moves, 1 : 5, risk 1.5% of the account, cycles of +10%); futures as in Chapter 20. 24,000 synthetic attempts per row and 8,000 on the real 2024&ndash;26 path (the yen rows use the real USDJPY series).")

def instr_table():
    base = [x for x in INSTR5 if x["instr"] == "US100"][0]["EV_month"]
    NAME = {"US100": "Nasdaq 100", "USDJPY": "USDJPY", "XAUUSD": "Gold", "US500": "S&amp;P 500", "EURUSD": "EURUSD", "GBPUSD": "GBPUSD"}
    rows = [[NAME[x["instr"]], f'{x["m"]:.2f}', usd(r100(x["EV_month"])), "&ndash;" if x["instr"] == "US100" and x["m"] == .75 else f'{(x["EV_month"]/base-1)*100:+.0f}%']
            for x in INSTR5]
    return table(["Market", "Stop (hourly moves)", "EV per month", "vs Nasdaq"], rows) + \
        note("FundedNext Stellar 2-Step rules, random direction, 24,000 synthetic attempts per row. The S&amp;P 500 moves with the Nasdaq (correlation about 0.9), so it cannot be traded against the Nasdaq accounts: it is no independent market.")

DORDER = ["FTMO 2-Step", "FundingPips 2-Step Flex (85%) v5", "The5ers High Stakes", "FXIFY Two Phase Classic (100%, 30 days)", "FundedNext Stellar 2-Step v5",
          "Fintokei ProTrader", "Hola Prime 2-Step Prime (bi-weekly 80%)", "Alpha Capital Pro 10%", "BrightFunded 2-Step Classic v5", "Blue Guardian 2-Step v5",
          "FunderPro Classic v5", "Maven 2-Step", "GFT 2-Step Standard v5"]
def disc_table():
    rows = [[sh(f).replace(" v5", ""), usd(DISC[f]["fee"]), usd(r100(DISC[f]["EV_month"])), f'+{usd(DISC[f]["gain_per_10pct"])}', f'+{DISC[f]["gain_pct"]*100:.1f}%'] for f in DORDER]
    return table(["Programme", "List fee", "EV per month", "Gain from 10% off", "Relative"], rows, cls="small") + \
        note("The same attempts priced twice (12,000 synthetic attempts, common random numbers). Where a fee is refunded, the refund is the amount actually paid, so a discount saves money only on attempts that never earn the refund.")

# ------------------------------------------------------------------ chapter 35
def plan5_table():
    rows = []
    for p in (P_A, P_AB, P_ABD, P_ABDS, P_ALL, P_FUT):
        x = L5[p]
        rows.append([LAB5[p], usd(r100(x["steady"])), f'<strong>{usd(r100(x["tiered"]))}</strong>', usd(r100(x["harsh"])),
                     usd(r100(x["year"])), f'{pct(x["ahead"][1])} / {pct(x["ahead"][3])} / {pct(x["ahead"][12])}',
                     f'{k_(x["low50"])} / {k_(x["low05"])}', f'{x["maxbr"]:.0f}'])
    return table(["Version", "Steady month, all paid", "Steady month, tiered refusals", "Steady month, harsh refusals", "First-year average, all paid",
                  "Ahead after 1 / 3 / 12 months", "Cash low: typical / 1 in 20", "Most failed accounts at one firm per month"],
                 rows, cls="small", hl=(2,), w0="27%") + \
        note(f"Lockstep engine: {L5[P_A]['n']} simulated years per version on 8 independent zero-edge paths, all accounts on one path and calendar, shared direction per market; no opposite positions occurred. Refusal scenarios: each payout refused with probability 2% / 5% / 15% (tiers A / B / D, &lsquo;tiered&rsquo;) or 5% / 10% / 30% (&lsquo;harsh&rsquo;); after a refusal the firm is dropped.")

def plan5_real():
    a = L5R[P_ABD]; b = L5R[P_A]
    return f"On the real 2024&ndash;26 path (gold and yen accounts mapped to the Nasdaq) the recommended version earned {usd(r100(a['steady']))} per steady month with every payout paid and {usd(r100(a['tiered']))} with tiered refusals; tier A alone {usd(r100(b['steady']))} and {usd(r100(b['tiered']))}."

def breach5_table():
    x = L5[REC]["breaches"]; y = L5[P_ABDS]["breaches"]; z = L5[P_FUT]["breaches"]
    firms = sorted(set(x) | set(z), key=lambda f: -max(x.get(f, 0), z.get(f, 0)))
    rows = [[f, f"{x.get(f, 0):.1f}" if f in x else "&ndash;", f"{y.get(f, 0):.1f}" if f in y else "&ndash;", f"{z.get(f, 0):.1f}" if f in z else "&ndash;"] for f in firms]
    return table(["Firm", "Recommended (23 accounts)", "+ The5ers small accounts", "Tier A + B + futures"], rows, cls="small") + \
        note("Failed evaluations plus lost funded accounts per firm per month. Several firms list many quick failures as a sign of gambling (Chapter 21.4).")

PLAN5 = [
    ("FTMO 2-Step", "A", "4", "Nasdaq", "+10%"),
    ("FundingPips 2-Step Flex, 85% split (changed)", "A", "4", "Nasdaq", "+12%"),
    ("The5ers High Stakes 100K", "A", "1", "Nasdaq", "+10%"),
    ("FXIFY Two Phase Classic, 100% every 30 days (changed)", "A", "1", "Nasdaq", "+10%; no day above 25% of the payout's profit"),
    ("FundedNext Stellar 2-Step", "A", "1", "Gold, independent", "+10%, 21-day cycles"),
    ("Fintokei ProTrader", "B", "4", "Nasdaq", "+10% (each payout &ge; 3%, all positions closed)"),
    ("Hola Prime 2-Step Prime, bi-weekly 80%", "B", "2 (master + copier)", "USDJPY, independent", "+10%; 3 profitable days; best day &le; 40%"),
    ("Alpha Capital Pro 10%", "D", "1", "Nasdaq", "+10%"),
    ("BrightFunded 2-Step Classic", "D", "1", "Nasdaq", "+10%"),
    ("Blue Guardian 2-Step", "D", "1", "Nasdaq", "+10% (open loss never 2%); 3 profitable days per phase"),
    ("GFT 2-Step Standard", "D", "1", "Nasdaq", "+6% for the first two payouts, then +10%; &le; $3,000 a day"),
    ("FunderPro Classic", "D", "1", "Nasdaq", "+10%"),
    ("Maven 2-Step", "D", "1", "Nasdaq", "+8%"),
]
def plan5_list():
    rows = [[f"<strong>{a}</strong>", t, n, m, c] for a, t, n, m, c in PLAN5]
    return table(["Firm and programme (100K)", "Tier", "Accounts", "Market", "Funded cycle"], rows, cls="small", num_from=9, w0="34%")

def key5_box():
    a = L5[P_A]; ab = L5[P_AB]; rec = L5[REC]; allc = L5[P_ALL]; fut = L5[P_FUT]; v4 = L5[P_V4FULL]; v4c = L5[P_V4FULLC]
    return f"""
  <div class="box warn"><h4>Version 5 update (4 October 2026): read Part 3 first</h4>
  <ol style="margin:0">
    <li><strong>Six of the eleven firms in version 4 have had their TrustPilot rating withheld for fake reviews</strong> (Alpha Capital, BrightFunded, Blue Guardian, FunderPro, Maven, GFT). Version 5 sorts firms into tiers and prices in a chance that payouts are refused (Chapter 33).</li>
    <li><strong>Every rule re-checked.</strong> Seven programmes had changed or had been recorded wrongly: FXIFY (now about {usd(r100(F5["FXIFY Two Phase Classic (100%, 30 days)"]["synth"]["EV_month"]))} a month per account instead of {usd(r100(V4["FXIFY Two-Phase"]["synth"]["EV_month"]))}), FundingPips Flex (no refund; use the 85% option), FundedNext (15% challenge reward only after Scale-Up), GFT, FunderPro, BrightFunded and Blue Guardian (Chapter 34).</li>
    <li><strong>Two firms added</strong> with clean public records: Fintokei (4 accounts) and Hola Prime (2 accounts on USDJPY, because it forbids copying from other firms). OANDA Prop Trader no longer exists; five other candidates were flagged and left out (Chapter 35).</li>
    <li><strong>Recommended per person: tier A and B firms, plus one account at each tier-D firm</strong> (23 accounts at 13 firms): {usd(r1000(rec["steady"]))} per steady month if every payout is paid, {usd(r1000(rec["tiered"]))} under the tiered refusal scenario. Version 4's full caps, at {usd(r1000(v4["steady"]))} as published, is worth {usd(r1000(v4c["steady"]))} with corrected rules and {usd(r1000(v4c["tiered"]))} under the same scenario (Chapter 36).</li>
    <li>Tier A only (11 accounts): {usd(r1000(a["steady"]))} all paid, {usd(r1000(a["tiered"]))} tiered. All tiers at full caps (31 accounts): {usd(r1000(allc["steady"]))} and {usd(r1000(allc["tiered"]))}. Futures (Topstep 5, Apex 20 at 90% off) add {usd(r1000(fut["steady"] - ab["steady"]))} all paid but only {usd(r1000(fut["tiered"] - ab["tiered"]))} tiered.</li>
    <li>Each 10% fee discount adds 2&ndash;5% per account (Chapter 35.4).</li>
  </ol></div>
"""

PART3 = lambda: f"""
<!-- ================================================================ PART 3 -->
<section class="part">
  <span class="num">Part 3</span>
  <h1>Version 5: firms you can trust, more of them, and the plan revised</h1>
  <p>Checked on 4 October 2026. Six of the eleven firms in the version 4 plan have had their public reviews flagged as manipulated. This part sorts every firm by how far its public record can be trusted, re-checks every rule, adds two firms with clean records, prices in the chance that payouts are refused, and revises the per-person plan. The trade itself (Chapters 24&ndash;26) does not change.</p>
</section>

<!-- 33 -->
<section class="chapter">
  <span class="eyebrow">Chapter 33 &middot; new in version 5</span>
  <h1>Which firms to trust</h1>
  <p>Every firm keeps the right to refuse a payout it judges to break its rules, so in the end each payout is the firm's decision. The main outside check on whether a firm pays is what its funded traders say in public. In August and September 2026 TrustPilot withheld the ratings of six of the eleven firms in the version 4 plan, each with the notices &ldquo;This company's rating is unavailable due to a breach of our guidelines&rdquo; and &ldquo;We've removed a number of fake reviews for this company&rdquo;. PropFirmMap downgraded each of them to D. Every notice below was read on the firms' TrustPilot pages on 4 October 2026.</p>
  <h2>33.1 The firms, by tier</h2>
  {rel_table()}
  <h2>33.2 What a withheld rating does and does not mean</h2>
  <p>It is a finding about reviews, not about payouts: fake praise was posted for the firm. It does not prove that the firm refuses payouts. But it removes the best public evidence that the firm pays, and the reviews that remain are telling: one in three at FunderPro and two in five at GFT are one-star, and PropFirmMap notes many payout-denial complaints at FunderPro. Version 4 assumed every payout is paid. Version 5 keeps that figure and adds two scenarios that put a chance of refusal on each tier:</p>
  <table><thead><tr><th>Scenario</th><th class="n">Tier A</th><th class="n">Tier B</th><th class="n">Tier D</th></tr></thead><tbody>
    <tr><td>All paid (versions 1&ndash;4)</td><td class="n">0%</td><td class="n">0%</td><td class="n">0%</td></tr>
    <tr class="hl"><td>Tiered</td><td class="n">2%</td><td class="n">5%</td><td class="n">15%</td></tr>
    <tr><td>Harsh</td><td class="n">5%</td><td class="n">10%</td><td class="n">30%</td></tr>
  </tbody></table>
  {note("Chance that each payout is refused. A refusal usually comes with the account closed, so after the first refusal the simulated person stops using that firm: no more fees and no more payouts there.")}
  <p>These chances are judgements, not measurements: no firm publishes how many payouts it refuses. They are there to show how the plan behaves if the flags mean what they might mean.</p>
  <h2>33.3 What it does to the version 4 plan</h2>
  {v4_refusal_table()}
  <p>Version 4's full caps put 14 of its 25 accounts at tier-D firms. With corrected rules and the tiered scenario it keeps {pct(L5[P_V4FULLC]["tiered"] / L5[P_V4FULL]["steady"])} of its published value; the one-account-per-firm default keeps {pct(L5[P_V4ONEC]["tiered"] / L5[P_V4ONE]["steady"])}. A firm with many accounts makes many payout requests, and each request is another chance of losing the whole firm. Spreading accounts across firms protects against that better than stacking them at one firm.</p>
</section>

<!-- 34 -->
<section class="chapter">
  <span class="eyebrow">Chapter 34 &middot; new in version 5</span>
  <h1>Every rule re-checked</h1>
  <p>Version 5 read each firm's current rule pages again, preferring the firm's own help centre to review sites. Seven of the eleven programmes in version 4 had changed or had been recorded wrongly. All figures in Part 3 use the corrected rules.</p>
  {corr_table()}
  <p>The corrections cut the tier-A firms most (FXIFY, FundingPips, FundedNext), so part of the gap between version 4 and version 5 is not about trust at all. Rules move every few weeks: re-read them before every purchase (Chapter 27).</p>
</section>

<!-- 35 -->
<section class="chapter">
  <span class="eyebrow">Chapter 35 &middot; new in version 5</span>
  <h1>More accounts at firms that can be trusted</h1>
  <p>With the tier-D firms discounted, the per-person value now depends on finding more capacity at firms with clean records. Every candidate below was checked against its own rule pages where possible, and against TrustPilot and PropFirmMap.</p>
  <h2>35.1 Firms checked</h2>
  {checked_table()}
  <h2>35.2 What each added account is worth</h2>
  {new_table()}
  <p>Fintokei is a static-loss 2-step like FTMO; its three profitable days per phase and its 6% second phase make it a little slower. Hola Prime's best-day and profitable-day rules slow its funded cycles; its monthly 95% option is worse than bi-weekly 80% because the money arrives later. The5ers' small accounts follow the same rules but cost more per dollar of allowance, so ten of them add only about {usd(r100(sum(F5[k]['synth']['EV_month'] * n for k, n in (('The5ers High Stakes 25K', 1), ('The5ers High Stakes 10K', 3), ('The5ers High Stakes 5K', 3), ('The5ers High Stakes 2.5K', 3)))))} a month. Futures remain thin: Apex pays only at 80&ndash;90% off, which it has offered almost continuously in 2026, but a code that disappears would turn it negative.</p>
  <h2>35.3 Which market an independent account should trade</h2>
  <p>Hola Prime forbids copying trades from accounts at other prop firms, and FundedNext forbids copying once an account is funded. Their accounts therefore trade their own market, never repeating the Nasdaq trades. Each needs a different market from every other independent account, or the two would repeat each other's trades.</p>
  {instr_table()}
  <p>USDJPY is nearly as good as the Nasdaq: its cost per unit of movement is low and it trades from 00:00 UTC. Gold costs about 8%; the euro and pound cost about a third. Version 5 trades FundedNext on gold (as in version 4) and Hola Prime on USDJPY, both with the plan's stop of 0.75 hourly moves.</p>
  <h2>35.4 Fee discounts</h2>
  {disc_table()}
  <p>Most firms run public discount codes most of the time (FTMO rarely does). A 10% discount adds 2&ndash;5% to an account's value, 20% about twice that. Use only the firm's own public codes, check that the discounted account has the same rules, and expect the refund to be the discounted amount.</p>
</section>

<!-- 36 -->
<section class="chapter">
  <span class="eyebrow">Chapter 36 &middot; new in version 5</span>
  <h1>The per-person plan, revised</h1>
  <h2>36.1 Six versions, with and without refusals</h2>
  {plan5_table()}
  <p>{plan5_real()}</p>
  <h2>36.2 What to run</h2>
  <ol>
    <li><strong>Recommended: tier A and B in full, one account at each tier-D firm</strong> (23 accounts at 13 firms). Under the tiered scenario it is worth about as much as all tiers at full caps, with a much smaller cash low and far fewer failed accounts per firm, because no single doubtful firm carries much of the value.</li>
    <li><strong>Most cautious: tier A and B only</strong> (17 accounts at 7 firms). Every account is at a firm with a clean public record. It gives up about a fifth of the tiered value.</li>
    <li><strong>Optional extras, each worth much less after refusals than before:</strong> full caps at the tier-D firms ({usd(r100(L5[P_ALL]["steady"] - L5[REC]["steady"]))} a month if every payout is paid, {usd(r100(L5[P_ALL]["tiered"] - L5[REC]["tiered"]))} tiered, and a much deeper cash low); the futures layer (Topstep 5, Apex 20 at 80&ndash;90% off: {usd(r100(L5[P_FUT]["steady"] - L5[P_AB]["steady"]))} all paid, {usd(r100(L5[P_FUT]["tiered"] - L5[P_AB]["tiered"]))} tiered, dozens of failed evaluations a month); The5ers' small accounts ({usd(r100(L5[P_ABDS]["steady"] - L5[REC]["steady"]))} all paid, nothing after refusals, and about {L5[P_ABDS]["breaches"]["The5ers"] - L5[REC]["breaches"]["The5ers"]:.0f} more failed accounts a month at The5ers).</li>
    <li><strong>Keep the plan private.</strong> If several people traded these rules, the same trades on many accounts would become prohibited group trading (Chapter 23).</li>
  </ol>
  <h2>36.3 The recommended accounts</h2>
  {plan5_list()}
  {note("Every Nasdaq account follows the shared direction rule (26.3); the gold and yen accounts each follow the same rule on their own market. Trade sizes, stops, targets, the calendar and the news rules are those of Chapter 24 for every account; at Fintokei also close every position before requesting a payout. Sign-up order, if added month by month: tier A first; then Fintokei and Hola Prime; then the tier-D singles.")}
  <h2>36.4 Failed accounts per firm</h2>
  {breach5_table()}
  <h2>36.5 What did not change</h2>
  <p>The trade (Chapters 24&ndash;26), the daily routine (Chapter 28), the payout routine (Chapter 29) and the warnings (Chapters 16, 23 and 31) all stand. The mathematics is unchanged: with no edge, the value comes only from the structure of the contracts, and only if the firms pay.</p>
</section>
"""

APPX_E = """
<section class="chapter">
  <span class="eyebrow">Appendix E</span>
  <h1>Version 5: sources</h1>
  <table class="small"><thead><tr><th>Topic</th><th>Source (read 4 October 2026)</th></tr></thead><tbody>
  <tr><td>TrustPilot status of every firm in Chapter 33</td><td>trustpilot.com/review/ (ftmo.com, the5ers.com, fundingpips.com, fundednext.com, fxify.com, holaprime.com, fintokei.com, alphacapitalgroup.uk, maventrading.com, brightfunded.com, blueguardian.com, funderpro.com, goatfundedtrader.com)</td></tr>
  <tr><td>Safety grades, account limits, current prices</td><td>propfirmmap.com/firms/ (each firm); propfirmmap.com/trust-check</td></tr>
  <tr><td>Blue Guardian, Audacity, AquaFunded suspensions (August 2025)</td><td>tradeinformer.com/broker-news/several-props-suspended-from-trustpilot-due-to-fake-reviews</td></tr>
  <tr><td>Fintokei ProTrader: plan table, terms (sign-up bonus = fee, &euro;500,000, billing every 14 days)</td><td>fintokei.com/protrader/; fintokei.com/downloads/Fintokei_provider_program_TaC_ProTrader_FPP.pdf; support.fintokei.com</td></tr>
  <tr><td>Hola Prime: 2-Step Prime rules; prohibited practices (copying, hedging, one-sided betting)</td><td>holaprime.com/forex/faq/hola-prime-challenges/hola-prime-2-step-prime-challenge/; holaprime.com/trading-rules-list/trading-rules-prohibited-trading-practices/</td></tr>
  <tr><td>The5ers High Stakes account limits and prices</td><td>the5ers.com/high-stakes/; propfirmbridge.com (The5ers High Stakes review)</td></tr>
  <tr><td>OANDA Prop Trader rules and closure</td><td>legal.oanda.com (Rules for Trading Challenges, 30 Jan 2026); quantvps.com (OANDA Prop Trader overview)</td></tr>
  <tr><td>Topstep prices, resets, Express Funded limits</td><td>help.topstep.com (pricing and payment questions); proptradingvibes.com (Topstep Combine rules, September 2026)</td></tr>
  <tr><td>Apex 4.0 rules, account limit, copying, discounts</td><td>phidiaspropfirm.com (Apex 4.0 explained); apextraderfunding.com help centre; propfirmmap.com (Apex)</td></tr>
  <tr><td>FundedNext copying once funded; FXIFY copying approval</td><td>help.fundednext.com; fxify.com FAQs (2 Phase Pro copy trading)</td></tr>
  <tr><td>Blueberry Funded, ThinkCapital, FTUK, E8, Funded Trading Plus</td><td>help.blueberryfunded.com; thinkcapital.com (Dual Step); faq.ftuk.com (Two-Step Program Rules); tradetanto.com (E8 rules); propvator.com (Funded Trading Plus)</td></tr>
  </tbody></table>
</section>
"""

# ------------------------------------------------------------------ assemble
head5 = rep(head, "Mathematics and execution &middot; Version 4 &middot; October 2026", "Mathematics and execution &middot; Version 5 &middot; October 2026")
TOC5 = TOC[:-1] + [("p", "III", "Part 3 &middot; Version 5"), ("", "33", "Which firms to trust"), ("", "34", "Every rule re-checked"),
                   ("", "35", "More accounts at firms that can be trusted"), ("", "36", "The per-person plan, revised"),
                   ("p", "A&ndash;E", "Appendices: formula sheet and glossary, account types (version 1), method and sources, version 4 and 5 sources")]
toc_cur = head5[head5.index('<ul class="toc">'):head5.index("</ul>", head5.index('<ul class="toc">')) + 5]
toc5 = '<ul class="toc">' + "".join(f'<li class="{c}"><span class="n">{n}</span><span class="t">{tx}</span></li>' if c else
    f'<li><span class="n">{n}</span><span class="t">{tx}</span></li>' for c, n, tx in TOC5) + "</ul>"
head5 = head5.replace(toc_cur, toc5)
head5 = head5.replace(".toc{font-size:8.6pt}.toc li{padding:0.45mm 0}", ".toc{font-size:8.1pt}.toc li{padding:0.3mm 0}")

kr = key_results()
i = kr.index("<table>")
kr = kr[:i] + key5_box() + kr[i:].replace("<table><thead><tr><th>Quantity</th>", '<table class="kr"><thead><tr><th style="width:50%">Quantity</th>', 1)
head5 = head5.replace("</head>", "<style>table.kr td.n{white-space:normal}</style></head>", 1)

NOTE5 = ('<div class="box warn"><h4>Version 5 note</h4><p style="margin:0">Six firms in this chapter (Alpha Capital, BrightFunded, Blue Guardian, FunderPro, Maven, GFT) '
         'have since had their TrustPilot rating withheld for fake reviews, and seven programmes&rsquo; rules had changed or were recorded wrongly (Chapter 34). Part 3 (Chapters 33&ndash;36) re-ranks the firms, corrects the rules, adds Fintokei and Hola Prime, and revises the per-person plan.</p></div>')
body5 = body
for ch in ("20", "21", "24", "27"):
    m = re.search(r'(<span class="eyebrow">Chapter ' + ch + r'[^<]*</span>\s*<h1>[^<]*</h1>)', body5); assert m, ch
    body5 = body5.replace(m.group(1), m.group(1) + "\n  " + NOTE5, 1)

doc = head5 + kr + p1 + body5 + PART3() + appx_body + APPX_D + APPX_E + appx_end
assert "{{" not in doc
open("prop_firm_option_v5.html", "w").write(doc)

from playwright.sync_api import sync_playwright
footer = ('<div style="width:100%;font-size:7.5pt;font-family:Arial,sans-serif;color:#5b6370;padding:0 19mm;'
          'display:flex;justify-content:space-between"><span>The Prop Firm Option &middot; v5</span>'
          '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
with sync_playwright() as p:
    exe = "/opt/pw-browsers/chromium"
    b = p.chromium.launch(executable_path=exe) if pathlib.Path(exe).exists() else p.chromium.launch()
    pg = b.new_page()
    pg.goto("file://" + str(pathlib.Path("prop_firm_option_v5.html").resolve()), wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(1500)
    pg.pdf(path="The_Prop_Firm_Option_v5.pdf", format="A4", print_background=True, prefer_css_page_size=True,
           display_header_footer=True, header_template="<div></div>", footer_template=footer)
    b.close()
print("built v5")
