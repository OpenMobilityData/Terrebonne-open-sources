# Readings of private parking, lot by lot: FIRST PASS, NOT USED

**Status (November 11, 2026): this first pass failed its checks and no figure in the note, the deck or the
folder README rests on it.** It is kept as the record of what was tried.

- **Frame:** `../tables/offstreet_frame.csv`, the 2,358 buildings with at least one dwelling whose lot lies in the
  corridor's 22 dissemination areas (96 of six dwellings or more), each attached to a strip (one side of one street
  segment) and numbered on it. Built by `../../scripts/offstreet_strips.py`, which also renders the strips from the
  Gouvernement du Québec's continuous aerial imagery (kept outside the repository).
- **Protocol:** `PROTOCOL.md` (version 1).
- **Readers:** eleven independent AI readers (the assistant's subagents), each given the protocol, a list of strips
  drawn at random (`batches.csv`, `todo_batch_NN.csv`) and nothing else. Batches 1 to 10 cover every strip once;
  batch 11 is a second reading of one strip in ten. Files `batch_NN.csv`, as written by the readers.
- **Collation and checks:** `../../scripts/offstreet_readings.py` → `../tables/offstreet_readings.csv`,
  `offstreet_readings_second_pass.csv`, `offstreet_reading_checks.csv`.

## What the checks show

| Check | Result |
|---|---|
| Buildings read | 2,358 of 2,358: driveway yes 1,030 (44 %), no 707 (30 %), unclear 621 (26 %) |
| Readers | « unclear » from 14 % to 44 % of a reader's rows; « low confidence » from 37 % to 77 % |
| Two readings of the same building, both decisive (122 buildings) | 91 % agree; every disagreement is no (first) against yes (second) |
| Two readings of the same building, either one unclear | 67 of 189 |
| Places, two readings of the same 189 buildings | 205 against 287 |
| Against the reading of October 25, 2026 of rue de Terrebonne (112 buildings, both decisive) | 53 % agree: no better than chance |

## Why

1. **Shade.** On the streets of paired duplexes the only car surface is a passage between two buildings, in full
   building shadow on leaf-off imagery; readers could not tell a driveway from a walkway.
2. **Shared driveways.** The protocol gave a passage shared by two lots to the lot holding most of its width and
   « no » to the other, so half of the lots served by a shared driveway were read as having none.
3. **Short front pads.** The protocol counted from the lot line; many front pads and basement-garage ramps lie
   partly on the public strip between the lot line and the sidewalk, with a car standing on them, and were read
   « no ».
4. **Long side passages.** « One car per 5 m » gave four or five places in tandem for a single-width passage.
5. **Rendering.** On one strip (1320240L1) three lots fall outside the image; large lots are cut by the image edge.
6. **No ground truth.** The October 25 reading was one reader's, from above, and is not a standard either: on the
   strips looked at again, each reading is wrong in places.
