# Readings of private parking, lot by lot

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

---

# Second pass (protocol version 2): read, AWAITING THE OWNER'S CHECK, not yet used

**Status (November 11, 2026): every lot has been read a second time under a corrected protocol and on enlarged
crops. The readers agree with each other far better than in the first pass, but agreement between readers is not
accuracy: no figure in the note, the deck or the folder README rests on these readings until the owner's check of a
random sample (below) is in.**

- **Crops:** `../../scripts/offstreet_crops.py`: 702 crops of up to five neighbouring lots at 20 pixels per metre
  (a building of six dwellings or more, or a large lot, alone at a smaller scale), dark tones lifted;
  `../tables/offstreet_crops.csv`. Images outside the repository.
- **Protocol:** `PROTOCOL_v2.md`; the readers' brief: `READER_BRIEF_v2.md`. Changes from version 1: both lots on a
  shared driveway have access; a front pad counts when a car fits between the sidewalk and the building, even partly
  on public ground; places are recorded as independent (a car can leave without another being moved) and total;
  « unclear » is reserved for a passage wide enough for a car with no car, paved mouth or garage visible.
- **Readers:** thirteen independent AI readers (the assistant's subagents). Batches 1 to 12 cover every crop once
  (`batches_v2.csv`, `v2_todo_batch_NN.csv`, `v2_batch_NN.csv`); batch 13 is a second reading of one crop in ten.
- **Collation and checks:** `../../scripts/offstreet_readings_v2.py` → `../tables/offstreet_readings_v2.csv`,
  `offstreet_readings_v2_second.csv`, `offstreet_reading_checks_v2.csv`.
- **The owner's check:** `owner_check_sample.csv`: 112 lots drawn at random with a fixed seed before any
  second-pass reading existed (100 buildings of five dwellings or fewer, 12 larger), judged by the owner on a
  private check page from street-level imagery or on the street, without seeing any reader's answer
  (`../../scripts/offstreet_check_page.py`). Its export goes in `owner_check.json`.

| Check | Result |
|---|---|
| Lots read | 2,358 of 2,358: car access yes 1,468 (62 %), no 394 (17 %), unclear 496 (21 %) |
| Buildings of five dwellings or fewer (2,262) | yes 1,428, no 364, unclear 470 |
| Buildings of six dwellings or more (96) | yes 40, no 30, unclear 26 |
| Places where access is yes | 1,735 independent, 2,406 total |
| Places where access is unclear (if it is a driveway) | 507 independent, 582 total |
| Readers | yes from 55 % to 73 % of a reader's rows, unclear from 13 % to 31 % |
| Two readings of the same lot, both decisive (174 lots) | 95 % agree (kappa 0.78): yes/yes 146, no/no 19, yes/no 3, no/yes 6 |
| Two readings of the same lot, three values (248 lots) | 84 % agree (kappa 0.70); unclear in either 74, in both 44 |
| Independent places, two readings (248 lots) | 223 against 243; within one place on 99.6 % of lots |
| Total places, two readings | 310 against 318; within one place on 95.6 % |

Points the readers reported as not settled by the protocol (to be ruled on with the owner's check in hand): a
passage lying wholly on the neighbour's side of the lot line; a paved or bare rear yard with no car and no visible
way in; a wide shared passage with room to park on each side; large buildings with a possible underground garage
or with parking just outside their outline; an attached wing that may be a garage; white rectangles that may be
temporary shelters; passages within measuring error (about 0.25 m) of the 2.3 m threshold.
