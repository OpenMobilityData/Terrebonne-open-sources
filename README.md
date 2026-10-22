# Terrebonne open sources

Public documents concerning the protected bike lane on rue de Terrebonne in the borough of Côte-des-Neiges–Notre-Dame-de-Grâce, Montréal, that were **not** obtained under the Access Act: borough and City publications, council records, open data. They are kept here, with their provenance, because many are hard to find, because the pages that carried them move or disappear, and because a document cited in a public analysis should resolve to a stable copy.

This repository is one of three on the same subject:

| Repository | Holds |
|---|---|
| [`Terrebonne-access-requests`](https://github.com/OpenMobilityData/Terrebonne-access-requests) | Records released under Quebec's Access Act, exactly as received, with derived summaries and tables |
| **`Terrebonne-open-sources`** (this one) | Public documents from open sources, as obtained, with their provenance |
| `Terrebonne-private` | Working papers (private) |

## How the repository is organized

```
<year>-<slug>/        one folder per document or set of documents
    README.md         what it is, who issued it, where and when it was obtained, what it says
    raw/              the documents exactly as obtained (file names normalized; content never edited)
    derived/          anything made from them (optional)
```

Rules:

- Nothing in `raw/` is ever modified. A document obtained as an excerpt of a larger bundle is labelled as such, with the bundle identified.
- Every folder README gives the issuing body, the date, the source (URL or council file) and the date obtained, and states whether the source link still works when last checked.
- READMEs describe and quote; they do not evaluate. Analysis, where there is any, is in documents in `derived/` (or in the derived documents of the access-requests repository), never in a README.
- Press articles are not reproduced (copyright); they are cited by title, outlet and date. Broadcast audio and video are not reproduced either; a transcript of an elected official's public statements may be published in `derived/` for criticism and review (fair dealing, *Copyright Act*, s. 29.1), with the source credited and linked.

## Contents

| Folder | Document | Issued by | Date |
|---|---|---|---|
| [`2020-temporary-lanes/`](2020-temporary-lanes/) | Council file of June 22, 2020 approving the "rues, secteurs et corridors à vocation familiale et active" program (the temporary lanes), and the motion of September 8, 2020 to remove the Terrebonne lanes | Arrondissement CDN–NDG | 2020-06 to 2020-09 |
| [`2023-exp-mobility-study/`](2023-exp-mobility-study/) | *Étude de mobilité – rue de Terrebonne* (Les Services EXP inc.), 351 pp., the study behind the 2024 project; the borough's press releases of October 30, 2023 (FR, EN) | Arrondissement CDN–NDG (commissioned); made public with the project announcement | 2023-10-30 |
| [`2020-2021-working-committee/`](2020-2021-working-committee/) | Resolution CA20 170210 creating the Comité de travail pour la mobilité sur la rue de Terrebonne; the committee's recommendations of June 13, 2021; the council file tabling them; the committee's vote results | Arrondissement CDN–NDG; the committee | 2020-09 to 2021-06 |
| [`2024-project-approval/`](2024-project-approval/) | The borough council's offer of February 5, 2024 (CA24 170018, 3–2) and the City council's acceptance of February 19, 2024 (CM24 0179, unanimous, grouped with other boroughs' 2024 works), and the borough's ordinance of June 3, 2024 making Terrebonne one-way for the lanes (CA24 170131, OCA24 17042, unanimous), with the three decisional files | Arrondissement CDN–NDG; Ville de Montréal | 2024-02; 2024-06 |
| [`2025-election-platform/`](2025-election-platform/) | Ensemble Montréal's 2025 election platform (65 pp., Oct 16, 2025): the cycling commitment is « un état des lieux du réseau cyclable »; the CDN-NDG section does not mention Terrebonne; with the City's page listing the borough's cycling facilities (Oct 24, 2025) | Ensemble Montréal; Ville de Montréal | 2025-10-16; 2025-10-24 |
| [`2026-city-audit-and-plan-velo/`](2026-city-audit-and-plan-velo/) | The City's press release of February 10, 2026 announcing the review of four lanes and the Plan vélo revision; the Réalisons Montréal project timeline as of October 14, 2026 | Ville de Montréal | 2026-02-10; 2026-10-14 |
| [`2026-cbc-daybreak-interview/`](2026-cbc-daybreak-interview/) | CBC *Daybreak* interview with Councillor Alexandre Teodoresco: transcript and fact check (EN/FR), with a one-paragraph summary; the audio is CBC's and is linked, not reproduced | CBC Radio One (interview); transcript and fact check by the repository's author | 2026-10-09 |
| [`2026-10-19-city-council/`](2026-10-19-city-council/) | City council of Montréal, October 19, 2026: transcripts, checked by ear, of the four exchanges on rue de Terrebonne (Peter McQueen's question to Alexandre Teodoresco; the public questions of Hannah Bunty, David Gamper and James Bugden, answered by Alan DeSousa and Alexandre Teodoresco); the recording is the City's and is not reproduced | Ville de Montréal (webcast) | October 19, 2026 |
| [`2026-evidence-graph/`](2026-evidence-graph/) | A graph, kept as data (nodes and edges CSV) and drawn two ways, of the public statements, documents, tables and derived figures on the winter conversion, with factual relations only (quoted, dated, sourced); browsable page via GitHub Pages | The repository's author, from the public records listed in its README | from 2026-10-20 |
| [`2026-eco-compteur-partnership/`](2026-eco-compteur-partnership/) | Eco-Compteur's release of June 4, 2026: the City's counter network moves from inductive loops to CITIX-AI Evo camera counting, chosen by tender; counts stay on the open-data platform; quotes the councillor for Loyola with his executive-committee title (optimization, municipal performance, innovation) | Eco-Compteur (Eco-Counter) | 2026-06-04 |
| [`2026-poster-winter-numbers/`](2026-poster-winter-numbers/) | One-page poster, *Rue de Terrebonne in winter: the numbers on one page*: monthly use, speeds, the figures said at council beside the counter's, the weather, the timeline; web page, PDF and preview | The repository's author, from public records | 2026-10-20 |
Two earlier repositories that held some of these files (`Terrebonne-EXP-Report`, `Terrebonne-working-committee`) were retired when this one was created.

## Provenance and use

Borough and City documents reproduced here are public records or publications; open data from the Ville de Montréal is under CC-BY 4.0. The READMEs are published under CC BY 4.0. The repository was assembled by Rick Hoge, a resident of the borough, as a personal project; it represents no position of any organization. Corrections are welcome through the issue tracker. Commits made with an AI assistant are marked as such in the commit log.
