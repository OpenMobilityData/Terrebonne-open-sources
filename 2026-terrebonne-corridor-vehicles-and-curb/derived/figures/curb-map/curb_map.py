"""Map of the corridor's block faces: legal curb share of each face (measured from the sign inventory).
Run:  ~/.venvs/omd/bin/python derived/figures/curb-map/curb_map.py"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CRS, TABLES  # noqa: E402

T = {"en": dict(title="Legal curb by block face in the corridor, from the City's sign inventory",
                sub="Each side of each street segment, drawn offset from the centre line. Blue: curb where no sign forbids stopping or parking at all times;\n"
                    "orange: stretches where such signs apply. Each face stops 10 m short of each intersection, as measured. Rue de Terrebonne: one parking band, south side west of Cavendish, north side east of it.",
                a="legal curb", h="signs disagree (counted for half)", b="forbidden at all times",
                note="Corridor: {k} km of legal curb on {f} block faces ({p} % of the curb net of 10 m at each end is forbidden at all times). Upper bound: driveways,\nhydrants, bus stops, hourly and permit rules are not deducted."),
     "fr": dict(title="Bordure légale par côté d’îlot dans le corridor, d’après l’inventaire de signalisation de la Ville",
                sub="Chaque côté de chaque tronçon, décalé de l’axe. Bleu : bordure où aucun panneau n’interdit l’arrêt ou le stationnement en tout temps ;\n"
                    "orange : tronçons visés par ces panneaux. Chaque côté s’arrête à 10 m de chaque intersection, comme mesuré. Rue de Terrebonne : une bande de stationnement, côté sud à l’ouest de Cavendish, côté nord à l’est.",
                a="bordure légale", h="panneaux contradictoires (comptés pour moitié)", b="interdit en tout temps",
                note="Corridor : {k} km de bordure légale sur {f} côtés d’îlot ({p} % de la bordure, nette de 10 m à chaque extrémité, est interdite en tout temps). Borne supérieure :\nentrées charretières, bornes d’incendie, arrêts d’autobus, règles horaires et vignettes non déduits."),
     }


def main():
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    cor = g[g.set == "corridor"]
    faces = gpd.read_file(TABLES / "block_faces.geojson").to_crs(CRS); faces = faces[faces.dauid.isin(cor.dauid)]
    f = gpd.read_file(TABLES / "curb_stretches.geojson").to_crs(CRS)          # each face less 10 m at each end, split where the signs change
    f = f[f.dauid.isin(cor.dauid)].copy()
    f["geometry"] = [l.offset_curve(7 if s == "L" else -7) for l, s in zip(f.geometry, f.side)]
    f = f[~f.geometry.is_empty]
    N = F.numbers(); c = N["sets"]["corridor"]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 7.4))
        cor.plot(ax=ax, color="#f3f4f2", edgecolor=F.SURFACE, linewidth=1)
        f[f.state == "legal"].plot(ax=ax, color=F.BLUE, linewidth=1.5)
        f[f.state == "half"].plot(ax=ax, color=F.BLUE, linewidth=1.0, linestyle=(0, (2, 1.5)))
        f[f.state == "banned"].plot(ax=ax, color=F.ORANGE, linewidth=1.5)
        ax.set_axis_off(); ax.set_aspect("equal")
        h = [matplotlib.lines.Line2D([], [], color=F.BLUE, lw=2, label=t["a"]), matplotlib.lines.Line2D([], [], color=F.BLUE, lw=1.2, ls=(0, (2, 1.5)), label=t["h"]), matplotlib.lines.Line2D([], [], color=F.ORANGE, lw=2, label=t["b"])]
        ax.legend(handles=h, loc="lower right", fontsize=8.5)
        note = t["note"].format(k=F.num(c["legal_curb_km"], lang, 1), f=len(faces), p=F.num(100 * c["forbidden_at_all_times_km"] / (c["legal_curb_km"] + c["forbidden_at_all_times_km"]), lang, 0))
        F.finish(fig, HERE, "curb_map", lang, t["title"], t["sub"], note, top=0.86, bottom=0.12, left=0.01, right=0.99)
    print("OK curb_map")


if __name__ == "__main__":
    main()
