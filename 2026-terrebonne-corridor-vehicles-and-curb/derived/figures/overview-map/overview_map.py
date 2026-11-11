"""Overview map: modelled automobiles and light trucks per household, by dissemination area, in the two FSAs of
the lane; the corridor areas outlined; the lane; the line between H4B and H4A at Royal.
Run:  ~/.venvs/omd/bin/python derived/figures/overview-map/overview_map.py"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CRS, LANE, TABLES  # noqa: E402

T = {"en": dict(title="Automobiles per household around the Terrebonne lane: a model below the FSA",
                sub="Automobiles and light trucks per household, 2024, by dissemination area. Registered totals are known for H4A and H4B only;\n"
                    "the split among areas is modelled from 2021 Census variables and scaled to each FSA's total.",
                cb="modelled automobiles per household", lane="protected lane (rue de Terrebonne)", cor="corridor: the 22 areas fronting the lane",
                note="{n} dissemination areas with a part in H4A or H4B. Registered (type inferred): H4A {a} per household, H4B {b}. Corridor, modelled: {c} ({lo}–{hi})."),
     "fr": dict(title="Automobiles par ménage autour de la piste Terrebonne : un modèle sous la RTA",
                sub="Automobiles et camions légers par ménage, 2024, par aire de diffusion. Les totaux immatriculés ne sont connus que pour H4A et H4B ;\n"
                    "la répartition entre les aires est modélisée à partir du Recensement de 2021 et ramenée au total de chaque RTA.",
                cb="automobiles modélisées par ménage", lane="piste protégée (rue de Terrebonne)", cor="corridor : les 22 aires riveraines de la piste",
                note="{n} aires de diffusion ayant une partie dans H4A ou H4B. Immatriculées (type inféré) : H4A {a} par ménage, H4B {b}. Corridor, modélisé : {c} ({lo}–{hi}).")}


def main():
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    faces = gpd.read_file(TABLES / "block_faces.geojson").to_crs(CRS).drop_duplicates("ID_TRC")
    lane = gpd.read_file(LANE).to_crs(CRS)
    N = F.numbers(); c = N["sets"]["corridor"]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 7.2))
        norm = matplotlib.colors.Normalize(0.4, 1.3)
        g.plot(ax=ax, column="per_household", cmap=F.SEQ, norm=norm, edgecolor=F.SURFACE, linewidth=0.8)
        faces.plot(ax=ax, color=F.SURFACE, linewidth=0.35, alpha=0.7)
        g[g.set == "corridor"].dissolve().boundary.plot(ax=ax, color=F.INK, linewidth=1.4)
        lane.plot(ax=ax, color=F.ORANGE, linewidth=2.6)
        for _, r in g[g.set == "corridor"].iterrows():
            p = r.geometry.representative_point()
            ax.text(p.x, p.y, F.num(r.per_household, lang, 2), ha="center", va="center", fontsize=6.5,
                    color=F.SURFACE if r.per_household > 0.85 else F.INK)
        ax.set_axis_off(); ax.set_aspect("equal")
        sm = matplotlib.cm.ScalarMappable(norm=norm, cmap=F.SEQ)
        cax = ax.inset_axes([0.0, 0.93, 0.3, 0.022])
        cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
        cax.set_title(t["cb"], fontsize=8.5, loc="left", color=F.MUTED); cb.outline.set_visible(False); cax.tick_params(labelsize=8)
        cax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: F.num(v, lang, 1)))
        h = [matplotlib.lines.Line2D([], [], color=F.ORANGE, lw=2.6, label=t["lane"]), matplotlib.lines.Line2D([], [], color=F.INK, lw=1.4, label=t["cor"])]
        ax.legend(handles=h, loc="lower right", fontsize=8.5)
        note = t["note"].format(n=N["da"]["n"], a=F.num(N["fsa"]["H4A"]["per_household"], lang, 2), b=F.num(N["fsa"]["H4B"]["per_household"], lang, 2),
                                c=F.num(c["per_household"], lang, 2), lo=F.num(c["per_household_low_90"], lang, 2), hi=F.num(c["per_household_high_90"], lang, 2))
        F.finish(fig, HERE, "overview_map", lang, t["title"], t["sub"], note, top=0.87, bottom=0.08, left=0.01, right=0.99)
    print("OK overview_map")


if __name__ == "__main__":
    main()
