# Reading protocol: private parking visible on each building's lot

One row per numbered building of each strip. A strip is one side of one street segment on the Gouvernement du
Québec's continuous aerial imagery (leaf-off, about 8 cm per pixel, resampled at **10 pixels per metre**): the
street runs along the bottom, the lots are above it. **Yellow outlines** are the lots to read, each with a yellow
number (the `label`; a `*` marks a building of six dwellings or more) and its civic number; thin blue outlines are
other lots. A car is about 45 to 50 pixels long and 18 to 20 pixels wide.

Read only what is visible inside the yellow outline (or on a surface shared across its edge). Do not use outside
knowledge of the street. Do not guess what is inside a building.

## Columns

| Column | Values | Rule |
|---|---|---|
| `strip` | as given | |
| `label` | as given | the yellow number, without the `*` |
| `driveway` | `yes` / `no` / `unclear` | `yes` if the lot holds a surface a car can be parked on, reachable from a street or a lane: a driveway, a paved or gravel pad, a garage apron or ramp, a parking lot. The surface must be at least about 2.3 m wide (23 pixels). A walkway, steps, a patio or terrace with no way in for a car, lawn, a garden: `no`. `unclear` when shade, a tree or image quality hides the answer. |
| `places` | integer, 0 or more | the number of cars that surface can hold on the lot, garage interiors NOT counted: one car per 5 m (50 pixels) of single-width driveway measured from the lot line at the street to where the surface ends (a garage door, the building, a fence); a double-width surface (about 5 m or more) counts twice; a parking lot: count the marked stalls, or the cars and empty spaces of the same size. A surface shorter than a car: 0, and `driveway` = `no`. If `driveway` is `no`: 0. If `unclear`: your best count, and say so in `notes`. A driveway shared by two lots: give each lot the places on its own side of the line; if one width serves both, give it to the lot holding most of it and 0 to the other, with a note on both rows. |
| `garage` | `yes` / `no` / `unclear` | `yes` if a garage is evident from above: a detached garage at the end of a driveway, a driveway ending at the building's wall or running down a ramp to a basement door, an entrance ramp to an underground garage. Its interior places are not counted in `places`. |
| `access` | `front` / `side street` / `lane` / `none` | where the car comes in: the street at the bottom of the strip (`front`), another street the lot touches (`side street`), a rear lane (`lane`); `none` when `driveway` is `no`. |
| `vehicle_on_lot` | `yes` / `no` | a car, van or truck is on the lot at the moment of the photo. |
| `confidence` | `high` / `medium` / `low` | |
| `notes` | free text, short, no commas | what you saw, especially for `unclear`, shared driveways and parking lots. |

## Things to keep straight

- The strip between the sidewalk and the roadway, and the sidewalk itself, are public: the part of a driveway that
  crosses them is not counted. Count from the lot line (the bottom edge of the yellow outline).
- Cars parked on the street (in the roadway at the bottom) are not on a lot.
- A building of six dwellings or more (`*`): look for a parking lot behind or beside it and for a garage ramp;
  count the surface stalls only.
- Read every numbered building; never skip a row. If the outline is cut by the edge of the image, read what shows
  and set `confidence` accordingly.
- Each strip is read on its own, in the order given.
