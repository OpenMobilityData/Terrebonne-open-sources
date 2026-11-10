#!/usr/bin/env python3
"""The fitted response to temperature of every series on one relative scale (count at 20 °C = 100; logarithmic
axis), with 95 % bands. Relative responses are what the series can share; levels are not shown.
Output: temperature_curve_{en,fr}.png|svg.  Usage: python3 temperature_curve.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
cur = pd.read_csv(os.path.join(T, 'temperature_curve.csv'))
for lang in ('en', 'fr'):
    fig, ax = plt.subplots(figsize=(8.2, 5.0)); L.style_axes(ax)
    for s in ['city', 'bixi', 'loop', 'east', 'west']:
        c = cur[cur.series == s]; col = L.SERIES[s][2]
        ax.fill_between(c.temp, c.lo, c.hi, color=col, alpha=0.12, lw=0)
        ax.plot(c.temp, c.index_20C_100, color=col, lw=2, label=L.SHORT[lang][s])
    ax.set_yscale('log'); ax.set_yticks([10, 20, 30, 50, 70, 100, 130]); ax.set_yticklabels(['10', '20', '30', '50', '70', '100', '130']); ax.minorticks_off()
    ax.axhline(100, color=L.AXIS, lw=0.8); ax.set_xlim(-20, 30)
    ax.set_xlabel(L.tr(lang, 'Daytime temperature, 08:00–16:00 (°C)', 'Température de jour, 8 h–16 h (°C)'))
    ax.set_ylabel(L.tr(lang, 'Count relative to the same day at 20 °C (= 100)', 'Comptage par rapport au même jour à 20 °C (= 100)'))
    ax.set_title(L.tr(lang, 'Response to temperature, each series relative to its own level at 20 °C', 'Réponse à la température, chaque série par rapport à son propre niveau à 20 °C'), loc='left')
    h, l = ax.get_legend_handles_labels(); ax.legend(h[::-1], l[::-1], frameon=False, fontsize=8, loc='lower right')
    fig.text(0.125, -0.01, L.tr(lang, 'Negative binomial models, one per series, with day type, year, season (two annual harmonics), rain, snowfall, snow on the ground and wind held fixed.\nBands: 95 % intervals (autocorrelation-robust). Logarithmic axis: equal vertical steps are equal percentage changes.', 'Modèles binomiaux négatifs, un par série, à type de jour, année, saison (deux harmoniques annuelles), pluie, neige, neige au sol et vent constants.\nBandes : intervalles à 95 % (robustes à l’autocorrélation). Axe logarithmique : des écarts verticaux égaux sont des variations en pourcentage égales.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'temperature_curve_{lang}'); plt.close(fig)
