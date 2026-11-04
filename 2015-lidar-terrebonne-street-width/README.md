# How wide is rue de Terrebonne? The roadway along the lane, from the City's 2015 LiDAR (note, deck, data)

**Issued by:** the author of these repositories (see the root README), from two City open datasets: the airborne LiDAR of 2015 (« LiDAR aérien 2015 », six 1 km tiles, NAD83(CSRS)/MTM 8, CC-BY 4.0; downloaded October 25, 2026, kept outside the repository, 3.4 GB) and the assessment-unit outlines (« Unités d'évaluation foncière », CC-BY 4.0; the extract in `../1954-underwriters-plans-terrebonne-garages/derived/city_assessment_units_terrebonne_bbox.geojson`). The street frame (lane axis and intersections from the City géobase) is the one built for the 1954–55 plans work.

**Date:** analysis of November 4, 2026.

**Question.** The winter layout adopted by the borough council on November 2, 2026 (file 1266880005) keeps the contraflow protected lane and turns the lane running with traffic into parking; the cross-section the borough's 2023 study drew for that type of layout (EXP 2023, Figure 6-6, p. 72) is 2.4 + 3.5 + 2.4 + 0.5 + 2.0 = 10.8 m from curb to curb. This folder measures the roadway's actual width along the whole lane.

| File | Content |
|---|---|
| [`derived/terrebonne_street_width_note_en.pdf`](derived/terrebonne_street_width_note_en.pdf) | The note (3 pp.): question, data and method, results, the table by block, caveats |
| [`derived/terrebonne_street_width_deck_en.pdf`](derived/terrebonne_street_width_deck_en.pdf) | The slide deck (10 slides, 16:9): question, data and method, the profile, cross-sections, the review figure with every curb detection, the west end, figures, what it means, caveats |
| [`derived/street_width_profile.csv`](derived/street_width_profile.csv) | Every station (every 2 m, 1207 stations): position, block, curb offsets north and south, curb-to-curb width, kept flag, right-of-way and sidewalk zones |
| [`derived/street_width_by_block.csv`](derived/street_width_by_block.csv) | Per block: stations kept, curb-to-curb median, p10, p90, min, max; right-of-way; sidewalk zones |
| [`derived/summary.json`](derived/summary.json) | The totals and the detector's parameters |
| [`derived/figures/street_width_profile_en.png`](derived/figures/street_width_profile_en.png) / [`_fr.png`](derived/figures/street_width_profile_fr.png) | Width along the lane (stations, block medians, the 10.8 m of the 2023 drawing); right-of-way and sidewalk zones |
| [`derived/figures/street_width_sections_en.png`](derived/figures/street_width_sections_en.png) / [`_fr.png`](derived/figures/street_width_sections_fr.png) | Six cross-sections with the curbs found |
| [`derived/figures/street_width_overhead_en.png`](derived/figures/street_width_overhead_en.png) / [`_fr.png`](derived/figures/street_width_overhead_fr.png) | Review figure: the LiDAR ground surface in the street frame (hillshade) with every curb detection and every dropped station, six panels |
| [`derived/figures/street_width_west_end_en.png`](derived/figures/street_width_west_end_en.png) / [`_fr.png`](derived/figures/street_width_west_end_fr.png) | The first 200 m at the Loyola campus end, widths written every 20 m |
| [`derived/width_profile.py`](derived/width_profile.py) | The analysis (needs the ground raster built by pdal for the 1954–55 work, outside the repository, and the sibling folder's `frame.py` and `mtm.py`) |
| [`derived/build_docs.py`](derived/build_docs.py) | Builds the note and the deck from the outputs |

## Method

The ground raster is the mean elevation of ground-class LiDAR returns on a 0.25 m grid along the corridor (pdal; pipeline in the data folder's README). A cross-section is sampled every 2 m along the lane's axis from its west end to Girouard, 16 m each side of the axis, every 0.1 m. Scanning outward from the axis on each side, the curb is the first place between 3 and 8 m from the axis where the ground rises by at least 7 cm over 0.5 m (a Montréal curb face is 10 to 15 cm high; a 1:12 driveway ramp rises 4 cm over that distance and does not pass, though a steeper apron sometimes does); its position is the point of steepest rise in that window. The LiDAR was flown at night with cars parked at the curbs, and under a car or a dense tree there are no ground returns: a station is kept only when both curbs are found and the width lies between 9 and 13 m (759 of 1207). The right-of-way is the distance between the first parcel outline on each side of the same section line; the sidewalk zone is the parcel line to the curb.

## Results

- Curb to curb: median 11.0 m over the 759 stations kept; p10 10.7 m, p90 12.4 m (the high tail is aprons taken for curbs). Block medians from 10.8 to 11.35 m.
- Right-of-way: 20.09 m at every block but the Belmore stub and three lots (the 66-foot standard, 20.12 m). Sidewalk zones, parcel line to curb: 4.4 m north, 4.73 m south.
- Against EXP's own statement of the existing section ([report p. 50, PDF p. 61](https://openmobilitydata.github.io/Terrebonne-open-sources/2023-exp-mobility-study/raw/EXP_Etude_de_mobilite_rue_de_Terrebonne_2023.pdf#page=61)): « L'emprise fonctionnelle actuelle de la rue de Terrebonne est d'environ 14,6 m, soit une chaussée d'environ 11 m et deux trottoirs d'environ 1,8 m. » The LiDAR's 11.0 m curb to curb is EXP's « environ 11 m »; EXP's 14.6 m « emprise fonctionnelle » is the roadway plus the two paved sidewalks, not the 20.1 m right-of-way, whose difference (about 2.7 m a side) is the grass strip between sidewalk and curb, which the LiDAR's sidewalk zones (4.4 and 4.7 m from parcel line to curb) include.
- Against the 2023 drawing: 10.8 m of lanes and parking in an 11.0 m roadway, about 0.2 m to spare across the street. Before 2024, two 3.3 m lanes (EXP 2023) and two parking bands of 2.2 m make the same 11.0 m.

| Block (west to east) | kept/stations | curb–curb median (m) | p10–p90 | right-of-way (m) | sidewalk N (m) | sidewalk S (m) |
|---|---|---|---|---|---|---|
| west end – Belmore | 19/30 | 11.0 | 10.7–11.32 | 20.09 | 4.44 | 4.67 |
| Belmore – Belmore | 4/12 | 11.0 | 10.9–11.31 | 28.48 | 4.6 | 12.03 |
| Belmore – Coronation | 13/26 | 10.8 | 10.62–11.66 | 20.09 | 4.5 | 4.82 |
| Coronation – Mayfair | 23/39 | 11.0 | 10.72–12.6 | 20.09 | 4.51 | 4.57 |
| Mayfair – Mariette | 34/45 | 11.0 | 10.7–11.27 | 20.09 | 4.46 | 4.69 |
| Mariette – Rosedale | 34/45 | 10.8 | 10.53–11.24 | 20.09 | 4.59 | 4.7 |
| Rosedale – King-Edward | 27/44 | 11.0 | 10.76–11.78 | 20.09 | 4.46 | 4.63 |
| King-Edward – Montclair | 34/46 | 11.1 | 10.73–12.55 | 20.09 | 4.39 | 4.61 |
| Montclair – Walkley | 26/45 | 11.0 | 10.7–11.25 | 20.09 | 4.46 | 4.72 |
| Walkley – Prince-of-Wales | 22/41 | 11.1 | 10.9–12.78 | 21.94 | 5.54 | 4.88 |
| Prince-of-Wales – Cumberland | 17/36 | 11.0 | 10.8–11.3 | 20.09 | 4.67 | 4.6 |
| Cumberland – Cavendish | 18/37 | 10.85 | 10.67–11.59 | 20.09 | 4.53 | 4.7 |
| Cavendish – Bessborough | 19/37 | 11.0 | 10.6–11.52 | 20.09 | 3.75 | 5.49 |
| Bessborough – Benny | 41/51 | 10.8 | 10.7–11.1 | 20.09 | 3.69 | 5.6 |
| Benny – Madison | 68/79 | 11.0 | 10.7–11.43 | 20.09 | 3.56 | 5.47 |
| Madison – Kensington | 26/42 | 11.1 | 10.7–12.65 | 20.09 | 4.39 | 4.7 |
| Kensington – Grand | 25/42 | 10.9 | 10.7–12.8 | 20.09 | 4.38 | 4.75 |
| Grand – Beaconsfield | 22/44 | 11.0 | 10.71–12.8 | 20.09 | 4.98 | 4.53 |
| Beaconsfield – Hingston | 26/40 | 11.0 | 10.75–12.8 | 20.09 | 4.48 | 4.67 |
| Hingston – Hampton | 28/49 | 11.15 | 10.87–12.73 | 20.09 | 4.34 | 4.66 |
| Hampton – Royal | 27/49 | 11.0 | 10.8–12.52 | 20.1 | 4.38 | 4.75 |
| Royal – Draper | 35/47 | 10.8 | 10.68–11.36 | 20.1 | 4.48 | 4.71 |
| Draper – Melrose | 25/44 | 11.0 | 10.64–11.94 | 20.09 | 4.38 | 4.8 |
| Melrose – Wilson | 25/41 | 11.0 | 10.6–12.6 | 20.1 | 5.23 | 3.97 |
| Wilson – Harvard | 22/38 | 10.9 | 10.61–12.06 | 20.1 | 4.4 | 4.79 |
| Harvard – d'Oxford | 23/40 | 10.9 | 10.8–12.78 | 20.1 | 4.27 | 4.94 |
| d'Oxford – Marcil | 30/39 | 11.0 | 10.7–11.61 | 20.1 | 4.31 | 4.81 |
| Marcil – Old Orchard | 24/39 | 11.0 | 10.56–11.37 | 20.1 | 4.4 | 4.69 |
| Old Orchard – Girouard | 22/40 | 11.35 | 10.8–12.6 | 20.1 | 4.57 | 4.42 |

## The west end

The public street ends where the lane ends, at the Loyola campus boundary (the géobase's last segment, 1320365, ends there; beyond it the roadway is the campus's). The last public block, west end to Belmore, reads 11.0 m curb to curb (19 of 30 stations), a 20.09 m right-of-way and sidewalk zones of 4.4 m north and 4.7 m south: the same section as the rest of the street. It is two-way with no parking on either side. The 2015 surface and the pre-2024 imagery cannot measure the 2024 bike lanes themselves; an 11.0 m roadway holds, for example, two 2.0 m lanes with 0.5 m buffers and two 3.0 m travel lanes (arithmetic, not the marking plan).

## Caveats

One reading is good to about 0.2 m (the grid is 0.25 m); the block medians are the figures to use. Blocks with few kept stations carry more uncertainty. The surface is 2015 and the markings 2024: the curbs have not moved; the markings are not in the LiDAR. The right-of-way is the City's parcel geometry, not a survey. Stations hidden by parked cars or trees are left out, not interpolated.

## Third-party sources

Ville de Montréal open data (CC-BY 4.0): LiDAR aérien 2015 (https://donnees.montreal.ca/dataset/lidar-aerien-2015), unités d'évaluation foncière, géobase. Nothing is redistributed here but the derived tables and figures.
