# The congregations on rue de Terrebonne in the CRA's charity returns, 2015–2024: is there a pattern after the 2024 lane? (note, data)

**Issued by:** the author of these repositories (see the root README), from the Canada Revenue Agency's « List of charities » open-data files on open.canada.ca (identification file 2024; Section D / Schedule 6 financial files 2015–2024; Open Government Licence – Canada), the City assessment roll (CC-BY 4.0) to place each address, and the borough's 2023 study (EXP, p. 40) for the drop-off zones. Companion to [`2024-st-monica-cra-t3010`](../2024-st-monica-cra-t3010/), whose question it extends to the other places of worship on the street. No information on directors, trustees or like officials is read or kept.

**Date:** analysis of November 7, 2026.

**Question.** If the 2024 lane caused financial hardship to a place of worship through parking, the effect should appear at every congregation on the same frontage in the same year. Which registered charities have an address on rue de Terrebonne along the lane, and does any of them show a 2024 apart from its own earlier years?

**Set.** The 2024 identification file lists three registered charities in the religious categories with a Terrebonne address between the lane's west end and Girouard: the parish of Sainte-Monique (6405, north side), the Yuen Kwok Buddhist Temple (6870, south side, west of Cavendish; returns from fiscal 2022 under BN suffix RR0002; the RR0001 suffix appears in no year) and the Deliverance Church of God 7th Day (a unit in the residential building at 6350; shown apart). No United congregation files at a Terrebonne address: the building EXP calls « Église Rosedale » has no return of its own. Four congregations within the Somerled–Monkland band were identified and set aside (`derived/congregations_band_candidates.csv`), the question being the street itself (owner's scope, Nov 7, 2026).

| File | Content |
|---|---|
| [`derived/terrebonne_congregations_t3010_note_en.pdf`](derived/terrebonne_congregations_t3010_note_en.pdf) | The note (3 pp.): abstract, question, data, method, results by congregation, discussion, reproducibility |
| [`derived/congregations.csv`](derived/congregations.csv) | The set: business number, name, address, class, position on the street frame (u along the lane, v across), side, notes |
| [`derived/congregations_long.csv`](derived/congregations_long.csv) | One row per congregation and fiscal year: lines 4500, 4530, 4610, 4650, 4700, 5100, 4880, 4200, 4350; gifts (4500 + 4530); revenue less expenditures |
| [`derived/summary.json`](derived/summary.json) | Every figure quoted: series, pre-lane base mean and range, 2024 against them, the twelve fabriques' reference changes from the St Monica folder |
| [`derived/figures/terrebonne_congregations_series_en.png`](derived/figures/terrebonne_congregations_series_en.png) | Revenue, gifts and expenditures by fiscal year, one panel per congregation |
| [`derived/congregations_band_candidates.csv`](derived/congregations_band_candidates.csv) | The four congregations within a block, for a later extension |
| [`derived/fetch_congregations.py`](derived/fetch_congregations.py), [`derived/congregations_comparison.py`](derived/congregations_comparison.py), [`derived/build_note.py`](derived/build_note.py) | Fetch (uses the St Monica folder's `fetch_open_data.py` and dataset ids), comparison, note |
| `raw/open-canada/<year>/financial_d_and_schedule_6_<year>*.csv`, [`raw/open-canada/SOURCES.tsv`](raw/open-canada/SOURCES.tsv) | The rows of the three business numbers extracted from each yearly file; URL, size, SHA-256, dataset modification date and download time of each full file |

**Findings.** Sainte-Monique's 2024 revenue ($251k) and gifts ($220k) lie within their 2019–2023 range (+3 % and −3 % against the five-year mean; −6 % against 2023, which places it 9th and 10th of 13 among the fabriques compared in the St Monica folder). The temple's 2024 revenue ($180k, all reported as gifts) is +7 % and its expenditures +23 % against 2022–2023, whose two returns carry identical figures to the dollar (one observation, in effect); 2024 is the highest year of its short series. The Deliverance church's returns are under $12k a year and nil in 2024. On the street itself the pattern test has one comparable congregation besides the parish; neither shows a first lane year apart from its own record. The 2025 returns (CRA open-data file expected in 2026; the folder's watcher reports it) will give the first full calendar year with the lane for both.

**Links.** Folder (this README rendered): `https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-terrebonne-congregations-cra-t3010`. GitHub Pages serves files, not folder indexes, so a folder URL on openmobilitydata.github.io returns 404; the PDFs are served: `https://openmobilitydata.github.io/Terrebonne-open-sources/2026-terrebonne-congregations-cra-t3010/derived/terrebonne_congregations_t3010_note_en.pdf`.

---

*Use of AI: the analysis, the note and this README were prepared with an AI assistant under the author's direction and review; see the repository's [Use of AI statement](../README.md#use-of-ai).*
