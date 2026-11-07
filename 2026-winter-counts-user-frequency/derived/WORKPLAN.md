# Work plan: winter bicycle counts on every sensor, a user-frequency distribution, and the survey in context

Written November 7, 2026 so that the work can be resumed by any session (the owner's Fable quota was at 92 %). Status lines at the bottom are updated at each commit. Conventions: public document (non-partisan, no recommendations, no imputation of motive, every figure with its source and page); English only (note + 16:9 beamer deck), as the owner asked; built by `derived/build_docs.py` on the pattern of `2015-lidar-terrebonne-street-width/derived/build_docs.py`; Python from `~/.venvs/omd` (openpyxl, numpy, scipy, matplotlib).

## Question
Can the winter bicycle counts on rue de Terrebonne (several sensors, overlapping periods) yield a distribution of individual users by riding frequency, and how does that distribution place the APC-NDG survey's figures (87 respondents cycled on Terrebonne last winter, 36 at least weekly; public filing of Nov 2, 2026) in context? Trips (passages) are the unit of exposure and of the counters; people are the unit of the survey. The document keeps both and never converts one into the other without stating the assumption.

## Sensors and inputs (all read in place, nothing copied but the two extracts in raw/)
| Sensor | Point | What | Period | Source |
|---|---|---|---|---|
| Borough Eco-Counter ZELT EVO loop | Terrebonne/Kensington (45.47022, −73.63204) | hourly, EB (IN_est) and WB (OUT_ouest), motor | Jul 26, 2025 → May 11, 2026 | `Terrebonne-access-requests/2026-300/raw/26072025_11052026.xlsx` (request 2026-300); daily to Aug 31, 2026: `2026-581/derived/kensington_daily_borough_release_2025-07_2026-08.csv` |
| Telraam S2 (owner) | King Edward (west of Cavendish), segment 13374 | hourly, Bike A>B / B>A, uptime; daylight only | Aug 15, 2024 → May 4, 2026 | dashboard exports, private copy `~/GitHub/Terrebonne-private/data/telraam/raw/raw-data-20YYWest60.xlsx` (`TELRAAM_RAW`); counts are Telraam's, only aggregates are published (see Terrebonne-telraam README « Data and licence ») |
| Telraam S2 (owner) | Draper, segment 13690 | same | Sep 24, 2024 → Jan 24, 2026 | `raw-data-20YYEast60.xlsx` |
| City detector det-00118 | Girouard/Terrebonne | hourly + daily, instance -01 = Terrebonne westbound (numeroVoie 1), -02 = Girouard N/S, -03 unlabelled | Oct 23, 2025 → Oct 2026 | City open data « Compteurs cyclistes permanents » (CC-BY 4.0), extract in `raw/city_detector_det-00118_…csv` (rows h and d only) |
| Miovision one-day counts | Grand and Cavendish | by approach, six peak hours and 12 h | Sep 19, 2024; Jan 29, 2025 | request 2026-581 (`2026-581/derived/miovision_counts_by_mode_2026-581.csv`, pages cited) and 2026-634 (by approach: Grand EB 8 / WB 0 in six peak hours, 12 in 12 h; Cavendish 5 / 5) |
| Weather | Montréal-Trudeau 7025251 | ECCC daily | 2024 (`raw/`), 2025–2026 (`2026-300/derived/`) | ECCC |
| Survey | — | 87 winter cyclists, 36 at least weekly, 161 kept, 205 responses | Oct 15 → Nov 2, 2026 | `Terrebonne-open-sources/2026-11-02-apc-survey-filing/` (public figures only; the finer frequency split comes with the Dec 1 filing) |

## Steps (each a function in `derived/winter_counts_analysis.py`, each writing its CSV/JSON/figure; `summary.json` collects every number the documents quote)
1. **Load** every series into one hourly frame (local time) and one daily frame with: weekday/weekend, holiday period (Dec 22 → Jan 4), ECCC snow (cm), mean temperature, snow on ground, daylight hours (NOAA sunrise/sunset at 45.47 N, 73.63 W), Telraam uptime per hour.
2. **Coverage table** per sensor and winter (W1 = Dec 1, 2024 → Mar 31, 2025: Telraam only; W2 = Dec 1, 2025 → Mar 31, 2026: all four; Kensington WB sound to Feb 28, 2026 only; Draper to Jan 23, 2026). Figure: timeline of coverage.
3. **Cross-sensor comparison** on matched hours (same hour, Telraam uptime ≥ 0.7, 8–16 h): ratios Telraam/Kensington by month and by hour of day (a flat ratio by hour = a real gradient, a dip at dawn/dusk = detection loss); Telraam direction mapping by correlation with Kensington EB/WB; Girouard WB vs Kensington WB (daily, hourly profile); the Jan 29, 2025 snapshot (Miovision at Grand and Cavendish, Telraam at King Edward and Draper, same hours). Output: `cross_sensor_ratios.csv`, figures.
4. **Kensington winter structure** (W2): hourly profile weekday/weekend; AM/PM matched round trips per weekday (EB 6–10 h with WB 15–20 h and the reverse); weekday quantiles; response to snow, cold, snow on ground, darkness, holidays; month trend; lag-1 autocorrelation of weekday residuals. Output `kensington_winter_days.csv`, figures.
5. **Model-free bounds** on distinct users: people ≥ max daily passages / m (m = 2 and 4), at each point and corridor-wide (max over points); trips corridor-wide between the largest point and the sum of points.
6. **Frequency-band model**: daily passages Y_d ~ NegBin(μ_d), μ_d = Σ_b N_b · p_b(day type, weather) · c_b, three bands defined by response templates (most weekdays / 1–3 days a week / a few times a month), fitted by maximum likelihood on W2 Dec 1 → Feb 28 totals + the matched-pairs series; profile-likelihood intervals; three template variants (sensitivity); the same fit on the Telraam series of W1 and W2 at King Edward (daylight factor) for the year-over-year check. Output `band_fit.csv`, figure of fitted vs observed, the implied share of passages by band.
7. **Corridor scaling**: people at Kensington → corridor, with the cross-sensor ratios (bounds, not a point estimate).
8. **Survey in context**: passages implied by the survey's 36 weekly + 51 occasional under stated riding-day assumptions (range), against the counted passages; coverage of each band by the survey (count / modelled people), the person-weighted vs passage-weighted distributions, the mode-shift answers in trips. Output `survey_context.csv`.
9. **Documents**: `build_docs.py` → `winter_counts_user_frequency_note_en.pdf` (A4) and `…_deck_en.pdf` (16:9); README with provenance, file table, Pages links; evidence-graph nodes (t_ nodes) in the same commit if the graph session allows, else listed here as to-do.

## Status
- [x] Folder, raw extracts (Girouard det-00118 h/d rows; ECCC 2024), this plan — Nov 7, 2026
- [x] winter_counts_analysis.py steps 1–8 (summary.json, CSVs, figures) — Nov 7 (snow-day ratio check and the frequent-core profile added the same day)
- [x] build_docs.py, note (12 pp., technical abstract + lay summary) + deck (16 slides) + lay_abstract_en_short.txt (in the note) and lay_abstract_en_long.txt — Nov 7
- [x] README, root README row — Nov 7
- [ ] Owner's review of the note and deck (publication grade: wording, the template choices, the snow-day finding); then evidence-graph nodes (t_winter_counts_bands, t_snowday_ratio, t_corridor_gradient, t_distinct_users_floor) and the .github profile map
- [ ] Open questions recorded in the note: the snow-day divergence (a side-by-side video check at the loop on a snow day); a passage-weighted intercept at the counting point; the Telraam direction split (unresolved); the Dec 1 survey report's finer frequency categories once public
