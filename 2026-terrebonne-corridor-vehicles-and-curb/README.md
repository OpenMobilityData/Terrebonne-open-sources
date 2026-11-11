# Automobiles and curb along rue de Terrebonne: registered vehicles known by FSA, modelled below it; legal curb measured by block face (note, deck, data) — DRAFT

**Issued by:** the author of these repositories (see the root README). **Status: DRAFT of November 11, 2026, under the author's review; figures may change.**

**Sources.** SAAQ, vehicle files released under the access Act for December 31, 2023 and 2024 (file 03.06.34729), by forward sortation area (FSA), as tabulated in [`Quebec-vehicle-registrations`](https://github.com/OpenMobilityData/Quebec-vehicle-registrations/blob/main/README.md) (`derived/tables/type_by_fsa.csv`; **vehicle type inferred**). Statistics Canada, 2021 Census profile by FSA (98-401-X2021013) and by dissemination area, Québec (98-401-X2021006), and the dissemination-area boundary file (Statistics Canada Open Licence; downloaded November 2026). City of Montréal open data (CC BY 4.0): géobase (downloaded October 14, 2026), « Signalisation – stationnement » (sign inventory, October 23, 2026), « Unités d'évaluation foncière » (assessment roll, October 25, 2026). FSA polygons: DMTI Spatial, CanMap Postal Code Suite v2024.3, and postal-code points: Service Objects (March 2024), both under licence and not redistributed. The 2015 LiDAR night count, the garage and driveway readings and the street frame come from [`1954-underwriters-plans-terrebonne-garages`](../1954-underwriters-plans-terrebonne-garages/); EXP's parking counts from [`2026-parking-supply-demand-survey-context`](../2026-parking-supply-demand-survey-context/).

**Date:** analysis of November 11, 2026.

**Question.** The SAAQ release locates each vehicle to its FSA only; the lane lies in H4B west of Royal and in H4A east of it. What can be said about the dissemination areas that front the lane: how many automobiles are registered there, and how much legal curb do they hold?

**Two kinds of figures, kept apart throughout.** Curb is **measured**, block face by block face, from the sign inventory. Automobiles below the FSA are **modelled** from census variables and scaled so that the areas of each FSA sum to its registered total: within an FSA the split is an estimate with an interval, never a count. The 2015 LiDAR and the imagery are a check, not an input.

| File | Content |
|---|---|
| [`docs/corridor_vehicles_curb_note_en.pdf`](https://openmobilitydata.github.io/Terrebonne-open-sources/2026-terrebonne-corridor-vehicles-and-curb/docs/corridor_vehicles_curb_note_en.pdf) | The note (11 pp.): lay summary, overview map, question, data, method, the two tests of the model, results, the 2015 check, what is and is not shown, tables |
| [`docs/corridor_vehicles_curb_deck_en.pdf`](https://openmobilitydata.github.io/Terrebonne-open-sources/2026-terrebonne-corridor-vehicles-and-curb/docs/corridor_vehicles_curb_deck_en.pdf) | The slide deck (16 slides, 16:9); its figures as PNG files named by slide number in `docs/deck_figures_en/` |
| [`derived/lay_abstract_en.txt`](derived/lay_abstract_en.txt) | The lay summary (300 words), plain text |
| [`derived/numbers.json`](derived/numbers.json) | Every number the note quotes |
| [`derived/tables/da_corridor.csv`](derived/tables/da_corridor.csv), [`.geojson`](derived/tables/da_corridor.geojson) | The 83 dissemination areas with a part in H4A or H4B: households, modelled automobiles with 90 % intervals (and intervals with the unexplained spread doubled), the two alternative specifications, legal curb, places at 5.5 m, the set (corridor or rest), the frontage on Terrebonne |
| [`derived/tables/corridor_sets.csv`](derived/tables/corridor_sets.csv) | Totals for the corridor, the rest and all areas |
| [`derived/tables/block_faces.csv`](derived/tables/block_faces.csv), [`.geojson`](derived/tables/block_faces.geojson) | Every block face of those areas: length, length net of 5 m at each end, length forbidden at all times, legal curb, poles, dissemination area |
| [`derived/tables/curb_by_da.csv`](derived/tables/curb_by_da.csv), [`terrebonne_curb_by_block.csv`](derived/tables/terrebonne_curb_by_block.csv) | Curb by dissemination area; rue de Terrebonne by block and side (the check of the sign reading) |
| [`derived/tables/fsa_model_table.csv`](derived/tables/fsa_model_table.csv), [`da_census.csv`](derived/tables/da_census.csv), [`da_fsa_shares.csv`](derived/tables/da_fsa_shares.csv), [`fsa_households_check.csv`](derived/tables/fsa_households_check.csv) | The census variables by FSA (with the automobiles of 2023 and 2024, inferred) and by dissemination area (census divisions of Montréal and Laval); the share of each area in each FSA; households rebuilt from areas against Statistics Canada's FSA profile |
| [`derived/tables/model_specifications.csv`](derived/tables/model_specifications.csv), [`model_coefficients.csv`](derived/tables/model_coefficients.csv), [`lofo_errors.csv`](derived/tables/lofo_errors.csv), [`downscaling_test.csv`](derived/tables/downscaling_test.csv), [`downscaling_summary.csv`](derived/tables/downscaling_summary.csv), [`fsa_scale_factors.csv`](derived/tables/fsa_scale_factors.csv), [`da_vehicles.csv`](derived/tables/da_vehicles.csv) | The model: specifications compared, coefficients, each FSA left out in turn, the downscaling test, the scale factors, the estimates by area |
| [`derived/tables/lidar_check_by_sector.csv`](derived/tables/lidar_check_by_sector.csv), [`lidar_check_by_da.csv`](derived/tables/lidar_check_by_da.csv) | Cars seen along Terrebonne on the 2015 LiDAR night against the model |
| `derived/figures/<type>/` | `overview-map`, `curb-map`, `area-estimates`, `model-tests`, `curb-and-automobiles`, `lidar-check`: PNG and SVG, English and French, each with its script |
| `scripts/` | `build_dataset.py`, `curb_supply.py`, `demand_model.py`, `corridor.py`, `build_docs.py [--final]`, `corridor_lib.py`, `fig_lib.py` |

![Overview map](derived/figures/overview-map/overview_map_en.png)

## Method, in brief

- **Areas and FSAs.** Dissemination areas do not nest in FSAs; each is shared among FSAs in proportion to the roll's dwellings in each FSA polygon (households rebuilt this way: H4A -1.2 %, H4B -1.2 % against Statistics Canada's FSA profile).
- **Corridor.** The 22 dissemination areas that hold a block face of rue de Terrebonne along the lane; they reach about one block to each side.
- **Legal curb.** Length of each block face, less 5 m at each end (assumption), less the stretches where a sign forbids stopping or parking at all times; arrows read as described in `curb_supply.py`. An upper bound: driveways, hydrants, bus stops, hourly rules, permit zones and seasonal rules are not deducted. Checked on rue de Terrebonne, where the reading finds one parking band (south side west of Cavendish, north side east of it), 1,370 m, 249 places at 5.5 m.
- **Automobiles.** Robust regression of the logarithm of automobiles per household on four census variables across 114 FSAs; prediction for each area; scaling to each FSA's registered total; 2,000 draws for the intervals.
- **Tests** (at the level of FSAs, the only one with registered counts): each FSA left out in turn; neighbouring FSAs grouped by threes and the group's total shared among them.

## Results (draft)

- Registered, by FSA (type inferred): H4A 9,598 automobiles and light trucks, 0.79 per household; H4B 7,351, 0.70.
- Downscaling test: the model's share of a group's total is off by 4.6 % at the median; a split in proportion to households, by 13.9 %. For H4A and H4B taken as a pair the two are close (-4.6 % and +6.0 % against -5.5 % and +7.1 %).
- Corridor, **modelled**: 4,622 automobiles for 5,471 households (90 % interval 4,382 to 4,927), 0.84 per household (0.80 to 0.90); the other areas of the two FSAs, 0.76. A single area's interval is about a quarter of its estimate either way.
- Corridor, **measured**: 46.8 km of curb, 39.3 km legal; 6,554 to 7,865 places at 6 to 5 m (upper bound).
- 0.65 modelled automobile per place of legal curb at 5.5 m. The note states why this ratio is not a measure of parking pressure in either direction (the curb figure is an upper bound; off-street parking is in neither term; where vehicles are kept is not measured).
- 2015 LiDAR night: 436 cars seen at the curbs and on the lots along Terrebonne for 573 dwellings addressed on the street (0.76 per dwelling) against 0.84 modelled per household; the area-by-area comparison shows no relation (rank correlation 0.31, 11 areas).

## Reproduce

```
~/.venvs/omd/bin/python scripts/build_dataset.py
~/.venvs/omd/bin/python scripts/curb_supply.py
~/.venvs/omd/bin/python scripts/demand_model.py --draws=2000
~/.venvs/omd/bin/python scripts/corridor.py
for f in derived/figures/*/*.py; do ~/.venvs/omd/bin/python $f; done
~/.venvs/omd/bin/python scripts/build_docs.py        # --final once the draft mark is lifted
```

The census, roll, sign, géobase and postal-code files are read from outside the repository (`~/Terrebonne-data/third-party/`, paths in `scripts/corridor_lib.py`); the sibling clone `Quebec-vehicle-registrations` supplies the FSA vehicle table. No raw file is kept here (`raw/` is absent: every source is a public dataset named above or a licensed product that is not redistributed).

---

*Use of AI: the analysis, the note and this README were prepared with an AI assistant under the author's direction and review; see the repository's [Use of AI statement](../README.md#use-of-ai).*
