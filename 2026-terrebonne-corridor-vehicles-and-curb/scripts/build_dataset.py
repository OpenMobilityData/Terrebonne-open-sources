"""Stage 1: the census tables the demand model needs, by FSA and by dissemination area, and the share of each
dissemination area that lies in each FSA.

Inputs (outside the repository): Statistics Canada, 2021 Census profile by forward sortation area
(98-401-X2021013) and by dissemination area, Québec (98-401-X2021006), dissemination-area boundaries
(lda_000a21a_e); Service Objects postal-code points (March 2024, under licence, not redistributed);
the FSA vehicle counts of Quebec-vehicle-registrations (derived/tables/type_by_fsa.csv; type INFERRED for 2023-2024).

A dissemination area is shared among FSAs in proportion to the dwellings of the City's assessment roll
(« Unités d'évaluation foncière », CC BY 4.0) found in each FSA polygon (DMTI Spatial, CanMap Postal Code Suite
v2024.3, under licence, not redistributed); where the roll has no dwelling (Laval), in proportion to postal codes.

Outputs (derived/tables/): fsa_model_table.csv, da_census.csv, da_fsa_shares.csv, fsa_households_check.csv
Run:  ~/.venvs/omd/bin/python scripts/build_dataset.py
"""
import duckdb
import geopandas as gpd
import pandas as pd

from corridor_lib import CACHE, CHAR, CRS, DA_CSV, DA_SHP, FSA_CSV, FSA_SHP, PC_CSV, ROLL, SAAQ, TABLES, YEAR


def profile(csv, level, where, cache):
    cache = CACHE / cache
    if not cache.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        ids = ",".join(f"'{i}'" for i in CHAR)
        duckdb.connect().execute(f"""
            COPY (SELECT ALT_GEO_CODE AS geo, CAST(CHARACTERISTIC_ID AS INTEGER) AS id, TRY_CAST(C1_COUNT_TOTAL AS DOUBLE) AS v
                  FROM read_csv('{csv}', all_varchar=true, encoding='latin-1', header=true)
                  WHERE GEO_LEVEL = '{level}' AND {where} AND CHARACTERISTIC_ID IN ({ids}))
            TO '{cache}' (FORMAT parquet)""")
    d = pd.read_parquet(cache)
    return d.pivot(index="geo", columns="id", values="v").rename(columns=CHAR)[list(CHAR.values())]


def roll_points():
    """Units of the assessment roll with at least one dwelling, as points (cached outside the repository)."""
    cache = CACHE / "roll_dwelling_points.parquet"
    if not cache.exists():
        import pyogrio
        r = pyogrio.read_dataframe(ROLL, columns=["ID_UEV", "NOMBRE_LOGEMENT"])
        r = r[r.NOMBRE_LOGEMENT.fillna(0) > 0].to_crs(CRS)
        r["geometry"] = r.representative_point()
        r.to_parquet(cache)
    return gpd.read_parquet(cache)


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    fsa = profile(FSA_CSV, "Forward sortation area", "left(ALT_GEO_CODE, 1) = 'H'", "census_fsa_H.parquet")
    fsa.index.name = "fsa"
    t = pd.read_csv(SAAQ / "derived/tables/type_by_fsa.csv")
    for y in (2023, 2024):
        fsa[f"automobiles_{y}_inferred"] = t[(t.year == y) & (t.vtype == "AU")].groupby("fsa").n.sum().reindex(fsa.index).round(0)
    fsa.to_csv(TABLES / "fsa_model_table.csv")
    print(f"FSAs beginning with H in the census profile: {len(fsa)}; with vehicles in {YEAR}: {fsa[f'automobiles_{YEAR}_inferred'].notna().sum()}")

    # dissemination areas of the census divisions of Montréal (2466) and Laval (2465): the H postal district
    da = profile(DA_CSV, "Dissemination area", "left(ALT_GEO_CODE, 4) IN ('2466', '2465')", "census_da_2466_2465.parquet")
    da.index.name = "dauid"
    g = gpd.read_file(DA_SHP, columns=["DAUID"], where="DAUID LIKE '2466%' OR DAUID LIKE '2465%'").to_crs(CRS)
    # 1. by dwellings: each unit of the City's assessment roll with dwellings is a point, in one dissemination
    #    area and one FSA polygon; the share is the share of the area's dwellings
    r = roll_points()
    fp = gpd.read_file(FSA_SHP, columns=["FSA"]).to_crs(CRS)
    fp = fp[fp.FSA.str.startswith("H")].rename(columns={"FSA": "fsa"})
    r = gpd.sjoin(r, g, predicate="within", how="inner").drop(columns="index_right")
    r = gpd.sjoin(r, fp, predicate="within", how="inner")
    sh = r.groupby(["DAUID", "fsa"]).NOMBRE_LOGEMENT.sum().rename("weight").reset_index()
    sh["basis"] = "dwellings of the assessment roll"
    # 2. no roll dwelling inside (Laval; areas without housing): by postal codes of each FSA inside the area
    pc = pd.read_csv(PC_CSV, dtype=str, on_bad_lines="skip", encoding="latin-1")
    pc = pc[(pc.PROVINCE_ABBR == "QC") & pc.PostalCode.str.startswith("H")]
    pcg = gpd.GeoDataFrame({"fsa": pc.PostalCode.str[:3].values},
                           geometry=gpd.points_from_xy(pc.Longitude.astype(float), pc.Latitude.astype(float)), crs=4326).to_crs(CRS)
    hit = gpd.sjoin(pcg, g[~g.DAUID.isin(sh.DAUID)], predicate="within", how="inner")
    s2 = hit.groupby(["DAUID", "fsa"]).size().rename("weight").reset_index()
    s2["basis"] = "postal codes"
    sh = pd.concat([sh, s2], ignore_index=True)
    # 3. neither: the FSA of the nearest postal code
    rest = g[~g.DAUID.isin(sh.DAUID)].copy()
    rest["geometry"] = rest.representative_point()
    near = gpd.sjoin_nearest(rest, pcg, how="left").drop_duplicates("DAUID")[["DAUID", "fsa"]].assign(weight=1.0, basis="nearest postal code")
    sh = pd.concat([sh, near], ignore_index=True)
    sh["share"] = sh.weight / sh.groupby("DAUID").weight.transform("sum")
    sh = sh.rename(columns={"DAUID": "dauid"}).sort_values(["dauid", "fsa"])
    sh.round({"share": 4}).to_csv(TABLES / "da_fsa_shares.csv", index=False)
    da["area_km2"] = (g.set_index("DAUID").geometry.area / 1e6).reindex(da.index).round(4)
    da.to_csv(TABLES / "da_census.csv")
    nb = sh.drop_duplicates("dauid").basis.value_counts().to_dict()
    print(f"dissemination areas: {len(da)}; shared by: {nb}; in more than one FSA: {(sh.groupby('dauid').size() > 1).sum()}")
    m = da.join(sh.set_index("dauid"), how="inner")
    est = (m[["households", "population"]].multiply(m.share, axis=0)).groupby(m.fsa).sum()
    cmp = fsa[["households", "population"]].join(est.add_suffix("_from_da"))
    cmp["households_pct_difference"] = (100 * (cmp.households_from_da / cmp.households - 1)).round(2)
    cmp["population_pct_difference"] = (100 * (cmp.population_from_da / cmp.population - 1)).round(2)
    cmp.round(0).assign(households_pct_difference=cmp.households_pct_difference, population_pct_difference=cmp.population_pct_difference).to_csv(TABLES / "fsa_households_check.csv")
    big = cmp[(cmp.households >= 1000) & ~cmp.index.str.startswith("H7")]
    print("households rebuilt from dissemination areas against the official FSA profile, island FSAs of 1,000 households or more:",
          len(big), "| median abs difference %.2f %%, 90th percentile %.2f %%, largest %.2f %%" % (
              big.households_pct_difference.abs().median(), big.households_pct_difference.abs().quantile(0.9), big.households_pct_difference.abs().max()))
    print(cmp.loc[["H4A", "H4B"]].round(1).to_string())
    print("missing values in the dissemination areas, by column:\n", da.isna().sum()[lambda s: s > 0].to_string())
    print("OK build_dataset")


if __name__ == "__main__":
    main()
