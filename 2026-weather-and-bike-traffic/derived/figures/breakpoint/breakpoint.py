#!/usr/bin/env python3
"""Profile of the model deviance over the temperature at which the slope changes, one line per series (difference
from each series' minimum). A flat-bottomed profile means the change of slope is gradual or poorly located.
Output: breakpoint_{en,fr}.png|svg.  Usage: python3 breakpoint.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import wx_lib as L, pandas as pd, numpy as np
plt = L.fig_setup(); T = L.TABLES
p = pd.read_csv(os.path.join(T, 'breakpoint_profile.csv'))
for lang in ('en', 'fr'):
    fig, ax = plt.subplots(figsize=(8.2, 4.2)); L.style_axes(ax)
    for s in ['west', 'east', 'loop', 'bixi', 'city']:
        d = p[p.series == s]; ax.plot(d.breakpoint, d.delta, color=L.SERIES[s][2], lw=2, label=L.SHORT[lang][s])
        m = d.loc[d.delta.idxmin()]; ax.plot(m.breakpoint, 0, 'o', color=L.SERIES[s][2], ms=7, mec='white', mew=1)
    ax.axhline(3.84, color=L.MUTED, lw=0.8, ls=(0, (4, 3))); ax.text(26.2, 3.84, '3.84' if lang == 'en' else '3,84', fontsize=7.5, color=L.MUTED, va='center')
    ax.set_ylim(-1, 40); ax.set_xlabel(L.tr(lang, 'Temperature at which the slope changes (°C)', 'Température à laquelle la pente change (°C)')); ax.set_ylabel(L.tr(lang, 'Deviance above the minimum', 'Déviance au-dessus du minimum'))
    ax.set_title(L.tr(lang, 'Where does the response to temperature change slope?', 'Où la réponse à la température change-t-elle de pente?'), loc='left'); ax.legend(frameon=False, fontsize=8, loc='upper left', bbox_to_anchor=(1.01, 1.0))
    fig.text(0.125, -0.02, L.tr(lang, 'Dot: the temperature with the lowest deviance. Dashed line: 3.84, the usual 95 % reference for one parameter; the bootstrap intervals in the tables are wider.', 'Point : température de déviance minimale. Tireté : 3,84, repère habituel à 95 % pour un paramètre; les intervalles bootstrap des tableaux sont plus larges.'), fontsize=7, color=L.MUTED, va='top')
    L.savefig(fig, HERE, f'breakpoint_{lang}'); plt.close(fig)
