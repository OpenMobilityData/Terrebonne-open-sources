# Reading protocol, version 2: can a car be parked off the street on this lot?

One row per numbered lot of each crop. A crop shows up to five neighbouring lots on one side of one street, from the
Gouvernement du Québec's aerial imagery (leaf-off, about 8 cm per pixel), enlarged to **20 pixels per metre** unless
the black band at the bottom of the image says otherwise, with the dark tones lifted so that shaded ground shows.
The street runs along the bottom; the lots are above it. **Yellow outlines** are the lots to read, each with a
yellow number at its rear (the `label`; a `*` marks a building of six dwellings or more) and its civic number. At
20 pixels per metre a car is about 94 pixels long and 38 wide; a walkway is 20 to 30 pixels wide; a single
driveway is 50 to 60 pixels wide.

From the street upward you will usually see: the roadway, the curb, a strip of grass or paving, the sidewalk, a
little more public ground, then the lot line (the bottom of the yellow outline), the front yard and the building.

Read only what the image shows. Do not use outside knowledge of the street. Do not guess what is inside a building.

## The question

**`car_access`: can a car be driven off the street and left standing clear of the sidewalk, on a surface that
serves this lot?** The surface may be:

- the lot's **own driveway** (beside or in front of the building);
- a **shared driveway**: a passage between two buildings, used by both, whichever side of the lot line it lies on.
  **Both lots get `yes`.** Do not give it to one lot only;
- a **front pad**: a paved surface in front of the building where a car fits between the house-side edge of the
  sidewalk and the building (about 4.5 m, 90 pixels, or more), **even if part of it lies on the public ground
  below the lot line**. A car standing there counts as evidence;
- a **rear pad or yard** reached from a lane or from a side street;
- a **parking lot**.

### How to decide, in order of strength of evidence

1. **A car, van or truck standing on such a surface** (not in the roadway): `yes`.
2. **A paved crossing of the public strip**: a band of paving, about 2.5 m wide or more, running from the curb
   across the grass strip and the sidewalk toward the lot (the mouth of a driveway), continuing onto the lot or into
   a passage: `yes`.
3. **A garage** evident at the end of a surface (a detached garage roof behind the building, a ramp going down
   to a basement door, a white temporary car shelter): `yes`.
4. **A passage between two buildings at least 2.3 m wide in all (46 pixels), with none of the above visible**
   (its mouth hidden by shade, a tree or a parked car): `unclear`.
5. A passage narrower than 2.3 m, a walkway, steps, lawn, a garden, a patio with no way in for a car: `no`.

Use `unclear` only for case 4 or when the image truly cannot be read; say why in `notes`.

## Columns

| Column | Values | Rule |
|---|---|---|
| `crop` | as given | |
| `label` | as given | the yellow number, without the `*` |
| `car_access` | `yes` / `no` / `unclear` | as above |
| `kind` | `own driveway` / `shared driveway` / `front pad` / `rear` / `parking lot` / `none` | the main surface; `none` when `car_access` is `no`; for `unclear`, the kind it would be |
| `places_independent` | integer | cars that can stand there **and leave without another car being moved**: an own single-width driveway or a front pad one car wide: 1; each further car width side by side: 1 more; a shared single-width passage: the places on this lot's own ground at the rear (a pad, the front of a garage) that the passage leads to, or 1 if the rear cannot be seen (say « rear hidden » in `notes`); a parking lot: its stalls. 0 when `car_access` is `no`. For `unclear`: the count it would have if it is a driveway. |
| `places_total` | integer | all the cars the surface can hold, one behind another included: one per 5.5 m (110 pixels) of length from the house-side edge of the sidewalk to where the surface ends, times the number of car widths. Never less than `places_independent`. A shared single-width passage itself holds none (parking in it blocks the neighbour): count only this lot's own ground. Garage interiors are not counted. |
| `garage` | `yes` / `no` / `unclear` | `yes` only when a garage is itself visible: a detached garage roof, a ramp down to a door, an entrance to an underground garage. A driveway that simply ends at a wall: `unclear`. A temporary shelter is not a garage: `no`, with a note. |
| `vehicle` | `yes` / `no` | a car, van or truck is standing on this lot's parking surface (including one standing on its front pad partly below the lot line). Vehicles in the roadway do not count. |
| `confidence` | `high` / `medium` / `low` | |
| `notes` | short free text, no commas | what decided it |

## Particular cases

- **Corner lots**: the way in is often from the side street; look along the side of the lot.
- **Buildings of six dwellings or more (`*`)**: look for a parking lot beside or behind, and for a garage ramp.
  Count marked stalls, or cars and empty spaces of the same size. If the parking evidently belonging to the
  building lies just outside the yellow outline, count it and say so in `notes`.
- **Two labels inside one outline**: give both the same reading and say so.
- **An outline cut by the edge of the image**: read what shows; `confidence` = `low`.
- **A boat, a trailer, a container**: evidence of a surface a vehicle reaches, but `vehicle` = `no`.
- Read every numbered lot; never skip a row.
