"""Shared chart style (the palette of the other OpenMobilityData repositories; the blue ramp is the sequential hue of
the dataviz reference palette, steps 250, 350, 450, 550 and 700, lightness falling at every step). Text wears ink
colours, never the series colour."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ratio_lib import ROOT, TABLES  # noqa: E402

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, MUTED, GRID, AXIS, SURFACE, GREY = "#1f2428", "#5f6b74", "#e2e4e1", "#c9cdd2", "#ffffff", "#9aa3ab"
GROUND, TOWN = "#ecedeb", "#f6f6f4"          # City territory without a ranked value; other municipalities
# classes of automobiles per 100 places (the value rounded to a whole number, as printed, so label and colour agree)
CLASSES = [(None, 59), (60, 69), (70, 79), (80, 99), (100, None)]
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]
LABEL_INK = [INK, INK, "#ffffff", "#ffffff", "#ffffff"]
RANKED = "ranked"

plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 10, "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": AXIS, "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "x",
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "svg.fonttype": "none",
    "legend.frameon": False, "hatch.linewidth": 0.5,
})

BOROUGH = {  # géobase spelling -> official name
    "Ahuntsic-Cartierville": "Ahuntsic-Cartierville", "Anjou": "Anjou",
    "Côte-des-Neiges-Notre-Dame-de-Grâce": "Côte-des-Neiges–Notre-Dame-de-Grâce", "Lachine": "Lachine", "LaSalle": "LaSalle",
    "Le Plateau-Mont-Royal": "Le Plateau-Mont-Royal", "Le Sud-Ouest": "Le Sud-Ouest", "L'Île-Bizard-Sainte-Geneviève": "L’Île-Bizard–Sainte-Geneviève",
    "Mercier-Hochelaga-Maisonneuve": "Mercier–Hochelaga-Maisonneuve", "Montréal-Nord": "Montréal-Nord", "Outremont": "Outremont",
    "Pierrefonds-Roxboro": "Pierrefonds-Roxboro", "Rivière-des-Prairies-Pointe-aux-Trembles": "Rivière-des-Prairies–Pointe-aux-Trembles",
    "Rosemont-La Petite-Patrie": "Rosemont–La Petite-Patrie", "Saint-Laurent": "Saint-Laurent", "Saint-Léonard": "Saint-Léonard", "Verdun": "Verdun",
    "Ville-Marie": "Ville-Marie", "Villeray-Saint-Michel-Parc-Extension": "Villeray–Saint-Michel–Parc-Extension"}


def klass(v):
    """Index of the class of a value of automobiles per 100 places (whole number)."""
    for i, (lo, hi) in enumerate(CLASSES):
        if (lo is None or v >= lo) and (hi is None or v <= hi):
            return i
    raise ValueError(v)


def class_label(i, lang):
    lo, hi = CLASSES[i]
    if lo is None:
        return f"under {hi + 1}" if lang == "en" else f"moins de {hi + 1}"
    if hi is None:
        return f"{lo} or more" if lang == "en" else f"{lo} ou plus"
    return f"{lo} to {hi}" if lang == "en" else f"{lo} à {hi}"


def num(x, lang, dec=0):
    s = f"{x:,.{dec}f}"
    return s if lang == "en" else s.replace(",", " ").replace(".", ",")


def numbers():
    return json.load(open(ROOT / "derived/numbers.json"))


def table():
    d = pd.read_csv(TABLES / "fsa_ratio.csv", index_col=0)
    d["per100"] = d.automobiles_per_100_places
    return d


def boroughs_label(s, min_share=25):
    """« Ville-Marie 72 %; Le Sud-Ouest 28 % » -> the official names of the boroughs holding at least min_share % of the FSA's City curb."""
    out = []
    for part in str(s).split("; "):
        name, pct = part.rsplit(" ", 2)[0], int(part.rsplit(" ", 2)[1])
        if pct >= min_share or not out:
            out.append(BOROUGH.get(name, name))
    return " / ".join(out)


def save(fig, here, stem, lang):
    for ext in ("png", "svg"):
        fig.savefig(Path(here) / f"{stem}_{lang}.{ext}", dpi=200)
    plt.close(fig)
