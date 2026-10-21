# Evidence graph: public statements, documents, data and derived figures on the Terrebonne winter conversion

**Issuer:** the repository's author (a resident of Côte-des-Neiges–Notre-Dame-de-Grâce), from public records. **Date:** started October 20, 2026; updated as the record grows. **Status:** a working map, not a finished document.

**Browse it:** https://openmobilitydata.github.io/Terrebonne-open-sources/2026-evidence-graph/evidence_graph.html (click a node for its full text, its source and its links; "Columns by type" orders each column by date; "Force layout" shows the clusters). Static drawing: [`evidence_graph.svg`](evidence_graph.svg) / [`evidence_graph.png`](evidence_graph.png).

## What it is

A graph kept as data: [`nodes.csv`](nodes.csv) (one row per statement, document, table, derived figure, agent or event, with its date and its source: page of an access-request bundle, recording time stamp, or file) and [`edges.csv`](edges.csv) (one row per relation; a `note` column states the point of difference for every `differs_from`, `unsupported_by` and `does_not_include` edge, shown in the page's side panel and as a tooltip in the SVG). [`render_graph.py`](render_graph.py) draws both renderings from the two files (Graphviz; Cytoscape.js).

Every statement node quotes words checked by ear against the recording and gives the time; every document and data node gives the page or file; every figure node shows its arithmetic in its label. Relations are a closed list of factual verbs: `attributed_to`, `contained_in`, `released_in`, `withheld_in`, `redacted_in`, `summarized_in`, `precedes`, `implements`, `computed_from`, `states` (a statement gives a figure), `matches` (a statement agrees with a data source), `refers_to`, `echoes`, `sets_aside`, `made_at` (a statement at the sitting, interview or meeting where it was made), `same_day`, `does_not_include`, `unsupported_by` (a stated figure for which the released record holds no count), `differs_from` and `same_data_other_denominator` (two figures from the same data, two readings). No relation expresses a judgment or a motive.

| Node type | Meaning |
|---|---|
| `agent` | who produced or said something |
| `document` | a dated document, released, withheld or redacted |
| `data` | a table or dataset, or a documented absence of one |
| `figure` | a number derived from data by a stated calculation |
| `statement` | a dated public statement, quoted, with its time stamp |
| `event` | a dated step in the process |

## Coverage and checks

The graph is meant to be exhaustive for the question at hand: every checked quotation, every document and table in the record that bears on the winter conversion, and every figure derived from them. Coverage as of October 21, 2026: the October 6, 2026 address and question period (clips 02–06), the CBC Daybreak interview of October 9, the City council exchanges of October 19, the borough mayor's November 26, 2025 answer and the mayor's office's December 12, 2025 reply, the Gazette (Oct 7) and Le Devoir (Oct 19), the 2026-581 bundle (mandate, service request, offer, purchase order, kick-off, scheduling e-mails, draft and final note, decks, camera tables, counter table), the 2025-697, 2026-300 and 2025-12847 releases, the 2024 approvals, the 2023 EXP study, the 2021 working committee, the City's February 10, 2026 release, the Telraam sensors, the City open-data detector, and the author's pending requests and reconsideration letter.

`render_graph.py` checks the structure at every build and writes [`validation_report.txt`](validation_report.txt): no orphan node; every statement has `made_at`, `attributed_to` and a source; every figure has `computed_from`; every bundle-01 document has a release status; every `differs_from`, `unsupported_by` or `does_not_include` edge has a note; and every question in [`questions.csv`](questions.csv) (the written questions prepared for the December 7 sitting, 3.1–3.12, each with the nodes that are its premises) cites nodes that exist. A build with problems still writes the page, and says so.

Rule for additions: a newly checked quotation or newly filed document gets its node and relations in the same commit as the transcript or file.

## Sources

Access request 2026-581 (bundle 01 page numbers) and 2026-300: [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests). Council recordings: borough council of October 6, 2026 (webcast 0k_KZf9uxTk) and City council of October 19, 2026 (rii3nUTuKRE; transcripts in [`../2026-10-19-city-council/`](../2026-10-19-city-council/)). CBC *Daybreak*, October 9, 2026 ([`../2026-cbc-daybreak-interview/`](../2026-cbc-daybreak-interview/)). *Le Devoir*, October 19, 2026. Telraam sensors: [Terrebonne-telraam](https://github.com/OpenMobilityData/Terrebonne-telraam). The APC Zoom meeting node rests on the association's minutes of the meeting the councillor cited at council as his consultation.

## Reproduce

`python3 render_graph.py` in this folder (needs Graphviz `dot`). The page loads Cytoscape.js 3.30.2 from cdnjs and has its data embedded; nothing else is fetched.
