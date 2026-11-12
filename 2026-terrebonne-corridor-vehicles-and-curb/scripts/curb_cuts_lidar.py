"""Test (owner's request, Nov 12, 2026): can the City's 2015 airborne LiDAR find the curb cuts (lowered curbs at
driveways and parking entrances) along rue de Terrebonne, judged against the owner's street-level check of every lot?

Method. Ground-classified returns (class 2) within 22 m of the lane's centre line (pdal export, cached outside the
repository). Every 0.5 m along the centre line, on each side, the returns within 0.75 m along the street give a
cross-section. The curb is located per stretch of 40 m as the offset where the ground steps up most (the sidewalk
side minus the roadway side, bands 0.2-1.0 m on each side of the candidate). At each station the curb step is the
median height of the sidewalk band minus that of the roadway band, both at the stretch's curb offset; at least 3
returns in each band, otherwise the station is « no data » (a parked car or a tree hides the curb). A cut is a run of
stations whose step, smoothed over 2.5 m, is at least REL_M under the local curb (40 m) and under ABS_M, at least MIN_RUN long, outside INTERSECTION_M of an intersection (corners are
lowered for pedestrians and are not driveways), gaps of no data up to GAP_M bridged.

Ground truth: the owner's check (1954-underwriters-plans-terrebonne-garages/derived/street_check/lots.csv). A lot is
expected to have a cut on Terrebonne when it has car access by its own or a shared driveway or a front pad and its
note does not place the access on a lane or the cross street; expected to have none when it has no car access and
no conversion. Corner lots, larger buildings, conversions and « cannot tell » are reported apart. A lot « has a
detected cut » when a cut run overlaps its frontage on its side of the street (shared driveways serve two lots).
The LiDAR is of 2015, the check of 2026: a driveway built or removed in between counts against the detector.

Outputs: derived/tables/terrebonne_curb_cuts_lidar.csv (runs), terrebonne_curb_cut_test_lots.csv (lot by lot),
derived/curb_cut_test.json.   Run: ~/.venvs/omd/bin/python scripts/curb_cuts_lidar.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import line_locate_point
from shapely.geometry import Point
from shapely.ops import linemerge

import offstreet_strips as S
from corridor_lib import CACHE, CRS, GARAGES, LANE, ROOT, TABLES

PTS = CACHE / "terrebonne_lane_ground_points.csv"
STEP, HALF_WIN, BAND = 0.5, 0.75, (0.2, 1.0)
SEARCH = (3.0, 11.0)          # where the curb may be, metres from the centre line
REL_M, ABS_M, MIN_RUN, GAP_M, INTERSECTION_M = 0.05, 0.10, 2.0, 1.0, 12.0   # setting retained after the sweep (tuned on the same lots: optimistic)
SWEEP = [(r, a, m) for r in (0.04, 0.05, 0.06, 0.07, 0.08) for a in (0.06, 0.08, 0.10, 0.12) for m in (2.0, 2.5, 3.0)]
STREET_KINDS = {"own driveway", "shared driveway", "front pad"}
LANE_WORDS = ("lane", "laneway", "alley", "rear", "back", "side street", "off of", "oxford", "draper")


def bands(z, d, c):
    lo, hi = BAND
    sw = z[(d >= c + lo) & (d <= c + hi)]; rd = z[(d >= c - hi) & (d <= c - lo)]
    return (np.median(sw) - np.median(rd)) if (len(sw) >= 3 and len(rd) >= 3) else np.nan


def main():
    lane = gpd.read_file(LANE).to_crs(CRS)
    U = lane.geometry.union_all(); L = linemerge(U) if U.geom_type == "MultiLineString" else U
    if L.coords[0][0] > L.coords[-1][0]:
        L = L.reverse()                                             # s grows eastward
    ends = set()
    for g in lane.geometry:
        for c in (g.coords[0], g.coords[-1]):
            ends.add(round(float(line_locate_point(L, Point(c))), 1))
    inter = np.array(sorted(ends))
    p = pd.read_csv(PTS)
    xy = np.c_[p.X.values, p.Y.values]
    s = line_locate_point(L, gpd.points_from_xy(p.X, p.Y))
    G = np.arange(0, L.length + 0.25, 0.25); P = np.array([L.interpolate(v).coords[0] for v in G])          # the line on a 0.25 m grid
    TG = np.gradient(P, axis=0); TG /= np.linalg.norm(TG, axis=1)[:, None]
    foot = np.c_[np.interp(s, G, P[:, 0]), np.interp(s, G, P[:, 1])]; t = TG[np.clip(np.rint(s / 0.25).astype(int), 0, len(G) - 1)]
    rel = xy - foot; d = t[:, 0] * rel[:, 1] - t[:, 1] * rel[:, 0]             # signed offset: + = left of the eastward line = north side
    p["s"], p["d"] = s, d
    rows = []
    for side, sg in (("N", 1), ("S", -1)):
        q = p[(np.sign(p.d) == sg) & (np.abs(p.d).between(SEARCH[0] - 1.2, SEARCH[1] + 1.2))]
        qs, qd, qz = q.s.values, np.abs(q.d.values), q.Z.values
        order = np.argsort(qs); qs, qd, qz = qs[order], qd[order], qz[order]
        st = np.arange(0, L.length, STEP)
        # 1. curb offset per 40 m stretch: the candidate with the largest median step over the stretch
        cand = np.arange(SEARCH[0], SEARCH[1], 0.1)
        curb = {}
        for k0 in np.arange(0, L.length, 40.0):
            i0, i1 = np.searchsorted(qs, [k0, k0 + 40.0])
            if i1 - i0 < 60:
                continue
            zz, dd, ss = qz[i0:i1], qd[i0:i1], qs[i0:i1]
            best, bc = -1, None
            for c in cand:
                steps = [bands(zz[(ss >= m - HALF_WIN) & (ss < m + HALF_WIN)], dd[(ss >= m - HALF_WIN) & (ss < m + HALF_WIN)], c) for m in np.arange(k0 + 2, k0 + 40, 4.0)]
                v = np.nanmedian(steps) if np.isfinite(steps).sum() >= 3 else -1
                if v > best:
                    best, bc = v, c
            curb[k0] = (bc, best)
        # 2. the step at every station, at its stretch's curb offset
        for m in st:
            k0 = 40.0 * np.floor(m / 40.0)
            if k0 not in curb or curb[k0][0] is None:
                rows.append((side, m, np.nan, np.nan)); continue
            c = curb[k0][0]
            i0, i1 = np.searchsorted(qs, [m - HALF_WIN, m + HALF_WIN])
            rows.append((side, m, c, bands(qz[i0:i1], qd[i0:i1], c)))
    prof = pd.DataFrame(rows, columns=["side", "s", "curb_offset", "step"])
    prof["near_intersection"] = [bool(np.min(np.abs(inter - v)) < INTERSECTION_M) for v in prof.s]
    prof = prof.sort_values(["side", "s"]).reset_index(drop=True)
    prof["sm"] = prof.groupby("side").step.transform(lambda x: x.rolling(5, center=True, min_periods=3).median())          # 2.5 m
    prof["base"] = prof.groupby("side").step.transform(lambda x: x.rolling(81, center=True, min_periods=20).quantile(0.6))  # the local curb, 40 m
    low = lambda rel, ab: (prof.sm < prof.base - rel) & (prof.sm < ab) & ~prof.near_intersection
    prof["low"] = low(REL_M, ABS_M)
    prof.to_csv(CACHE / "terrebonne_curb_profile.csv", index=False)            # every station, for inspection
    # 3. runs of low stations, bridging short gaps of no data
    def find_runs(mask, min_run):
        runs = []
        for side, g in prof.assign(lowm=mask).groupby("side"):
            cur = None; gap = 0.0
            for r in g.itertuples():
                if r.lowm:
                    cur = [r.s, r.s, [r.step]] if cur is None else [cur[0], r.s, cur[2] + [r.step]]; gap = 0.0
                elif np.isnan(r.step) and cur is not None and gap + STEP <= GAP_M and not r.near_intersection:
                    gap += STEP
                else:
                    if cur is not None and cur[1] - cur[0] + STEP >= min_run:
                        runs.append({"side": side, "s_from": cur[0], "s_to": cur[1] + STEP, "length_m": cur[1] - cur[0] + STEP, "median_step_m": float(np.nanmedian(cur[2]))})
                    cur, gap = None, 0.0
            if cur is not None and cur[1] - cur[0] + STEP >= min_run:
                runs.append({"side": side, "s_from": cur[0], "s_to": cur[1] + STEP, "length_m": cur[1] - cur[0] + STEP, "median_step_m": float(np.nanmedian(cur[2]))})
        return pd.DataFrame(runs, columns=["side", "s_from", "s_to", "length_m", "median_step_m"])
    runs = find_runs(prof.low, MIN_RUN)
    R = runs; R.round(2).to_csv(TABLES / "terrebonne_curb_cuts_lidar.csv", index=False)
    # 4. the lots: frontage on their side, expected against detected
    b, alll, gb = S.frame()
    lots = pd.read_csv(GARAGES / "street_check" / "lots.csv", dtype={"key": str})
    out = []
    for r in lots.itertuples():
        poly = b.loc[r.key].geometry
        coords = np.vstack([np.array(gg.exterior.coords) for gg in (poly.geoms if poly.geom_type == "MultiPolygon" else [poly])])
        sv = line_locate_point(L, gpd.points_from_xy(coords[:, 0], coords[:, 1]))
        near = np.array([L.distance(Point(c)) for c in coords]) < 40
        s0, s1 = (sv[near].min(), sv[near].max()) if near.any() else (np.nan, np.nan)
        note = str(r.note if isinstance(r.note, str) else "").lower()
        corner = "Terrebonne" not in str(r.roll_street)
        large = str(r.large) == "True"
        if corner or large or r.access not in ("yes", "no") or str(r.converted).startswith("yes"):
            expect = "apart: " + ("corner lot" if corner else "larger building" if large else "converted" if str(r.converted).startswith("yes") else "cannot tell")
        elif r.access == "yes" and r.kind in STREET_KINDS and not any(w in note for w in LANE_WORDS):
            expect = "cut"
        elif r.access == "no":
            expect = "no cut"
        else:
            expect = "apart: access from a lane or rear"
        hit = R[(R.side == r.side) & (R.s_to > s0 - 0.5) & (R.s_from < s1 + 0.5)] if np.isfinite(s0) else R.iloc[0:0]
        pr = prof[(prof.side == r.side) & prof.s.between(s0, s1)]
        out.append({"n": r.n, "key": r.key, "civic": f"{r.civic_lo}" + ("" if r.civic_hi == r.civic_lo else f"-{r.civic_hi}"), "side": r.side,
                    "s_from": round(s0, 1), "s_to": round(s1, 1), "access": r.access, "kind": r.kind, "converted": r.converted, "expect": expect,
                    "detected": bool(len(hit)), "cut_m": round(float(hit.length_m.sum()), 1), "frontage_no_data_share": round(float(pr.step.isna().mean()), 2) if len(pr) else np.nan})
    T = pd.DataFrame(out); T.to_csv(TABLES / "terrebonne_curb_cut_test_lots.csv", index=False)
    E = T[T.expect.isin(["cut", "no cut"])]
    tp = int(((E.expect == "cut") & E.detected).sum()); fn = int(((E.expect == "cut") & ~E.detected).sum())
    fp = int(((E.expect == "no cut") & E.detected).sum()); tn = int(((E.expect == "no cut") & ~E.detected).sum())
    conv = T[T.expect == "apart: converted"]
    pos, neg = T[T.expect == "cut"], T[T.expect == "no cut"]
    def hits(rr, lots):
        return int(sum(((rr.side == r.side) & (rr.s_to > r.s_from - 0.5) & (rr.s_from < r.s_to + 0.5)).any() for r in lots.itertuples()))
    sw = []
    for rel, ab, mr in SWEEP:
        rr = find_runs(low(rel, ab), mr)
        sw.append({"rel_m": rel, "abs_m": ab, "min_run_m": mr, "detected_of_expected_cut": hits(rr, pos), "detected_of_expected_no_cut": hits(rr, neg), "runs": len(rr), "metres": round(float(rr.length_m.sum()), 1)})
    pd.DataFrame(sw).to_csv(TABLES / "terrebonne_curb_cut_sweep.csv", index=False)
    matched = [x.length_m for x in R.itertuples() if ((pos.side == x.side) & (pos.s_to > x.s_from - 0.5) & (pos.s_from < x.s_to + 0.5)).any()]
    res = {"stations": int(len(prof)), "no_data_share": round(float(prof.step.isna().mean()), 3),
           "curb_step_median_m": round(float(prof.base.median()), 3),
           "runs": int(len(R)), "run_length_median_m": round(float(R.length_m.median()), 1) if len(R) else None,
           "run_length_total_m": round(float(R.length_m.sum()), 1) if len(R) else 0.0,
           "lots": {"expected_cut": tp + fn, "detected_of_expected_cut": tp, "expected_no_cut": fp + tn, "detected_of_expected_no_cut": fp,
                    "recall": round(tp / (tp + fn), 3) if tp + fn else None, "false_alarm_rate": round(fp / (fp + tn), 3) if fp + tn else None,
                    "apart": T.expect.value_counts().to_dict(), "converted_with_cut_detected": int(conv.detected.sum()), "converted": int(len(conv))},
           "matched_run_length_m_quartiles": [round(float(v), 1) for v in np.quantile(matched, [.25, .5, .75])] if matched else None,
           "step_at_expected_cut_lots_median_m": round(float(np.nanmedian([prof[(prof.side == r.side) & prof.s.between(r.s_from, r.s_to)].sm.min() for r in pos.itertuples()])), 3),
           "step_at_expected_no_cut_lots_median_m": round(float(np.nanmedian([prof[(prof.side == r.side) & prof.s.between(r.s_from, r.s_to)].sm.min() for r in neg.itertuples()])), 3),
           "parameters": {"relative_drop_m": REL_M, "below_m": ABS_M, "min_run_m": MIN_RUN, "gap_m": GAP_M, "intersection_m": INTERSECTION_M, "window_m": 2 * HALF_WIN, "band_m": BAND}}
    json.dump(res, open(ROOT / "derived/curb_cut_test.json", "w"), indent=1)
    print(json.dumps(res, indent=1))
    print("OK curb_cuts_lidar")


if __name__ == "__main__":
    main()
