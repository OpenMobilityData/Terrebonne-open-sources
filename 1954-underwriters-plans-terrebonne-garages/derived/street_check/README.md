# Street-level check of the buildings addressed on rue de Terrebonne (November 12, 2026)

Every lot addressed on rue de Terrebonne along the lane (154 lots: 141 on the City's assessment roll under Terrebonne, plus 13 corner lots that carried a Terrebonne address in 1954–55 and are now listed under the cross street; frame in `../street_check_frame.csv`) was judged by the author from street-level imagery on November 12, 2026, on a private check page that showed no earlier reading. The check replaces the aerial reading of October 25, 2026 for the present-day figures, because a check of the wider corridor from street-level imagery had found that a reading from above misses driveways.

| File | Content |
|---|---|
| `owner_street_check.json` | The author's answers as exported from the check page (154 lots; fields: car access, kind, parking converted, independent and total places, garage, what the judgment rests on, note) |
| `compare.py` | Joins the answers to the 1954 table and to the October 25 reading; writes the files below |
| `comparison.csv` | One row per building of the October 25 frame: the 1954–55 garage, the October 25 reading, the street check |
| `lots.csv` | One row per lot of the street: the street check, the 1954–55 garage where the building is in the 1954 table |
| `summary.json`, `summary.txt` | The figures |

Conventions: « car access » is yes when at least one private place is usable today; a lot whose parking was turned to another use with none left is car access « no » and parking converted « yes, none left »; « yes, some left » is a partial conversion. Where the 1954–55 plans show a garage they take priority for conversions, because conversions cannot all be seen from the street: a garage as built with no parking today is counted as a conversion with none left; a garage as built, with access today but no garage today, as a conversion with some left (`converted_basis` says which rule applied; the author's own answer is kept in `converted_owner`). The building at 6324 (a single house in 1954–55) now falls inside the school lot at 6440 and holds no dwelling: it is left out of the comparison (122 buildings instead of 123). Garage interiors and the places in the underground garages of the larger buildings are not counted.

Results (`summary.json`): on the 122 buildings, car access today at 99 of the 118 decided (84 %; 81–84 % whatever the 4 undecided are), by dwellings 225 of 259 (87 %); garage as built or access today 110 of 118 (93 %); parking converted: 12 with none left, 16 with some left. The October 25 reading had 79 of 123 (64 %) and 89 of 123 (72 %). Row by row, the aerial « no » became « yes » 32 times and its « yes » became « no » 9 times. Whole street (154 lots): access at 129 of 149 decided (87 %); buildings of five dwellings or fewer: 124 of 143 with access, 165 independent places, 266 with tandem; 5 of the 6 larger buildings have an underground garage.
