"""Shared paths and constants: automobiles per curb parking place by FSA, City of Montréal."""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES = ROOT / "derived" / "tables"
FIGS = ROOT / "derived" / "figures"
REPO = ROOT.parent
CORRIDOR = REPO / "2026-terrebonne-corridor-vehicles-and-curb"
TP = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party"))
SAAQ = Path(os.environ.get("SAAQ_REPO", REPO.parent / "Quebec-vehicle-registrations"))
CACHE = Path(os.environ.get("RATIO_CACHE", Path.home() / "Terrebonne-data/cache/cars-per-curb-place-by-fsa"))

GEOBASE = TP / "montreal-opendata/geobase_2026-10-14.json"                                    # City open data, CC BY 4.0
SIGNS = TP / "montreal-opendata/signalisation-2026-10-23/signalisation_stationnement.csv"    # City open data, CC BY 4.0
LIMITS = TP / "montreal-opendata/limadmin/limadmin.json"                                     # City open data, CC BY 4.0
DISTRICTS = TP / "montreal-opendata/districts-electoraux/districts-electoraux-2025.json"     # City open data, CC BY 4.0
FSA_SHP = TP / "canmap-v2024.3/CanMapPostalCodeSuitev2024.3/Shapefiles/ForwardSortationAreasRegion.shp"   # DMTI Spatial, under licence
VEHICLES = SAAQ / "derived/tables/type_by_fsa_municipality.csv"
LANE = REPO / "1954-underwriters-plans-terrebonne-garages/derived/terrebonne_lane_geobase.geojson"

CRS = 32188                      # NAD83 / MTM zone 8, metres
YEAR = 2024                      # vehicle file of December 31, 2024 (type inferred)
MONTREAL = "66023"               # municipality code of the City of Montréal
PLACE_M = 5.5                    # length of a parking place (assumption, as in the corridor note); 5.0 and 6.0 as bounds
PLACE_BOUNDS = (5.0, 6.0)
DENSE = 8.0                      # poles per km of curb at or above which a borough's sign inventory is taken as complete
MIN_COMPLETE = 0.90              # an FSA is ranked when at least this share of its City curb lies in such boroughs
MIN_AUTOS = 1000                 # and its City part holds at least this many registered automobiles and light trucks
MAX_UNSIGNED = 40.0              # and at most this percentage of its curb (net of ends) lies on block faces that carry no sign at all
# FSAs whose registered count exceeds 1.5 times what their census profile predicts (vehicles registered to businesses);
# from the corridor analysis, derived/tables/lofo_errors.csv
FLEET = ("H2Y", "H2Z", "H3A", "H3B", "H4P", "H9P")
OUTLINED = ("Notre-Dame-de-Grâce", "Loyola", "Snowdon")       # electoral districts (2025) outlined on the map
LANE_FSAS = ("H4A", "H4B")       # the lane lies in H4B west of Royal and in H4A east of it
