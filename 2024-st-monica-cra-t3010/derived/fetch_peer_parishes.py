#!/usr/bin/env python3
"""Fetch the financial-section rows of the parishes listed in peer_parishes.csv
(the subject parish and the other Catholic parishes, « fabriques », of the same
postal areas, as found in the CRA's 2024 identification file) from the yearly
« List of charities » datasets on open.canada.ca, and store them as extracts in
../raw/open-canada-peers/<year>/ with SOURCES.tsv (full file URL, size, SHA-256,
dataset modification date, rows kept, download time).

Usage:  python3 fetch_peer_parishes.py            # years 2015–2024
        python3 fetch_peer_parishes.py 2023 2024
Only the financial file of each year is read (Section D / Schedule 6); nothing about
directors, trustees or like officials is ever downloaded. Uses the API and download
code of fetch_open_data.py.
"""
import csv, hashlib, io, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_open_data as fod

OUT = os.path.join(HERE, '..', 'raw', 'open-canada-peers')
PEERS = os.path.join(HERE, 'peer_parishes.csv')
DATASETS = os.path.join(HERE, 'open_canada_datasets.csv')
YEARS = list(range(2015, 2025))

def main():
    years = [int(a) for a in sys.argv[1:]] or YEARS
    bns = {r['bn'] for r in csv.DictReader(open(PEERS, encoding='utf-8'))}
    ids = {int(r['year']): r['dataset_id'] for r in csv.DictReader(open(DATASETS, encoding='utf-8')) if r['dataset_id']}
    os.makedirs(OUT, exist_ok=True)
    srcp = os.path.join(OUT, 'SOURCES.tsv')
    log = list(csv.DictReader(open(srcp, encoding='utf-8'), delimiter='\t')) if os.path.exists(srcp) else []
    for y in years:
        print(f'== {y}')
        modified, res = fod.resources(ids[y])
        fin = [r for r in res if r['format'].upper() == 'CSV' and 'financial' in r['name'].lower() and 'outside' not in r['name'].lower()]
        if not fin:
            print('  no financial file listed'); continue
        url = fin[0]['url']; fname = os.path.basename(url.split('?')[0])
        print(f'  downloading {url}')
        data = fod.get(url, binary=True)
        text = data.decode('utf-8-sig', 'replace')
        rdr = csv.reader(io.StringIO(text)); hdr = next(rdr)
        kept = [row for row in rdr if row and row[0].strip() in bns]
        ydir = os.path.join(OUT, str(y)); os.makedirs(ydir, exist_ok=True)
        with open(os.path.join(ydir, fname), 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f); w.writerow(hdr); w.writerows(sorted(kept, key=lambda r: r[0]))
        log = [l for l in log if not (l['year'] == str(y) and l['local_file'] == f'{y}/{fname}')]
        log.append(dict(year=y, local_file=f'{y}/{fname}', source_url=url, full_file_bytes=len(data),
                        full_file_sha256=hashlib.sha256(data).hexdigest(), rows_kept=len(kept), dataset_modified=modified,
                        downloaded_utc=datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')))
        print(f'  {fname}: {len(kept)} of {len(bns)} parishes found ({len(data)/1e6:.1f} MB read)')
    with open(srcp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'local_file', 'source_url', 'full_file_bytes', 'full_file_sha256', 'rows_kept', 'dataset_modified', 'downloaded_utc'], delimiter='\t')
        w.writeheader(); w.writerows(sorted(log, key=lambda l: (str(l['year']), l['local_file'])))

if __name__ == '__main__':
    main()
