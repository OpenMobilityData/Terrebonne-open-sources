#!/usr/bin/env python3
"""Fetch the Section D / Schedule 6 rows of the congregations listed in congregations.csv from the yearly « List of charities »
datasets on open.canada.ca (2015–2024), as extracts in ../raw/open-canada/<year>/ with SOURCES.tsv. Uses the API and download
code of the St Monica folder's fetch_open_data.py (same dataset ids). Only the financial file is read; nothing about directors.
Usage: python3 fetch_congregations.py [years]"""
import csv, hashlib, io, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); SM = os.path.join(HERE, '..', '..', '2024-st-monica-cra-t3010', 'derived')
sys.path.insert(0, SM); import fetch_open_data as fod
OUT = os.path.join(HERE, '..', 'raw', 'open-canada'); YEARS = list(range(2015, 2025))
def main():
    years = [int(a) for a in sys.argv[1:]] or YEARS
    bns = {r['bn'] for r in csv.DictReader(open(os.path.join(HERE, 'congregations.csv'), encoding='utf-8'))}
    ids = {int(r['year']): r['dataset_id'] for r in csv.DictReader(open(os.path.join(SM, 'open_canada_datasets.csv'), encoding='utf-8')) if r['dataset_id']}
    os.makedirs(OUT, exist_ok=True); srcp = os.path.join(OUT, 'SOURCES.tsv')
    log = list(csv.DictReader(open(srcp, encoding='utf-8'), delimiter='\t')) if os.path.exists(srcp) else []
    for y in years:
        modified, res = fod.resources(ids[y])
        fin = [r for r in res if r['format'].upper() == 'CSV' and 'financial' in r['name'].lower() and 'outside' not in r['name'].lower() and ('schedule' in r['name'].lower() or '_d_' in r['name'].lower() or 'section_d' in r['name'].lower())]
        if not fin: fin = [r for r in res if r['format'].upper() == 'CSV' and 'financial' in r['name'].lower() and 'outside' not in r['name'].lower()]
        if not fin: print(y, 'no financial file'); continue
        url = fin[0]['url']; fname = os.path.basename(url.split('?')[0]); data = fod.get(url, binary=True)
        rdr = csv.reader(io.StringIO(data.decode('utf-8-sig', 'replace'))); hdr = next(rdr); kept = [row for row in rdr if row and row[0].strip() in bns]
        ydir = os.path.join(OUT, str(y)); os.makedirs(ydir, exist_ok=True)
        with open(os.path.join(ydir, fname), 'w', newline='', encoding='utf-8') as f: w = csv.writer(f); w.writerow(hdr); w.writerows(sorted(kept, key=lambda r: r[0]))
        log = [l for l in log if not (str(l['year']) == str(y) and l['local_file'] == f'{y}/{fname}')]
        log.append(dict(year=y, local_file=f'{y}/{fname}', source_url=url, full_file_bytes=len(data), full_file_sha256=hashlib.sha256(data).hexdigest(), rows_kept=len(kept), dataset_modified=modified, downloaded_utc=datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')))
        print(f'{y} {fname}: {len(kept)} of {len(bns)} found ({len(data)/1e6:.1f} MB)', flush=True)
    with open(srcp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'local_file', 'source_url', 'full_file_bytes', 'full_file_sha256', 'rows_kept', 'dataset_modified', 'downloaded_utc'], delimiter='\t'); w.writeheader(); w.writerows(sorted(log, key=lambda l: (str(l['year']), l['local_file'])))
if __name__ == '__main__': main()
