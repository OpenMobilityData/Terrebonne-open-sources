# Cars queued behind a cyclist in a shared winter lane on rue de Terrebonne (note, deck, model)

**Issued by:** the author of these repositories (see the root README), from documents released by the borough under the Access Act and City open data.
**Date:** analysis of November 8, 2026.
**Sources:** the borough's Eco-Counter loop at Terrebonne/Kensington, hourly, July 26, 2025 – May 11, 2026 (request 2026-300, [`raw/26072025_11052026.xlsx`](https://github.com/OpenMobilityData/Terrebonne-access-requests/tree/main/2026-300/raw) in Terrebonne-access-requests); the Miovision count at Terrebonne/Grand of January 29, 2025, by movement (request 2026-634, B2, [`raw/attachments/`](https://github.com/OpenMobilityData/Terrebonne-access-requests/tree/main/2026-634/raw/attachments)); the City géobase street frame of [`../1954-underwriters-plans-terrebonne-garages/`](../1954-underwriters-plans-terrebonne-garages/) (CC-BY 4.0). Context: the borough's file 1266880005 of November 2, 2026 ([`../2026-11-02-borough-council/`](../2026-11-02-borough-council/)), EXP 2023, Figure 6-6 ([`../2023-exp-mobility-study/`](../2023-exp-mobility-study/)), the Highway Safety Code (LégisQuébec, text current to October 15, 2026).
**Obtained:** the released files as cited; nothing new is reproduced here.

## Question

In the winter layout put to the borough council on November 2, 2026, cyclists riding in the direction of motor traffic would share the traffic lane with cars: « Les cyclistes circulant dans le même sens que la circulation seraient alors appelés à partager la voie de circulation avec les véhicules motorisés » (file 1266880005, p. 3). The only drawing of such a layout on the record (EXP 2023, Figure 6-6, p. 72) gives that lane 3.5 m between two parking lanes, which leaves no room to pass a cyclist with the clearance of art. 341. The note estimates how many cars build up behind one cyclist at the winter morning peak, east of Cavendish.

## Files

| File | What it is |
|---|---|
| [`derived/shared_lane_queue_note_en.pdf`](derived/shared_lane_queue_note_en.pdf) (+ `.tex`) | Note (6 pp.): abstract, lay summary, the rules, data, model, results, limits |
| [`derived/shared_lane_queue_deck_en.pdf`](derived/shared_lane_queue_deck_en.pdf) (+ `.tex`) | Slide deck (9 slides) |
| [`derived/lay_abstract_en_long.txt`](derived/lay_abstract_en_long.txt), [`derived/lay_abstract_en_short.txt`](derived/lay_abstract_en_short.txt) | Lay summaries (the short one is in the note) |
| [`derived/summary.json`](derived/summary.json) | Every number in the note and deck |
| [`derived/hourly_flows_winter_weekdays.csv`](derived/hourly_flows_winter_weekdays.csv) | Motor vehicles (mean, 90th percentile) and eastbound bicycles per hour, winter weekdays Dec 1 – Mar 31, 2025-26 (87 days) |
| [`derived/scenarios.csv`](derived/scenarios.csv) | The three cases by distance: expected queue, cars caught, simulation mean, median, 10th–90th percentiles, share with no car behind, mean over the ride |
| [`derived/sensitivity_1km.csv`](derived/sensitivity_1km.csv) | Expected queue after 1 km by cyclist and car speed |
| [`derived/figures/`](derived/figures/) | `hourly_flows_en.png`, `queue_by_distance_en.png`, `sensitivity_1km_en.png` |
| [`derived/queue_analysis.py`](derived/queue_analysis.py) | Reads the released workbooks, runs the model and the simulation, writes the tables, `summary.json` and the figures |
| [`derived/build_docs.py`](derived/build_docs.py) | Builds the note, the deck and the lay summaries from `summary.json` |

## Method and results

Cars catch up with a slower cyclist at λ = q (1/v_bike − 1/v_car) per kilometre ridden; with no passing they queue, and a queued car leaves when it turns off at a cross street (share s at each of the 17 cross streets in the 1.52 km from Cavendish to Girouard). Expected queue (λ/μ)(1 − e^(−μx)), μ = s × cross streets per km; a simulation of the same process gives the spread.

- Flows: 120 motor vehicles at 07:00–08:00 on the 87 winter weekdays (160 on a busy day, 90th percentile), 3.6 eastbound bicycles; the Miovision count at Grand gives 128 eastbound cars an hour between 07:00 and 09:00, 17.5 % of them turning off.
- Central case (cyclist 15 km/h, cars 25 km/h, 7 % turning off at each cross street): 3.2 cars caught per km; 2.2 cars behind after 1 km, 2.8 at Girouard (simulation median 3, 10th–90th percentiles 1–5).
- Range: 0.6 after 1 km (light traffic, fast cyclist) to 8.4 at Girouard (busy morning, slow cyclist on snow).
- Drivers' side: about 12 of the 120 peak-hour cars follow a cyclist, each losing at most 1.6 min per kilometre.

The speeds are assumptions, not measurements; the turn-off share was measured at one intersection; west of Cavendish (westbound) has no comparable count. See the note's « What the estimate leaves out ».

## Reproduce

```
cd derived
~/.venvs/omd/bin/python queue_analysis.py   # needs the sibling clone of Terrebonne-access-requests (openpyxl, matplotlib, numpy)
~/.venvs/omd/bin/python build_docs.py       # pdflatex
```
