# Tables of the press record (built by build_tables.py from events.csv and page_log.csv)

A record of what the digitized newspapers reported, not a census. The collection thins sharply after the 1960s: the later decades are a floor.

## Confirmed deaths by decade of the event and age group

| Decade | under 10 | 10 to 14 | under 15, place not printed | under 15, listed apart | 15 to 17 | 15 to 17, bridge | 14 or 15 (papers differ) | not given |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1890s |  |  |  |  |  |  |  | 1 |
| 1910s |  | 1 |  |  |  |  |  |  |
| 1920s |  | 8 |  |  | 1 |  |  | 1 |
| 1930s |  | 8 | 1 | 2 | 12 |  |  | 1 |
| 1940s | 2 | 13 | 1 |  | 8 | 2 | 1 |  |
| 1950s | 2 | 13 | 4 |  | 2 |  |  | 1 |
| 1960s | 2 | 9 | 1 |  | 1 |  |  |  |
| 1970s | 1 | 1 | 2 |  |  |  |  |  |
| 1980s |  | 2 |  |  |  |  |  |  |
| 1990s |  | 1 |  |  |  |  |  |  |
| 2000s | 1 |  |  |  |  |  |  |  |
| **All** | **8** | **56** | **9** | **2** | **24** | **2** | **1** | **4** |

Under 15 with the collision on the island: **64** (8 under 10, 56 aged 10 to 14): 62 with a road vehicle (39 truck or other heavy motor vehicle, 14 car, 1 taxi, 4 bus or trolleybus, 3 horse-drawn vehicle, 1 car and horse-drawn vehicle); 1 none (a fall); 1 tram. Listed apart by the author's rulings (protocol amendment 8) and in no count: 1 (drowning), 1 (tricycle). Horse-drawn vehicles are counted only where the page says so; in the 1910s and 1920s « camion » was also used of a horse-drawn dray, so their number is a minimum. For 1 of these deaths (March 28, 1967) the reports differ on whether he was riding or walking beside his bicycle; kept in the count (amendment 8e).

## Under 15, with the municipality inferred where it is not printed (protocol amendment 7)

Of the 9 deaths under 15 whose item does not print where the collision took place, 5 are placed on the island and 4 off it, from the street names, the hospital and the home towns printed; the basis of each is in `events.csv`, column `inference_basis`. Both counts are kept.

| Decade | Place printed or streets named | Inferred on the island | Both | Inferred off the island |
|---|---:|---:|---:|---:|
| 1910s | 1 |  | 1 |  |
| 1920s | 8 |  | 8 |  |
| 1930s | 8 | 1 | 9 |  |
| 1940s | 15 | 1 | 16 |  |
| 1950s | 15 | 2 | 17 | 2 |
| 1960s | 11 |  | 11 | 1 |
| 1970s | 2 | 1 | 3 | 1 |
| 1980s | 2 |  | 2 |  |
| 1990s | 1 |  | 1 |  |
| 2000s | 1 |  | 1 |  |
| **All** | **64** | **5** | **69** | **4** |

With the inferred rows: **69** under 15 on the island: 65 with a road vehicle (39 truck or other heavy motor vehicle, 16 car, 1 taxi, 4 bus or trolleybus, 3 horse-drawn vehicle, 1 car and horse-drawn vehicle, 1 vehicle, kind not stated); 2 none (a fall); 1 tram; 1 versions differ (a car, or no vehicle).

## The other party, deaths under 15 with the collision on the island (column `other_party_class` of `events.csv`, assigned from what the page prints)

| Other party | As printed | With the inferred rows |
|---|---:|---:|
| truck or other heavy motor vehicle | 39 | 39 |
| car | 14 | 16 |
| bus or trolleybus | 4 | 4 |
| horse-drawn vehicle | 3 | 3 |
| none (a fall) | 1 | 2 |
| car and horse-drawn vehicle | 1 | 1 |
| tram | 1 | 1 |
| taxi | 1 | 1 |
| vehicle, kind not stated |  | 1 |
| versions differ (a car, or no vehicle) |  | 1 |
| **All** | **64** | **69** |

## What the 368 issues opened showed (383 rows: an issue can hold two events)

| Result on the page | Rows |
|---|---:|
| cyclist killed, collision on the island | 187 |
| cyclist killed, off the island | 100 |
| not a cyclist | 38 |
| cyclist not killed (injured, or outcome not stated) | 32 |
| cyclist killed, place unclear or a bridge | 16 |
| mode not stated | 10 |
