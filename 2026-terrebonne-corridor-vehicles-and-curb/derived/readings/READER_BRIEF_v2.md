# Brief for a second-pass reader (replace NN by your batch number, two digits)

You are one of several independent readers of aerial imagery. For each numbered lot on a set of image crops, you
record whether a car can be parked off the street on that lot, following a written protocol exactly. Work alone,
from the images only.

1. Read the protocol in full first:
   /Users/rhoge/GitHub/Terrebonne-open-sources/2026-terrebonne-corridor-vehicles-and-curb/derived/readings/PROTOCOL_v2.md
2. Read your to-do list:
   /Users/rhoge/GitHub/Terrebonne-open-sources/2026-terrebonne-corridor-vehicles-and-curb/derived/readings/v2_todo_batch_NN.csv
   (columns: crop, label, civic_lo, civic_hi, street, dwellings, large, px_per_m). It lists every lot you must read,
   crop by crop, in order. px_per_m is the scale of that crop (20 unless the lot is large).
3. For each crop, open its image with the Read tool:
   /Users/rhoge/Terrebonne-data/third-party/quebec-imagerie/corridor-crops-2026-11-11/<crop>.png
   Look at each yellow-numbered lot in turn: its front (between the sidewalk and the building), each side of the
   building, and its rear. Decide every column of the protocol for it. You may cut and enlarge parts of an image
   into your scratchpad directory if that helps you see; do not change the image's tones.
4. Write your readings to
   /Users/rhoge/GitHub/Terrebonne-open-sources/2026-terrebonne-corridor-vehicles-and-curb/derived/readings/v2_batch_NN.csv
   with exactly this header line:
   crop,label,car_access,kind,places_independent,places_total,garage,vehicle,confidence,notes
   one row per lot of the to-do list, same order, no commas inside notes. Append to the file every few crops so that
   no work is lost.
5. When done, check that the file has exactly one row for every (crop, label) of the to-do list, no duplicate and
   no missing row, that every value is one the protocol allows, that places_total is never less than
   places_independent, and that both are 0 wherever car_access is no. Fix any gap by re-opening the crop.

Rules: do not read any other file in those folders (no other batch's readings, no other table, no earlier
protocol or README), do not use any knowledge of the neighbourhood, do not run git, do not use the network, do not
modify any file other than your v2_batch_NN.csv (and files in your scratchpad). Every row must come from looking at
its crop: never fill a row from a pattern or from a neighbour. If an image cannot be opened, write the row with
car_access=unclear, kind=none, places 0 and 0, confidence=low, notes=image not readable.

Final report (short): the number of crops and rows written; the count of car_access yes / no / unclear; and any
point where the protocol did not tell you what to do, with the crop and label where it arose.
