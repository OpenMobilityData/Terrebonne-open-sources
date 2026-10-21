# Evidence graph: public statements, documents, data and derived figures on the Terrebonne winter conversion

**Issuer:** the repository's author (a resident of Côte-des-Neiges–Notre-Dame-de-Grâce), from public records. **Date:** started October 20, 2026; updated as the record grows. **Status:** a working map, not a finished document.

**Browse it:** https://openmobilitydata.github.io/Terrebonne-open-sources/2026-evidence-graph/evidence_graph.html (click a node for its full text, its source and its links; "Columns by type" orders each column by date; "Force layout" shows the clusters). Static drawing: [`evidence_graph.svg`](evidence_graph.svg) / [`evidence_graph.png`](evidence_graph.png).

## What it is

A graph kept as data: [`nodes.csv`](nodes.csv) (one row per statement, document, table, derived figure, agent or event, with its date and its source: page of an access-request bundle, recording time stamp, or file) and [`edges.csv`](edges.csv) (one row per relation). [`render_graph.py`](render_graph.py) draws both renderings from the two files (Graphviz; Cytoscape.js).

Every statement node quotes words checked by ear against the recording and gives the time; every document and data node gives the page or file; every figure node shows its arithmetic in its label. Relations are a closed list of factual verbs: `attributed_to`, `contained_in`, `released_in`, `withheld_in`, `redacted_in`, `summarized_in`, `precedes`, `implements`, `computed_from`, `states` (a statement gives a figure), `matches` (a statement agrees with a data source), `refers_to`, `echoes`, `sets_aside`, `same_day`, `does_not_include`, `unsupported_by` (a stated figure for which the released record holds no count), `differs_from` and `same_data_other_denominator` (two figures from the same data, two readings). No relation expresses a judgment or a motive.

| Node type | Meaning |
|---|---|
| `agent` | who produced or said something |
| `document` | a dated document, released, withheld or redacted |
| `data` | a table or dataset, or a documented absence of one |
| `figure` | a number derived from data by a stated calculation |
| `statement` | a dated public statement, quoted, with its time stamp |
| `event` | a dated step in the process |

## Sources

Access request 2026-581 (bundle 01 page numbers) and 2026-300: [Terrebonne-access-requests](https://github.com/OpenMobilityData/Terrebonne-access-requests). Council recordings: borough council of October 6, 2026 (webcast 0k_KZf9uxTk) and City council of October 19, 2026 (rii3nUTuKRE; transcripts in [`../2026-10-19-city-council/`](../2026-10-19-city-council/)). CBC *Daybreak*, October 9, 2026 ([`../2026-cbc-daybreak-interview/`](../2026-cbc-daybreak-interview/)). *Le Devoir*, October 19, 2026. Telraam sensors: [Terrebonne-telraam](https://github.com/OpenMobilityData/Terrebonne-telraam). The APC Zoom meeting node rests on the association's minutes of the meeting the councillor cited at council as his consultation.

## Reproduce

`python3 render_graph.py` in this folder (needs Graphviz `dot`). The page loads Cytoscape.js 3.30.2 from cdnjs and has its data embedded; nothing else is fetched.
