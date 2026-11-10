#!/usr/bin/env python3
"""Winter days (Nov 16 – Mar 31): change in the daily count per 5 cm of snowfall on the day itself and on each of
the seven days before, temperature, rain, wind, day type and snow on the ground held fixed. One panel per series.
Output: snow_lags_{en,fr}.png|svg.  Usage: python3 snow_lags.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
g = pd.read_csv(os.path.join(T, 'snow_lags_winter.csv'))
for lang in ('en', 'fr'):
    fig, axes = plt.subplots(1, 3, figsize=(9.2, 3.3), sharey=True, gridspec_kw={'wspace': 0.08})
    for ax, s in zip(axes, ['west', 'east', 'loop']):
        d = g[g.series == s]; L.style_axes(ax); ax.grid(axis='x', visible=False); col = L.SERIES[s][2]
        ax.axhline(0, color=L.INK, lw=0.8); ax.vlines(d.lag_days, d.lo, d.hi, color=col, lw=1.6); ax.plot(d.lag_days, d.pct_per_5cm, 'o', color=col, ms=6, mec='white', mew=0.8)
        ax.set_title(L.SHORT[lang][s], loc='left'); ax.set_xticks(range(8)); ax.set_xlabel(L.tr(lang, 'Days after the snowfall', 'Jours après la chute de neige'))
    axes[0].set_ylabel(L.tr(lang, 'Change per 5 cm of snow (%)', 'Variation par 5 cm de neige (%)'))
    fig.text(0.125, -0.06, L.tr(lang, 'Negative binomial models on winter days, one per series; lines: 95 % intervals (autocorrelation-robust). Day 0 is the day of the snowfall.', 'Modèles binomiaux négatifs sur les jours d’hiver, un par série; traits : intervalles à 95 % (robustes à l’autocorrélation). Le jour 0 est celui de la chute de neige.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'snow_lags_{lang}'); plt.close(fig)
