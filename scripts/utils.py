# %%
# pragma: exclude file
# This class and functions only work with access to
# data that are not present in the repo during testing.
import json
from pathlib import Path

import pandas as pd
from constants import DATA_SHEET_PATHS, ID_TO_TECHNOLOGY_MAP, TRIAL_TO_ID_MAP


def get_trial_to_id_map():
    """
    Returns a dictionary of trial IDs to map.
    """
    facility_df = pd.read_excel(DATA_SHEET_PATHS.get("OPERATING_CONDITIONS_PATH"), sheet_name=1, skiprows=1)
    for _, row in facility_df.iterrows():
        if row["Trial Facility Name"] not in TRIAL_TO_ID_MAP:
            TRIAL_TO_ID_MAP[row["Trial Facility Name"]] = row["Public Trial ID"]
    return TRIAL_TO_ID_MAP


def anonymize_brand(brand: str, brand_mapping: dict):
    """Anonymizes brand names by mapping them to a generic brand.
        Sorry for the global variable.

    >>> brand_mapping = {"Brand 1": "Brand A"}
    >>> anonymize_brand("Brand 1", brand_mapping)
    'Brand A'

    Args:
        brand: The brand name

    Returns:
        The anonymized brand name (eg "Brand A")
    """
    if brand not in brand_mapping:
        numeric_brands = [
            value for value in brand_mapping.values() if isinstance(value, int)
        ]
        max_numeric = max(numeric_brands) if numeric_brands else 0
        brand_mapping[brand] = max_numeric + 1
    anon_brand = brand_mapping[brand]
    if isinstance(anon_brand, int):
        return f"Brand {anon_brand}"
    else:
        return anon_brand


def map_technology(trial_id: str) -> str:
    """Maps trial IDs to the technology used in the trial.
    >>> map_technology('EASP')
    'Aerated Static Pile'

    Args:
        trial_id: The trial ID.

    Returns:
        The technology used in the trial.
    """
    for key in ID_TO_TECHNOLOGY_MAP:
        if key in trial_id:
            return ID_TO_TECHNOLOGY_MAP[key]
    return "Unknown"


class DefaultDataFrames:
    """
    Class to store default dataframes for the pipeline.
    Methods
    -------
    __init__():
        Initializes the DefaultDataFrames class and loads all dataframes.
    load_items_df():
        Loads the items dataframe from an Excel file and processes it.
    load_items2id():
        Loads a mapping of item descriptions to item
        IDs from the items dataframe and an additional Excel file.
    load_df_trials():
        Loads the trials dataframe from an Excel file.
    load_brand_mapping():
        Loads the brand mapping dataframe from an Excel file and processes it.
    load_operating_conditions():
        Loads various operating conditions dataframes
        from an Excel file and processes them.

    """

    def __init__(self):
        self.load_items_df()
        self.load_items2id()
        self.load_df_trials()
        self.load_operating_conditions()
        self.load_brand_mapping()

    def load_items_df(self):
        df_items = pd.read_excel(
            DATA_SHEET_PATHS.get("ITEMS_PATH"),
            sheet_name="Item Inventory",
            skiprows=3,
        )
        df_items["Start Weight"] = df_items["Average Initial Weight, g"]
        old_json = json.load(Path.open(DATA_SHEET_PATHS.get("OLD_ITEMS_JSON")))
        df_items["Item ID"] = df_items["Item ID"].fillna(
            df_items["Item Description Refined"].map(old_json)
        )
        df_items = df_items.rename(columns={"Brand": "Item Brand"})
        self.df_items = df_items

    def load_items2id(self):
        item2id = {
            key.strip(): value
            for key, value in self.df_items.set_index(
                "Item Description Refined"
            )["Item ID"]
            .to_dict()
            .items()
        }

        extra_items = pd.read_excel(DATA_SHEET_PATHS.get("EXTRA_ITEMS_PATH"))
        extra_items = extra_items.set_index("OG Description")[
            "Item ID"
        ].to_dict()

        self.item2id = item2id | extra_items

    def load_df_trials(self):
        self.df_trials = pd.read_excel(DATA_SHEET_PATHS.get("TRIALS_PATH"))[
            [
                "Public Trial ID",
                "Test Method",
                "Display Method",
            ]
        ]

    def load_brand_mapping(self):
        # read third sheet
        brand_mapping_df = pd.read_excel(
            DATA_SHEET_PATHS.get("BRAND_ANONYMIZATION_PATH"),
            sheet_name="Company Anonymization",
        )
        brand_mapping_df = brand_mapping_df[
            (brand_mapping_df["Brand for Display"].notna())
            & (brand_mapping_df["Brand"].notna())
        ]
        brand_mapping = {}
        for _, row in brand_mapping_df.iterrows():
            brand_mapping[row["Brand"]] = row["Brand for Display"]
        self.brand_mapping = brand_mapping

    def load_operating_conditions(self):
        df_temps = pd.read_excel(
            DATA_SHEET_PATHS.get("OPERATING_CONDITIONS_PATH"),
            sheet_name=3,
            skiprows=1,
            index_col="Time Step",
        )
        trial_to_id_map = get_trial_to_id_map()
        df_temps = df_temps[
            [col for col in df_temps.columns if col in trial_to_id_map]
        ]
        df_temps.columns = [
            trial_to_id_map[col.replace("*", "")] for col in df_temps.columns
        ]
        # ONLY USE THE FIRST 45 DAYS
        df_temps_avg = (
            df_temps.iloc[0:45].mean().to_frame("Average Temperature (F)")
        )
        df_temps["Operating Condition"] = "Temperature"
        df_temps["Time Unit"] = "Day"

        df_trial_duration = pd.read_excel(
            DATA_SHEET_PATHS.get("OPERATING_CONDITIONS_PATH"),
            sheet_name=2,
            skiprows=3,
        )
        df_trial_duration.columns = [
            col.replace("\n", "").strip() for col in df_trial_duration.columns
        ]
        df_trial_duration = df_trial_duration[
            ["Facility Designation", "Endpoint Analysis (trial length)"]
        ].rename(
            columns={
                "Facility Designation": "Trial ID",
                "Endpoint Analysis (trial length)": "Trial Duration",
            }
        )
        df_trial_duration["Trial ID"] = (
            df_trial_duration["Trial ID"]
            .str.replace("( ", "(", regex=False)
            .str.replace(" )", ")", regex=False)
            .map(trial_to_id_map)
        )
        df_trial_duration = df_trial_duration.set_index("Trial ID")

        df_moisture = pd.read_excel(
            DATA_SHEET_PATHS.get("OPERATING_CONDITIONS_PATH"),
            sheet_name=4,
            skiprows=1,
            index_col="Week",
        )
        # Filter out rows with non-numeric week values
        df_moisture = df_moisture.reset_index()
        df_moisture = df_moisture[
            pd.to_numeric(df_moisture["Week"], errors="coerce").notna()
        ]
        df_moisture = df_moisture.set_index("Week")
        df_moisture.columns = [
            trial_to_id_map[col.replace("*", "")] for col in df_moisture.columns
        ]
        df_moisture_avg = df_moisture.mean().to_frame(
            "Average % Moisture (In Field)"
        )
        df_moisture["Operating Condition"] = "Moisture"
        df_moisture["Time Unit"] = "Week"

        df_o2 = pd.read_excel(
            DATA_SHEET_PATHS.get("OPERATING_CONDITIONS_PATH"),
            sheet_name=6,
            skiprows=1,
            index_col="Week",
        )
        df_o2 = df_o2.reset_index()
        df_o2 = df_o2[pd.to_numeric(df_o2["Week"], errors="coerce").notna()]
        df_o2 = df_o2.set_index("Week")
        df_o2.columns = [
            TRIAL_TO_ID_MAP[col.replace("*", "")] for col in df_o2.columns
        ]
        df_o2["Operating Condition"] = "Oxygen"
        df_o2["Time Unit"] = "Week"

        self.df_temps = df_temps
        self.df_temps_avg = df_temps_avg
        self.df_moisture = df_moisture
        self.df_moisture_avg = df_moisture_avg
        self.df_o2 = df_o2
        self.df_trial_duration = df_trial_duration

        self.df_operating_conditions_avg = pd.concat(
            [df_trial_duration, df_temps_avg, df_moisture_avg], axis=1
        )
