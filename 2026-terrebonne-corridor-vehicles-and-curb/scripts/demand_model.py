"""Stage 3: automobiles and light trucks below the FSA: a model, not a measurement.

The SAAQ release locates each vehicle of 2023-2024 to its FSA only. The model:
  1. fit, across the FSAs beginning with H that hold 1,000 households or more, the logarithm of automobiles and
     light trucks per household (2024, type INFERRED) on four 2021 Census variables: share of renter households,
     share of commuters who drive, persons per household, logarithm of the median household income
     (robust regression, Huber weights: a few FSAs hold fleets registered to businesses);
  2. predict the rate of every dissemination area from its own census variables;
  3. scale the predictions so that the parts of the dissemination areas lying in each FSA sum to the FSA's
     registered total.
Tests: each FSA left out in turn (does the model find an FSA's rate from its census variables?) and a
downscaling test one level up: neighbouring FSAs grouped by threes, the model fitted without them, the group's
registered total shared among its members by the model, compared with their registered totals and with the
plain split in proportion to households.
Intervals (Monte Carlo): FSAs resampled and the model refitted; the sampling error of the 25 % sample variables
in each dissemination area; an unexplained factor per dissemination area whose spread is the one measured by
the downscaling test (dissemination areas are about twenty times smaller than FSAs: their true spread may be
larger; a second set of intervals doubles it); every draw rescaled to the FSA totals.

Outputs (derived/tables/): model_specifications.csv, model_coefficients.csv, lofo_errors.csv,
downscaling_test.csv, downscaling_summary.csv, fsa_scale_factors.csv, da_vehicles.csv; the draws go to the cache.
Run:  ~/.venvs/omd/bin/python scripts/demand_model.py [--draws=2000]
"""
import sys
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.cluster.vq import kmeans2

from corridor_lib import CACHE, CRS, FSA_SHP, FSAS, MIN_HH, TABLES, YEAR

warnings.filterwarnings("ignore")
SPECS = {"households only": [],
         "tenure, dwelling type": ["renter", "ground", "apt_high"],
         "commuting": ["car_share"],
         "tenure, commuting, household size": ["renter", "car_share", "hhsize"],
         "tenure, commuting, household size, income": ["renter", "car_share", "hhsize", "log_income"],
         "tenure, commuting, household size, income, dwelling type": ["renter", "car_share", "hhsize", "log_income", "ground", "apt_high"]}
CHOSEN = "tenure, commuting, household size, income"
ALT = ["tenure, commuting, household size", "tenure, commuting, household size, income, dwelling type"]
LABEL = {"const": "constant", "renter": "share of renter households", "car_share": "share of commuters who drive",
         "hhsize": "persons per household", "log_income": "log of median household income",
         "ground": "share of single, semi-detached and row houses", "apt_high": "share of apartments in buildings of five storeys or more"}
SEED = 20261111


def features(d):
    hh = d.households
    X = pd.DataFrame(index=d.index)
    X["renter"] = d.renter / (d.owner + d.renter)
    X["car_share"] = d.commute_car_driver / d.commuters
    X["hhsize"] = d.persons_in_households / hh
    X["log_income"] = np.log(d.median_household_income.where(d.median_household_income > 0))
    X["ground"] = (d.dw_single + d.dw_semi + d.dw_row + d.dw_other_attached) / hh
    X["apt_high"] = d.dw_apt_high / hh
    return X


def design(X, cols):
    Z = X[cols].copy()
    Z.insert(0, "const", 1.0)
    return Z


def fit(X, lr, cols, idx):
    return sm.RLM(lr[idx], design(X.loc[idx], cols), M=sm.robust.norms.HuberT()).fit()


def pct(e):
    a = np.abs(np.expm1(e))
    return {"median_abs_pct": 100 * a.median(), "p75_abs_pct": 100 * a.quantile(0.75), "p90_abs_pct": 100 * a.quantile(0.9), "largest_abs_pct": 100 * a.max()}


def main():
    B = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--draws=")), 2000))
    rng = np.random.default_rng(SEED)
    col = f"automobiles_{YEAR}_inferred"
    allf = pd.read_csv(TABLES / "fsa_model_table.csv", index_col=0)
    f = allf[(allf.households >= MIN_HH) & allf[col].notna()].copy()
    X = features(f); lr = np.log(f[col] / f.households)
    print(f"FSAs fitted: {len(f)}; automobiles per household: median {np.exp(lr).median():.2f}, range {np.exp(lr).min():.2f} to {np.exp(lr).max():.2f}")

    # 1. specifications, each FSA left out in turn
    rows, lofo = [], {}
    for name, cols in SPECS.items():
        e = pd.Series({i: fit(X, lr, cols, f.index.drop(i)).predict(design(X.loc[[i]], cols)).iloc[0] - lr[i] for i in f.index})
        lofo[name] = e
        rows.append({"specification": name, "variables": len(cols), **pct(e), "H4A_pct": 100 * np.expm1(e["H4A"]), "H4B_pct": 100 * np.expm1(e["H4B"]),
                     "chosen": name == CHOSEN})
    sp = pd.DataFrame(rows); sp.round(1).to_csv(TABLES / "model_specifications.csv", index=False)
    print(sp.round(1).to_string(index=False))
    cols = SPECS[CHOSEN]
    m = fit(X, lr, cols, f.index)
    co = pd.DataFrame({"variable": [LABEL[c] for c in m.params.index], "coefficient": m.params.values, "standard_error": m.bse.values})
    co.round(4).to_csv(TABLES / "model_coefficients.csv", index=False)
    print(co.round(3).to_string(index=False))
    e = lofo[CHOSEN]
    fleet = e[np.expm1(-e) > 0.5].index            # registered count more than 1.5 times the left-out prediction
    lo = pd.DataFrame({"households": f.households, "automobiles_per_household": np.exp(lr).round(3),
                       "predicted_when_left_out": np.exp(lr + e).round(3), "error_pct": (100 * np.expm1(e)).round(1),
                       "registered_over_1.5_times_predicted": f.index.isin(fleet)})
    lo.to_csv(TABLES / "lofo_errors.csv")
    print("FSAs whose registered count exceeds 1.5 times the left-out prediction:", ", ".join(fleet))

    # 2. downscaling test: groups of neighbouring FSAs
    fp = gpd.read_file(FSA_SHP, columns=["FSA"]).to_crs(CRS)
    fp = fp[fp.FSA.isin(f.index)].dissolve("FSA")
    cen = fp.geometry.representative_point()
    xy = np.c_[cen.x, cen.y][[list(fp.index).index(i) for i in f.index]]
    _, lab = kmeans2(xy, len(f) // 3, minit="++", seed=SEED)
    f["group"] = lab
    rows = []
    for gid, members in f.groupby("group").groups.items():
        if len(members) < 2:
            continue
        rest = f.index.difference(members)
        mg = fit(X, lr, cols, rest)
        w = f.households[members] * np.exp(mg.predict(design(X.loc[members], cols)))
        tot = f.loc[members, col].sum()
        est = tot * w / w.sum(); plain = tot * f.households[members] / f.households[members].sum()
        for i in members:
            rows.append({"fsa": i, "group": gid, "group_size": len(members), "registered": f.loc[i, col], "model_share": round(est[i]),
                         "households_share": round(plain[i]), "model_error_pct": 100 * (est[i] / f.loc[i, col] - 1),
                         "households_error_pct": 100 * (plain[i] / f.loc[i, col] - 1), "group_has_fleet_fsa": bool(set(members) & set(fleet))})
    ds = pd.DataFrame(rows); ds.round(1).to_csv(TABLES / "downscaling_test.csv", index=False)
    # the pair of the lane's own FSAs
    pair = list(FSAS); rest = f.index.difference(pair); mg = fit(X, lr, cols, rest)
    w = f.households[pair] * np.exp(mg.predict(design(X.loc[pair], cols))); tot = f.loc[pair, col].sum()
    pe = {i: 100 * (tot * w[i] / w.sum() / f.loc[i, col] - 1) for i in pair}
    ph = {i: 100 * (tot * f.households[i] / f.households[pair].sum() / f.loc[i, col] - 1) for i in pair}
    srows = []
    for name, d in (("all groups", ds), ("groups without an FSA of the fleet list", ds[~ds.group_has_fleet_fsa])):
        for meth in ("model", "households"):
            a = d[f"{meth}_error_pct"].abs()
            srows.append({"set": name, "method": "model" if meth == "model" else "in proportion to households", "fsas": len(d), "groups": d.group.nunique(),
                          "median_abs_pct": a.median(), "p75_abs_pct": a.quantile(0.75), "p90_abs_pct": a.quantile(0.9)})
    srows.append({"set": "H4A and H4B as one group", "method": "model", "fsas": 2, "groups": 1, "median_abs_pct": np.mean(np.abs(list(pe.values()))), "H4A_pct": pe["H4A"], "H4B_pct": pe["H4B"]})
    srows.append({"set": "H4A and H4B as one group", "method": "in proportion to households", "fsas": 2, "groups": 1, "median_abs_pct": np.mean(np.abs(list(ph.values()))), "H4A_pct": ph["H4A"], "H4B_pct": ph["H4B"]})
    dsum = pd.DataFrame(srows); dsum.round(1).to_csv(TABLES / "downscaling_summary.csv", index=False)
    print(dsum.round(1).to_string(index=False))
    clean = ds[~ds.group_has_fleet_fsa]
    le = np.log1p(clean.model_error_pct / 100)
    sigma = 1.4826 * np.median(np.abs(le - np.median(le)))
    print(f"spread of the unexplained factor (robust standard deviation of the log error, groups without a fleet FSA): {sigma:.3f}")

    # 3. dissemination areas
    da = pd.read_csv(TABLES / "da_census.csv", dtype={"dauid": str}).set_index("dauid")
    sh = pd.read_csv(TABLES / "da_fsa_shares.csv", dtype={"dauid": str})
    sh = sh[sh.fsa.isin(allf.index[allf[col].notna()])]
    da = da[da.households.fillna(0) > 0]
    sh = sh[sh.dauid.isin(da.index)]
    XD = features(da)
    main_fsa = sh.sort_values("share").groupby("dauid").fsa.last().reindex(da.index)
    XF = features(allf)
    imputed = pd.Series("", index=da.index)
    for c in set(sum(SPECS.values(), [])):
        bad = ~np.isfinite(XD[c])
        XD.loc[bad, c] = XF[c].reindex(main_fsa[bad]).values
        imputed[bad] = imputed[bad] + c + " "
    XD = XD.fillna(XF.loc[f.index].median())
    V = allf[col]
    di = pd.Index(da.index); fi = {k: n for n, k in enumerate(sorted(sh.fsa.unique()))}
    S = np.zeros((len(di), len(fi)))
    S[di.get_indexer(sh.dauid), sh.fsa.map(fi).values] = sh.share.values
    Vf = V.reindex(list(fi)).values
    hh = da.households.values

    def scaled(rate):
        part = (hh * rate)[:, None] * S                      # vehicles of each area's part in each FSA, before scaling
        k = Vf / part.sum(axis=0)
        return part * k, k

    part0, k0 = scaled(np.exp(m.predict(design(XD, cols)).values))
    kk = pd.DataFrame({"fsa": list(fi), "registered": Vf, "scale_factor": k0}).set_index("fsa")
    kk.round(3).to_csv(TABLES / "fsa_scale_factors.csv")
    print("scale factors:", {i: round(kk.scale_factor[i], 3) for i in FSAS}, "| all FSAs: median %.2f, 10th-90th percentile %.2f-%.2f" % (
        kk.scale_factor.median(), kk.scale_factor.quantile(0.1), kk.scale_factor.quantile(0.9)))
    alt = {a: scaled(np.exp(fit(X, lr, SPECS[a], f.index).predict(design(XD, SPECS[a])).values))[0].sum(axis=1) for a in ALT}

    n_car = np.maximum(da.commuters.fillna(0).values / 4, 1); n_ten = np.maximum((da.owner + da.renter).fillna(0).values / 4, 1)
    draws = {1: np.empty((len(di), B)), 2: np.empty((len(di), B))}
    for b in range(B):
        idx = rng.choice(f.index, len(f))
        mb = sm.RLM(lr[idx].values, design(X.loc[idx], cols).values, M=sm.robust.norms.HuberT()).fit()
        Xb = XD.copy()
        Xb["car_share"] = rng.binomial(np.round(n_car).astype(int), XD.car_share.clip(0, 1).values) / np.round(n_car)
        Xb["renter"] = rng.binomial(np.round(n_ten).astype(int), XD.renter.clip(0, 1).values) / np.round(n_ten)
        base = design(Xb, cols).values @ mb.params
        z = rng.standard_normal(len(di))
        for mult in (1, 2):
            draws[mult][:, b] = scaled(np.exp(base + mult * sigma * z))[0].sum(axis=1)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / "da_vehicle_draws.npz", dauid=np.array(di), draws=draws[1], draws_wide=draws[2])
    q = lambda a, p: np.quantile(a, p, axis=1)
    out = pd.DataFrame({"households": hh, "main_fsa": main_fsa.values,
                        "share_in_H4A": S[:, fi["H4A"]].round(3), "share_in_H4B": S[:, fi["H4B"]].round(3),
                        "automobiles_modelled": part0.sum(axis=1).round(0),
                        "low_90": q(draws[1], 0.05).round(0), "high_90": q(draws[1], 0.95).round(0),
                        "low_90_wide": q(draws[2], 0.05).round(0), "high_90_wide": q(draws[2], 0.95).round(0)}, index=di)
    out["per_household"] = (out.automobiles_modelled / out.households).round(2)
    out["per_household_low_90"] = (out.low_90 / out.households).round(2); out["per_household_high_90"] = (out.high_90 / out.households).round(2)
    for a in ALT:
        out["alt_" + ("3_variables" if a == ALT[0] else "6_variables")] = alt[a].round(0)
    for c in cols:
        out[c] = XD[c].round(3)
    out["imputed_from_fsa"] = imputed.str.strip()
    out = out[(out.share_in_H4A + out.share_in_H4B) > 0]
    out.to_csv(TABLES / "da_vehicles.csv")
    chk = {i: (part0[:, fi[i]].sum(), V[i]) for i in FSAS}
    print("dissemination areas with a part in H4A or H4B:", len(out), "| parts sum to the registered totals:", {i: (round(a), round(b)) for i, (a, b) in chk.items()})
    print("per household across those areas: 10th %.2f, median %.2f, 90th %.2f" % tuple(out.per_household.quantile([0.1, 0.5, 0.9])))
    hw = 100 * ((out.high_90 - out.low_90) / 2 / out.automobiles_modelled).median()
    hw2 = 100 * ((out.high_90_wide - out.low_90_wide) / 2 / out.automobiles_modelled).median()
    print(f"half-width of the 90 per cent interval, median over those areas: {hw:.0f} per cent (wide: {hw2:.0f} per cent)")
    print("imputed:", (out.imputed_from_fsa != "").sum())
    print("OK demand_model")


if __name__ == "__main__":
    main()
