"""Cross-check figure for social media and the deck (owner's request, Nov 12, 2026): one block of rue de Terrebonne,
Hingston to Hampton, on the 1954-55 Underwriters' plans (the « Autos Bast » basement garages drawn with the houses)
beside the Québec government's aerial image, with the same markers (the author's reading of the plans combined
with the street-level check of November 12, 2026). Built from the 1954 folder's one-block figure
(method_detail_hingston_hampton_<lang>.pdf, method_figures.py), its top (aerial) and bottom (plans) panels, rendered
at 300 dpi; the scans are BAnQ's (notice 0000174390), consulted there; this crop of one block is a frontage strip
(owner's ruling, Oct 25, 2026).
Run:  ~/.venvs/omd/bin/python derived/figures/social-maps/then_and_now.py"""
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CACHE, GARAGES  # noqa: E402

Image.MAX_IMAGE_PIXELS = None
T = {"en": dict(title="Garages built with the houses, and car access today: one block of Terrebonne, Hingston to Hampton",
                a="1954–55: the fire-insurance plan writes « Autos Bast » (basement garages) along the north side",
                b="On recent aerial imagery: the same houses, their aprons, cars in the driveways (markers: car access as checked from the street, Nov. 2026)",
                k1="garage as built, car access today", k2="garage as built, no parking today (converted)", k3="no garage as built, car access today",
                src="Underwriters' Survey Bureau, Insurance plan of the city of Montreal, vol. 7, sheets 787-5 and 787-7 (1954–55; BAnQ, notice 0000174390); "
                    "aerial imagery: Gouvernement du Québec (Imagerie_GQ). Markers: the author's reading of the plans and street-level check, Nov. 12, 2026. "
                    "A cross-check, not a primary source. Preliminary results, not peer reviewed."),
     "fr": dict(title="Garages construits avec les maisons, et accès automobile aujourd’hui : un îlot de Terrebonne, de Hingston à Hampton",
                a="1954–1955 : le plan d’assurance-incendie inscrit « Autos Bast » (garages au sous-sol) le long du côté nord",
                b="Sur l’imagerie aérienne récente : les mêmes maisons, leurs aires pavées, des voitures dans les entrées (repères : accès vérifié à hauteur de rue, nov. 2026)",
                k1="garage d’origine, accès automobile aujourd’hui", k2="garage d’origine, plus de stationnement (converti)", k3="sans garage d’origine, accès aujourd’hui",
                src="Underwriters' Survey Bureau, Insurance plan of the city of Montreal, vol. 7, feuillets 787-5 et 787-7 (1954–1955 ; BAnQ, notice 0000174390) ; "
                    "imagerie aérienne : Gouvernement du Québec (Imagerie_GQ). Repères : lecture des plans et vérification à hauteur de rue de l’auteur, 12 nov. 2026. "
                    "Une vérification croisée, pas une source principale. Résultats préliminaires, non révisés par les pairs."),
     }


def panels(lang):
    pdf = GARAGES / "figures" / f"method_detail_hingston_hampton_{lang}.pdf"
    out = CACHE / f"method_detail_hingston_hampton_{lang}_300dpi"; png = Path(str(out) + ".png")
    if not png.exists() or png.stat().st_mtime < pdf.stat().st_mtime:
        subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", str(pdf), str(out)], check=True)
    im = np.asarray(Image.open(png).convert("RGB")); g = im.mean(axis=2)
    dark = g < 60
    rows = np.where(dark.sum(axis=1) > 0.45 * im.shape[1])[0]; cols = np.where(dark.sum(axis=0) > 0.15 * im.shape[0])[0]
    def groups(v):
        out_ = []
        for r in v:
            if out_ and r - out_[-1][-1] <= 3:
                out_[-1].append(r)
            else:
                out_.append([r])
        return [(x[0], x[-1]) for x in out_]
    R, C = groups(rows), groups(cols)
    assert len(R) == 6 and len(C) == 2, (R, C)                      # three framed panels
    x0, x1 = C[0][1] + 1, C[1][0]
    aerial = im[R[0][1] + 1:R[1][0], x0:x1]; plans = im[R[4][1] + 1:R[5][0], x0:x1]
    return plans, aerial


def main():
    for lang, t in T.items():
        plans, aerial = panels(lang)
        fig = plt.figure(figsize=(16, 6.8))
        for k, (img, cap) in enumerate(((plans, t["a"]), (aerial, t["b"]))):
            ax = fig.add_axes([0.01 + 0.495 * k, 0.17, 0.485, 0.66])
            ax.imshow(img); ax.set_axis_off()
            ax.set_title(cap, loc="left", fontsize=10.5, color=F.INK, wrap=True)
        H = [Line2D([], [], ls="", marker="o", markersize=9, markerfacecolor=c, markeredgecolor="black", label=lab)
             for c, lab in (("#2a78d6", t["k1"]), ("#6250d6", t["k2"]), ("#1baf7a", t["k3"]))]
        fig.legend(handles=H, loc="lower left", bbox_to_anchor=(0.01, 0.075), ncol=3, fontsize=10.5, frameon=False)
        fig.text(0.012, 0.965, t["title"], fontsize=16, fontweight="bold", va="top", color=F.INK)
        fig.text(0.012, 0.015, t["src"], fontsize=8.5, va="bottom", color=F.MUTED, wrap=True)
        fig.savefig(HERE / f"then_and_now_{lang}.png", dpi=200); plt.close(fig)
    print("OK then_and_now")


if __name__ == "__main__":
    main()
