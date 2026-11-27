# Children on the island of Montréal and in the City of Montréal, by census: what was found

Compiled November 27, 2026, in one sitting. The figures are in `children_island_by_census.csv`, one row per age group as printed, each with its document, table, PDF page, printed page and the row as printed. This note says what was found for each census, what is missing and why, and every boundary caveat. Nothing was read on BAnQ's sites.

## 1. How to read the file

- **Two geographies, never mixed.** `island` = the island as the census names it (« Montreal Island », « Île-de-Montréal », from 1981 the census division « Île-de-Montréal » / « Communauté urbaine de Montréal », in the City's 2006 yearbook « agglomération de Montréal »). `city` = the City of Montréal within its limits at that census. `island with Île-Jésus` = a census division that joins the two islands (1956, 1961, 1966, 1971 county tables). `other` = units recorded only so they are not mistaken for one of the first two (Laval in 1966 and 1971; the 1941 metropolitan area).
- **Nothing is adjusted or harmonized.** The City's limits changed by annexation through the century and again in 2002 and 2006; the island's census unit did not change in area in the years read, but its name and its grouping with Île Jésus did.
- **Rows marked « NOT PRINTED »** are additions of two or four printed figures (5 to 9 plus 10 to 14; males plus females; under 1 plus 1 to 4). They are in the file for convenience and labelled as mine.
- **`read_on`** says whether each figure was read on the page image or only in the text layer.

## 2. A warning about the scans

The census volumes came from the Internet Archive (Statistics Canada's own scans and the University of Toronto's). The Statistics Canada scans are stored with a compression that can replace a digit by a look-alike (6, 8, 9, 0 and 3 are exchanged). It was caught on the 1921 volume: the page image shows 132,670, 02,054, 188,603 and 21,086 where the text layer (made before the compression) and the table's own arithmetic give 132,679, 62,054, 188,693 and 21,686. **Reading the image is therefore not enough for these files.** Every figure taken from them was also checked by the table's arithmetic: males plus females against the total, or the age groups against the printed total, or the island against the joined division less Île Jésus. The check made is stated in the `note` of each row. The 1941 volume III (a colour scan from the University of Toronto) is not affected.

From 1971 on, Statistics Canada rounds every count at random to a multiple of 5, so males plus females can differ from the total by 5 or 10, and two tables of the same bulletin can differ by 5 for the same cell.

## 3. Summary (5 to 14 years is the sum of the two printed groups unless stated)

| Census | Island: total | 0-4 | 5-9 | 10-14 | 5-14 | City: total | 0-4 | 5-9 | 10-14 | 5-14 | Source |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1911 | not attempted | | | | | not attempted | | | | | |
| 1921 | not found by age | | | | | 618,506 | 69,607 (« under 5 ») | not printed | not printed | 132,679 (printed as 5-14) | original |
| 1931 | 1,003,868 | 98,915 | 100,777 | 94,255 | 195,032 | 818,577 | 81,602 | 82,881 | 77,092 | 159,973 | original |
| 1941 | 1,116,800 | 87,420 | 90,943 | 101,288 | 192,231 | 903,007 | 71,882 | 74,624 | 82,870 | 157,494 | original (island printed by sex; sums are mine) |
| 1951 | 1,320,232 | 137,031 | 111,672 | 86,766 | 198,438 | 1,021,520 | 103,080 | 84,607 | 66,953 | 151,560 | original |
| 1956 | 1,507,653 | 158,969 | 140,814 | 114,924 | 255,738 | 1,109,439 | 112,000 | 97,560 | 81,792 | 179,352 | original |
| 1961 | 1,747,696 | 190,329 | 166,117 | 150,261 | 316,378 | 1,191,062 | 120,827 | 103,632 | 96,823 | 200,455 | original |
| 1966 | not printed alone (see 4) | | | | | 1,222,255 | 105,646 | 105,011 | 99,270 | 204,281 | original |
| 1971 | not printed alone (see 4) | | | | | 1,214,350 | 79,375 | 95,080 | 100,510 | 195,590 | original |
| 1976 | 1,869,640 | 106,935 (under 1 + 1-4) | 121,750 | 152,935 | 274,685 | 1,080,545 | 55,455 (under 1 + 1-4) | 62,300 | 80,340 | 142,640 | original |
| 1981 | 1,760,122 | 96,500 | 91,160 | 110,810 | 201,970 | 980,354 | 48,130 | 44,375 | 54,615 | 98,990 | original (by sex; sums are mine; the city from the text layer only) |
| 1986 | 1,752,582 (total only) | | | | | 1,015,420 (total only) | | | | | original (printed in the 1991 profile) |
| 1991 | 1,775,871 | 100,850 | 89,175 | 92,520 | 181,695 | 1,017,666 | 55,150 | 46,135 | 47,115 | 93,250 | original (by sex; sums are mine) |
| 1996 | not obtained | | | | | not obtained | | | | | |
| 2001 | 1,812,723 (total only) | | | | | 1,583,590 (total only, limits of 2006) | | | | | secondary |
| 2006 | 1,854,442 | 94,665 | 92,025 | 99,545 | 191,570 | 1,620,693 | 83,520 | 77,930 | 82,975 | 160,905 | secondary |
| 2011 | 1,886,480 | 0-14 only: 287,635 | | | | 1,649,520 | 0-14 only: 247,975 | | | | secondary |

## 4. 1966 and 1971: the island is not printed alone

In both censuses the county table has a single division « Île-de-Montréal et Île-Jésus ». Printed:

| Census | Unit | Total | 0-4 | 5-9 | 10-14 |
|---|---|---|---|---|---|
| 1966 | Île-de-Montréal et Île-Jésus | 2,119,266 | 209,385 | 212,886 | 189,805 |
| 1966 | Laval (Ville de), c. | 196,088 | 26,220 | 29,215 | 21,815 |
| 1971 | Île-de-Montréal et Île-Jésus | 2,187,155 | 159,505 | 198,560 | 205,095 |
| 1971 | Laval, c. | 228,010 | 19,645 | 29,270 | 29,580 |

The City of Laval, created in 1965, covers Île Jésus. **If, and only if, the reader accepts that the joined division less Laval is the island**, the subtraction gives: 1966, 1,923,178 in all, 183,165 aged 0 to 4, 183,671 aged 5 to 9, 167,990 aged 10 to 14 (351,661 aged 5 to 14); 1971, 1,959,145 in all, 139,860, 169,290 and 175,515 (344,805 aged 5 to 14; the 1971 figures are rounded to 5 and the 5-9 cell is printed 198,560 in one table and 198,565 in another). These subtractions are mine, are not printed in the census, and are **not** in the CSV. The same bulletins list every municipality of the island with its ages (the metropolitan-area table), so the island could also be had by adding its municipalities; that was not done.

## 5. Census by census

- **1911.** Not attempted (time). The printed volumes of the Fifth Census are the place to look.
- **1921.** Volume II (Population: age, conjugal condition …; PDF saved). Its age tables cover the provinces and « cities and towns of 7,500 and over » only: Table 13 gives the City with the groups under 5, 5 to 14, 15 to 24 …, so 5 to 14 is printed but 5 to 9 and 10 to 14 are not (Table 17 gives single years of age for the same cities and would allow it: not read). **No table of ages by county was found in volume II, so the island is missing for 1921.** The bulletin « Age distribution » of the same census (bulletin XV) is on publications.gc.ca, which could not be read (section 6).
- **1931.** Island: volume II (Population by areas), Table 24, by county or census division; « Montreal Island » and « Jesus Island » are separate rows. City: Bulletin XXXVII (cities, towns and villages of 5,000 and over). Volume III (Ages of the people) was also downloaded and has no table by county: it is in the folder but nothing was taken from it.
- **1941.** Island: volume II (Population by local subdivisions), Table 22, where « Montréal Island » and « Jésus Island » are sub-rows of « Montréal & Jésus Islands », printed for males and females only. City: volume III (Ages of the population), Table 13, cities of 30,000 and over. Volume III also gives « Greater Montréal » (the metropolitan area of 1941: 1,139,921), which is not the island.
- **1951.** Volume I, Table 25 (census metropolitan areas): « Montreal Island » and « Montréal, city proper » on consecutive rows.
- **1956.** Bulletin 1-9 (Age groups), Table 20 (census metropolitan areas and component parts). The county table (Table 18) gives the two islands joined: 1,577,063 (text layer only).
- **1961.** Bulletin 1.2-2 (Age groups), Table 24 (metropolitan areas and components) for both; the county table (Table 22) gives « Montreal & Jesus Islands » with the two islands as sub-rows.
- **1966.** Bulletin « Age groups » (92-610): county table joined (section 4); City and Laval in the table of municipalities of 10,000 and over.
- **1971.** Bulletin « Age groups » (92-715): the same situation as 1966.
- **1976.** Bulletin « Five-year age groups » (92-823): « Île-de-Montréal » is again a census division of its own (Table 13); City in Table 15. The first age group is split into « under 1 » and « 1-4 ».
- **1981.** Island: the national volume of census divisions (95-902), Table 1, by sex. City: the Québec volume of census divisions and subdivisions; only its text file was taken (the PDF would have passed the size limit), so the City's 1981 figures are **text layer only**, matched to the row labels by order and checked by their sums. To be confirmed on the page.
- **1986.** No age table found. The totals of the division (1,752,582) and of the City (1,015,420) are printed in the 1991 profile. The 1986 profiles exist in print (Statistics Canada's « Profiles » series); none was located on the Internet Archive in the searches made.
- **1991.** Profile of census divisions and subdivisions in Québec, Part A (95-325), volume 1: « Communauté urbaine de Montréal » (census division) and « Montréal, V », by sex. Volume 2 of the same profile was downloaded first by mistake (the division is in volume 1); it is in the folder and nothing was taken from it.
- **1996.** Not obtained. The profile of census divisions and subdivisions in Québec (95-186-XPB, four volumes) is on the Internet Archive; not downloaded (size limit). Statistics Canada's own pages refused the request (section 6).
- **2001.** Not obtained from Statistics Canada (refused). The City's 2006 yearbook prints the 2001 totals only. A web search summary of Statistics Canada's 2001 Community Profile for census division 2466 (« Communauté-Urbaine-de-Montréal ») showed « Age 5-14 · 194,785 » and a 1996 population of 1,775,846: these come from the search summary, not from a page read, and are not in the CSV.
- **2006.** Secondary: the City's « Annuaire statistique de l'agglomération de Montréal, Recensement de 2006 », which reprints Statistics Canada's counts for the agglomeration and for the City within its limits of 2006 (after the demergers).
- **2011.** Secondary, and only the group 0 to 14: a City profile of July 2015. A web search summary of Statistics Canada's 2011 Census Profile for the division showed a total of 1,886,480 and 106,425 aged 0 to 4 (not read on the page, not in the CSV).

## 6. What could not be reached, and why

- **publications.gc.ca** (Government of Canada Publications), which holds Statistics Canada's scans of every volume and bulletin: the catalogue pages open, but each PDF address answers with a page « Information archived on the Web » whose « Continue to publication » button points back to the same address. With a plain request, and with a cookie jar, the same page came back; the page-fetching tool got « 502 Bad Gateway ». Nothing further was tried. The same volumes were then found on the Internet Archive.
- **Statistics Canada, www12.statcan.gc.ca** (Census Profile 2011, Community Profiles 2001): « 403 Forbidden » to the page-fetching tool, three pages. Not retried.
- **Size limit of the sitting** (about 400 MB): the 1981 Québec subdivisions PDF (12.6 MB), the 1996 profile and the 1986 profiles were left out for that reason; two downloads proved useless (1931 volume III, 48 MB; 1991 profile volume 2, 18.5 MB).

## 7. Secondary compilations consulted

- Ville de Montréal, Montréal en statistiques, « Annuaire statistique de l'agglomération de Montréal, Recensement de 2006 » (used for 2006 and the 2001 totals).
- Ville de Montréal, Montréal en statistiques, « Un portrait des aînés, Ville de Montréal », July 2015 (used for 2011, 0 to 14 only).
- Ville de Montréal, « Population », a one-page sheet of July 19, 2007 on the 2006 age pyramid (downloaded, nothing taken).
- The Institut de la statistique du Québec's tables by administrative region were not opened: a search summary says its series by age begins in 1996 and consists of yearly estimates, not census counts.

## 8. Boundary caveats in one place

- **City of Montréal:** limits of each census year. The City grew by annexation during the century, was merged with the rest of the island in 2002 and lost fifteen municipalities again on January 1, 2006 (the 2006 yearbook's « Ville de Montréal » is the City after that date). The dates and extent of the annexations were not looked up today and no list is given here: the City's counts are not comparable from one census to the next without one.
- **Island:** « Montreal Island » as a county or census division in 1931 and 1941 (the 1921 volume notes that « Montreal and Jesus Islands » « includes counties of Hochelaga, Jacques Cartier and Laval »); a part of the census metropolitan area in the 1951, 1956 and 1961 tables used; joined with Île Jésus in the county tables of 1956 to 1971; a census division of its own from 1976 (« Île-de-Montréal », then « Communauté urbaine de Montréal »); the « agglomération » in the City's 2006 and 2011 documents. Whether Île Bizard and the small islands are inside each of these units was not checked table by table.
- **1941 metropolitan area** (« Greater Montréal ») is larger than the island in some directions and is recorded as `other`.
