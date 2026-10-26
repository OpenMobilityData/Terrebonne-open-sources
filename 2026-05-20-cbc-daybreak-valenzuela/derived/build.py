#!/usr/bin/env python3
"""Daybreak May 20, 2026 fact check (same build as the Nov 6, 2025 folder). Stamp a version tag (YYYY-MM-DD-hh-mm-ss, America/Toronto) into the
derived documents, compile them, and regenerate the summary-point extracts
and text files.

Usage:  python3 build.py            # stamp now, build everything
        python3 build.py --no-stamp # rebuild without changing the tag

The tag lives in each .tex as  \\newcommand{\\docversion}{...}  and appears in
the page footer (small grey) and in the PDF metadata (Subject). The .txt
files carry it as a last line. One tag is shared by all files built in the
same run, so a set of files can be identified as belonging together.
"""
import re, subprocess, sys, unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import os
HERE = os.path.dirname(os.path.abspath(__file__))
SUMMARIES = {
    'en': 'Daybreak_2026-05-20_Valenzuela_fact_check_en.tex',
    'fr': 'Daybreak_2026-05-20_Valenzuela_fact_check_fr.tex',
}
EXTRACTS = {
    'en': 'Daybreak_2026-05-20_Valenzuela_summary_points_en.tex',
    'fr': 'Daybreak_2026-05-20_Valenzuela_summary_points_fr.tex',
}
TXT_HEAD = {
    'en': ["CBC Daybreak, May 20, 2026: the borough mayor's statements on the Terrebonne bike path checked against the record",
           "Summary points of the fact check. Full document, sources, page references and the transcript: https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-05-20-cbc-daybreak-valenzuela", ""],
    'fr': ["CBC Daybreak, 20 mai 2026 : les affirmations de la mairesse sur la piste cyclable de Terrebonne vérifiées au dossier",
           "Points sommaires de la vérification. Document complet, sources, références aux pages et transcription : https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-05-20-cbc-daybreak-valenzuela", ""],
}

def stamp(path, tag):
    s = open(path, encoding='utf-8').read()
    s2, n = re.subn(r'\\newcommand\{\\docversion\}\{[^}]*\}', r'\\newcommand{\\docversion}{%s}' % tag, s)
    assert n == 1, f'{path}: expected one \\docversion definition, found {n}'
    open(path, 'w', encoding='utf-8').write(s2)

def compile_tex(path):
    for _ in range(2):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', path], cwd=HERE,
                           capture_output=True, text=True, errors='replace')
    out = r.stdout
    bad = [l for l in out.splitlines() if l.startswith('!') or 'Overfull' in l]
    pages = re.search(r'Output written on \S+ \((\d+) pages?', out)
    print(f'{path}: {pages.group(1) if pages else "?"} pages' + (f'  WARN {bad}' if bad else ''))

def extract(src_tex, dst_tex):
    src = open(src_tex, encoding='utf-8').read()
    a = src.index('\\begin{enumerate}[nosep]'); b = src.index('\\end{enumerate}', a) + len('\\end{enumerate}')
    d = open(dst_tex, encoding='utf-8').read()
    x = d.index('\\begin{enumerate}'); y = d.index('\\end{enumerate}') + len('\\end{enumerate}')
    opts = d[x:d.index(']', x) + 1]
    open(dst_tex, 'w', encoding='utf-8').write(d[:x] + src[a:b].replace('\\begin{enumerate}[nosep]', opts) + d[y:])

def detex(s):
    s = re.sub(r'\\cliptime\{([^}]*)\}', r'[\1]', s)
    s = re.sub(r'\\pgl\{([^}]*)\}\{([^}]*)\}', r'[2026-581, p. \2]', s)
    s = re.sub(r'\\pg\{([^}]*)\}', r'[2026-581, p. \1]', s)
    s = re.sub(r'\\exppg\{([^}]*)\}', r'[EXP 2023, p. \1]', s)
    s = re.sub(r'\\tr\{([^}]*)\}', r'[City council, Oct 19, 2026, \1]', s)
    s = re.sub(r'\\octsix\{[^}]*\}\{([^}]*)\}', r'[Borough council, Oct 6, 2026, \1]', s)
    s = re.sub(r'\\septeight\{([^}]*)\}', r'[Borough council, Sept 8, 2026, \1]', s)
    s = re.sub(r'\\dbocttime\{([^}]*)\}', r'[Daybreak, Oct 9, 2026, \1]', s)
    s = re.sub(r'\\cjad\{([^}]*)\}', r'[CJAD, Aug 20, 2025, \1]', s)
    s = re.sub(r'\\dbnov\{([^}]*)\}', r'[Daybreak, Nov 6, 2025, \1]', s)
    s = re.sub(r'\\doc\{[^}]*\}\{([^}]*)\}', r'\1', s)
    s = s.replace('\\%', '%').replace('\\$', '$')
    s = s.replace('\\textsuperscript{er}', 'er')
    s = s.replace('{,}', ',').replace('\\,', ' ').replace('~', ' ')
    s = re.sub(r'\\ldots\\\s', ' … ', s); s = s.replace('\\ldots', '…')
    for pat, ch in [(r"\\'\{?e\}?", 'é'), (r"\\'\{?E\}?", 'É'), (r"\\`\{?e\}?", 'è'), (r"\\`\{?a\}?", 'à'),
                    (r"\\\^\{?o\}?", 'ô'), (r"\\\^\{?a\}?", 'â'), (r"\\\^\{?e\}?", 'ê'), (r"\\c\{c\}", 'ç')]:
        s = re.sub(pat, ch, s)
    s = s.replace('``', '“').replace("''", '”')
    s = re.sub(r'\\begin\{minipage\}\[t\]\{\\linewidth\}', '', s); s = re.sub(r'\\end\{minipage\}\\vspace\{[^}]*\}', '', s)
    s = re.sub(r'\\textbf\{([^}]*)\}', r'\1', s); s = re.sub(r'\\emph\{([^}]*)\}', r'\1', s)
    s = s.replace('$-95$ \\%', '−95 %').replace('$-95$\\%', '−95%').replace('\\$', '$').replace('\\%', '%').replace('--', '–')
    return re.sub(r'\s+', ' ', s).strip()

def build_txt(tex, out, head, tag, lang):
    src = open(tex, encoding='utf-8').read()
    a = src.index('\\begin{enumerate}'); b = src.index('\\end{enumerate}')
    items = [i.strip() for i in src[src.index(']', a) + 1:b].split('\\item') if i.strip()]
    lines = head + ['']
    for it in items: lines += [detex(it), '']
    lines.append(('Version ' if lang == 'en' else 'Version ') + tag)
    txt = '\n'.join(lines) + '\n'
    assert '{' not in txt and '\\' not in txt, re.findall(r'.{25}[{\\].{25}', txt)
    open(out, 'w', encoding='utf-8').write(txt)
    print(f'{out}: {len(items)} points, version {tag}')

def main():
    no_stamp = '--no-stamp' in sys.argv
    tag = datetime.now(ZoneInfo('America/Toronto')).strftime('%Y-%m-%d-%H-%M-%S')
    LANGS = [l for l in ('en', 'fr') if os.path.exists(f'{HERE}/{SUMMARIES[l]}')]
    for lang in LANGS:
        extract(f'{HERE}/{SUMMARIES[lang]}', f'{HERE}/{EXTRACTS[lang]}')
    files = [SUMMARIES[l] for l in LANGS] + [EXTRACTS[l] for l in LANGS]
    if not no_stamp:
        for f in files: stamp(f'{HERE}/{f}', tag)
    else:
        tag = re.search(r'\\newcommand\{\\docversion\}\{([^}]*)\}', open(f'{HERE}/{SUMMARIES["en"]}', encoding='utf-8').read()).group(1)
    for f in files: compile_tex(f)
    for lang in LANGS:
        build_txt(f'{HERE}/{EXTRACTS[lang]}', f'{HERE}/{EXTRACTS[lang][:-4]}.txt', TXT_HEAD[lang], tag, lang)
    print('version tag:', tag)

if __name__ == '__main__':
    main()
