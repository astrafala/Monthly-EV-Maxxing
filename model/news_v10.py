"""
Version 10: a calendar of high-impact news releases on the synthetic paths' dates, and the hours the plan stays flat.

Several firms restrict trading around high-impact ("red folder") releases (rules_inventory_v10.json): FTMO's FTMO Account
(no order opened or closed, a stop or take-profit hit included, from 2 minutes before to 2 minutes after a release on the
targeted instruments), The5ers (no order executed from 2 minutes before to 2 minutes after, every programme and stage),
Maven (2 minutes either side, evaluations and funded accounts, take-profits included), Blue Guardian, BrightFunded,
FundingPips, FundedNext and Alpha Capital funded accounts (5 minutes either side; FundedNext counts 40% of such a
trade's profit), GFT (5 minutes either side, profit of such a trade capped at 1% of the account), FXIFY (5 minutes either
side), FunderPro funded accounts (no entry within 2 minutes) and Topstep (no new position ahead of US CPI releases on equity
index futures). Version 9's plan text said the plan is flat around news, but the engine traded through every release;
only a bounding proxy (flat 12:00-14:00 UTC every weekday) was simulated (version 10, n22).

The plan's rule, simulated here: on an account whose firm restricts news at its current stage, no position is open during
any hourly bar that overlaps the window from 10 minutes before to 10 minutes after a high-impact release that moves the
traded market (US releases for every market; euro-area releases for EURUSD; Japanese releases for USDJPY), and no position
is opened in the bar before such a bar. A position still open at the start of a blocked bar is closed at that bar's open,
which is outside every firm's window. Ten minutes covers every firm's window (2 or 5 minutes), so the same blocked bars
serve every firm.

The synthetic paths have no news: their volatility is the same in every hour, so the calendar decides only when the plan
may hold a position. Release dates follow each agency's usual pattern (first Friday, second week, last business day ...),
not an official schedule for 2030 onward, which does not exist yet; the list is deliberately broad (it includes weekly
jobless claims, ADP, consumer sentiment and durable goods, which calendars often rate medium impact), so the blocked time
is if anything overstated. Times are local (New York, Frankfurt, Tokyo) and converted to UTC with each place's own
daylight-saving rules.
"""
import datetime as _dt, zoneinfo, functools
import numpy as np

NY = zoneinfo.ZoneInfo("America/New_York")
FRA = zoneinfo.ZoneInfo("Europe/Berlin")
TYO = zoneinfo.ZoneInfo("Asia/Tokyo")
UTC = _dt.timezone.utc
EPOCH = _dt.datetime(2030, 1, 1, tzinfo=UTC)        # bar 0 of every synthetic path (multi.load_synth)
WINDOW_MIN = 10.0                                   # minutes either side of a release (covers every firm's 2 or 5)

def _wd(y, m, d):
    return _dt.date(y, m, d).weekday()

def _nth_weekday(y, m, weekday, n):
    """n-th (1-based) given weekday of the month; n = -1: the last"""
    if n > 0:
        d = _dt.date(y, m, 1); off = (weekday - d.weekday()) % 7
        return d + _dt.timedelta(days=off + 7 * (n - 1))
    nxt = _dt.date(y + (m == 12), m % 12 + 1, 1); d = nxt - _dt.timedelta(days=1)
    return d - _dt.timedelta(days=(d.weekday() - weekday) % 7)

def _bday_on_or_after(d):
    while d.weekday() >= 5: d += _dt.timedelta(days=1)
    return d

def _nth_bday(y, m, n):
    d = _bday_on_or_after(_dt.date(y, m, 1)); k = 1
    while k < n:
        d = _bday_on_or_after(d + _dt.timedelta(days=1)); k += 1
    return d

def _last_bday(y, m):
    nxt = _dt.date(y + (m == 12), m % 12 + 1, 1); d = nxt - _dt.timedelta(days=1)
    while d.weekday() >= 5: d -= _dt.timedelta(days=1)
    return d

def _at(d, hh, mm, tz):
    return _dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz).astimezone(UTC)

# FOMC meetings: eight a year; the decision is announced on the second day (a Wednesday) in these weeks of the month
_FOMC = {1: -1, 3: 3, 5: 1, 6: 2, 7: -1, 9: 3, 11: 1, 12: 2}          # n-th Wednesday (-1: last)
_ECB = {1: 4, 3: 2, 4: 3, 6: 1, 7: 3, 9: 2, 10: 4, 12: 3}           # n-th Thursday
_BOJ = {1: 4, 3: 3, 4: 4, 6: 3, 7: 4, 9: 3, 10: 4, 12: 3}           # n-th Friday (the decision's second day)

def us_events(y):
    out = []
    for m in range(1, 13):
        nfp = _nth_weekday(y, m, 4, 1)
        out += [(_at(nfp, 8, 30, NY), "NFP")]
        out += [(_at(nfp - _dt.timedelta(days=2), 8, 15, NY), "ADP")]
        cpi = _bday_on_or_after(_dt.date(y, m, 12))
        if cpi.weekday() == 0: cpi += _dt.timedelta(days=1)          # CPI is released Tuesday to Thursday
        if cpi.weekday() == 4: cpi += _dt.timedelta(days=4)
        out += [(_at(cpi, 8, 30, NY), "CPI")]
        out += [(_at(_bday_on_or_after(cpi + _dt.timedelta(days=1)), 8, 30, NY), "PPI")]
        out += [(_at(_bday_on_or_after(_dt.date(y, m, 15)), 8, 30, NY), "Retail sales")]
        out += [(_at(_bday_on_or_after(_dt.date(y, m, 26)), 8, 30, NY), "Durable goods")]
        out += [(_at(_last_bday(y, m), 8, 30, NY), "PCE")]
        if m in (1, 4, 7, 10): out += [(_at(_nth_weekday(y, m, 3, -1), 8, 30, NY), "GDP")]
        out += [(_at(_nth_bday(y, m, 1), 10, 0, NY), "ISM manufacturing")]
        out += [(_at(_nth_bday(y, m, 3), 10, 0, NY), "ISM services")]
        out += [(_at(_nth_weekday(y, m, 1, 1), 10, 0, NY), "JOLTS")]
        out += [(_at(_nth_weekday(y, m, 1, -1), 10, 0, NY), "Consumer confidence")]
        out += [(_at(_nth_weekday(y, m, 4, 2), 10, 0, NY), "Consumer sentiment")]
        if m in _FOMC:
            d = _nth_weekday(y, m, 2, _FOMC[m])
            out += [(_at(d, 14, 0, NY), "FOMC"), (_at(d, 14, 30, NY), "FOMC press conference"),
                    (_at(d + _dt.timedelta(days=21), 14, 0, NY), "FOMC minutes")]
        if m in (2, 7):                                              # semi-annual testimony, two days
            d = _nth_weekday(y, m, 1, 2)
            out += [(_at(d, 10, 0, NY), "Fed testimony"), (_at(d + _dt.timedelta(days=1), 10, 0, NY), "Fed testimony")]
    d = _dt.date(y, 1, 1)                                            # weekly jobless claims, Thursdays
    d += _dt.timedelta(days=(3 - d.weekday()) % 7)
    while d.year == y:
        out.append((_at(d, 8, 30, NY), "Jobless claims")); d += _dt.timedelta(days=7)
    return out

def eur_events(y):
    out = []
    for m in range(1, 13):
        out += [(_at(_nth_bday(y, m, 1), 11, 0, FRA), "Euro-area flash CPI")]
        out += [(_at(_last_bday(y, m), 14, 0, FRA), "German preliminary CPI")]
        d = _bday_on_or_after(_dt.date(y, m, 23))
        out += [(_at(d, 9, 30, FRA), "German flash PMI"), (_at(d, 10, 0, FRA), "Euro-area flash PMI")]
        if m in _ECB:
            d = _nth_weekday(y, m, 3, _ECB[m])
            out += [(_at(d, 14, 15, FRA), "ECB decision"), (_at(d, 14, 45, FRA), "ECB press conference")]
    return out

def jpy_events(y):
    out = []
    for m in range(1, 13):
        out += [(_at(_nth_weekday(y, m, 4, -1), 8, 30, TYO), "Tokyo core CPI")]
        out += [(_at(_nth_weekday(y, m, 4, 3), 8, 30, TYO), "National core CPI")]
        if m in _BOJ:
            d = _nth_weekday(y, m, 4, _BOJ[m])
            out += [(_at(d, 12, 0, TYO), "BOJ decision"), (_at(d, 15, 30, TYO), "BOJ press conference")]
    return out

def events(instr, years, cpi_only=False):
    """(UTC time, name) of the releases that move instr, in the first `years` years of a path"""
    y0 = EPOCH.year; y1 = y0 + int(np.ceil(years)) + 1
    out = []
    for y in range(y0, y1):
        u = us_events(y)
        if cpi_only:
            out += [e for e in u if e[1] == "CPI"]; continue
        out += u
        if instr == "EURUSD": out += eur_events(y)
        if instr == "USDJPY": out += jpy_events(y)
    return sorted(out)

@functools.lru_cache(maxsize=64)
def blocked(instr, T, cpi_only=False, window_min=WINDOW_MIN):
    """boolean array over the path's T hourly bars: True where the bar overlaps a release's window (bar 0 = the path's
    first hour, 2030-01-01 00:00 UTC)"""
    years = T / (365.25 * 24) + 1
    nb = np.zeros(T, dtype=bool); w = window_min / 60.0
    for t, _ in events(instr, years, cpi_only):
        h = (t - EPOCH).total_seconds() / 3600.0
        a = int(np.floor(h - w)); b = int(np.floor(h + w - 1e-9))
        for i in range(max(a, 0), min(b, T - 1) + 1): nb[i] = True
    return nb

def summary(instr="US100", years=4):
    """events per month and blocked weekday hours per month (document)"""
    ev = events(instr, years)
    T = int(years * 365.25 * 24)
    nb = blocked(instr, T)
    hours = np.arange(T); wd = np.array([(EPOCH + _dt.timedelta(hours=int(h))).weekday() for h in hours[::24]])
    return dict(events_per_month=len([e for e in ev if (e[0] - EPOCH).total_seconds() / 3600 < T]) / (12 * years),
                blocked_hours_per_month=float(nb.sum()) / (12 * years), weekdays_share=float((wd < 5).mean()))

if __name__ == "__main__":
    for nm in ("US100", "XAUUSD", "EURUSD", "USDJPY"):
        print(nm, summary(nm))
    for t, n in events("US100", 1)[:30]: print(t.isoformat(), n)
