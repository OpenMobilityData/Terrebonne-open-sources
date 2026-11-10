#!/usr/bin/env python3
"""Percentage change in the daily count associated with rain, snowfall, snow on the ground and wind, temperature
and season held fixed: one row per condition, one mark per series, 95 % intervals.
Output: effects_{en,fr}.png|svg.  Usage: python3 effects.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
e = pd.read_csv(os.path.join(T, 'effects_main.csv')); e = e[e.model == 'main']
TERMS = [('rain_under2', 'Rain, under 2 mm', 'Pluie, moins de 2 mm'), ('rain_2to10', 'Rain, 2 to 10 mm', 'Pluie, 2 à 10 mm'), ('rain_over10', 'Rain, over 10 mm', 'Pluie, plus de 10 mm'),
         ('snow_under2', 'Snowfall, under 2 cm', 'Neige, moins de 2 cm'), ('snow_2to10', 'Snowfall, 2 cm or more', 'Neige, 2 cm ou plus'),
         ('snow_on_ground', 'Snow on the ground (1 cm or more)', 'Neige au sol (1 cm ou plus)'), ('wind_per_10kmh', 'Wind, per 10 km/h', 'Vent, par 10 km/h')]
ORDER = ['west', 'east', 'loop', 'bixi', 'city']; MK = {'west': 'o', 'east': 's', 'loop': 'D', 'bixi': '^', 'city': 'P'}
for lang in ('en', 'fr'):
    fig, ax = plt.subplots(figsize=(8.2, 6.2)); L.style_axes(ax); ax.grid(axis='y', visible=False)
    for i, (t, en, fr) in enumerate(TERMS):
        for j, s in enumerate(ORDER):
            r = e[(e.term == t) & (e.series == s)]
            if r.empty: continue
            r = r.iloc[0]; y = -i + 0.3 - j * 0.15
            ax.plot([r.lo, r.hi], [y, y], color=L.SERIES[s][2], lw=1.6, solid_capstyle='round')
            ax.plot(r.pct, y, MK[s], color=L.SERIES[s][2], ms=6, mec='white', mew=0.8, label=L.SHORT[lang][s] if i == 0 else None)
        if i: ax.axhline(-i + 0.5, color=L.GRID, lw=0.6)
    ax.axvline(0, color=L.INK, lw=0.8); ax.set_yticks([-i for i in range(len(TERMS))]); ax.set_yticklabels([L.tr(lang, en, fr) for _, en, fr in TERMS], fontsize=8.5, color=L.INK)
    ax.set_xlabel(L.tr(lang, 'Change in the daily count (%), compared with a day without the condition', 'Variation du comptage quotidien (%), par rapport à un jour sans la condition'))
    ax.set_title(L.tr(lang, 'Rain, snow and wind: change in the daily count at a given temperature and time of year', 'Pluie, neige et vent : variation du comptage quotidien à température et période de l’année données'), loc='left')
    ax.legend(frameon=False, fontsize=8, loc='lower left', ncol=1)
    fig.text(0.125, -0.01, L.tr(lang, 'Negative binomial models, one per series; lines: 95 % intervals (autocorrelation-robust). Rain and snowfall are the day’s totals at Montréal-Trudeau (24 h).\nA series has no mark where it has fewer than five such days (BIXI: April 15 to November 15 only). Snowfall of 10 cm or more is merged with 2 to 10 cm.', 'Modèles binomiaux négatifs, un par série; traits : intervalles à 95 % (robustes à l’autocorrélation). Pluie et neige : totaux du jour à Montréal-Trudeau (24 h).\nUne série n’a pas de marque lorsqu’elle compte moins de cinq jours de ce type (BIXI : du 15 avril au 15 novembre seulement). La neige de 10 cm ou plus est regroupée avec 2 à 10 cm.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'effects_{lang}'); plt.close(fig)
