"""Social-media versions of the two corridor maps (owner's request, Nov 12, 2026): landscape, larger type, short titles,
the Loyola / Notre-Dame-de-Grâce district line, a one-line source and the « preliminary, not peer reviewed » mention.
Same tables and same conventions as corridor-parking-map and status-map (the full versions keep the per-area table and
the notes): automobiles MODELLED (SAAQ 2024 below the FSA), curb MEASURED (legal stretches, 10 m short of each
intersection), private places on Terrebonne counted lot by lot from street level; status = modelled automobiles as a
share of places (green < 80 %, yellow 80-100 %, red > 100 %), which compares cars with capacity, not occupancy.
Run:  ~/.venvs/omd/bin/python derived/figures/social-maps/social_maps.py"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from shapely.affinity import rotate
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
import offstreet_strips as S  # noqa: E402
from corridor_lib import CRS, DISTRICTS, GARAGES, LANE, ROOT, TABLES  # noqa: E402

VIOLET = "#6250d6"
T = {"en": dict(
        t1="The Terrebonne corridor: registered cars, curb and private parking",
        s1="Areas shaded by registered automobiles (modelled from SAAQ data, 2024). Orange: legal curb, 10 m short of intersections. Green: private places on rue de Terrebonne, checked lot by lot.",
        t2="Registered cars as a share of parking places, area by area",
        s2="Green: under 80 %. Yellow: 80 to 100 %. Red: over 100 %. A share compares registered cars with places: a stand-in for overnight demand, not a count of parked cars.",
        a="A. Curb and private places", b="B. Curb alone (every registered car kept on the street)",
        cb="modelled automobiles per area", curb="legal curb", p1="1 private place", p2="2", p3="3 or more", ug="underground garage (not counted)",
        conv="parking converted, none left", none="no private place", lane="the lane", hatch="A, hatched: mostly large buildings, whose garages are not counted",
        dist="{d}: {a} % with private places, {b} % curb alone", loy="Loyola district", ndg="NDG district",
        src="Sources: SAAQ vehicle files (access request 03.06.34729); Statistics Canada, 2021 Census; City of Montréal open data (géobase, parking signs, roll, districts). "
            "Preliminary results, not peer reviewed. Method and data: github.com/OpenMobilityData/Terrebonne-open-sources"),
     "fr": dict(
        t1="Le corridor de Terrebonne : voitures immatriculées, bordure et stationnement privé",
        s1="Aires colorées selon les automobiles immatriculées (modélisées d’après les données de la SAAQ, 2024). Orange : bordure légale, à 10 m des intersections. Vert : places privées rue de Terrebonne, vérifiées lot par lot.",
        t2="Voitures immatriculées en part des places de stationnement, aire par aire",
        s2="Vert : moins de 80 %. Jaune : 80 à 100 %. Rouge : plus de 100 %. Une part compare des voitures immatriculées à des places : un indicateur de la demande de nuit, pas un dénombrement de voitures garées.",
        a="A. Bordure et places privées", b="B. Bordure seulement (chaque voiture immatriculée gardée dans la rue)",
        cb="automobiles modélisées par aire", curb="bordure légale", p1="1 place privée", p2="2", p3="3 ou plus", ug="garage souterrain (non compté)",
        conv="stationnement converti, aucune place", none="aucune place privée", lane="la piste", hatch="A, hachuré : surtout de grands immeubles, dont les garages ne sont pas comptés",
        dist="{d} : {a} % avec les places privées, {b} % bordure seulement", loy="District de Loyola", ndg="District de NDG",
        src="Sources : fichiers de véhicules de la SAAQ (demande 03.06.34729) ; Statistique Canada, Recensement de 2021 ; données ouvertes de la Ville de Montréal (géobase, panneaux, rôle, districts). "
            "Résultats préliminaires, non révisés par les pairs. Méthode et données : github.com/OpenMobilityData/Terrebonne-open-sources"),
     }


def state(r):
    return (F.GOOD, "#ffffff") if r < 0.8 else (F.WARNING, "#0b0b0b") if r <= 1.0 else (F.CRITICAL, "#ffffff")


def main():
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    m = pd.read_csv(TABLES / "offstreet_measured_by_da.csv", dtype={"dauid": str}).sort_values(["west_to_east", "frontage"]).reset_index(drop=True)
    m["no"] = np.arange(1, len(m) + 1); curb = m.legal_m / 5.5
    m["r_with"] = m.automobiles_modelled / (curb + m.private_independent); m["r_curb"] = m.automobiles_modelled / curb
    m["large_share"] = (m.dwellings_in_large_buildings / m.households).clip(upper=1)
    cor = g[g.set == "corridor"][["dauid", "geometry"]].merge(m, on="dauid"); assert len(cor) == 22
    # districts: each area by its largest overlap; the shared boundary as a line
    dist = gpd.read_file(DISTRICTS).to_crs(CRS)[["NOM_DISTRICT", "geometry"]]
    ov = gpd.overlay(cor[["dauid", "geometry"]], dist, how="intersection"); ov["a"] = ov.area
    cor["district"] = cor.dauid.map(ov.sort_values("a", ascending=False).drop_duplicates("dauid").set_index("dauid").NOM_DISTRICT)
    loy, ndg = (dist[dist.NOM_DISTRICT == n].geometry.union_all() for n in ("Loyola", "Notre-Dame-de-Grâce"))
    line = loy.boundary.intersection(ndg.boundary).intersection(cor.geometry.union_all().buffer(30))
    tot = {}
    for d_, x in cor.groupby("district"):
        c_ = (x.legal_m / 5.5).sum(); tot[d_] = (round(100 * x.automobiles_modelled.sum() / (c_ + x.private_independent.sum())), round(100 * x.automobiles_modelled.sum() / c_))
    f = gpd.read_file(TABLES / "curb_stretches.geojson").to_crs(CRS); f = f[f.dauid.isin(cor.dauid)].copy()
    f["geometry"] = [l.offset_curve(7 if s_ == "L" else -7) for l, s_ in zip(f.geometry, f.side)]; f = f[~f.geometry.is_empty]
    lane = gpd.read_file(LANE).to_crs(CRS)
    b, alll, gb = S.frame()
    lots = pd.read_csv(GARAGES / "street_check" / "lots.csv", dtype={"key": str})
    lots["pt"] = [b.loc[k].geometry.representative_point() for k in lots.key]
    num = pd.to_numeric(lots.places_independent, errors="coerce").fillna(0); large = lots.large.astype(str) == "True"
    cats = {"p1": (lots.access == "yes") & ~large & (num == 1), "p2": (lots.access == "yes") & ~large & (num == 2), "p3": (lots.access == "yes") & ~large & (num >= 3),
            "ug": large & (lots.kind == "parking lot"), "conv": (lots.access == "no") & (lots.converted == "yes, none left"), "none": (lots.access == "no") & (lots.converted != "yes, none left")}
    # turn so that the lane runs west to east
    U = lane.geometry.union_all(); L = linemerge(U) if U.geom_type == "MultiLineString" else U
    a_, z_ = np.array(L.coords[0]), np.array(L.coords[-1])
    if a_[0] > z_[0]:
        a_, z_ = z_, a_
    ANG = np.degrees(np.arctan2(z_[1] - a_[1], z_[0] - a_[0])); ORG = tuple(((a_ + z_) / 2).tolist())
    turn = lambda x: rotate(x, -ANG, origin=ORG)
    cor["geometry"] = cor.geometry.map(turn); f["geometry"] = f.geometry.map(turn); lane["geometry"] = lane.geometry.map(turn); lots["pt"] = lots.pt.map(turn)
    line = turn(line); nx, ny = np.sin(np.radians(ANG)), np.cos(np.radians(ANG))
    norm = matplotlib.colors.Normalize(vmin=0, vmax=float(cor.automobiles_modelled.max()))
    style = {"p1": dict(marker="o", s=26, c=F.AQUA), "p2": dict(marker="o", s=60, c=F.AQUA), "p3": dict(marker="o", s=105, c=F.AQUA), "ug": dict(marker="s", s=70, c=F.AQUA),
             "conv": dict(marker="o", s=48, facecolors="none", edgecolors=VIOLET, linewidths=2.0), "none": dict(marker="o", s=24, facecolors=F.SURFACE, edgecolors=F.INK, linewidths=0.9)}

    def furniture(ax, lang, t):
        if not line.is_empty:
            gpd.GeoSeries([line]).plot(ax=ax, color=F.INK, linewidth=2.2, linestyle=(0, (6, 3)), zorder=7)
            cx = np.array(line.centroid.coords[0]); top = ax.get_ylim()[1]
            ax.text(cx[0] - 25, top, t["loy"], ha="right", va="top", fontsize=11, fontweight="bold", color=F.INK, zorder=8)
            ax.text(cx[0] + 25, top, t["ndg"], ha="left", va="top", fontsize=11, fontweight="bold", color=F.INK, zorder=8)
        x0_, x1_ = ax.get_xlim(); y0_, y1_ = ax.get_ylim(); ln = 0.08 * (y1_ - y0_); bx, by = x1_ - 0.03 * (x1_ - x0_), y0_ + 0.2 * (y1_ - y0_)
        ax.annotate("", xy=(bx + ln * nx, by + ln * ny), xytext=(bx, by), arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.7", color=F.INK, lw=1.8))
        ax.text(bx + 1.4 * ln * nx, by + 1.4 * ln * ny, "N", ha="center", va="center", fontsize=12, fontweight="bold", color=F.INK)

    def head(fig, title, sub, src):
        fig.text(0.015, 0.975, title, fontsize=17, fontweight="bold", va="top", color=F.INK)
        fig.text(0.015, 0.925, sub, fontsize=10.5, va="top", color=F.MUTED, wrap=True)
        fig.text(0.015, 0.015, src, fontsize=8.2, va="bottom", color=F.MUTED, wrap=True)

    for lang, t in T.items():
        # 1. everything on one map
        fig = plt.figure(figsize=(12, 6.6))
        ax = fig.add_axes([0.01, 0.2, 0.98, 0.68])
        cor.plot(ax=ax, column="automobiles_modelled", cmap=F.SEQ, norm=norm, edgecolor=F.SURFACE, linewidth=1.4)
        f[f.state == "legal"].plot(ax=ax, color=F.ORANGE, linewidth=1.4)
        f[f.state == "half"].plot(ax=ax, color=F.ORANGE, linewidth=0.9, linestyle=(0, (2, 1.5)))
        lane.plot(ax=ax, color=F.INK, linewidth=0.9, linestyle=(0, (3, 2)))
        for k, sel in cats.items():
            pts = lots[sel].pt
            if len(pts):
                kw = dict(style[k]); kw.setdefault("edgecolors", F.SURFACE); kw.setdefault("linewidths", 0.6)
                ax.scatter([p.x for p in pts], [p.y for p in pts], zorder=5, **kw)
        ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view(); furniture(ax, lang, t)
        H = [Line2D([], [], color=F.ORANGE, lw=2.2, label=t["curb"])]
        for k in ("p1", "p2", "p3", "ug", "conv", "none"):
            st = style[k]; fc = st.get("c", st.get("facecolors"))
            H.append(Line2D([], [], ls="", marker=st["marker"], markersize=np.sqrt(st["s"]), markerfacecolor=fc if fc != "none" else "none",
                            markeredgecolor=st.get("edgecolors", F.SURFACE), label=t[k]))
        fig.legend(handles=H, loc="lower left", bbox_to_anchor=(0.012, 0.075), ncol=4, fontsize=9.5, frameon=False, columnspacing=1.6)
        cax = fig.add_axes([0.72, 0.125, 0.25, 0.02])
        cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=F.SEQ), cax=cax, orientation="horizontal")
        cbar.outline.set_visible(False); cbar.ax.tick_params(labelsize=9); cbar.set_label(t["cb"], fontsize=9.5, color=F.MUTED)
        head(fig, t["t1"], t["s1"], t["src"])
        fig.savefig(HERE / f"corridor_parking_social_{lang}.png", dpi=200); plt.close(fig)
        # 2. the status colours
        fig = plt.figure(figsize=(12, 9.6))
        for col, ttl, box, dk in (("r_with", t["a"], [0.01, 0.55, 0.98, 0.31], 0), ("r_curb", t["b"], [0.01, 0.18, 0.98, 0.31], 1)):
            ax = fig.add_axes(box)
            cor.plot(ax=ax, color=[state(r)[0] for r in cor[col]], edgecolor=F.SURFACE, linewidth=1.6)
            if col == "r_with":
                cor[cor.large_share > 0.5].plot(ax=ax, facecolor="none", edgecolor=F.SURFACE, hatch="///", linewidth=0)
            lane.plot(ax=ax, color=F.INK, linewidth=0.9, linestyle=(0, (3, 2)))
            for r in cor.itertuples():
                p = r.geometry.representative_point(); fc, ink = state(getattr(r, col)); v = 100 * getattr(r, col)
                lab = (f"{v:.1f} %" if abs(v - 100) < 0.5 or abs(v - 80) < 0.5 else f"{v:.0f} %")
                ax.text(p.x, p.y, lab if lang == "en" else lab.replace(".", ","), fontsize=9, ha="center", va="center", color=ink, fontweight="bold", zorder=6,
                        bbox=dict(boxstyle="round,pad=0.22", fc=fc, ec="none"))
            ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view(); furniture(ax, lang, t)
            ax.set_title(ttl, loc="left", fontsize=12, color=F.INK, pad=16)
        fig.text(0.015, 0.125, "   ·   ".join(t["dist"].format(d=t["loy"] if d_ == "Loyola" else t["ndg"], a=tot[d_][0], b=tot[d_][1]) for d_ in ("Loyola", "Notre-Dame-de-Grâce")),
                 fontsize=11.5, fontweight="bold", va="center", color=F.INK)
        for k, (c, lab) in enumerate(((F.GOOD, "< 80 %"), (F.WARNING, "80–100 %"), (F.CRITICAL, "> 100 %"))):
            fig.patches.append(Rectangle((0.015 + 0.09 * k, 0.083), 0.014, 0.014, transform=fig.transFigure, fc=c, ec="none"))
            fig.text(0.033 + 0.09 * k, 0.09, lab, fontsize=10, color=F.INK, va="center")
        fig.patches.append(Rectangle((0.30, 0.083), 0.024, 0.016, transform=fig.transFigure, fc=F.GREY, ec=F.SURFACE, hatch="///", lw=0))
        fig.text(0.33, 0.09, t["hatch"], fontsize=10, color=F.INK, va="center")
        head(fig, t["t2"], t["s2"], t["src"])
        fig.savefig(HERE / f"status_social_{lang}.png", dpi=200); plt.close(fig)
    json.dump({"by_district_pct_with_private_and_curb_only": tot}, open(HERE / "district_shares.json", "w"), indent=1, ensure_ascii=False)
    print("district shares:", tot)
    print("OK social_maps")


if __name__ == "__main__":
    main()
