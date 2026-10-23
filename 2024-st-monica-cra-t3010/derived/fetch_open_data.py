#!/usr/bin/env python3
"""Fetch the parish's rows from the CRA's yearly "List of charities" files on
open.canada.ca and store them as row extracts under ../raw/open-canada/<year>/.

Why extracts: each yearly file holds every registered charity (tens of MB); the
repository keeps only the header and the rows of BN 130341852RR0001, labelled as
an excerpt, with the full file's URL, size and SHA-256 in SOURCES.tsv.

Usage:
  python3 fetch_open_data.py                 # every year marked to_fetch in open_canada_datasets.csv
  python3 fetch_open_data.py 2023 2024       # these years only
  python3 fetch_open_data.py --list 2024     # only list the dataset's resources (no download)

For each dataset the script asks the portal's CKAN API (package_show) for the
resource list, downloads every CSV whose name contains one of KEEP (financial,
general information, identification, programs) to a scratch folder, keeps the
parish's rows and deletes nothing else. Files about directors, trustees or like
officials are never downloaded (names). If the API is refused, it falls back to
the financial_resource_url column of open_canada_datasets.csv.
"""
import csv, hashlib, io, json, os, sys, tempfile, datetime, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'raw', 'open-canada')
CFG = os.path.join(HERE, 'open_canada_datasets.csv')
BN = '130341852RR0001'
KEEP = ('financial', 'general', 'ident', 'program')
SKIP = ('director', 'trustee', 'official', 'donee', 'country', 'countries')
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'

def get(url, binary=False, timeout=600):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode('utf-8', 'replace')

def resources(dataset_id):
    api = f'https://open.canada.ca/data/api/3/action/package_show?id={dataset_id}'
    d = json.loads(get(api))
    p = d['result']
    out = []
    for r in p['resources']:
        name = r.get('name')
        name = name.get('en', '') if isinstance(name, dict) else (name or '')
        out.append(dict(name=name, url=r['url'], format=r.get('format', ''), size=r.get('size')))
    return p.get('metadata_modified', '')[:10], out

def extract(data, year, fname, url, modified, log):
    text = data.decode('utf-8-sig', 'replace')
    rdr = csv.reader(io.StringIO(text))
    hdr = next(rdr)
    kept = [row for row in rdr if row and row[0].strip() == BN]
    ydir = os.path.join(OUT, str(year)); os.makedirs(ydir, exist_ok=True)
    local = os.path.join(str(year), fname)
    with open(os.path.join(OUT, local), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(kept)
    log.append(dict(year=year, local_file=local, source_url=url, full_file_bytes=len(data),
                    full_file_sha256=hashlib.sha256(data).hexdigest(), rows_kept=len(kept),
                    dataset_modified=modified, downloaded_utc=datetime.datetime.now(datetime.UTC).isoformat(timespec='seconds')))
    print(f'  {year} {fname}: {len(kept)} row(s) of the parish kept ({len(data)/1e6:.1f} MB read)')

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    list_only = '--list' in sys.argv
    cfg = list(csv.DictReader(open(CFG, encoding='utf-8')))
    years = [int(a) for a in args] or [int(r['year']) for r in cfg if r['status'] == 'to_fetch']
    os.makedirs(OUT, exist_ok=True)
    srcp = os.path.join(OUT, 'SOURCES.tsv')
    log = []
    if os.path.exists(srcp):
        log = list(csv.DictReader(open(srcp, encoding='utf-8'), delimiter='\t'))
    for row in cfg:
        y = int(row['year'])
        if y not in years:
            continue
        print(f'== {y}')
        modified, res = '', []
        if row['dataset_id']:
            try:
                modified, res = resources(row['dataset_id'])
            except Exception as e:
                print(f'  API not usable ({e}); falling back to the known URL')
        if list_only:
            for r in res: print('   ', r['name'], '|', r['format'], '|', r['size'], '|', r['url'])
            continue
        todo = [r['url'] for r in res if r['format'].upper() == 'CSV' and any(k in r['name'].lower() for k in KEEP)
                and not any(s in r['name'].lower() for s in SKIP)]
        if not todo and row['financial_resource_url']:
            todo = [row['financial_resource_url']]
        if not todo:
            print('  nothing to fetch (no dataset id or URL)'); continue
        for url in todo:
            fname = os.path.basename(url.split('?')[0]) or f'resource_{y}.csv'
            if not fname.endswith('.csv'):
                fname += '.csv'
            print(f'  downloading {url}')
            try:
                data = get(url, binary=True)
            except Exception as e:
                print(f'  FAILED: {e}'); continue
            log = [l for l in log if not (l['year'] == str(y) and l['local_file'] == f'{y}/{fname}')]
            extract(data, y, fname, url, modified, log)
    with open(srcp, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['year', 'local_file', 'source_url', 'full_file_bytes', 'full_file_sha256', 'rows_kept', 'dataset_modified', 'downloaded_utc'], delimiter='\t')
        w.writeheader(); w.writerows(sorted(log, key=lambda l: (str(l['year']), l['local_file'])))
    print(f'SOURCES.tsv: {len(log)} file(s)')

if __name__ == '__main__':
    main()
