# Off-street parking on rue de Terrebonne as built: the 1954–55 fire-insurance plans

**Issuer of the source:** Underwriters' Survey Bureau, Limited (Toronto and Montreal), *Insurance plan of the city of Montreal*, volume 7, sheets 739-2, 739-3, 739-4, 739-5, 775, 784-1, 784-2, 785-1, 787-5, 787-6, 787-7, 789-12, 789-13, 789-14, 789-15, 789-16 and 798-3. **Dates on the sheets:** « Montreal, vol. 7, November 1954 » (most sheets), « April 1955 » (775), « December 1955 » (739-4). **Scale:** 100 feet to 1 inch (sheet 785-1 at 200 feet to 1 inch). **Date obtained:** 2024 (scans of an archival copy, item 174390; the holding institution is to be confirmed). **Derived work:** this folder, October 25, 2026; counts, tables, maps, a note and a web page by the repository's author.

**View:** [web page](https://openmobilitydata.github.io/Terrebonne-open-sources/1954-underwriters-plans-terrebonne-garages/) · [note (PDF)](derived/terrebonne_garages_1954_note_en.pdf) · [table, one row per building](derived/buildings_geo.csv) · maps: [on the City's parcels](derived/figures/terrebonne_garages_1954_map_city_en.png) ([PDF](derived/figures/terrebonne_garages_1954_map_city_en.pdf), [FR](derived/figures/terrebonne_garages_1954_map_city_fr.png)) · [on the 1954–55 sheets](derived/figures/terrebonne_garages_1954_map_underwriters_en.png) ([PDF](derived/figures/terrebonne_garages_1954_map_underwriters_en.pdf), [FR](derived/figures/terrebonne_garages_1954_map_underwriters_fr.png)).

## What the plans show

Each sheet draws every building with its construction, number of storeys and civic number, and writes *Auto* or *Autos* on every garage: in the basement (*Auto Bt*, *Autos Bast*), attached, or detached in the yard. Driveways without a garage are not marked. Each sheet carries the printed notice:

> This plan is the property of the UNDERWRITERS' SURVEY BUREAU, LIMITED, (unauthorized reproduction prohibited) and is loaned on the following conditions: that the plan is to be kept in good order, that it is to be used only in connection with business of Companies, Members of the Canadian Underwriters' Association and is to be returned on request to the UNDERWRITERS' SURVEY BUREAU, LIMITED, Toronto and Montreal.
>
> COPYRIGHT REGISTERED AT OTTAWA BY THE UNDERWRITERS' SURVEY BUREAU, LIMITED, TORONTO AND MONTREAL

Sheet 787-8 (south side of Terrebonne between Hampton and Melrose, the Royal and Draper blocks) is missing from the copy available and from every other copy found.

## Status of the scans (why `raw/` is empty)

The scans are not reproduced here. The facts bearing on their status, recorded without a legal opinion: the sheets are dated 1954–55 and name a corporate author; under Canada's Copyright Act the term for a work whose author is not an identified natural person ran, until December 30, 2022, to the end of the 50th year after first publication (s. 6.1 as it then stood), which for a 1954–55 publication would have ended in 2004–2005; the 2022 extension to 70 years did not revive terms that had already expired; if an individual surveyor were held to be the author, the term would instead run from that person's death. Whether the copies digitized by archives are offered as public domain or under conditions is for the holding institution to state. The excerpts used in the map with the 1954–55 underlay (the frontage strip of each sheet, at reduced resolution, as the evidence behind a count) are the part of the source the derived work is about; the fair-dealing provisions of the Act (ss. 29–29.2: research, private study, education, criticism, review, news reporting, with the source and author named) are the provisions a reader would weigh. The full-resolution scans stay with the author.

## Method

1. **Reading.** Every building on the Terrebonne block faces, both sides, from the west end of the protected lane (Belmore) to avenue Girouard, was read from the scans at two to four times magnification into `derived/buildings_1954.csv` (one row per building: sheet, side, block, cross streets, civic numbers, building type, the street it is addressed on, corner lot, garage yes/no, kind of garage, presumed access, confidence, notes). The unit is the building with a Terrebonne civic number; a semi-detached pair is two buildings. Corner buildings addressed on the cross street are listed and left out of the share, as are the churches, the presbytery and the vacant frontages.
2. **Georeferencing.** Each sheet is fitted to the City's géobase (CC-BY 4.0) by a similarity transform on the pixel positions of its Terrebonne intersections (`derived/controls.csv`, `derived/georef.py` → `sheet_transforms.json`); residuals 0–4 m (one at 7 m). Checked by drawing the City's assessment-roll parcels over each sheet.
3. **Join to the City's roll.** Each row is matched to the *unités d'évaluation foncière* (CC-BY 4.0) by civic number and street, or by position for corner buildings renumbered on the cross street since 1954 (`derived/buildings.py` → `derived/buildings_geo.csv`, with the unit id, position, dwelling count and year of construction). Unmatched rows are placed schematically along their block face (`match` = schematic).
4. **Tables, maps, note, page.** `derived/summary.py` (→ `summary.json`, `summary.txt`), `derived/maps.py` (both maps, EN and FR; the 1954 underlay needs the scans), `derived/build_note.py` (the note in LaTeX → PDF and `index.html`).

## Results (October 25, 2026)

| | Buildings addressed on Terrebonne | With a garage as built | Share |
|---|---|---|---|
| North side | 90 | 57 | 63 % |
| South side (sheet 787-8 missing) | 36 | 18 | 50 % |
| **Both sides** | **126** | **75** | **60 %** (59.5) |
| High-confidence readings only | 97 | 60 | 62 % |
| Dwellings in the same buildings (City roll, 121 buildings matched) | 324 | 192 | 59 % |

Of the 75 garages: 46 basement, 14 detached, 15 attached or in an annex; the door opens on Terrebonne for 64, on either street for 10 corner lots, on a rear lane for 1. Also on the block faces: 28 corner buildings addressed on the cross street (13 with a garage), 2 churches, the presbytery, 2 vacant frontages. Years of construction from the roll: 118 of 121 matched buildings date from 1955 or earlier (median 1932).

**Caveats:** garages, not driveways (a lower bound for "driveway or garage as built"); as built in 1954–55, not as used today (conversions in both directions since, and the size of old garages); buildings, not households; one sheet missing; readings graded medium are flagged row by row.

## Files

| Path | Content |
|---|---|
| `derived/buildings_1954.csv` | The reading, one row per building (161 rows incl. corner and non-residential buildings) |
| `derived/buildings_geo.csv` | The same rows joined to the City's roll: unit id, lon/lat, position along the street (u, v), dwellings, year of construction, match method |
| `derived/controls.csv`, `derived/sheet_transforms.json` | Control points and the fitted transform of each sheet |
| `derived/terrebonne_intersections_geobase.csv`, `derived/terrebonne_lane_geobase.geojson`, `derived/geobase_terrebonne_bbox.geojson` | Ville de Montréal géobase extracts (CC-BY 4.0), download of 2026-10-14 |
| `derived/city_assessment_units_terrebonne_bbox.geojson` | Ville de Montréal, unités d'évaluation foncière (CC-BY 4.0), download of 2026-10-25, units around the street |
| `derived/summary.json`, `derived/summary.txt` | The tables |
| `derived/figures/` | The two maps, EN and FR, PNG and PDF |
| `derived/terrebonne_garages_1954_note_en.tex` / `.pdf` | The note |
| `index.html` | The web page |
| `derived/*.py` | `frame.py`, `georef.py`, `buildings.py`, `summary.py`, `maps.py`, `build_note.py` |

Third-party data are named with their licence; the scans are not redistributed. Counts and positions are the author's reading and may contain errors; the row-by-row table is meant to let anyone find them.
