#!/usr/bin/env python3
"""Day length and what a daylight-only sensor sees. Left: share of each Telraam sensor's all-daylight daily total
that falls inside the fixed 08:00–16:00 window, by month (the rest is counted only when the evening is light).
Right: the loop counter (24 h): share of the 24-hour total inside the same window, by month.
Output: daylight_{en,fr}.png|svg.  Usage: python3 daylight.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
MN = {'en': ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'], 'fr': ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']}
rows = []
for lang in ('en', 'fr'):
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), sharey=True, gridspec_kw={'wspace': 0.08})
    ax = axes[0]; L.style_axes(ax); ax.grid(axis='x', visible=False)
    for s in ('west', 'east'):
        d = pd.read_csv(os.path.join(L.DERIVED, f'daily_{s}.csv'), parse_dates=['date']).set_index('date'); d = d[d.valid == 1]
        m = (d.groupby(d.index.month).bike.sum() / d.groupby(d.index.month).bike_all.sum() * 100)
        ax.plot(m.index, m.values, '-o', color=L.SERIES[s][2], lw=2, ms=5, mec='white', mew=0.8, label=L.SHORT[lang][s])
        if lang == 'en': rows += [{'series': s, 'month': int(k), 'share_08_16_pct': round(v, 1), 'basis': 'all-daylight total'} for k, v in m.items()]
    ax.set_title(L.tr(lang, 'Telraam: share of the daylight total counted 08:00–16:00', 'Telraam : part du total de jour comptée de 8 h à 16 h'), loc='left'); ax.legend(frameon=False, fontsize=8, loc='lower center')
    ax.set_ylabel('%'); ax.set_ylim(0, 100)
    ax = axes[1]; L.style_axes(ax); ax.grid(axis='x', visible=False)
    k = pd.read_csv(os.path.join(L.DERIVED, 'daily_loop.csv'), parse_dates=['date']).set_index('date'); k = k[(k.valid == 1) & k.bike_h.notna() & (k.index < L.WB_DEGRADED_FROM)]
    k2 = pd.read_csv(os.path.join(L.DERIVED, 'daily_loop.csv'), parse_dates=['date']).set_index('date'); k2 = k2[(k2.valid_eb == 1)]
    m = k2.groupby(k2.index.month).eb_win.sum() / k2.groupby(k2.index.month).eb.sum() * 100; m = m.reindex(range(1, 13))
    ax.plot(m.index, m.values, '-o', color=L.SERIES['loop'][2], lw=2, ms=5, mec='white', mew=0.8)
    if lang == 'en': rows += [{'series': 'loop_eastbound', 'month': int(a), 'share_08_16_pct': round(v, 1), 'basis': '24-hour total'} for a, v in m.dropna().items()]
    ax.set_title(L.tr(lang, 'Kensington loop (eastbound): share of the 24-hour total, 08:00–16:00', 'Boucle Kensington (vers l’est) : part du total de 24 h, 8 h–16 h'), loc='left')
    for a in axes: a.set_xticks(range(1, 13)); a.set_xticklabels(MN[lang]); a.set_xlabel(L.tr(lang, 'Month', 'Mois'))
    fig.text(0.125, -0.04, L.tr(lang, 'Left: a Telraam sensor counts only in daylight, so its daily total covers 9 hours in December and 16 in June; the fixed window covers the same 8 hours all year.\nRight: the loop counts day and night; June has no complete day in the hourly release (July 26, 2025 to May 11, 2026; released June 4, 2026).', 'À gauche : un capteur Telraam ne compte que de jour; son total quotidien couvre donc 9 heures en décembre et 16 en juin; la fenêtre fixe couvre les mêmes 8 heures toute l’année.\nÀ droite : la boucle compte jour et nuit; juin n’a aucun jour complet dans les données horaires (26 juillet 2025 au 11 mai 2026; transmises le 4 juin 2026).'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'daylight_{lang}'); plt.close(fig)
pd.DataFrame(rows).to_csv(os.path.join(T, 'window_share_by_month.csv'), index=False)
