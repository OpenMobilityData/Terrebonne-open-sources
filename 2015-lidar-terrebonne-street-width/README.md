# How wide is rue de Terrebonne? The roadway along the lane, from the City's 2015 LiDAR (note, deck, data)

**Issued by:** the author of these repositories (see the root README), from two City open datasets: the airborne LiDAR of 2015 (« LiDAR aérien 2015 », six 1 km tiles, NAD83(CSRS)/MTM 8, CC-BY 4.0; downloaded October 25, 2026, kept outside the repository, 3.4 GB) and the assessment-unit outlines (« Unités d'évaluation foncière », CC-BY 4.0; the extract in `../1954-underwriters-plans-terrebonne-garages/derived/city_assessment_units_terrebonne_bbox.geojson`). The street frame (lane axis and intersections from the City géobase) is the one built for the 1954–55 plans work.

**Date:** analysis of November 4, 2026.

**Question.** The winter layout adopted by the borough council on November 2, 2026 (file 1266880005) keeps the contraflow protected lane and turns the lane running with traffic into parking; the cross-section the borough's 2023 study drew for that type of layout (EXP 2023, Figure 6-6, p. 72) is 2.4 + 3.5 + 2.4 + 0.5 + 2.0 = 10.8 m from curb to curb. This folder measures the roadway's actual width along the whole lane and, since the evening of November 4, the width of the cross streets, the one-way streets with parking on both sides and a shared lane that the winter layout resembles.

| File | Content |
|---|---|
| [`derived/terrebonne_street_width_note_en.pdf`](derived/terrebonne_street_width_note_en.pdf) | The note: question, data and method, results, EXP's sections, the cross streets (figures and table by street), the table by block, caveats |
| [`derived/terrebonne_street_width_deck_en.pdf`](derived/terrebonne_street_width_deck_en.pdf) | The slide deck (19 slides, 16:9): question, data and method, the profile, cross-sections, the review figure with every curb detection, the west end, EXP's 2023, built and winter sections with a comparison table, the cross streets (five slides), figures, what it means, caveats |
| [`derived/street_width_profile.csv`](derived/street_width_profile.csv) | Every station (every 2 m, 1207 stations): position, block, curb offsets north and south, curb-to-curb width, kept flag, right-of-way and sidewalk zones |
| [`derived/street_width_by_block.csv`](derived/street_width_by_block.csv) | Per block: stations kept, curb-to-curb median, p10, p90, min, max; right-of-way; sidewalk zones |
| [`derived/summary.json`](derived/summary.json) | The totals and the detector's parameters |
| [`derived/figures/street_width_profile_en.png`](derived/figures/street_width_profile_en.png) / [`_fr.png`](derived/figures/street_width_profile_fr.png) | Width along the lane (stations, block medians, the 10.8 m of the 2023 drawing); right-of-way and sidewalk zones |
| [`derived/figures/street_width_sections_en.png`](derived/figures/street_width_sections_en.png) / [`_fr.png`](derived/figures/street_width_sections_fr.png) | Six cross-sections with the curbs found |
| [`derived/figures/street_width_overhead_en.png`](derived/figures/street_width_overhead_en.png) / [`_fr.png`](derived/figures/street_width_overhead_fr.png) | Review figure: the LiDAR ground surface in the street frame (hillshade) with every curb detection and every dropped station, six panels |
| [`derived/figures/street_width_west_end_en.png`](derived/figures/street_width_west_end_en.png) / [`_fr.png`](derived/figures/street_width_west_end_fr.png) | The first 200 m at the Loyola campus end, widths written every 20 m |
| [`raw/exp2023_fig3-1_configuration_2023.png`](raw/exp2023_fig3-1_configuration_2023.png), [`raw/exp2023_fig6-6_amenagement_A.png`](raw/exp2023_fig6-6_amenagement_A.png), [`raw/exp2023_fig6-7_amenagement_B.png`](raw/exp2023_fig6-7_amenagement_B.png), [`raw/exp2023_fig6-8_amenagement_C.png`](raw/exp2023_fig6-8_amenagement_C.png) | EXP 2023's cross-sections, cropped from the published study (report pp. 25 and 72; PDF pp. 36 and 83): the 2023 street (2.2 + 3.3 + 3.3 + 2.2 = 11.0 m), Aménagement B as built (10.8 m), A (the winter layout's type, 10.8 m), C (10.8 m) |
| [`derived/width_profile.py`](derived/width_profile.py) | The analysis (needs the ground raster built by pdal for the 1954–55 work, outside the repository, and the sibling folder's `frame.py` and `mtm.py`) |
| [`derived/cross_street_blocks.csv`](derived/cross_street_blocks.csv) | The cross streets, per block (first block north and south of Terrebonne, 53 blocks at 28 streets): stations kept, most frequent reading, median, p10, p90, one-way status, block length, parking-sign poles per side and those with « \A EN TOUT TEMPS » |
| [`derived/cross_street_profile.csv`](derived/cross_street_profile.csv) | The cross streets, every station (every 2 m from 20 to 240 m past the intersection): curb offsets left and right, width, kept flag, MTM 8 coordinates |
| [`derived/cross_street_summary.json`](derived/cross_street_summary.json) | The totals for the cross streets (local one-way blocks, two-way boulevards, Terrebonne's own stations for comparison) and the detector's parameters |
| [`derived/figures/cross_street_widths_en.png`](derived/figures/cross_street_widths_en.png) / [`_fr.png`](derived/figures/cross_street_widths_fr.png) | Width of the first block north and south of Terrebonne, street by street: most frequent reading, median, 10th–90th percentiles; Terrebonne's 11.0 m and the winter section's 8.3 m |
| [`derived/figures/cross_street_widths_hist_en.png`](derived/figures/cross_street_widths_hist_en.png) / [`_fr.png`](derived/figures/cross_street_widths_hist_fr.png) | Every station kept: the local cross streets against Terrebonne |
| [`derived/figures/cross_street_widths_review_en.png`](derived/figures/cross_street_widths_review_en.png) / [`_fr.png`](derived/figures/cross_street_widths_review_fr.png) | Review figure: the ground surface along every block with every curb detection |
| [`derived/cross_street_widths.py`](derived/cross_street_widths.py) | The cross-street analysis (same raster and detector; the géobase for the cross streets' axes; the sign inventory) |
| [`derived/build_docs.py`](derived/build_docs.py) | Builds the note and the deck from the outputs of both scripts |

## Method

The ground raster is the mean elevation of ground-class LiDAR returns on a 0.25 m grid along the corridor (pdal; pipeline in the data folder's README). A cross-section is sampled every 2 m along the lane's axis from its west end to Girouard, 16 m each side of the axis, every 0.1 m. Scanning outward from the axis on each side, the curb is the first place between 3 and 8 m from the axis where the ground rises by at least 7 cm over 0.5 m (a Montréal curb face is 10 to 15 cm high; a 1:12 driveway ramp rises 4 cm over that distance and does not pass, though a steeper apron sometimes does); its position is the point of steepest rise in that window. The LiDAR was flown at night with cars parked at the curbs, and under a car or a dense tree there are no ground returns: a station is kept only when both curbs are found and the width lies between 9 and 13 m (759 of 1207). The right-of-way is the distance between the first parcel outline on each side of the same section line; the sidewalk zone is the parcel line to the curb.

## Results

- Curb to curb: median 11.0 m over the 759 stations kept; p10 10.7 m, p90 12.4 m (the high tail is aprons taken for curbs). Block medians from 10.8 to 11.35 m.
- Right-of-way: 20.09 m at every block but the Belmore stub and three lots (the 66-foot standard, 20.12 m). Sidewalk zones, parcel line to curb: 4.4 m north, 4.73 m south.
- EXP's Figure 3-1 (report p. 25) draws the 2023 street as 1.8 + 2.2 + 3.3 + 3.3 + 2.2 + 1.8 m: 11.0 m curb to curb, the LiDAR's figure; Aménagement B as built (Fig. 6-7) and A, the winter layout's type (Fig. 6-6), both use 10.8 m of it.
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

## The cross streets

**Question (added November 4, 2026, evening).** Most of the streets that cross Terrebonne between the lane's west end and Girouard are one-way local streets with parking on both sides and a single lane shared by cars and bicycles: the arrangement the winter layout gives the direction riding with traffic, without the contraflow lane (2.0 m) and its buffer (0.5 m). The winter section leaves 8.3 m for parking, shared lane and parking (2.4 + 3.5 + 2.4). How wide are the cross streets, and do they share a typical width?

**Method.** The same ground raster and the same curb detector, applied to the first block of each cross street on each side of Terrebonne (the géobase segments that meet the intersection), from 20 m past the intersection (clear of the curb returns) to 240 m or the block's end: a cross-section every 2 m, 14 m each side; the curb window 2.5 to 8 m from the axis (11 m for the three two-way boulevards, Cavendish, Grand and Girouard); a station kept when both curbs are found and the width lies between 5 and 13 m (22 m for the boulevards). 53 blocks at 28 streets, 5,397 stations, 3,749 kept. A lowered curb at a driveway apron, or a curb hidden under a tree, makes the detector read the next rise further out, so a block's readings have a tight core and a tail toward wider values, never narrower: the figure reported per block is the most frequent reading (0.2 m bins), with the median and the 10th–90th percentiles beside it. The City's parking-sign inventory (« Signalisation – Stationnement », October 23, 2026 copy) gives, for each side of each block, the number of sign poles within 12 m of the axis and the number carrying « \A EN TOUT TEMPS ».

**Results.**

- The local cross streets (47 blocks, all one-way; 46 with ten or more stations kept) read 9.0 to 9.4 m curb to curb: over all their stations the most frequent reading is 9.1 m and the median 9.4 m; block by block, 42 of 46 lie between 8.9 and 9.6 m. The others: Belmore south 8.8 m; Coronation south 7.9 m; Prince-of-Wales south 11.0 m (a 69 m stub, 10 stations); Madison north 12.5 m (42 of 110 stations kept, 33 % of them within 0.5 m of that reading: low confidence).
- Every local block has parking signs on both sides, with at most 3 « \A EN TOUT TEMPS » poles per side (the corner clearances): parking on both sides, under the time restrictions the signs give, is the rule.
- The three two-way boulevards are wider: Cavendish 16.5–16.6 m, Grand 15.8–15.9 m, Girouard 13.9 m.
- Rue de Terrebonne itself: 11.0 m (most frequent reading 10.95 m, median 11.0 m), 1.6 to 2.0 m wider than its local cross streets.
- The arithmetic: the winter section spends 2.5 m on the contraflow lane and its buffer and leaves 8.3 m for parking, shared lane and parking. A cross street of 9.0 to 9.4 m with the same two 2.4 m parking bands leaves 4.2 to 4.6 m for its shared lane. The 3.5 m shared lane the winter layout draws on Terrebonne is 0.7 to 1.1 m narrower than the lane the cross streets give the same arrangement. In the part that a cyclist riding with traffic uses, the cross streets are about a metre wider than the winter layout.

Most frequent reading / median (m) and stations kept, first block north and south of Terrebonne; \* = fewer than half the stations within 0.5 m of the most frequent reading; signs = parking-sign poles left + right of the block's axis (« \A EN TOUT TEMPS » poles in brackets).

| Street (west to east) | direction | north block | signs | south block | signs |
|---|---|---|---|---|---|
| Belmore | one-way | 9.2 / 9.3 (59) | 5+4 (0) | 8.8 / 9.0 (82) | 5+5 (0) |
| Coronation | one-way | 9.3 / 9.4 (74) | 4+4 (1) | 7.9 / 8.2 (67) | 4+4 (1) |
| Mayfair | one-way | 9.3 / 9.4 (76) | 6+3 (0) | 9.3 / 9.4 (71) | 3+3 (0) |
| Mariette | one-way | 9.3 / 9.5 (74) | 4+7 (0) | 9.1 / 9.1 (78) | 5+4 (2) |
| Rosedale | one-way | 9.6 / 9.7 (90) | 6+2 (0) | 9.3 / 9.6 (87) | 4+3 (0) |
| King-Edward | one-way | 9.3 / 9.6 (66) | 3+6 (0) | 9.0 / 9.3 (79) | 5+6 (1) |
| Montclair | one-way | 9.0 / 9.3 (79) | 3+3 (0) | 9.3 / 9.3 (79) | 4+2 (0) |
| Walkley | one-way | – (3) | 3+2 (4) | 9.3 / 9.6 (69) | 0+0 (0) |
| Prince-of-Wales | one-way | 9.3 / 9.4 (71) | 5+4 (0) | 11.0 / 11.0 (10) | 1+2 (0) |
| Cumberland | one-way | 9.3 / 9.4 (61) | 4+3 (0) | – | – |
| Cavendish | two-way | 16.5 / 16.7 (63) | 4+3 (0) | 16.6 / 16.6 (14) | 1+1 (0) |
| Bessborough | one-way | 9.1 / 9.3 (32) | 4+5 (5) | – | – |
| Benny | one-way | – | – | 9.0 / 9.3 (91) | 12+7 (2) |
| Madison | one-way | 12.5 / 10.8 (42)\* | 3+3 (0) | 9.0 / 9.3 (78) | 4+3 (0) |
| Kensington | one-way | 9.3 / 9.4 (81) | 4+4 (0) | 9.3 / 9.7 (80) | 3+4 (0) |
| Grand | two-way | 15.9 / 16.1 (98) | 2+4 (0) | 15.8 / 15.9 (86) | 5+4 (0) |
| Beaconsfield | one-way | 9.4 / 9.4 (84) | 5+5 (2) | 9.4 / 9.4 (104) | 7+7 (0) |
| Hingston | one-way | 9.3 / 9.3 (75) | 5+5 (2) | 9.1 / 9.4 (68) | 4+5 (0) |
| Hampton | one-way | 9.1 / 9.3 (78) | 4+3 (1) | 9.1 / 9.3 (86) | 7+6 (0) |
| Royal | one-way | 9.3 / 9.3 (93) | 4+3 (0) | 9.1 / 9.3 (98) | 6+6 (0) |
| Draper | one-way | 9.0 / 9.2 (57) | 3+4 (1) | 9.1 / 9.2 (77) | 3+5 (1) |
| Melrose | one-way | 9.1 / 10.5 (80)\* | 3+5 (0) | 9.1 / 9.3 (88) | 5+3 (0) |
| Wilson | one-way | 9.1 / 9.4 (60) | 3+4 (0) | 9.1 / 9.2 (96) | 4+4 (0) |
| Harvard | one-way | 9.2 / 9.6 (93) | 4+4 (1) | 9.3 / 10.8 (79)\* | 4+4 (0) |
| d'Oxford | one-way | 9.1 / 9.2 (77) | 4+3 (0) | 8.9 / 9.6 (81)\* | 5+3 (1) |
| Marcil | one-way | 9.4 / 9.4 (90) | 3+6 (0) | 9.1 / 9.4 (76) | 10+6 (0) |
| Old Orchard | one-way | 9.1 / 9.3 (65) | 5+7 (2) | 9.1 / 9.3 (71) | 9+8 (2) |
| Girouard | two-way | 13.9 / 13.9 (30) | 4+2 (2) | – (3) | 0+0 (0) |

**Caveats, for this part.** The cross streets' parking bands are not marked: cars park at the curb, and a parked car takes 2.0 to 2.2 m with its mirrors, so the 2.4 m band is the drawing's figure applied for comparison. Snow windrows narrow Terrebonne and its cross streets alike. Only the first block on each side is measured. The sign counts are an indicator of the parking regime, not a reading of the regulations.

## Caveats

One reading is good to about 0.2 m (the grid is 0.25 m); the block medians are the figures to use. Blocks with few kept stations carry more uncertainty. The surface is 2015 and the markings 2024: the curbs have not moved; the markings are not in the LiDAR. The right-of-way is the City's parcel geometry, not a survey. Stations hidden by parked cars or trees are left out, not interpolated.

## Third-party sources

Ville de Montréal open data (CC-BY 4.0): LiDAR aérien 2015 (https://donnees.montreal.ca/dataset/lidar-aerien-2015), unités d'évaluation foncière, géobase. Nothing is redistributed here but the derived tables and figures.
