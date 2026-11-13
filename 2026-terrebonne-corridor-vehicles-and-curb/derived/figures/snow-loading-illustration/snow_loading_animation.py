"""Short video (about 15 s, 1920x1080, H.264, no sound) of the snow-loading ILLUSTRATION, night by night (owner's request,
Nov 12, 2026, for the Facebook post). Same data and same caveat as snow_loading_illustration.py: the nightly share of the
curb under a ban is real (the operation of January 17-22, 2026, City truckload counts); which streets are banned each night
is invented, and every frame says so.
Frames: all legal curb sides pale; then each night, its sides in colour, earlier nights grey (already cleared); finally the
whole operation in colour. Cross-fades between states. Needs ffmpeg.
Run:  ~/.venvs/omd/bin/python derived/figures/snow-loading-illustration/snow_loading_animation.py"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
import snow_loading_illustration as I  # noqa: E402

FPS, HOLD, FADE, HOLD_END = 25, 50, 10, 90
PALE, DONE = "#dfe2dd", "#9aa3ab"
T = {"en": dict(
        title="How a snow-loading operation moves through the corridor",
        badge="ILLUSTRATION – not the City's schedule",
        start="Before the operation: every side of a street where parking is allowed",
        night="Night {i}: parking banned on the coloured sides ({p} % of the corridor's curb)",
        end="The whole operation: each side of a street banned on one night",
        key_done="already cleared", key_todo="not yet", lane="the lane",
        foot="The share of the curb under a ban each night is real (City truckload counts, one operation in January 2026). Which streets are cleared on which night is NOT published:\n"
             "the order shown is invented. Preliminary results, not peer reviewed. github.com/OpenMobilityData/Terrebonne-open-sources"),
     "fr": dict(
        title="Comment une opération de chargement de la neige traverse le corridor",
        badge="ILLUSTRATION – pas l’horaire de la Ville",
        start="Avant l’opération : chaque côté de rue où le stationnement est permis",
        night="Nuit {i} : stationnement interdit sur les côtés colorés ({p} % de la bordure du corridor)",
        end="L’opération entière : chaque côté de rue interdit une nuit",
        key_done="déjà déneigé", key_todo="pas encore", lane="la piste",
        foot="La part de la bordure interdite chaque nuit est réelle (chargements de la Ville, une opération de janvier 2026). Les rues déneigées chaque nuit ne sont PAS publiées :\n"
             "l’ordre montré est inventé. Résultats préliminaires, non révisés par des pairs. github.com/OpenMobilityData/Terrebonne-open-sources")}


def frame(cs, da, lane, edge, by_night, t, state, path):
    """state = -1 (before), 0..n-1 (that night), n (whole operation)."""
    n = len(by_night)
    fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
    ax = fig.add_axes([0.01, 0.20, 0.98, 0.62])
    da.plot(ax=ax, facecolor="#f4f5f2", edgecolor=F.SURFACE, linewidth=1.2)
    edge.plot(ax=ax, color=F.MUTED, linewidth=1.0, linestyle=(0, (1, 2)))
    for i in range(n):
        sub = cs[cs.night == i]
        if state == n:
            col, lw = I.COL[i], 3.2
        elif i < state:
            col, lw = DONE, 2.2
        elif i == state:
            col, lw = I.COL[i], 4.2
        else:
            col, lw = PALE, 2.2
        sub.plot(ax=ax, color=col, linewidth=lw, capstyle="round", zorder=3 if i == state else 2)
    lane.plot(ax=ax, color=F.INK, linewidth=1.1, linestyle=(0, (3, 2)), zorder=4)
    ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view()
    fig.text(0.015, 0.965, t["title"], fontsize=26, fontweight="bold", va="top", color=F.INK)
    fig.text(0.015, 0.905, t["badge"], fontsize=17, fontweight="bold", va="top", color=F.INK,
             bbox=dict(boxstyle="round,pad=0.4", fc="#fff3c4", ec=F.INK, lw=1.4))
    msg = t["start"] if state < 0 else t["end"] if state == n else t["night"].format(i=state + 1, p=f"{100 * by_night.iloc[state]:.0f}")
    fig.text(0.015, 0.175, msg, fontsize=22, va="top", color=F.INK, fontweight="bold")
    # night ticker: one chip per night, the current one in colour
    for i in range(n):
        x0 = 0.015 + i * 0.075
        on = state == n or i == state
        fc = I.COL[i] if on else (DONE if 0 <= state and i < state else PALE)
        fig.patches.append(plt.Rectangle((x0, 0.075), 0.065, 0.04, transform=fig.transFigure, fc=fc, ec="none"))
        lab = (t["night"].split(":")[0] if ":" in t["night"] else "").format(i=i + 1)
        fig.text(x0 + 0.0325, 0.095, lab, ha="center", va="center", fontsize=13, color="#ffffff" if on and i >= 2 else F.INK, fontweight="bold")
    h = [Line2D([], [], color=DONE, lw=3), Line2D([], [], color=PALE, lw=3), Line2D([], [], color=F.INK, lw=1.2, ls=(0, (3, 2)))]
    fig.legend(h, [t["key_done"], t["key_todo"], t["lane"]], loc="lower right", bbox_to_anchor=(0.99, 0.07), ncol=3, fontsize=14, frameon=False)
    fig.text(0.015, 0.012, t["foot"], fontsize=11.5, color=F.MUTED, va="bottom", linespacing=1.35)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    cs, da, lane, edge, by_night = I.prepare()
    n = len(by_night)
    for lang, t in T.items():
        tmp = Path(tempfile.mkdtemp())
        keys = []
        for st in range(-1, n + 1):
            p = tmp / f"key_{st + 1:02d}.png"; frame(cs, da, lane, edge, by_night, t, st, p); keys.append(p)
        imgs = [Image.open(k).convert("RGB") for k in keys]
        seq = tmp / "seq"; seq.mkdir(); k = 0
        for j, im in enumerate(imgs):
            for _ in range(HOLD_END if j == len(imgs) - 1 else HOLD):
                im.save(seq / f"f{k:05d}.png"); k += 1
            if j < len(imgs) - 1:
                for f in range(1, FADE + 1):
                    Image.blend(im, imgs[j + 1], f / (FADE + 1)).save(seq / f"f{k:05d}.png"); k += 1
        out = HERE / f"snow_loading_animation_{lang}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(seq / "f%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-crf", "20", "-preset", "slow", "-movflags", "+faststart", str(out)], check=True)
        shutil.copyfile(keys[len(keys) // 2], HERE / f"snow_loading_animation_{lang}_frame.png")      # a middle frame, for review
        shutil.rmtree(tmp)
        print(out.name, f"{k / FPS:.1f} s", f"{out.stat().st_size / 1e6:.1f} MB")
    print("OK snow_loading_animation")


if __name__ == "__main__":
    main()
