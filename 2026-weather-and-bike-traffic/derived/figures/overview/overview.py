#!/usr/bin/env python3
"""Overview: daytime temperature and the daily count of each series over the whole record, one panel per series
(each on its own scale: the series are never compared in level). Winters (Nov 16 – Mar 31) shaded.
Output: overview_{en,fr}.png|svg beside this script.  Usage: python3 overview.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'scripts'))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup()
wx = pd.read_csv(os.path.join(L.DERIVED, 'weather_daily.csv'), parse_dates=['date']).set_index('date')
ORDER = ['west', 'east', 'loop', 'bixi', 'city']
for lang in ('en', 'fr'):
    fig, axes = plt.subplots(6, 1, figsize=(9.2, 10.2), sharex=True, gridspec_kw={'height_ratios': [1.1, 1, 1, 1, 1, 1], 'hspace': 0.42})
    lo, hi = pd.Timestamp('2024-08-01'), wx.index.max()
    ax = axes[0]; L.style_axes(ax); L.shade_winters(ax, lo, hi)
    ax.plot(wx.index, wx.t_day, color=L.MUTED, lw=0.5, alpha=0.6); ax.plot(wx.index, wx.t_day.rolling(7, center=True).mean(), color=L.INK, lw=1.4)
    ax.axhline(0, color=L.AXIS, lw=0.8); ax.set_title(L.tr(lang, 'Daytime temperature at Montréal-Trudeau, 08:00–16:00 (°C; thick line: 7-day mean)', 'Température de jour à Montréal-Trudeau, 8 h–16 h (°C; trait épais : moyenne sur 7 jours)'), loc='left')
    for ax, s in zip(axes[1:], ORDER):
        d = L.read_daily(s); L.style_axes(ax); L.shade_winters(ax, lo, hi)
        full = d.y.reindex(pd.date_range(d.index.min(), d.index.max()))
        ax.plot(full.index, full.values, color=L.SERIES[s][2], lw=0.5, alpha=0.45)
        ax.plot(full.index, full.rolling(7, center=True, min_periods=5).mean(), color=L.SERIES[s][2], lw=1.6)
        ax.set_ylim(0, None); ax.set_title(f"{L.SHORT[lang][s]} — {L.SERIES_NOTE[lang][s]} " + L.tr(lang, f'({len(d)} valid days)', f'({len(d)} jours valides)'), loc='left')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, p, lang=lang: L.num(v, lang)))
    axes[-1].set_xlim(lo, hi)
    fig.text(0.125, 0.075, L.tr(lang, 'Each panel has its own scale. Shaded: November 16 to March 31. Gaps: days without a valid count. Thin line: daily; thick line: 7-day mean.\nSources: Telraam (citizen-operated sensors, API pull of Nov 9, 2026); borough loop counter, request 2026-300 (released June 4, 2026); BIXI Montréal open data;\nCity of Montréal open data (permanent counters); Environment and Climate Change Canada.',
             'Chaque panneau a sa propre échelle. En gris : du 16 novembre au 31 mars. Interruptions : jours sans comptage valide. Trait fin : quotidien; trait épais : moyenne sur 7 jours.\nSources : Telraam (capteurs exploités par des citoyens, extraction API du 9 nov. 2026); compteur de l’arrondissement, demande 2026-300 (transmise le 4 juin 2026); données ouvertes de BIXI Montréal;\ndonnées ouvertes de la Ville de Montréal (compteurs permanents); Environnement et Changement climatique Canada.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'overview_{lang}'); plt.close(fig)
