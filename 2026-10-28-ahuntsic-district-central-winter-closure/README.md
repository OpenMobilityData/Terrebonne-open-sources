# Ahuntsic-Cartierville, October 28, 2026: notice to residents on the winter closure of the District central bike lanes (November 16, 2026 to March 31, 2027)

**Issued by:** Arrondissement d'Ahuntsic-Cartierville, Ville de Montréal (« Avis au voisinage », dated October 28, 2026, borough and City marks in the footer).

**Obtained:** a photograph of the printed notice, posted on November 4, 2026 in the public Facebook group « Vélo d'hiver - Montréal » with the comment « Et voilà, un autre démantèlement. »; the screenshot of the post was received the same morning from a member of the Association des piétons et cyclistes de NDG and is kept exactly as received (`raw/`). The person who posted it is not named here.

**Link status:** the notice was not found on montreal.ca or in the borough's news releases on November 4, 2026 (search); no URL. The borough's page « Un réseau cyclable 4 saisons dans Ahuntsic-Cartierville » (montreal.ca/articles/…-39963) describes the borough's four-season network without naming the District central streets.

| File | Content |
|---|---|
| [`raw/2026-11-04_facebook_velo-dhiver_avis_district_central_as_received.webp`](raw/2026-11-04_facebook_velo-dhiver_avis_district_central_as_received.webp) | The screenshot as received (WebP, 1,600 × 2,040; SHA-256 `626c0218…6485d410`) |
| [`derived/avis_district_central_2026-10-28.png`](derived/avis_district_central_2026-10-28.png) | The same image as PNG |
| [`derived/district_central_network.csv`](derived/district_central_network.csv) | The City's bike-network attributes of the streets named in the notice (script [`district_central_network.py`](derived/district_central_network.py)) |

## What the notice says (transcribed from the photograph; the layout's bold kept)

Avis au voisinage

Période prévue : 16 novembre 2026 au 31 mars 2027

**Fermeture de la piste cyclable du District central durant l'hiver**
Changement du lieu de dépôt de vos matières

Rues concernées :
Avenue du Parc, entre le boulevard Crémazie Ouest et la rue Chabanel Ouest
Rue Meilleur, entre les rues Chabanel Ouest et de Port-Royal Ouest
Rue de Port-Royal Ouest, entre les rues Meilleur et Tolhurst
Rue Tolhurst, entre les rues de Port-Royal Ouest et Fleury Ouest
Rue Legendre Ouest, entre les avenues du Parc et de l'Esplanade

**Où déposer vos matières**
Lors des collectes, vous êtes invités à déposer vos bacs et matières **sur votre terrain** en bordure du trottoir. Cette mesure sera applicable seulement durant la fermeture de la piste cyclable, soit du 16 novembre 2026 au 31 mars 2027.

**Pourquoi ce changement?**
Ce changement est temporaire; il ne sera en vigueur que pendant l'hiver. Les pistes cyclables qui longent les rues Tolhurst, de Port-Royal, Meilleur, Chabanel, ainsi que l'avenue du Parc ne seront pas déneigées et seront fermées durant l'hiver. Vous pourrez donc déposer vos bacs et matières sur votre terrain et non dans la zone hachurée.

**Stationnement près du trottoir**
Comme la piste cyclable sera fermée l'hiver, les automobilistes pourront faire fi du marquage actuel au sol* et stationner leur voiture sur les deux côtés de la rue, à une distance maximale de 15 cm du trottoir, en respectant toutefois les heures d'interdiction indiquées sur les panneaux.

**Retour à la normale**
Les pistes cyclables seront de nouveau fonctionnelles à partir du 1er avril 2027.

\*Le marquage actuel au sol fait référence aux deux bandes blanches qui longent la piste cyclable, aux zones hachurées et aux cases de stationnement. Ce marquage doit être respecté seulement d'avril à la mi-novembre.

Merci de votre collaboration.
Commentaires ou questions : composez le 311.

Ahuntsic-Cartierville · Montréal · 28 octobre 2026

## What the City's bike-network file says of these streets

The City's open dataset « Réseau cyclable » (donnees.montreal.ca, CC BY 4.0; copy downloaded October 14, 2026) carries, for each segment, the fields `SAISONS4` (« Fait parti du réseau accessible 4 saisons (oui/non) ») and `PROTEGE_4S` (« Aménagement protégé faisant parti du réseau accessible 4 saisons (oui/non) »), as the dataset's field list on Données Québec defines them. Joined with the géobase on the segment id, the segments on the streets named in the notice (Ahuntsic-Cartierville; the avenue du Parc segments did not match by name) read as follows (lengths in metres, summed by street and attribute; `derived/district_central_network.csv`):

| Street | Lane type | Separator | SAISONS4 | PROTEGE_4S | m |
|---|---|---|---|---|---|
| Chabanel Ouest | Piste cyclable sur rue | Délinéateur | Oui | Oui | 178 |
| Legendre Ouest | Piste cyclable sur rue | Délinéateur | Oui | Oui | 749 |
| Legendre Est | Piste cyclable sur rue | Délinéateur | Oui | Oui | 596 |
| Legendre Est | Chaussée désignée | | Oui | Non | 395 |
| Meilleur | Piste cyclable sur rue | Délinéateur | Oui | Oui | 518 |
| Meilleur | Bande cyclable | | Oui | Non | 528 |
| Port-Royal Ouest | Piste cyclable sur rue | Délinéateur | Oui | Oui | 308 |
| Port-Royal Est | Bande cyclable | | Non | Non | 290 |
| Port-Royal Est | Chaussée désignée | | Non | Non | 81 |
| Port-Royal Est | Piste cyclable sur rue | Marquage au sol | Oui | Non | 72 |
| Tolhurst | Piste cyclable sur rue | Délinéateur | Oui | Oui | 661 |
| Tolhurst | Bande cyclable | | Oui | Non | 1,061 |

For comparison, the same file lists rue de Terrebonne in Côte-des-Neiges–Notre-Dame-de-Grâce as « Piste cyclable sur rue », separator « Délinéateur », SAISONS4 « Oui », PROTEGE_4S « Oui » over 2,413 m (plus 121 m of « Bande cyclable », SAISONS4 « Oui »).

The notice's dates, November 16 to March 31 with a return on April 1, are the City's winter period for bike lanes as used in its own counts and maps (mid-November to the end of March).

## Press coverage and the borough's record (checked November 9, 2026)

**Press** (cited, not reproduced): La Presse, Henri Ouellette-Vézina, « Ahuntsic-Cartierville | Des pistes cyclables seront fermées pour l'hiver », [November 4, 2026](https://www.lapresse.ca/actualites/grand-montreal/2026-11-04/ahuntsic-cartierville/des-pistes-cyclables-seront-fermees-pour-l-hiver.php): the information « a été annoncée aux résidents dans un « avis au voisinage » distribué aux portes »; « Les infrastructures étaient demeurées ouvertes l'hiver dernier »; the City's stated grounds, « enjeux liés à la gestion du stationnement ainsi que les besoins opérationnels et économiques »; the borough mayor, Maude Théroux-Séguin: « On ne démantèle pas les pistes cyclables. C'est une mesure temporaire, qui s'applique uniquement pendant la période hivernale ». Le Devoir, Jeanne Corriveau, « Ahuntsic-Cartierville ferme deux pistes cyclables pour l'hiver », [November 4, 2026](https://www.ledevoir.com/actualites/transports-urbanisme/1022402/ahuntsic-cartierville-ferme-deux-pistes-cyclables-hiver): 267 parking places restored; « Le document décisionnel que Le Devoir a pu consulter » gives as reasons « les enjeux de stationnement et les « besoins opérationnels et économiques du secteur » » and the aim « d'optimiser l'utilisation de l'espace public »; the District central lane « fait partie des pistes analysées dans le cadre d'un audit lancé par l'administration de Soraya Martinez Ferrada et dont les résultats n'ont pas encore été dévoilés ». Journal des voisins, Amine Esseghir, « Hiver dans le District central : les pistes cyclables mises sur pause », [November 6, 2026](https://journaldesvoisins.com/hiver-dans-le-district-central-les-pistes-cyclables-mises-sur-pause/): the mayor, « On suspend la piste pour l'hiver, comme cela se fait ailleurs »; 265 places; about 150 000 $ of snow clearing; 47 km of lanes cleared this winter against 50. CTV News Montreal / Noovo Info, Anastasia Dextrene, « Some bike paths will close this winter in Montreal », [November 6, 2026](https://www.ctvnews.ca/montreal/article/some-bike-paths-will-close-this-winter-in-montreal/). Both La Presse and Le Devoir describe the Terrebonne measure as a dismantling already chosen (« a aussi choisi de démanteler une partie de la piste cyclable », « Après le démantèlement partiel »); on November 4 the Terrebonne offer had been adopted by the borough council (November 2) and not yet accepted by City council.

**The borough council's record.** The agendas with decision summaries of the ordinary sittings of September 14, October 6 and November 9, 2026, the minutes of September 14, and the agendas of the extraordinary sittings of October 6 (2027 budget and ten-year capital programme) and October 26 (a building project on avenue de l'Esplanade) carry no resolution, ordinance or decision summary on the District central or Legendre Ouest lanes, their winter closure or parking on those streets (archive `ville.montreal.qc.ca/documents/Adi_Public/CA_Ahu/`, files `CA_Ahu_ODJP_ORDI_<date>_19h00_FR.pdf`, `CA_Ahu_PV_ORDI_2026-09-14_19h00_FR.pdf`, `CA_Ahu_ODJP_EXTRA_2026-10-06_18h00_FR.pdf`, `CA_Ahu_ODJP_EXTRA_2026-10-26_15h00_FR.pdf`, read November 9, 2026). The November 9 agenda tables the report on powers delegated to officials for September 1–30, 2026 (item 30.01, file 1269863001, under art. 130 of the Charter; the list of decisions is an attachment, not reproduced in the bundle); the report for October 2026, the month of the notice, falls to the December sitting. The borough's pages « Un réseau cyclable 4 saisons dans Ahuntsic-Cartierville » (updated May 8, 2026) and « Le réseau cyclable dans Ahuntsic-Cartierville » (April 16, 2026) do not mention the closure. No release on montreal.ca was found.

**The sitting of November 9, 2026.** Three passages of the public question period concern the closure (webcast `LgInh4tSJh8`, from 0:30:40 and from 1:04:20); the machine draft, not yet checked by ear, the agenda and the page references are in [`2026-11-09-ahuntsic-cartierville-borough-council/`](../2026-11-09-ahuntsic-cartierville-borough-council/).
