from pathlib import Path

USE_LEGACY_DATA_FORMATS = True  # Or False
CURRENT_DIR = Path(__file__).resolve().parent
DATA_DIR = CURRENT_DIR / "../data/"
APP_DATA_DIR = CURRENT_DIR / "../dashboard/data/"

# TODO: Can also keep bags, etc if we want them
TRIAL_COLS = [
    "Trial ID",
    "Test Method",
    "Item ID",
    "Item Format",
    "Item Brand",
    "Item Name",
    "Item Description Refined",
    # "Item Description Refined (Trial)",
    "Material Class I",
    "Material Class II",
    "Material Class III",
    # "Start Weight",
    "% Residuals (Mass)",
    "% Residuals (Area)",
]

TRIAL_TO_ID_MAP = {
    "Facility 1 (Windrow)": "WR004-01",
    "Facility 2 (CASP)": "CASP005-01",
    "Facility 3 (EASP)": "EASP001-01",
    "Facility 4 (In-Vessel)": "IV002-01",
    "Facility 5 (EASP)": "EASP002-01",
    "Facility 6 (CASP)": "CASP006-01",
    "Facility 7 (CASP)": "CASP004-02",
    "Facility 8 (ASP)": "ASP001-01",
    "Facility 9 (EASP)": "EASP003-01",
    "Facility 10 (Windrow)": "WR005-01",
    "Facility 1": "WR004-01",
    "Facility 2": "CASP005-01",
    "Facility 3": "EASP001-01",
    "Facility 4": "IV002-01",
    "Facility 5": "EASP002-01",
    "Facility 6": "CASP006-01",
    "Facility 7": "CASP004-02",
    "Facility 8": "ASP001-01",
    "Facility 9": "EASP003-01",
    "Facility 10": "WR005-01",
}


OUTLIER_THRESHOLD = 10

DATA_SHEET_PATHS = {
    "ITEMS_PATH": DATA_DIR / "CFTP-TestItemInventory-Jan-2025.xlsx",
    "EXTRA_ITEMS_PATH": DATA_DIR / "Item IDS for CASP004 CASP003.xlsx",
    "TRIALS_PATH": DATA_DIR / "CFTP_TrialDetails.xlsx",
    "OPERATING_CONDITIONS_PATH": DATA_DIR
    / "Donated Data 2023 - Compiled Facility Conditions for DSI.xlsx",
    "OLD_ITEMS_JSON": DATA_DIR / "old_items.json",
    "BRAND_ANONYMIZATION_PATH": DATA_DIR
    / "CFTP_TestItemInventory.xlsx",
}

TRIAL_DATA_PATHS = {
    "NEW_TEMPLATE_PATH": DATA_DIR
    / "CFTP_DisintegrationData.xlsx",
    "CASP004_PATH": DATA_DIR
    / "CASP004-01 - Results Pre-Processed for Analysis from PDF Tables.xlsx",
    "TEN_TRIALS_PATH": DATA_DIR
    / "Donated Data 2023 - Compiled Field Results for DSI.xlsx",
    "PDF_TRIALS": DATA_DIR / "Compiled Field Results - CFTP Gathered Data.xlsx",
}

ID_TO_TECHNOLOGY_MAP = {
    "WR": "Windrow",
    "CASP": "Aerated Static Pile",
    "EASP": "Aerated Static Pile",
    "ASP": "Aerated Static Pile",
    "IV": "In-Vessel",
    "AD": "Anaerobic Digestion",
}

EXCLUDED_TECHNOLOGIES = ["Anaerobic Digestion"]

# CANONICAL_COLUMNS = {
#   "TRIAL_DETAILS": {
#     "Technology": "Technology",
#   }
# }
