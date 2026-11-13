"""ILLUSTRATION of how a snow-loading operation moves through the corridor, night by night (owner's request, Nov 12, 2026,
for a social-media post with captions). Only the ORDER of the streets is invented; it is labelled as such on the image.

Real (City of Montréal, snow-removal transactions, CC BY 4.0): the operation of January 17-22, 2026, its truckloads per
night in each sector (CDN-301, CDN-111, CDN-112), and each sector's outline for 2025-26.
Assumed (the note's central case, section 4.7): each side of each block face is under a ban one night per operation, and a
night's share of the sector's curb under a ban equals its share of the operation's truckloads.
Invented for the picture: WHICH stretches are cleared each night. Here a sweep from west to east through each sector, the
second side of each street about one night behind the first. The City does not publish which streets are cleared on which
night (Info-Neige / Planif-Neige is a live service, no history).
Run:  ~/.venvs/omd/bin/python derived/figures/snow-loading-illustration/snow_loading_illustration.py"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex
from matplotlib.lines import Line2D
from shapely.affinity import rotate
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CRS, LANE, REPO, TABLES, TP  # noqa: E402

DAYS = pd.date_range("2026-01-17", "2026-01-22")
SEASON = "2025-2026"
LOADING = REPO.parent / "Terrebonne-access-requests" / "2026-300" / "derived" / "loading_daily.csv"
SECT = TP / "montreal-opendata" / "secteurs-deneigement" / f"secteurs_deneigement_saison_{SEASON}.geojson"
CMAP = plt.get_cmap("YlGnBu")
COL = [to_hex(CMAP(v)) for v in np.linspace(0.32, 0.97, len(DAYS))]
MON = {"en": ["Jan."], "fr": ["janv."]}
T = {"en": dict(
        title="How a snow-loading operation moves through the corridor: an illustration",
        sub="Each coloured line is a side of a street with legal parking, coloured by the night its parking is banned for loading. The City does not publish which streets are cleared\n"
            "on which night, so the ORDER shown here is invented. What is real: how much was loaded each night of the operation of January 17–22, 2026 (bars, below).",
        badge="ILLUSTRATION – not the City's schedule", night="night {i}", lane="the lane (rue de Terrebonne)", sector="snow-removal sector boundary", sec="sector {s}: its own operation, the same nights",
        bars="Share of the corridor's curb under a ban, each night (from the City's truckload counts, Jan. 17–22, 2026): real",
        foot="Assumed, as in the note's central case: each side of a street is banned one night per operation; a night's share of the curb follows its share of the truckloads. "
             "Illustrated: a sweep west to east, the second side of each street a night behind the first.\nSources: City of Montréal, snow-removal transactions and sectors, géobase, parking signs (CC BY 4.0). "
             "Preliminary results, not peer reviewed. github.com/OpenMobilityData/Terrebonne-open-sources"),
     "fr": dict(
        title="Comment une opération de chargement de la neige traverse le corridor : une illustration",
        sub="Chaque trait coloré est un côté de rue où le stationnement est permis, coloré selon la nuit où il y est interdit pour le chargement. La Ville ne publie pas quelles rues sont\n"
            "déneigées quelle nuit : l’ORDRE montré ici est inventé. Ce qui est réel : la quantité chargée chaque nuit de l’opération du 17 au 22 janvier 2026 (barres, en bas).",
        badge="ILLUSTRATION – pas l’horaire de la Ville", night="nuit {i}", lane="la piste (rue de Terrebonne)", sector="limite de secteur de déneigement", sec="secteur {s} : sa propre opération, les mêmes nuits",
        bars="Part de la bordure du corridor interdite, chaque nuit (d’après les chargements de la Ville, 17–22 janv. 2026) : réel",
        foot="Hypothèses, comme le cas central de la note : chaque côté de rue est interdit une nuit par opération ; la part de la bordure d’une nuit suit sa part des chargements. "
             "Illustré : un balayage d’ouest en est, le second côté de chaque rue une nuit après le premier.\nSources : Ville de Montréal, transactions et secteurs de déneigement, géobase, panneaux de stationnement (CC BY 4.0). "
             "Résultats préliminaires, non révisés par des pairs. github.com/OpenMobilityData/Terrebonne-open-sources")}


def main():
    da = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS); da = da[da.set == "corridor"]
    cs = gpd.read_file(TABLES / "curb_stretches.geojson").to_crs(CRS)
    cs = cs[cs.dauid.isin(da.dauid) & cs.state.isin(["legal", "half"])].copy()
    cs["w"] = np.where(cs.state == "half", 0.5, 1.0) * cs.length_m
    cs = cs[(cs.w > 0) & ~cs.geometry.is_empty].reset_index(drop=True)
    sec = gpd.read_file(SECT).to_crs(CRS); sec = sec[sec.ArrondissementCode == "CDN"].dissolve("NomSecteur").reset_index()
    j = gpd.sjoin(cs.assign(geometry=cs.geometry.interpolate(0.5, normalized=True)), sec[["NomSecteur", "geometry"]], predicate="within", how="left")
    cs["sector"] = j.groupby(level=0).NomSecteur.first()
    cs["sector"] = cs.sector.fillna(gpd.sjoin_nearest(cs[cs.sector.isna()], sec[["NomSecteur", "geometry"]]).groupby(level=0).NomSecteur.first())

    ld = pd.read_csv(LOADING, parse_dates=["day"])
    ld = ld[(ld.ArrondissementCode == "CDN") & ld.day.isin(DAYS)].groupby(["NomSecteur", "day"]).loads.sum().unstack(fill_value=0).reindex(columns=DAYS, fill_value=0)

    # orientation: the lane horizontal, west on the left (as in the other maps)
    lane = gpd.read_file(LANE).to_crs(CRS)
    U = lane.geometry.union_all(); L = linemerge(U) if U.geom_type == "MultiLineString" else U
    a_, z_ = np.array(L.coords[0]), np.array(L.coords[-1])
    if a_[0] > z_[0]:
        a_, z_ = z_, a_
    ANG = np.degrees(np.arctan2(z_[1] - a_[1], z_[0] - a_[0])); ORG = tuple(((a_ + z_) / 2).tolist())
    rot = lambda g: g.map(lambda x: rotate(x, -ANG, origin=ORG))
    cs["geometry"] = rot(cs.geometry); da["geometry"] = rot(da.geometry); lane["geometry"] = rot(lane.geometry); sec["geometry"] = rot(sec.geometry)
    cs["x"] = cs.geometry.interpolate(0.5, normalized=True).x

    # nights: a sweep west to east in each sector; the second side (R) about one night behind; each night's length = its truckload share
    cs["night"] = -1
    for s, g in cs.groupby("sector"):
        share = ld.loc[s].values / ld.loc[s].values.sum() if s in ld.index and ld.loc[s].sum() else None
        if share is None:
            continue
        n = int((share > 0).sum()); span = g.x.max() - g.x.min()
        key = g.x + np.where(g.side == "R", span / max(n, 1), 0.0)
        order = key.sort_values().index
        cum = cs.loc[order, "w"].cumsum() / cs.loc[order, "w"].sum()
        cs.loc[order, "night"] = np.searchsorted(np.cumsum(share), cum.values - 1e-9)
    assert (cs.night >= 0).all()
    tot = cs.w.sum()
    by_night = cs.groupby("night").w.sum().reindex(range(len(DAYS)), fill_value=0) / tot
    print("share of the corridor's curb by night:", by_night.round(3).tolist(), "sectors:", cs.groupby("sector").w.sum().round().to_dict())

    cs["geometry"] = [l.offset_curve(7 if s_ == "L" else -7) for l, s_ in zip(cs.geometry, cs.side)]
    cs = cs[~cs.geometry.is_empty]
    bounds = da.geometry.union_all().buffer(40)
    edge = sec.boundary.intersection(bounds)
    for lang, t in T.items():
        fig = plt.figure(figsize=(16, 9))
        ax = fig.add_axes([0.005, 0.33, 0.99, 0.52])
        da.plot(ax=ax, facecolor="#f4f5f2", edgecolor=F.SURFACE, linewidth=1.2)
        edge.plot(ax=ax, color=F.MUTED, linewidth=1.0, linestyle=(0, (1, 2)))
        for i in range(len(DAYS)):
            cs[cs.night == i].plot(ax=ax, color=COL[i], linewidth=2.6, capstyle="round")
        lane.plot(ax=ax, color=F.INK, linewidth=1.0, linestyle=(0, (3, 2)))
        ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view()
        y_top = cs.geometry.bounds.maxy.max()
        for sname, g in cs.groupby("sector"):
            if g.w.sum() < 2000:
                continue
            ax.text(g.x.median(), y_top + 55, t["sec"].format(s=sname), ha="center", va="bottom", fontsize=11, color=F.MUTED, fontweight="bold")
        ax.text(0.0, 1.0, t["badge"], transform=ax.transAxes, ha="left", va="top", fontsize=13, fontweight="bold", color=F.INK,
                bbox=dict(boxstyle="round,pad=0.45", fc="#fff3c4", ec=F.INK, lw=1.2), zorder=10)
        # bars: the real part, each night's share of the corridor's curb
        bx = fig.add_axes([0.03, 0.105, 0.55, 0.15])
        x = np.arange(len(DAYS))
        bx.bar(x, 100 * by_night.values, color=COL, width=0.66, edgecolor="none")
        for xi, v in zip(x, by_night.values):
            bx.text(xi, 100 * v + 0.8, f"{100 * v:.0f} %", ha="center", va="bottom", fontsize=11, color=F.INK)
        bx.set_xticks(x); bx.set_xticklabels([t["night"].format(i=i + 1, d=d.day) for i, d in enumerate(DAYS)], fontsize=10.5)
        bx.set_ylim(0, 100 * by_night.max() * 1.3); bx.set_yticks([]); bx.grid(False)
        for s_ in ("left",):
            bx.spines[s_].set_visible(False)
        bx.set_title(t["bars"], loc="left", fontsize=10.5, color=F.INK, pad=6)
        h = [Line2D([], [], color=F.INK, lw=1, ls=(0, (3, 2))), Line2D([], [], color=F.MUTED, lw=1, ls=(0, (1, 2)))]
        fig.legend(h, [t["lane"], t["sector"]], loc="lower left", bbox_to_anchor=(0.64, 0.17), ncol=1, fontsize=10, frameon=False)
        fig.text(0.012, 0.975, t["title"], fontsize=17, fontweight="bold", va="top", color=F.INK)
        fig.text(0.012, 0.925, t["sub"], fontsize=11, color=F.MUTED, va="top", linespacing=1.3)
        fig.text(0.012, 0.012, t["foot"], fontsize=8.3, color=F.MUTED, va="bottom", linespacing=1.35)
        for ext in ("png", "svg"):
            fig.savefig(HERE / f"snow_loading_illustration_{lang}.{ext}", dpi=200)
        plt.close(fig)
    print("OK snow_loading_illustration")


if __name__ == "__main__":
    main()
