# Weather, daylight, snow and bicycle traffic on rue de Terrebonne

How the daily number of bicycles counted on rue de Terrebonne varies with temperature, wind chill, rain, snowfall, snow on the ground, wind, day length and the City's snow-loading operations, from every count series available for the street, each analysed on its own. The folder holds the scripts, the daily tables, the model tables, the figures (English and French), a note and a slide deck. It describes and measures; it makes no recommendation.

**Status: draft of November 10, 2026, under the author's review.** The note and the deck are marked DRAFT until that review is done.

## The count series

The series are never added together and never compared in level: they count different things at different places. What they can share is a relative response (a percentage change).

| Series | What is counted | Period used | Source |
|---|---|---|---|
| King Edward | Bicycles, both directions, **08:00–16:00**, Telraam S2 camera sensor (west of Cavendish) | August 16, 2024 → November 8, 2026 | Citizen-operated sensor, installed by Terrebonne residents; Telraam API pull of November 9, 2026 ([Terrebonne-telraam](https://github.com/OpenMobilityData/Terrebonne-telraam)) |
| Draper | The same, east of Cavendish | September 25, 2024 → January 24, 2026 and May 7 → October 21, 2026 | The same |
| Kensington loop | Bicycles **eastbound**, 24 hours, the borough's Eco-Counter loop | July 27, 2025 → May 10, 2026 | Hourly workbook released June 4, 2026 under access request [2026-300](https://github.com/OpenMobilityData/Terrebonne-access-requests/tree/main/2026-300) |
| BIXI station | Trips starting or ending at « Grand Boulevard / de Terrebonne » (6 m from the lane) | April 15 → November 15 of 2024, 2025 and 2026 (to August 31, 2026) for the models; all days with trips in the charts | BIXI Montréal open data |
| City counters | Bicycles, 24 hours, twelve of the City's permanent loop counters elsewhere in Montréal (none on Terrebonne) | January 1, 2025 → November 6, 2026 | City of Montréal open data, files downloaded November 7, 2026 |

Limits of each series, stated once here and again in the note:

- **Telraam counts in daylight only.** A sensor's daily total covers about 9 hours in December and 16 in June, so the daily total moves with day length even if nobody changes their habits. Every analysis here therefore uses the count in a **fixed window, 08:00 to 16:00**, which is daylight on every day of the year at this latitude. The window leaves out the evening peak. A day is valid when the sensor reported at least 8 hours with at least 6 hours of summed uptime (the rule of the Terrebonne-telraam repository) **and** all eight window hours with an uptime of at least 0.5. Days that fail are left out; nothing is interpolated. Both sensors have gaps (King Edward: no valid day in February 2026; Draper: none from February to April 2026). Whether the API's hourly counts are already scaled for uptime could not be confirmed from Telraam's documentation; the counts are used as delivered.
- **The loop is one site, one year.** The westbound channel under-counts from about March 1, 2026 (see the [note of October 21, 2026](https://github.com/OpenMobilityData/Terrebonne-access-requests/blob/main/2026-581/derived/counter_revisions_and_westbound_channel_2026-10-21.md)), so the models use the eastbound channel, which the hourly release carries to May 10, 2026. The daily table released October 9, 2026 under request 2026-581 (both directions, to August 31, 2026) is used only to list the days excluded (May 29–31, 2026, zeros; June 7–9, 2026).
- **BIXI trips are not bicycles passing a point**, and BIXI publishes no station service dates: a day without a trip is absent from the file, not a zero. The station recorded trips in the winter of 2025–26 and none in the winter of 2024–25.
- **The City counters are a reference for the response to weather elsewhere**, not a measure of anything on Terrebonne.
- **Weather is measured at Montréal-Trudeau airport**, about 9 km from the street: Environment and Climate Change Canada, station MONTREAL INTL A, climate ID 7025251. Daily rain, snowfall and snow on the ground are 24-hour values; the hourly file gives temperature, wind and observed conditions but no hourly precipitation amount.

## Files

| Path | What |
|---|---|
| [`raw/eccc/`](raw/eccc/) | Environment and Climate Change Canada files as downloaded: daily by year (2024–2026), hourly by month (August 2024 → November 2026). Never edited |
| [`scripts/fetch_eccc.py`](scripts/fetch_eccc.py) | Downloads them |
| [`scripts/wx_lib.py`](scripts/wx_lib.py) | Loaders for every series, sunrise and sunset (NOAA equations), Québec public holidays, the wind-chill index, shared figure style |
| [`scripts/bixi_daily.py`](scripts/bixi_daily.py) → [`derived/bixi_daily_terrebonne.csv`](derived/bixi_daily_terrebonne.csv), [`derived/bixi_daily_system.csv`](derived/bixi_daily_system.csv), [`derived/tables/bixi_stations.csv`](derived/tables/bixi_stations.csv) | Daily trips at the station on the lane, and the whole system's trips per day, from BIXI's yearly trip files (read from a local copy, not redistributed) |
| [`scripts/city_counters_daily.py`](scripts/city_counters_daily.py) → [`derived/city_counters_daily.csv`](derived/city_counters_daily.csv), [`derived/tables/city_counters_kept.csv`](derived/tables/city_counters_kept.csv) | The reference series: the twelve City loop counters that report on at least 97 % of days with no run of more than two zero days, summed on the days when all twelve report |
| [`scripts/build_dataset.py`](scripts/build_dataset.py) → `derived/daily_<series>.csv`, [`derived/weather_daily.csv`](derived/weather_daily.csv), [`derived/tables/coverage_by_month.csv`](derived/tables/coverage_by_month.csv) | One table per series: the day's count and validity flags, weather, calendar, day length, snow loading (sector CDN-301 and the borough), lagged snowfall |
| [`scripts/models.py`](scripts/models.py) → [`derived/tables/`](derived/tables/), [`derived/numbers.json`](derived/numbers.json) | Every model and every table (list below) |
| `derived/figures/<type>/` | One folder per figure type, the script beside its PNG and SVG, English and French: `overview`, `temperature-scatter`, `temperature-curve`, `effects`, `season-weather`, `daylight`, `snow-lags`, `breakpoint` |
| [`scripts/build_docs.py`](scripts/build_docs.py) → [`docs/`](docs/) | The note (with a lay summary of at most 300 words, also written to [`derived/lay_abstract_en.txt`](derived/lay_abstract_en.txt)) and the slide deck (English), built from `numbers.json` and the tables |

Tables in `derived/tables/`: `model_summary.csv` (days, dispersion, change-of-slope temperature with its bootstrap interval, slopes, AIC of each variant), `temperature_curve.csv`, `breakpoint_profile.csv`, `effects_main.csv` (rain, snowfall, snow on the ground, wind, day type; main and within-month models; snow loading), `deviance_blocks.csv`, `snow_lags_winter.csv`, `snow_episodes_daily.csv` and `snow_episodes_summary.csv`, `year_terms.csv`, `cross_validation.csv`, `temperature_bands_weekdays.csv`, `loop_window_share_by_month.csv`, `loop_evening_hours_light_dark.csv`, `window_share_by_month.csv`.

## Method, in brief

Each series gets its own negative binomial regression with a log link, so that every effect is a percentage change and the series can be compared without comparing levels. Terms: day type (weekday, Saturday, Sunday or holiday), the Christmas period, the counting year, two annual harmonics for the season, daytime temperature (08:00–16:00) as a line with one change of slope whose position is estimated, rain and snowfall of the day in classes, snow on the ground, daytime wind, and the snowfall of the day before. Standard errors are robust to autocorrelation (Newey–West, seven lags); the interval for the change of slope comes from a moving-block bootstrap (14-day blocks, 300 replicates). Variants: temperature as a spline; wind chill in place of temperature; calendar-month fixed effects in place of the season terms; winter days with seven lags of snowfall and a snow-loading flag; an hourly model of the loop with a darkness term; leave-one-month-out prediction. The note gives the reasons for each choice and what each cannot show.

The earlier MATLAB analyses of the Telraam counts (2024–2026) were read before this work and are listed in the note's appendix with what was kept and what was not; none of that code is in this repository.

## Reproducing

```
~/.venvs/omd/bin/python scripts/fetch_eccc.py
~/.venvs/omd/bin/python scripts/bixi_daily.py            # needs BIXI's yearly ZIP files in ~/Terrebonne-data/third-party/bixi/
~/.venvs/omd/bin/python scripts/city_counters_daily.py   # needs the City's counter files in ~/Terrebonne-data/third-party/montreal-opendata/
~/.venvs/omd/bin/python scripts/build_dataset.py         # needs the sibling clones Terrebonne-telraam (with data/api/) and Terrebonne-access-requests
~/.venvs/omd/bin/python scripts/models.py --boot=300
for f in derived/figures/*/*.py; do ~/.venvs/omd/bin/python "$f"; done
~/.venvs/omd/bin/python scripts/build_docs.py
```

Python 3 with pandas, numpy, scipy, statsmodels, matplotlib and openpyxl; pdflatex for the documents.

## Sources and licences

| Source | Where | Terms |
|---|---|---|
| Environment and Climate Change Canada, historical climate data, Montréal-Trudeau (7025251) | [climate.weather.gc.ca](https://climate.weather.gc.ca/), downloaded November 10, 2026 | [Environment and Climate Change Canada Data Servers End-use Licence](https://eccc-msc.github.io/open-data/licence/readme_en/); files reproduced in `raw/eccc/` with attribution |
| Telraam counts (two citizen-operated sensors) | Telraam API | The counts belong to Telraam and are not republished (see the Terrebonne-telraam README, « Data and licence »); only daily window totals computed from them appear here |
| Borough loop counter, Kensington | Access requests 2026-300 and 2026-581, [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests) | Released under the Act respecting access to documents held by public bodies |
| City snow-removal transactions (`loading_daily.csv`) | City of Montréal open data, via Terrebonne-access-requests `2026-300/derived/` | CC BY 4.0, Ville de Montréal |
| City permanent bicycle counters | [donnees.montreal.ca](https://donnees.montreal.ca/dataset/cyclistes), files of November 7, 2026 | CC BY 4.0, Ville de Montréal |
| BIXI trip history, 2024–2026 | [bixi.com/en/open-data](https://bixi.com/en/open-data/), downloaded November 10, 2026 (the 2026 file was last modified September 29, 2026 and runs to August 31) | The City's portal lists the dataset under CC BY 4.0: « la paternité des données doit être attribuée à BIXI Montréal ». BIXI's own page states no licence. The yearly files are not redistributed here; the daily totals are, attributed to BIXI Montréal |

The author's own work in this folder (text, figures, tables, method) is under CC BY 4.0 and the scripts under the MIT licence, as in the rest of the repository; neither covers the third parties' data.
