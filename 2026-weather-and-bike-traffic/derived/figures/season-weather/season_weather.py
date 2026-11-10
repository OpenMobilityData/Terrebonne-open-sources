#!/usr/bin/env python3
"""Share of the day-to-day variation (deviance) accounted for by calendar and season terms alone, by weather alone,
and by both: the part only weather explains, the part only calendar and season explain, and the part either would.
Output: season_weather_{en,fr}.png|svg.  Usage: python3 season_weather.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
b = pd.read_csv(os.path.join(T, 'deviance_blocks.csv')).set_index('series')
PARTS = [('shared', '#8a949b', 'Either set of terms (shared)', 'L’un ou l’autre ensemble (commun)'), ('unique_weather', '#2a78d6', 'Weather only', 'Météo seulement'), ('unique_calendar_season', '#eb6834', 'Calendar and season only', 'Calendrier et saison seulement')]
ORDER = ['west', 'east', 'loop', 'gir', 'bixi', 'city']
for lang in ('en', 'fr'):
    fig, ax = plt.subplots(figsize=(8.2, 4.1)); L.style_axes(ax); ax.grid(axis='y', visible=False)
    for i, s in enumerate(ORDER):
        left = 0
        for k, col, en, fr in PARTS:
            v = 100 * b.loc[s, k]; ax.barh(-i, v - 0.4, left=left + 0.2, color=col, height=0.55, label=L.tr(lang, en, fr) if i == 0 else None)
            if v >= 4: ax.text(left + v / 2, -i, f'{v:.0f}', ha='center', va='center', fontsize=8, color='white', fontweight='bold')
            left += v
        ax.text(left + 1, -i, L.tr(lang, f'{left:.0f} % in all', f'{left:.0f} % en tout'), va='center', fontsize=8, color=L.INK)
    ax.set_yticks([-i for i in range(len(ORDER))]); ax.set_yticklabels([L.SHORT[lang][s] for s in ORDER], color=L.INK); ax.set_xlim(0, 108)
    ax.set_xlabel(L.tr(lang, 'Share of the deviance of daily counts accounted for (%)', 'Part de la déviance des comptages quotidiens expliquée (%)'))
    ax.set_title(L.tr(lang, 'What accounts for the day-to-day variation: weather, calendar and season', 'Ce qui rend compte de la variation d’un jour à l’autre : météo, calendrier et saison'), loc='left')
    ax.legend(frameon=False, fontsize=8, loc='upper center', bbox_to_anchor=(0.45, -0.22), ncol=3)
    L.savefig(fig, HERE, f'season_weather_{lang}'); plt.close(fig)
