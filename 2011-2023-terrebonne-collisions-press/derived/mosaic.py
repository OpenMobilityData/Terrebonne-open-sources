#!/usr/bin/env python3
"""Mosaic of the press captures about collisions ON rue de Terrebonne (the subset in TERREBONNE), four tiles a row,
each capture scaled to a common width and cropped to its top part (headline, date, lead), with a caption line.
Output: derived/terrebonne_collisions_press_mosaic.png (and _wide.jpg for posting). Usage: python3 mosaic.py"""
import os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(HERE), 'raw')
TERREBONNE = [
 ('2011-05-31_cbc_toddler-killed-3-injured-ndg-collision_terrebonne-grand.png', 'CBC News, May 31, 2011 — Terrebonne / Grand: a 3-year-old killed, 3 injured'),
 ('2011-06-25_ctv_ndg-residents-rally-for-safety-from-cars_terrebonne-grand.png', 'CTV Montreal, June 25, 2011 — residents\' petition after the May 31 death'),
 ('2011-07-25_ctv_west-end-street-hit-by-yet-another-car-crash_terrebonne-kensington.png', 'CTV Montreal, July 25, 2011 — Terrebonne / Kensington: car into a house'),
 ('2011-09-28_ctv_another-crash-at-accident-prone-ndg-corner_terrebonne-kensington.png', 'CTV Montreal, Sept. 28, 2011 — Terrebonne / Kensington: « about a dozen accidents … over the past five years »'),
 ('2011_ctv_related-image_car-crash-accident-plagued-part-of-ndg.png', 'CTV Montreal, 2011 — residents\' photo of a crash at the same corner'),
 ('2019-09-03_cbc_ndg-pedestrian-84-dies-after-being-hit-by-dump-truck_terrebonne-girouard.png', 'CBC News, Sept. 3, 2019 — Terrebonne / Girouard: pedestrian, 84, killed by a dump truck'),
 ('2019-09-04_gazette_hanes_yet-another-family-grieving-a-pedestrian-killed_terrebonne-girouard.png', 'Montreal Gazette, Sept. 4, 2019 — the 15th pedestrian killed in Montreal that year'),
]
W, HMAX, PAD, CAP, COLS = 760, 820, 24, 70, 4
def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Supplemental/Arial.ttf', '/Library/Fonts/Arial.ttf'):
        if os.path.exists(p): return ImageFont.truetype(p, sz)
    return ImageFont.load_default()
tiles = []
for fn, cap in TERREBONNE:
    im = Image.open(os.path.join(RAW, fn)).convert('RGB')
    im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
    if im.height > HMAX: im = im.crop((0, 0, W, HMAX))
    tiles.append((im, cap))
rows = (len(tiles) + COLS - 1) // COLS
TH = HMAX + CAP
sheet = Image.new('RGB', (COLS * (W + PAD) + PAD, 120 + rows * (TH + PAD) + PAD), '#f4f3ef')
d = ImageDraw.Draw(sheet)
d.text((PAD, 28), 'Collisions on rue de Terrebonne in the press, 2011–2019: two deaths and a « dozen accidents » corner, before the 2024 lanes', fill='#111', font=font(34))
d.text((PAD, 76), 'Captures of the articles (CBC, CTV Montreal, Montreal Gazette), reproduced for criticism and review; sources and links in the folder README. Not a complete record: what residents kept.', fill='#52514e', font=font(22))
for i, (im, cap) in enumerate(tiles):
    r, c = divmod(i, COLS); x, y = PAD + c * (W + PAD), 120 + r * (TH + PAD)
    box = Image.new('RGB', (W, HMAX), 'white'); box.paste(im, (0, 0)); sheet.paste(box, (x, y))
    d.rectangle((x, y, x + W - 1, y + HMAX - 1), outline='#c9c7c0', width=2)
    # caption, wrapped
    words, lines, cur = cap.split(), [], ''
    f = font(22)
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if d.textlength(t, font=f) > W - 8: lines.append(cur); cur = w_
        else: cur = t
    lines.append(cur)
    for k, ln in enumerate(lines[:2]): d.text((x + 2, y + HMAX + 8 + k * 28), ln, fill='#111', font=f)
out = os.path.join(HERE, 'terrebonne_collisions_press_mosaic.png'); sheet.save(out, optimize=True)
sheet.convert('RGB').save(os.path.join(HERE, 'terrebonne_collisions_press_mosaic.jpg'), quality=85)
print(out, sheet.size)
