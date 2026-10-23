# The parish of St Monica's charity returns (T3010), 2008 to 2024

**Issuer:** Canada Revenue Agency (CRA), Charities Directorate: the public part of the registered charity information returns (form T3010) filed by *La fabrique de la paroisse de Sainte-Monique* (account name on the returns « THE FABRIQUE OF THE PARISH OF ST MONICA, ARCHIDIOCESE DE MONTREAL »), business number 130341852RR0001, 6405 rue de Terrebonne, Montréal. **Fiscal years:** ending December 31, 2008 to 2024 (seventeen returns). **Obtained:** 2008–2018 by a data request to the Charities Directorate (web form « Request publicly available data from the List of charities », November 10, 2024), answered by e-mail on December 6, 2024 with four zip files of CSV; 2019–2024 as row extracts of the CRA's yearly open-data files on open.canada.ca (« *year* List of charities », Open Government Licence – Canada), fetched October 23, 2026. **Date of the data:** for the e-mailed years, the CRA's reply: 2008 as of September 7, 2017; 2009 as of June 30, 2018; 2010–2012 as of April 30, 2019; 2013–2016 as of April 30, 2024; 2017–2018 as of October 31, 2024; for the open-data years, the datasets' modification date, October 4, 2026. **Licence:** public information under the *Income Tax Act*, s. 149.1(15), the CRA's reply carrying the disclaimer quoted in the note; the open-data files under the Open Government Licence – Canada. **Link status (October 23, 2026):** the request form is at canada.ca (`/charities-giving/charities/guidance-videos-forms/request-charities-listings.html`); the Charities Listings application (`apps.cra-arc.gc.ca/ebci/hacc/srch/pub/`) shows each year's return in a browser; the portal's dataset pages and download links answered (the API on its `/data/en/api/3/` path; the `/data/api/3/` path answered 504 all day); no 2025 dataset was listed (the CRA has published each year's file late in the following year).

**Read:** [the data note](derived/st_monica_t3010_note_en.pdf) (EN) or [la note de données](derived/st_monica_t3010_note_fr.pdf) (FR): an abstract on what the returns show against the hypothesis of a measurable effect of the 2024 lane and what they cannot test, then provenance, the lines, the method, the figures 2008–2024 described in the return's own terms, what is not here. The tables and charts in `derived/` are their material.

## What it is

Every registered charity files form T3010 each year; its financial section (Section D or Schedule 6) is public and the CRA releases it line by line. The files here are the CRA's own CSV exports of the parish's returns, with the CRA's code lists. The folder exists because the parish stands on rue de Terrebonne and its situation has been raised in the public debate on the 2024 bike lane; the returns are the public record of its finances. The README describes; the note documents and reads the figures in the return's own terms; neither attributes a figure to a cause.

## Files

| Path | Content |
|---|---|
| `raw/cra-charities-listings-2024-12-06/<year>/` | The CSV files of the CRA's reply, unchanged: the financial section (2008: the whole return in one file, `T3010 Return.csv`), general information, programs, qualified donees, schedules 1, 2, 3 and 5, countries (as present for each year) |
| `raw/cra-charities-listings-2024-12-06/references/` | The CRA's code lists sent with the data (categories, programs, designations, provinces, countries, form versions) |
| `raw/cra-charities-listings-2024-12-06/registered-charities-2024-10-31/` | The charity's listing record as of October 31, 2024 (legal and account names, address, contact details of the parish) |
| `raw/open-canada/<year>/` | Row extracts (header + the parish's row) of the yearly open-data files, 2019–2024: the financial section (`financial_d_and_schedule_6_<year>_updated.csv`), general information (sections A–C), identification, programs; `SOURCES.tsv` gives each full file's URL, size, SHA-256, modification date, rows kept and download time; written by `derived/fetch_open_data.py` |
| `raw/open-canada/references/` | The CRA's *List of charities data dictionary* v2.0 (EN/FR) and code list, from the 2024 dataset |
| `derived/t3010_lines.csv` | Every numbered line of every year on file: fiscal year, line, value, text, label, label status, form, source, « as of » date, file |
| `derived/t3010_summary.csv` | The key lines by year, with revenue less expenditures, source and « as of » date |
| `derived/line_labels.csv` | The line numbers with labels (EN/FR) and a status: *checked*, *dictionary* (the CRA's data dictionary), *quick_view*, *form* |
| `derived/figures/` | Four charts, EN and FR, SVG/PNG/PDF: revenue and expenditures; revenue by line; expenditures by line; assets by line |
| `derived/st_monica_t3010_note_en.tex`, `.pdf`, `..._fr.tex`, `.pdf` | The data note, EN and FR (version stamped by the build; `summary_table_en.tex`, `summary_table_fr.tex` are its table) |
| `derived/build.py` | Builds everything above from `raw/` (tables, checks, charts, the note) |
| `derived/fetch_open_data.py`, `open_canada_datasets.csv` | Fetches the parish's rows from the open-data files of a year (`--search` lists the portal's datasets, `--list` a dataset's files, `--extract` takes a file downloaded by hand); the dataset identifiers 2008–2024 with each year's status |
| `derived/manual_entries.csv` | Values typed from the CRA's quick view, if ever needed, each with its date (empty since October 23, 2026) |
| `derived/manual_vintage_check_2026-10-23.txt` | The check of the 2019–2023 transcription (interim source until October 23, 2026) against the files: 113 of 120 values identical, the six differences, the lines in one source only |
| `derived/build_report.txt` | What the last build read and checked |

## Left out, on purpose

Two kinds of file from the CRA's reply are not reproduced: the directors, trustees and like officials listings (form T1235: names of individuals) and the basic contact files (the 2008 one names the parish's contact person). Nothing in this folder names a person. The parish's weekly bulletins, which carried its own financial statements until 2023, are not reproduced either (they name individuals); they are on the parish's website.

## How to update

1. When the CRA publishes the next year's dataset (expected late in the following year), add its identifier to `open_canada_datasets.csv` with status `to_fetch` (`python3 derived/fetch_open_data.py --search` lists the portal's datasets) and run `python3 derived/fetch_open_data.py`.
2. `python3 derived/build.py` rebuilds the tables, the charts and both notes, and reports any disagreement between sources and any arithmetic gap in the returns (one in seventeen years: 2018, asset lines 750,031 vs line 4200 750,051).
3. Extend section 5 of both notes to the new year in the same descriptive style.
