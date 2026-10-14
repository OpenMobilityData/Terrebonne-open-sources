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
- READMEs describe and quote; they do not evaluate. Analysis belongs in the derived documents of the access-requests repository.
- Press articles are not reproduced (copyright); they are cited by title, outlet and date.

## Contents

| Folder | Document | Issued by | Date |
|---|---|---|---|
| [`2023-exp-mobility-study/`](2023-exp-mobility-study/) | *Étude de mobilité – rue de Terrebonne* (Les Services EXP inc.), 351 pp., the study behind the 2024 project | Arrondissement CDN–NDG (commissioned); made public with the project announcement | 2023-10-30 |
| [`2020-2021-working-committee/`](2020-2021-working-committee/) | Resolution CA20 170210 creating the Comité de travail pour la mobilité sur la rue de Terrebonne; the committee's recommendations of June 13, 2021; the council file tabling them; the committee's vote results | Arrondissement CDN–NDG; the committee | 2020-09 to 2021-06 |

Earlier publications of some of these files (`OpenMobilityData/Terrebonne-EXP-Report`, `OpenMobilityData/Terrebonne-working-committee`) are superseded by this repository.

## Provenance and use

Borough and City documents reproduced here are public records or publications; open data from the Ville de Montréal is under CC-BY 4.0. The READMEs are published under CC BY 4.0. The repository was assembled by Rick Hoge, a resident of the borough, as a personal project; it represents no position of any organization. Corrections are welcome through the issue tracker. Commits made with an AI assistant are marked as such in the commit log.
