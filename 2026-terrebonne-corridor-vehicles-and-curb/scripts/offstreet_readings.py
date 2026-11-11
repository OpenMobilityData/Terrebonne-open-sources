"""Stage 5b: collate the readings of private parking and check them.

Input: derived/readings/batch_NN.csv (one file per reader; batches 1 to 10 cover every strip once, batch 11 is an
independent second reading of one strip in ten), derived/readings/batches.csv, derived/tables/offstreet_frame.csv.
Checks: every building read once in the first pass; allowed values; agreement between the first and the second
reading (driveway yes/no, places); agreement with the reading of October 25, 2026 of the buildings addressed on
rue de Terrebonne (folder 1954-underwriters-plans-terrebonne-garages, present_day column driveway_today).

Outputs (derived/tables/): offstreet_readings.csv (one row per building, first pass, with the frame's columns),
offstreet_readings_second_pass.csv, offstreet_reading_checks.csv
Run:  ~/.venvs/omd/bin/python scripts/offstreet_readings.py
"""
import sys

import numpy as np
import pandas as pd

from corridor_lib import GARAGES, ROOT, TABLES

RD = ROOT / "derived" / "readings"
ALLOWED = {"driveway": {"yes", "no", "unclear"}, "garage": {"yes", "no", "unclear"}, "access": {"front", "side street", "lane", "none"},
           "vehicle_on_lot": {"yes", "no"}, "confidence": {"high", "medium", "low"}}


def load(n):
    p = RD / f"batch_{n:02d}.csv"
    d = pd.read_csv(p, dtype=str, keep_default_na=False, on_bad_lines="warn")
    d.columns = [c.strip() for c in d.columns]
    for c in d.columns:
        d[c] = d[c].str.strip()
    d["label"] = d.label.str.replace("*", "", regex=False).astype(int)
    d["places"] = pd.to_numeric(d.places, errors="coerce")
    d["batch"] = n
    return d


def kappa(a, b):
    cats = sorted(set(a) | set(b)); n = len(a)
    po = np.mean(np.array(a) == np.array(b))
    pe = sum((list(a).count(c) / n) * (list(b).count(c) / n) for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    f = pd.read_csv(TABLES / "offstreet_frame.csv", dtype={"dauid": str, "uev_ids": str})
    bt = pd.read_csv(RD / "batches.csv")
    problems = []
    first = pd.concat([load(n) for n in sorted(bt[bt["pass"] == 1].batch.unique())], ignore_index=True)
    second = pd.concat([load(n) for n in sorted(bt[bt["pass"] == 2].batch.unique())], ignore_index=True)
    for name, d in (("first", first), ("second", second)):
        for c, ok in ALLOWED.items():
            bad = d[~d[c].isin(ok)]
            if len(bad):
                problems.append(f"{name} pass: {len(bad)} rows with a value of {c} outside the protocol: {sorted(bad[c].unique())[:6]}")
        if d.places.isna().any():
            problems.append(f"{name} pass: {int(d.places.isna().sum())} rows without a number of places")
        dup = d.duplicated(["strip", "label"]).sum()
        if dup:
            problems.append(f"{name} pass: {dup} duplicate rows")
    m = f.merge(first, on=["strip", "label"], how="left", indicator=True)
    miss = m[m._merge == "left_only"]
    if len(miss):
        problems.append(f"first pass: {len(miss)} buildings of the frame without a reading (strips {sorted(miss.strip.unique())[:8]})")
    extra = first.merge(f[["strip", "label"]], on=["strip", "label"], how="left", indicator=True)
    if (extra._merge == "left_only").any():
        problems.append(f"first pass: {(extra._merge == 'left_only').sum()} rows that are not in the frame")
    inc = m[(m.driveway == "no") & (m.places > 0)]
    if len(inc):
        problems.append(f"first pass: {len(inc)} rows with driveway = no and places > 0")
    m = m.drop(columns="_merge")
    m.to_csv(TABLES / "offstreet_readings.csv", index=False)
    second.to_csv(TABLES / "offstreet_readings_second_pass.csv", index=False)

    checks = []
    # 1. two independent readings of the same building
    j = first.merge(second, on=["strip", "label"], suffixes=("_1", "_2"))
    yn = j[j.driveway_1.isin(["yes", "no"]) & j.driveway_2.isin(["yes", "no"])]
    checks.append({"check": "two readings of the same building: driveway yes/no", "buildings": len(yn), "agree_pct": round(100 * (yn.driveway_1 == yn.driveway_2).mean(), 1),
                   "kappa": round(kappa(list(yn.driveway_1), list(yn.driveway_2)), 2),
                   "detail": f"yes/yes {((yn.driveway_1 == 'yes') & (yn.driveway_2 == 'yes')).sum()}, no/no {((yn.driveway_1 == 'no') & (yn.driveway_2 == 'no')).sum()}, "
                             f"yes/no {((yn.driveway_1 == 'yes') & (yn.driveway_2 == 'no')).sum()}, no/yes {((yn.driveway_1 == 'no') & (yn.driveway_2 == 'yes')).sum()}; "
                             f"unclear in either: {len(j) - len(yn)} of {len(j)}"})
    checks.append({"check": "two readings of the same building: places", "buildings": len(j), "agree_pct": round(100 * (j.places_1 == j.places_2).mean(), 1),
                   "kappa": np.nan, "detail": f"total places {int(j.places_1.sum())} (first) against {int(j.places_2.sum())} (second); within one place {100 * ((j.places_1 - j.places_2).abs() <= 1).mean():.1f} %; "
                                              f"mean absolute difference {(j.places_1 - j.places_2).abs().mean():.2f}"})
    # 2. the reading of October 25, 2026 on rue de Terrebonne
    b = pd.read_csv(GARAGES / "buildings_geo.csv", dtype={"uev_id": str})
    b = b[b.driveway_today.isin(["yes", "no"]) & b.uev_id.notna()]
    key = {}
    for _, r in m.iterrows():
        for u in str(r.uev_ids).split():
            key[u.zfill(8)] = (r.driveway, r.places, r.strip, r.label)
    b["new"] = [key.get(str(u).zfill(8), (None,))[0] for u in b.uev_id]
    c = b[b.new.isin(["yes", "no"])]
    checks.append({"check": "against the reading of October 25, 2026 (rue de Terrebonne): driveway yes/no", "buildings": len(c),
                   "agree_pct": round(100 * (c.new == c.driveway_today).mean(), 1), "kappa": round(kappa(list(c.new), list(c.driveway_today)), 2),
                   "detail": f"Oct 25 yes: {(c.driveway_today == 'yes').sum()}, new yes: {(c.new == 'yes').sum()}; Oct 25 yes and new no {((c.driveway_today == 'yes') & (c.new == 'no')).sum()}, "
                             f"Oct 25 no and new yes {((c.driveway_today == 'no') & (c.new == 'yes')).sum()}; not matched or unclear: {len(b) - len(c)} of {len(b)}"})
    # 3. by reader
    for n, g in m.groupby("batch"):
        checks.append({"check": f"reader {int(n):02d}", "buildings": len(g), "agree_pct": np.nan, "kappa": np.nan,
                       "detail": f"driveway yes {100 * (g.driveway == 'yes').mean():.0f} %, unclear {100 * (g.driveway == 'unclear').mean():.0f} %, places per building {g.places.mean():.2f}, "
                                 f"low confidence {100 * (g.confidence == 'low').mean():.0f} %"})
    ck = pd.DataFrame(checks); ck.to_csv(TABLES / "offstreet_reading_checks.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 160)
    print(ck.to_string(index=False))
    print(f"buildings read: {m.driveway.notna().sum()} of {len(f)}; driveway yes {(m.driveway == 'yes').sum()}, no {(m.driveway == 'no').sum()}, unclear {(m.driveway == 'unclear').sum()}; places {m.places.sum():.0f}")
    if problems:
        print("PROBLEMS:"); [print("  -", p) for p in problems]
        sys.exit(1)
    print("OK offstreet_readings")


if __name__ == "__main__":
    main()
