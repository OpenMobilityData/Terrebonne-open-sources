"""Shared paths and constants for the corridor analysis."""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLES = ROOT / "derived" / "tables"
FIGS = ROOT / "derived" / "figures"
REPO = ROOT.parent
GARAGES = REPO / "1954-underwriters-plans-terrebonne-garages" / "derived"
TP = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party"))
SAAQ = Path(os.environ.get("SAAQ_REPO", REPO.parent / "Quebec-vehicle-registrations"))
CACHE = Path(os.environ.get("CORRIDOR_CACHE", Path.home() / "Terrebonne-data/cache/corridor-vehicles-and-curb"))

DA_CSV = TP / "statcan-census-2021/98-401-X2021006_Quebec_DA/98-401-X2021006_English_CSV_data_Quebec.csv"
FSA_CSV = TP / "statcan-census-2021/98-401-X2021013_FSA/98-401-X2021013_English_CSV_data.csv"
DA_SHP = TP / "statcan-census-2021/boundaries/lda_000a21a_e/lda_000a21a_e.shp"
PC_CSV = TP / "serviceobjects-2024-03/CanadianPostalCodes202403.csv"
ROLL = TP / "montreal-opendata/unites-evaluation-fonciere/uniteevaluationfonciere.geojson"
FSA_SHP = TP / "canmap-v2024.3/CanMapPostalCodeSuitev2024.3/Shapefiles/ForwardSortationAreasRegion.shp"
GEOBASE = TP / "montreal-opendata/geobase_2026-10-14.json"
SIGNS = TP / "montreal-opendata/signalisation-2026-10-23/signalisation_stationnement.csv"
LANE = GARAGES / "terrebonne_lane_geobase.geojson"

CRS = 32188                      # NAD83 / MTM zone 8, metres
YEAR = 2024                      # vehicle file of December 31, 2024 (type inferred)
MIN_HH = 1000                    # FSAs used to fit: at least this many households
FSAS = ("H4A", "H4B")            # the two FSAs the lane lies in

# 2021 Census profile, characteristic ids (the same in the profiles by FSA and by dissemination area)
CHAR = {1: "population", 5: "households", 9: "pop_0_14", 13: "pop_15_64", 24: "pop_65_plus",
        42: "dw_single", 43: "dw_semi", 44: "dw_row", 45: "dw_duplex", 46: "dw_apt_low", 47: "dw_apt_high",
        48: "dw_other_attached", 49: "dw_movable",
        51: "hh_1", 52: "hh_2", 53: "hh_3", 54: "hh_4", 55: "hh_5plus", 56: "persons_in_households",
        243: "median_household_income", 1415: "owner", 1416: "renter", 1419: "condominium",
        2593: "employed", 2594: "worked_at_home", 2603: "commuters", 2605: "commute_car_driver",
        2606: "commute_car_passenger", 2607: "commute_transit", 2608: "commute_walk", 2609: "commute_bicycle"}
