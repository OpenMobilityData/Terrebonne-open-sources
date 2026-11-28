#!/usr/bin/env python3
"""Checks that this folder's README still matches its files and the folders it depends on. Run before every commit that
touches this folder or one of the folders listed in dependencies.csv:

  python3 derived/check_folder.py        (from the folder; needs pdfinfo and git)

It reports, and exits with status 1 on any problem:
  1. links: every relative link of the README points to a file or folder that exists; every link into raw/ points to a
     file that exists, and a « #page=N » does not exceed the file's page count;
  2. orphans: every file under raw/ is linked from the README at least once;
  3. table: every row of derived/arterial_check.csv is in the README as printed;
  4. dependencies: for each row of derived/dependencies.csv whose « depends_on » is a path of this repository, the path
     exists, and its last commit is not later than « last_checked » (otherwise the statement must be re-read and the date
     updated); external dependencies are listed with their date and their « recheck_when » for a reader to act on.
"""
import csv, os, re, subprocess, sys
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); REPO = os.path.dirname(H); NAME = os.path.basename(H)
readme = open(os.path.join(H, 'README.md'), encoding='utf-8').read()
PAGES = f'https://openmobilitydata.github.io/Terrebonne-open-sources/{NAME}/'
bad = []
def npages(p):
    out = subprocess.run(['pdfinfo', p], capture_output=True, text=True).stdout
    m = re.search(r'^Pages:\s+(\d+)', out, re.M); return int(m.group(1)) if m else 0
linked = set()
for target in re.findall(r'\]\(([^)\s]+)\)', readme):
    if target.startswith(PAGES): rel = target[len(PAGES):]
    elif target.startswith('http'): continue
    else: rel = target
    path, _, frag = rel.partition('#')
    full = os.path.normpath(os.path.join(H, path))
    if not os.path.exists(full): bad.append(f'link to a missing file or folder: {target}'); continue
    linked.add(full)
    m = re.match(r'page=(\d+)', frag)
    if m and full.endswith('.pdf') and int(m.group(1)) > npages(full): bad.append(f'page beyond the end of the file: {target}')
for root, _, files in os.walk(os.path.join(H, 'raw')):
    for fn in files:
        if os.path.join(root, fn) not in linked: bad.append(f'file not linked from the README: {os.path.relpath(os.path.join(root, fn), H)}')
for r in csv.DictReader(open(os.path.join(H, 'derived', 'arterial_check.csv'), encoding='utf-8')):
    row = f"| {r['street']} | {r['borough']} | {r['facility_type']} | {r['protected_four_season']} | {r['facilities']} | {r['metres_on_arterial_segments']} | {r['metres_on_other_segments']} |"
    if row not in readme: bad.append(f'table row not in the README as printed: {row}')
print('Dependencies:')
for d in csv.DictReader(open(os.path.join(H, 'derived', 'dependencies.csv'), encoding='utf-8')):
    dep = d['depends_on']
    if dep.startswith('http'):
        print(f"  external, checked {d['last_checked']}: {dep}\n      re-check when: {d['recheck_when']}"); continue
    base = H if dep.startswith('derived/') else REPO
    if not os.path.exists(os.path.join(base, dep)): bad.append(f'dependency missing: {dep}'); continue
    last = subprocess.run(['git', '-C', REPO, 'log', '-1', '--format=%cs', '--', os.path.relpath(os.path.join(base, dep), REPO)], capture_output=True, text=True).stdout.strip()
    state = 'ok' if (not last or last <= d['last_checked']) else 'CHANGED SINCE THE LAST CHECK'
    print(f"  {dep}: last commit {last or 'none yet'}, checked {d['last_checked']}: {state}\n      re-check when: {d['recheck_when']}")
    if state != 'ok': bad.append(f"{dep} changed on {last}, after the last check ({d['last_checked']}): re-read « {d['statement_in_readme']} » and update last_checked")
print('\n'.join('PROBLEM: ' + b for b in bad) if bad else 'No problem found.'); sys.exit(1 if bad else 0)
