"""Stage 5b, second pass: collate the readings of private parking (protocol version 2) and check them.

Input: derived/readings/v2_batch_NN.csv (batches 1 to 12 cover every crop once; batch 13 is an independent second
reading of one crop in ten), derived/readings/batches_v2.csv, derived/tables/offstreet_crops.csv and
offstreet_frame.csv; if present, the owner's check (derived/readings/owner_check.json, exported from the check page).
Checks: every lot read once in the first reading; allowed values; places consistent; agreement between the two
readings; agreement with the owner's check on the random sample (sensitivity, specificity, places).

Outputs (derived/tables/): offstreet_readings_v2.csv, offstreet_readings_v2_second.csv, offstreet_reading_checks_v2.csv,
offstreet_owner_check.csv (when the owner's check exists)
Run:  ~/.venvs/omd/bin/python scripts/offstreet_readings_v2.py
"""
import json
import sys

import numpy as np
import pandas as pd

from corridor_lib import ROOT, TABLES

RD = ROOT / "derived" / "readings"
ALLOWED = {"car_access": {"yes", "no", "unclear"}, "kind": {"own driveway", "shared driveway", "front pad", "rear", "parking lot", "none"},
           "garage": {"yes", "no", "unclear"}, "vehicle": {"yes", "no"}, "confidence": {"high", "medium", "low"}}


def load(n):
    d = pd.read_csv(RD / f"v2_batch_{n:02d}.csv", dtype=str, keep_default_na=False, on_bad_lines="warn")
    d.columns = [c.strip() for c in d.columns]
    for c in d.columns:
        d[c] = d[c].str.strip()
    d["label"] = d.label.str.replace("*", "", regex=False).astype(int)
    for c in ("places_independent", "places_total"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["batch"] = n
    return d


def kappa(a, b):
    a, b = list(a), list(b); n = len(a)
    if n == 0:
        return float("nan")
    po = np.mean(np.array(a) == np.array(b)); pe = sum((a.count(c) / n) * (b.count(c) / n) for c in set(a) | set(b))
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def main():
    crops = pd.read_csv(TABLES / "offstreet_crops.csv")
    f = pd.read_csv(TABLES / "offstreet_frame.csv", dtype={"dauid": str, "uev_ids": str})
    bt = pd.read_csv(RD / "batches_v2.csv")
    have = lambda n: (RD / f"v2_batch_{n:02d}.csv").exists()
    b1 = [n for n in sorted(bt[bt["pass"] == 1].batch.unique()) if have(n)]; b2 = [n for n in sorted(bt[bt["pass"] == 2].batch.unique()) if have(n)]
    problems = []
    missing_batches = [n for n in sorted(bt.batch.unique()) if not have(n)]
    if missing_batches:
        problems.append(f"batches not yet written: {missing_batches}")
    first = pd.concat([load(n) for n in b1], ignore_index=True)
    second = pd.concat([load(n) for n in b2], ignore_index=True) if b2 else first.iloc[0:0]
    for name, d in (("first", first), ("second", second)):
        for c, ok in ALLOWED.items():
            bad = d[~d[c].isin(ok)]
            if len(bad):
                problems.append(f"{name} reading: {len(bad)} rows with a value of {c} outside the protocol: {sorted(bad[c].unique())[:6]}")
        if d[["places_independent", "places_total"]].isna().any().any():
            problems.append(f"{name} reading: rows without a number of places")
        if d.duplicated(["crop", "label"]).sum():
            problems.append(f"{name} reading: {d.duplicated(['crop', 'label']).sum()} duplicate rows")
        if (d.places_total < d.places_independent).any():
            problems.append(f"{name} reading: {(d.places_total < d.places_independent).sum()} rows with fewer total than independent places")
        if ((d.car_access == "no") & (d.places_total > 0)).any():
            problems.append(f"{name} reading: {((d.car_access == 'no') & (d.places_total > 0)).sum()} rows with access = no and places > 0")
    m = crops.merge(first, on=["crop", "label"], how="left", indicator=True)
    miss = m[m._merge == "left_only"]
    if len(miss):
        problems.append(f"first reading: {len(miss)} lots without a reading")
    m = m.drop(columns="_merge").merge(f.drop(columns=["label"]), on=["key", "strip"], how="left")
    m.to_csv(TABLES / "offstreet_readings_v2.csv", index=False)
    second.to_csv(TABLES / "offstreet_readings_v2_second.csv", index=False)

    checks = []
    j = first.merge(second, on=["crop", "label"], suffixes=("_1", "_2"))
    if len(j):
        yn = j[j.car_access_1.isin(["yes", "no"]) & j.car_access_2.isin(["yes", "no"])]
        checks.append({"check": "two readings of the same lot: car access, both decisive", "lots": len(yn), "agree_pct": round(100 * (yn.car_access_1 == yn.car_access_2).mean(), 1),
                       "kappa": round(kappa(yn.car_access_1, yn.car_access_2), 2),
                       "detail": f"yes/yes {((yn.car_access_1 == 'yes') & (yn.car_access_2 == 'yes')).sum()}, no/no {((yn.car_access_1 == 'no') & (yn.car_access_2 == 'no')).sum()}, "
                                 f"yes/no {((yn.car_access_1 == 'yes') & (yn.car_access_2 == 'no')).sum()}, no/yes {((yn.car_access_1 == 'no') & (yn.car_access_2 == 'yes')).sum()}"})
        checks.append({"check": "two readings of the same lot: car access, three values", "lots": len(j), "agree_pct": round(100 * (j.car_access_1 == j.car_access_2).mean(), 1),
                       "kappa": round(kappa(j.car_access_1, j.car_access_2), 2), "detail": f"unclear in either: {len(j) - len(yn)}; unclear in both: {((j.car_access_1 == 'unclear') & (j.car_access_2 == 'unclear')).sum()}"})
        for c in ("places_independent", "places_total"):
            checks.append({"check": f"two readings of the same lot: {c}", "lots": len(j), "agree_pct": round(100 * (j[c + '_1'] == j[c + '_2']).mean(), 1), "kappa": np.nan,
                           "detail": f"sum {int(j[c + '_1'].sum())} against {int(j[c + '_2'].sum())}; within one {100 * ((j[c + '_1'] - j[c + '_2']).abs() <= 1).mean():.1f} %; mean absolute difference {(j[c + '_1'] - j[c + '_2']).abs().mean():.2f}"})
    for n, g in m.groupby("batch"):
        checks.append({"check": f"reader {int(n):02d}", "lots": len(g), "agree_pct": np.nan, "kappa": np.nan,
                       "detail": f"access yes {100 * (g.car_access == 'yes').mean():.0f} %, unclear {100 * (g.car_access == 'unclear').mean():.0f} %, independent places per lot {g.places_independent.mean():.2f}, "
                                 f"total {g.places_total.mean():.2f}, low confidence {100 * (g.confidence == 'low').mean():.0f} %"})
    oc = RD / "owner_check.json"
    if oc.exists():
        o = pd.DataFrame(json.load(open(oc))["answers"])
        o = o[o.get("car_access", "").astype(str) != ""].merge(m, on="key", suffixes=("_owner", ""))
        for c in ("places_independent", "places_total"):
            o[c + "_owner"] = pd.to_numeric(o[c + "_owner"], errors="coerce")
        o.to_csv(TABLES / "offstreet_owner_check.csv", index=False)
        for name, d in (("five dwellings or fewer", o[~o.large]), ("six dwellings or more", o[o.large])):
            dd = d[d.car_access_owner.isin(["yes", "no"])]
            ry = dd[dd.car_access == "yes"]; rn = dd[dd.car_access == "no"]; ru = dd[dd.car_access == "unclear"]
            oy = dd[dd.car_access_owner == "yes"]; on = dd[dd.car_access_owner == "no"]
            checks.append({"check": f"against the owner's check, {name}: car access", "lots": len(dd),
                           "agree_pct": round(100 * (dd[dd.car_access != 'unclear'].car_access == dd[dd.car_access != 'unclear'].car_access_owner).mean(), 1) if len(dd) else np.nan,
                           "kappa": round(kappa(dd[dd.car_access != 'unclear'].car_access, dd[dd.car_access != 'unclear'].car_access_owner), 2),
                           "detail": f"owner yes {len(oy)}, no {len(on)}, cannot tell {len(d) - len(dd)}; reader yes: {(ry.car_access_owner == 'yes').sum()} of {len(ry)} confirmed; "
                                     f"reader no: {(rn.car_access_owner == 'no').sum()} of {len(rn)} confirmed; reader unclear ({len(ru)}): owner yes {(ru.car_access_owner == 'yes').sum()}, no {(ru.car_access_owner == 'no').sum()}"})
            for c in ("places_independent", "places_total"):
                x = dd[dd[c + "_owner"].notna()]
                checks.append({"check": f"against the owner's check, {name}: {c}", "lots": len(x), "agree_pct": round(100 * (x[c] == x[c + '_owner']).mean(), 1) if len(x) else np.nan, "kappa": np.nan,
                               "detail": f"sum: reader {x[c].sum():.0f}, owner {x[c + '_owner'].sum():.0f}"})
    ck = pd.DataFrame(checks); ck.to_csv(TABLES / "offstreet_reading_checks_v2.csv", index=False)
    pd.set_option("display.width", 260); pd.set_option("display.max_colwidth", 190)
    print(ck.to_string(index=False))
    print(f"lots read: {m.car_access.notna().sum()} of {len(crops)}; access yes {(m.car_access == 'yes').sum()}, no {(m.car_access == 'no').sum()}, unclear {(m.car_access == 'unclear').sum()}; "
          f"independent places {m.places_independent.sum():.0f}, total {m.places_total.sum():.0f}")
    if problems:
        print("PROBLEMS:"); [print("  -", p) for p in problems]
        sys.exit(1)
    print("OK offstreet_readings_v2")


if __name__ == "__main__":
    main()
