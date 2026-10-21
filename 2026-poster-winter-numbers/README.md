# Rue de Terrebonne in winter: the numbers on one page (poster)

**Issuer:** the repository's author (a resident of Côte-des-Neiges–Notre-Dame-de-Grâce), from public records. **Date:** first built October 20, 2026; rebuilt from the data whenever the inputs change (the build date is printed on the page). **Format:** one sheet (11 × 26 in English, 11 × 28 in French; poster or two-page handout), in English and French.

**View:** English [web page](https://openmobilitydata.github.io/Terrebonne-open-sources/2026-poster-winter-numbers/poster_terrebonne_winter_numbers_en.html) · [PDF](poster_terrebonne_winter_numbers_en.pdf) · [preview](poster_terrebonne_winter_numbers_en.png) — Français [page web](https://openmobilitydata.github.io/Terrebonne-open-sources/2026-poster-winter-numbers/poster_terrebonne_winter_numbers_fr.html) · [PDF](poster_terrebonne_winter_numbers_fr.pdf) · [aperçu](poster_terrebonne_winter_numbers_fr.png)

## What it shows

Five numbered panels, each with its sources:

1. **How many use it, month by month.** Median and mean bicycle passages per day for each month, August 2025 to July 2026, with motor vehicles per day, from the borough's counter at Kensington (access request 2026-581, bundle 01, pp. 74–81); the winter window (December 1 to March 31: 4,891 passages, 40 a day, no day without a bicycle).
2. **Speeds on a 30 km/h street.** The 85th-percentile speed (V85) and the share of cars over 30 and over 40 km/h by season, from the two Telraam sensors at King Edward and Draper ([Terrebonne-telraam](https://github.com/OpenMobilityData/Terrebonne-telraam)); daylight hours with at least 20 cars.
3. **What was said, and what the counter shows.** The figures given at council on October 6 and October 19, 2026 ("99 %", "8 … 4 cyclists", "3.6 %") beside the counter's figures (40 a day; 7.6 % of the rest-of-year daily rate; the share-of-year arithmetic), with the violin plot of the winter days.
4. **The weather.** Last winter at Trudeau airport (Environment Canada station 7025251) and the day behind the "8", January 29, 2025, with the citizen sensors' counts that day.
5. **The timeline.** Dated decisions and requests from the 2024 approvals to the December 2026 votes, from the council records and the access-request bundle.

Quotations are checked by ear against the recordings (borough council October 6, 2026, webcast 0k_KZf9uxTk; City council October 19, 2026, rii3nUTuKRE; CBC *Daybreak*, October 9, 2026). Figures are reproducible from [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests) (2026-581, `derived/figures/`) and Terrebonne-telraam.

## How it is built (and kept current)

`python3 build_poster.py` computes every number from the data, fills the two templates and prints the PDFs and previews (Google Chrome headless). Run it after any input changes; nothing on the page is typed by hand except the prose in the templates and the hand-curated files below.

| Input | Where | Feeds |
|---|---|---|
| Counter daily table | `Terrebonne-access-requests/2026-581/derived/kensington_daily_borough_release_2025-07_2026-08.csv` | Panel 1 (monthly medians, means, motor vehicles; winter and year totals), panel 3 (per-day and share-of-year figures) |
| Monthly chart and winter violin (SVG) | `…/2026-581/derived/figures/kensington-monthly/`, `kensington-violins/` (built by their own scripts) | Copied into `poster_assets/` |
| Telraam speeds and daily counts | `Terrebonne-telraam/derived/speeds_by_season.csv`, `daily.csv` (from `scripts/telraam_summaries.py`) | Panel 2; the January 29, 2025 sensor counts in panel 4 |
| Environment Canada daily data, 2025 and 2026 | `…/2026-300/derived/en_climate_daily_QC_7025251_{2025,2026}_P1D.csv` | Panel 4 (last winter; January 29, 2025) |
| Snow-loading results | `…/2026-300/derived/exposure_tables.txt` (from `exposure_analysis.py`) | Panel 4 (loading days in sector CDN-301; share of winter passages on unconstrained days) |
| `timeline.csv` (hand-curated, EN/FR) | this folder | Panel 5 |
| `manual_facts.json` (numbers from analyses outside this build, each with its source) | this folder | The camera counts and their like-for-like comparison, the 2022 traffic volume, the lane width, the season's loading rank |
| `templates/poster_en.html`, `poster_fr.html`, `poster.css` | this folder | The prose, in both languages, with `{{placeholders}}` for every number |

Order after new data: rebuild the figures in the access-requests repository, run `telraam_summaries.py` in the Telraam repository, then `build_poster.py` here; commit all three.

## Files

| File | Content |
|---|---|
| `poster_terrebonne_winter_numbers_{en,fr}.html` | The poster as a web page (the SVG charts in `poster_assets/`) |
| `poster_terrebonne_winter_numbers_{en,fr}.pdf` | One sheet, printed from the page |
| `poster_terrebonne_winter_numbers_{en,fr}.png` | Preview image |
| `build_poster.py`, `templates/`, `timeline.csv`, `manual_facts.json` | The build (see above) |
| `poster_assets/` | The monthly chart and the winter violin plot (SVG, EN and FR), copied from the access-requests repository by the build |
