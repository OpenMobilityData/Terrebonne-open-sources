# Work plan: parking supply and demand around rue de Terrebonne, and the survey's parking answers in context

Companion to `2026-winter-counts-user-frequency/` (same conventions: English note with technical abstract and short lay summary, deck, `summary.json`, figures, scripts; public document, non-partisan, every figure with its source and page). Written November 7, 2026; status at the bottom.

## Question
The APC-NDG survey's parking answers (corridor residents, vehicles, off-street places, where the car was parked last night, winter hardship) are counts of respondents. What do the external measurements say about the population they come from: EXP's 2022 parking inventory and occupancy survey (report of September 2023), the 1954–55 Underwriters' plans with the LiDAR/optical reading of off-street parking, the 2015 LiDAR night and the daytime orthophoto counts of cars at the curbs, the City assessment roll (dwellings), and the five-winter record of snow-removal nights?

## Inputs (read in place)
| Source | What | Where |
|---|---|---|
| EXP 2023 study | supply (report p. 40: 230 WB + 248 EB on Terrebonne; 328 N + 301 S on the cross-street stubs within 50 m); occupancy and vacant places by sector, side and period, Thursday Sept 29 and Saturday Oct 1, 2022 (Tables 3-2 p. 43 and 3-3 p. 48; survey periods p. 4); Table 7-1 p. 88 (475 current, 375 after standards, scenarios 161/172/171); residual capacity Tables 7-2–7-4 pp. 89–90 | `../2023-exp-mobility-study/raw/EXP_…2023.pdf`; transcription `derived/exp2023_parking_tables_transcribed.csv` (PDF page = report page + 11) |
| 1954–55 plans + present day | garage as built / driveway today per building; by dwellings (roll join); cars at the curbs per block (2015 LiDAR night, by eye; daytime orthophoto) | `../1954-underwriters-plans-terrebonne-garages/derived/{summary.json, on_street_cars_by_block.csv, buildings_geo.csv}` |
| City assessment roll | dwellings per unit; the band Somerled–Monkland via the street frame | `~/Terrebonne-data/third-party/montreal-opendata/unites-evaluation-fonciere/terrebonne_bbox_extract.geojson` (CC-BY 4.0); géobase for Somerled/Monkland offsets |
| Survey | anonymized responses as of Nov 7, 2026 (206; public filing of Nov 2 = 205); hardship criteria as in the filing's methods page | `~/Terrebonne-data/survey-responses/anonymized_2026-11-07.csv` (public with the Dec 1 filing) |
| Five winters | loading nights and storm-to-loading nights, Dec 1–Mar 31, 2021-22 to 2025-26 | decision model appendix (scripts/winter_constraint_nights.py; City snow-removal transactions + ECCC), transcribed in the script |

## Steps (functions of `derived/parking_analysis.py`)
1. EXP supply ledger and occupancy: supply per sector/side derived from vacant places and occupancy; occupied cars and vacant places per period on Terrebonne and on the cross-street stubs; the Thursday evening (18:30–19:30) as the residential reference.
2. The curb counts: 2015 LiDAR night and daytime orthophoto per block (29 blocks), both sides, against the block's nominal capacity (length / 6 m) and EXP's sector supply; the converted side.
3. Off-street: the 1954/present-day shares (buildings, dwellings, by side) against the survey's off-street answers (corridor; on Terrebonne; within a block) with binomial intervals.
4. Demand floor from the survey: corridor respondents' vehicles, where parked last night, street parkers, hardship strict/loose, by on-street / within-block.
5. Population: dwellings on Terrebonne and in the band (roll), survey coverage.
6. Winter: the five-winter constraint nights against the hardship answers.
7. summary.json, CSVs, figures; `build_docs.py` → note + deck + lay abstracts (short in the note; long as txt); README; root README row.

## Status
- [x] Folder, plan, EXP tables transcribed — Nov 7
- [ ] parking_analysis.py
- [ ] build_docs.py, note, deck, lay abstracts
- [ ] README, root README row; owner's review; graph nodes
