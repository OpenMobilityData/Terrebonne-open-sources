"""One map of the corridor's parking, every source together (owner's request, Nov 12, 2026):
- fill: the dissemination areas fronting the lane, shaded by their MODELLED automobiles (SAAQ file of December 31,
  2024, type inferred, modelled below the FSA; demand_model.py);
- lines: the legal curb by block face, MEASURED from the City's sign inventory (curb_supply.py; an upper bound);
- markers: on rue de Terrebonne, every lot judged from street level by the owner on November 12, 2026, sized by
  its independent private places as counted (1954-underwriters-plans-terrebonne-garages/derived/street_check/);
- table: per area, modelled automobiles (90 % interval), curb places at 5.5 m, and the private places of its small
  buildings estimated from the reading of every lot calibrated on the owner's random sample (offstreet.py; 90 %).
Elsewhere than Terrebonne no private place is drawn lot by lot: per lot those are readings from above, which the
owner's check showed to miss driveways; only the calibrated total per area is used. No ratio of automobiles to places
is shown: capacity is not use.
Run:  ~/.venvs/omd/bin/python derived/figures/corridor-parking-map/corridor_parking_map.py"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from shapely.affinity import rotate
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
import offstreet_strips as S  # noqa: E402
from corridor_lib import CRS, GARAGES, LANE, TABLES  # noqa: E402

VIOLET = "#6250d6"
PLACE = 5.5
T = {"en": dict(
        title="Parking in the Terrebonne corridor: modelled automobiles, measured curb, measured private places",
        sub="Fill: automobiles registered to each area's households, MODELLED from the SAAQ file of 2024. Orange: legal curb by block face (measured, upper bound).\n"
            "Green on rue de Terrebonne: each lot's private places, counted from street level on Nov. 12, 2026. Table: the same three, and private places, per area.",
        cb="modelled automobiles per area (2024)",
        curb="legal curb, 10 m short of each intersection", curb_half="signs disagree (counted for half)", curb_no="parking forbidden at all times",
        p1="1 private place", p2="2 private places", p3="3 or more private places", conv="parking converted, no place left", none="no private place", ug="underground garage (places not counted)",
        ct="could not be told", lane="the lane (rue de Terrebonne)",
        th=["area", "automobiles\n(modelled, 90 %)", "curb places\n(5.5 m)", "private places\n(small buildings, 90 %)"], tot="corridor",
        note="Curb: géobase faces less 10 m at each end and stretches forbidden at all times; driveways, hydrants, bus stops, hourly and permit rules not deducted. Private places: cars that can leave\n"
             "without another being moved; garage interiors and the {g} larger buildings' garages not counted; off Terrebonne, the reading of every lot calibrated on {k} lots checked from the street.\n"
             "Places are capacity, not use: the table does not measure how full the street is."),
     "fr": dict(
        title="Le stationnement dans le corridor de Terrebonne : automobiles modélisées, bordure et places privées mesurées",
        sub="Fond : automobiles immatriculées aux ménages de chaque aire, MODÉLISÉES d’après le fichier SAAQ de 2024. Orange : bordure légale par côté d’îlot (mesurée, borne supérieure).\n"
            "Vert, rue de Terrebonne : places privées de chaque lot, comptées à hauteur de rue le 12 nov. 2026. Tableau : les trois, et les places privées, par aire.",
        cb="automobiles modélisées par aire (2024)",
        curb="bordure légale, à 10 m de chaque intersection", curb_half="panneaux contradictoires (comptés pour moitié)", curb_no="stationnement interdit en tout temps",
        p1="1 place privée", p2="2 places privées", p3="3 places privées ou plus", conv="stationnement converti, aucune place restante", none="aucune place privée", ug="garage souterrain (places non comptées)",
        ct="indéterminé", lane="la piste (rue de Terrebonne)",
        th=["aire", "automobiles\n(modélisées, 90 %)", "places en bordure\n(5,5 m)", "places privées\n(petits immeubles, 90 %)"], tot="corridor",
        note="Bordure : côtés de la géobase moins 10 m à chaque extrémité et les tronçons interdits en tout temps ; entrées, bornes d’incendie, arrêts d’autobus, règles horaires et vignettes non déduits.\n"
             "Places privées : voitures qui peuvent partir sans en déplacer une autre ; intérieurs de garage et garages des {g} grands immeubles non comptés ; hors Terrebonne, la lecture de chaque lot\n"
             "calibrée sur {k} lots vérifiés à hauteur de rue. Une place est une capacité, pas un usage : le tableau ne mesure pas le taux d’occupation de la rue."),
     }


def main():
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    m = pd.read_csv(TABLES / "offstreet_measured_by_da.csv", dtype={"dauid": str})
    m = m.sort_values(["west_to_east", "frontage"]).reset_index(drop=True); m["no"] = np.arange(1, len(m) + 1)
    cor = g[g.set == "corridor"][["dauid", "geometry"]].merge(m, on="dauid")
    assert len(cor) == len(m) == 22
    # the curb as measured: each block face less 10 m at each end, split where the signs change (curb_supply.py)
    f = gpd.read_file(TABLES / "curb_stretches.geojson").to_crs(CRS)
    f = f[f.dauid.isin(cor.dauid)].copy()
    f["geometry"] = [l.offset_curve(7 if s == "L" else -7) for l, s in zip(f.geometry, f.side)]
    f = f[~f.geometry.is_empty]
    lane = gpd.read_file(LANE).to_crs(CRS)
    # the street check: one point per lot, at the lot's representative point
    b, alll, gb = S.frame()
    lots = pd.read_csv(GARAGES / "street_check" / "lots.csv", dtype={"key": str})
    lots["pt"] = [b.loc[k].geometry.representative_point() for k in lots.key]
    num = pd.to_numeric(lots.places_independent, errors="coerce").fillna(0)
    large = lots.large.astype(str) == "True"
    cats = {"p1": (lots.access == "yes") & ~large & (num == 1), "p2": (lots.access == "yes") & ~large & (num == 2),
            "p3": (lots.access == "yes") & ~large & (num >= 3), "ug": large & (lots.kind == "parking lot"),
            "conv": (lots.access == "no") & (lots.converted == "yes, none left"),
            "none": (lots.access == "no") & (lots.converted != "yes, none left"), "ct": ~lots.access.isin(["yes", "no"])}
    left = len(lots) - sum(int(v.sum()) for v in cats.values())
    assert left >= 0
    O = __import__("json").load(open(HERE.parents[1] / "offstreet.json"))
    oc, ok = O["corridor"], O["check"]
    N = F.numbers()["sets"]["corridor"]
    norm = matplotlib.colors.Normalize(vmin=0, vmax=float(cor.automobiles_modelled.max()))
    # turn the map so that the lane runs left to right, west at left (north side of Terrebonne above)
    L = linemerge(lane.geometry.union_all()) if lane.geometry.union_all().geom_type == "MultiLineString" else lane.geometry.union_all()
    a_, z_ = np.array(L.coords[0]), np.array(L.coords[-1])
    if a_[0] > z_[0]:
        a_, z_ = z_, a_
    ANG = np.degrees(np.arctan2(z_[1] - a_[1], z_[0] - a_[0])); ORG = tuple(((a_ + z_) / 2).tolist())
    turn = lambda geom: rotate(geom, -ANG, origin=ORG)
    cor["geometry"] = cor.geometry.map(turn); f["geometry"] = f.geometry.map(turn); lane["geometry"] = lane.geometry.map(turn)
    lots["pt"] = lots.pt.map(turn)
    style = {"p1": dict(marker="o", s=22, c=F.AQUA), "p2": dict(marker="o", s=52, c=F.AQUA), "p3": dict(marker="o", s=92, c=F.AQUA),
             "ug": dict(marker="s", s=60, c=F.AQUA), "conv": dict(marker="o", s=40, facecolors="none", edgecolors=VIOLET, linewidths=1.8),
             "none": dict(marker="o", s=20, facecolors=F.SURFACE, edgecolors=F.INK, linewidths=0.8), "ct": dict(marker="x", s=20, c=F.INK, linewidths=0.9)}
    for lang, t in T.items():
        fig = plt.figure(figsize=(16, 11))
        ax = fig.add_axes([0.01, 0.44, 0.98, 0.43])
        cor.plot(ax=ax, column="automobiles_modelled", cmap=F.SEQ, norm=norm, edgecolor=F.SURFACE, linewidth=1.4)
        f[f.state == "legal"].plot(ax=ax, color=F.ORANGE, linewidth=1.4)
        f[f.state == "half"].plot(ax=ax, color=F.ORANGE, linewidth=0.9, linestyle=(0, (2, 1.5)))
        f[f.state == "banned"].plot(ax=ax, color=F.GREY, linewidth=0.9)
        lane.plot(ax=ax, color=F.INK, linewidth=0.9, linestyle=(0, (3, 2)))
        for k, sel in cats.items():
            pts = lots[sel].pt
            if len(pts):
                kw = dict(style[k]); kw.setdefault("edgecolors", F.SURFACE); kw.setdefault("linewidths", 0.6)
                ax.scatter([p.x for p in pts], [p.y for p in pts], zorder=5, **kw)
        for r in cor.itertuples():
            p = r.geometry.representative_point()
            ax.text(p.x, p.y, str(r.no), fontsize=8.5, ha="center", va="center", zorder=6, color=F.INK,
                    bbox=dict(boxstyle="round,pad=0.2", fc=F.SURFACE, ec=F.AXIS, lw=0.5))
        ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view()
        # north arrow: true north after the turn
        nx, ny = np.sin(np.radians(ANG)), np.cos(np.radians(ANG))
        x0_, x1_ = ax.get_xlim(); y0_, y1_ = ax.get_ylim(); ln = 0.06 * (y1_ - y0_)        # in map metres, so the angle is true
        bx, by = x1_ - 0.03 * (x1_ - x0_), y1_ - 0.30 * (y1_ - y0_)
        ax.annotate("", xy=(bx + ln * nx, by + ln * ny), xytext=(bx, by), arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.7", color=F.INK, lw=1.8))
        ax.text(bx + 1.35 * ln * nx, by + 1.35 * ln * ny, "N", ha="center", va="center", fontsize=11, fontweight="bold", color=F.INK)
        # legend, column by column: private places | curb and lane | other lots
        H = []
        for k in ("p1", "p2", "p3", "ug"):
            st = style[k]
            H.append(Line2D([], [], ls="", marker=st["marker"], markersize=np.sqrt(st["s"]), markerfacecolor=st["c"], markeredgecolor=F.SURFACE, label=t[k] + f" ({int(cats[k].sum())})"))
        H += [Line2D([], [], color=F.ORANGE, lw=2, label=t["curb"]), Line2D([], [], color=F.ORANGE, lw=1.2, ls=(0, (2, 1.5)), label=t["curb_half"]), Line2D([], [], color=F.GREY, lw=1.2, label=t["curb_no"]),
              Line2D([], [], color=F.INK, lw=1, ls=(0, (3, 2)), label=t["lane"])]
        for k in ("conv", "none", "ct"):
            st = style[k]; fc = st.get("c", st.get("facecolors"))
            H.append(Line2D([], [], ls="", marker=st["marker"], markersize=np.sqrt(st["s"]), markerfacecolor=fc if fc != "none" else "none",
                            markeredgecolor=st.get("edgecolors", F.INK) if k != "ct" else F.INK, color=F.INK, label=t[k] + f" ({int(cats[k].sum())})"))
        fig.legend(handles=H, loc="upper left", bbox_to_anchor=(0.01, 0.435), ncol=3, fontsize=8.5, frameon=False, columnspacing=2.5)
        cax = fig.add_axes([0.77, 0.405, 0.2, 0.012])
        cb = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=F.SEQ), cax=cax, orientation="horizontal")
        cb.outline.set_visible(False); cb.ax.tick_params(labelsize=8); cb.set_label(t["cb"], fontsize=8.5, color=F.MUTED)
        # table: areas 1-11 left, 12-22 and the corridor right
        xs, dy, y0 = (0.0, 0.045, 0.2, 0.3), 0.0172, 0.31
        rows = [[str(r.no), f"{F.num(r.automobiles_modelled, lang)}  ({F.num(r.low_90, lang)}–{F.num(r.high_90, lang)})",
                 F.num(r.curb_places, lang), f"{F.num(r.private_independent, lang)}  ({F.num(r.private_independent_low, lang)}–{F.num(r.private_independent_high, lang)})"]
                for r in m.itertuples()]
        tot = [t["tot"], f"{F.num(N['automobiles_modelled'], lang)}  ({F.num(N['low_90'], lang)}–{F.num(N['high_90'], lang)})",
               F.num(N["places_5.5m"], lang), f"{F.num(oc['private_independent'], lang)}  ({F.num(oc['private_independent_low'], lang)}–{F.num(oc['private_independent_high'], lang)})"]
        for x0, part in ((0.02, rows[:11]), (0.52, rows[11:])):
            for x, h in zip(xs, t["th"]):
                fig.text(x0 + x, y0, h, fontsize=8.2, color=F.MUTED, va="bottom", ha="left")
            for i, vals in enumerate(part):
                y = y0 - (i + 1) * dy
                if i % 2 == 0:
                    fig.patches.append(matplotlib.patches.Rectangle((x0 - 0.004, y - 0.004), 0.455, dy, transform=fig.transFigure, color="#f3f4f2", zorder=0))
                for x, v in zip(xs, vals):
                    fig.text(x0 + x, y, v, fontsize=8.2, va="bottom", ha="left")
        y = y0 - 12 * dy - 0.004
        fig.lines.append(Line2D([0.516, 0.971], [y + dy - 0.002] * 2, transform=fig.transFigure, color=F.AXIS, lw=0.8))
        for x, v in zip(xs, tot):
            fig.text(0.52 + x, y, v, fontsize=8.2, va="bottom", ha="left", fontweight="bold")
        note = t["note"].format(g=oc["large_buildings"], k=ok["small_judged"])
        F.finish(fig, HERE, "corridor_parking_map", lang, t["title"], t["sub"], note, top=0.99, bottom=0.01, left=0.0, right=1.0)
    print("lots by marker:", {k: int(v.sum()) for k, v in cats.items()}, "unclassified", left)
    print("OK corridor_parking_map")


if __name__ == "__main__":
    main()
