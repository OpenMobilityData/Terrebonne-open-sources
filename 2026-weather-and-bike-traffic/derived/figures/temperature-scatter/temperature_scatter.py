#!/usr/bin/env python3
"""Daily count against daytime temperature, one panel per series (own scale), points marked dry / rain / snow,
with the median count of days without precipitation in 2.5-degree bands (bands with at least five such days). Output: temperature_scatter_{en,fr}.png|svg.  Usage: python3 temperature_scatter.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
CAT = [('dry', '#8a949b', 'o', 9), ('rain', '#2a78d6', 'v', 13), ('snow', '#eb6834', 'X', 15)]
NAME = {'en': {'dry': 'No precipitation', 'rain': 'Rain (0.2 mm or more)', 'snow': 'Snowfall (0.2 cm or more)'}, 'fr': {'dry': 'Sans précipitations', 'rain': 'Pluie (0,2 mm ou plus)', 'snow': 'Neige (0,2 cm ou plus)'}}
for lang in ('en', 'fr'):
    fig, axes = plt.subplots(3, 2, figsize=(9.2, 10.4), gridspec_kw={'hspace': 0.42, 'wspace': 0.18})
    for ax, s in zip(axes.flat, ['west', 'loop', 'east', 'gir', 'bixi', 'city']):
        d = L.read_daily(s); L.style_axes(ax)
        d['cat'] = np.where(d.snow >= 0.2, 'snow', np.where(d.rain >= 0.2, 'rain', 'dry'))
        for c, col, mk, sz in CAT:
            g = d[d.cat == c]; ax.scatter(g.t_day, g.y, s=sz, marker=mk, color=col, alpha=0.6 if c == 'dry' else 0.8, lw=0, label=f"{NAME[lang][c]}" if s == 'west' else None, zorder=2 if c == 'dry' else 3)
        g = d[d.cat == 'dry'].copy(); g['bin'] = np.floor(g.t_day / 2.5) * 2.5 + 1.25
        m = g.groupby('bin').y.agg(['median', 'size']); m = m[m['size'] >= 5]
        ax.plot(m.index, m['median'], color=L.INK, lw=1.8, zorder=4)
        ax.set_ylim(0, None); ax.set_title(f"{L.SHORT[lang][s]} — {L.SERIES_NOTE[lang][s]}", loc='left')
        ax.set_xlabel(L.tr(lang, 'Daytime temperature, 08:00–16:00 (°C)', 'Température de jour, 8 h–16 h (°C)'))
    axes[0, 0].legend(frameon=False, fontsize=7.5, loc='upper left', handletextpad=0.2)
    fig.text(0.125, 0.055, L.tr(lang, 'Each panel has its own scale. Black line: median count of the days without precipitation, by 2.5-degree band (bands with at least five such days).\nRain and snowfall are the day\u2019s totals at Montréal-Trudeau. BIXI: all days with trips, winter included.', 'Chaque panneau a sa propre échelle. Trait noir : médiane des jours sans précipitations, par tranche de 2,5 degrés (tranches d\u2019au moins cinq jours).\nPluie et neige : totaux du jour à Montréal-Trudeau. BIXI : tous les jours avec trajets, hiver compris.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'temperature_scatter_{lang}'); plt.close(fig)
