"""Processes data from the CFTP for display on a public dashboard."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from constants import TRIAL_COLS
from utils import DefaultDataFrames, get_trial_to_id_map


class AbstractDataPipeline(ABC):
    """An abstract base class for a data pipeline.

    This class provides a template for data pipelines, including methods for
    loading, preprocessing, and calculating results from data. It also includes
    a method for running the entire pipeline and saving the results.

    Attributes:
        data_filepath: Path to the data file.
        items: DataFrame containing item information.
        item2id: Dictionary mapping items to IDs.
        trial: Trial identifier.
        output_filepath: Path to save the output file.
        data: Loaded data.
    """

    def __init__(
        self,
        data_filepath: Path,
        items: pd.DataFrame = None,
        item2id: Dict[str, Any] = None,
        trials: pd.DataFrame = None,
        trial_name: Optional[str] = None,
        sheet_name: int = 0,
        skiprows: int = 0,
    ) -> None:
        """Initializes the AbstractDataPipeline with the given parameters.

        Args:
            data_filepath: Path to the data file.
            items: DataFrame containing item information.
            item2id: Dictionary mapping items to IDs.
            trial_name: Trial name. Defaults to None.
            trials: DataFrame containing trial information. Defaults to TRIALS.
            sheet_name: Sheet name or index to load. Defaults to 0.
            skiprows: Number of rows to skip at the start of the file. Defaults to 0.
        """

        default_dfs = DefaultDataFrames()

        self.data_filepath = data_filepath
        filename = self.data_filepath.stem
        self.trial_name = trial_name
        self.trials = default_dfs.df_trials if trials is None else trials
        file_suffix = (
            f"_{trial_name}_clean.csv" if self.trial_name else "_clean.csv"
        )
        self.output_filepath = self.data_filepath.with_name(
            filename + file_suffix
        )

        # TODO: This is kind of messy and could probably be better
        self.raw_data = self.load_data(
            data_filepath, sheet_name=sheet_name, skiprows=skiprows
        )
        self.items = default_dfs.df_items if items is None else items
        self.item2id = default_dfs.item2id if item2id is None else item2id

    @abstractmethod
    def load_data(
        self, data_filepath: Path, sheet_name: int = 0, skip_rows: int = 0
    ) -> pd.DataFrame:
        """Loads data from the specified file.

        This method should be implemented by subclasses to load data from the
        specified file path.

        Args:
            data_filepath: Path to the data file.
            sheet_name: Sheet name or index to load. Defaults to 0.
            skip_rows: Number of rows to skip at the start of the file. Defaults to 0.

        Returns:
            Loaded data.
        """
        pass

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocesses the data.

        This method can be overridden by subclasses to provide specific
        preprocessing steps.

        Args:
            data: Data to preprocess.

        Returns:
            Preprocessed data.
        """
        return data

    def join_with_items(self, data: pd.DataFrame) -> pd.DataFrame:
        """Joins the data with item information.

        Args:
            data: Data to join.

        Returns:
            Data joined with item information.
        """
        return self.items.merge(data, on="Item ID")

    def calculate_results(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates results from the data.

        This method can be overridden by subclasses to provide specific
        calculations.

        Args:
            data: Data to calculate results from.

        Returns:
            Data with calculated results.
        """
        return data

    def merge_with_trials(self, data: pd.DataFrame) -> pd.DataFrame:
        """Merges the data with trial information.

        Args:
            data: Data to merge.

        Returns:
            Data merged with trial information.
        """
        if "Trial ID" not in data.columns:
            raise ValueError(f"Trial ID column not found in data: {data.columns}, expected 'Trial ID'.\n {self.data_filepath}")
        return data.merge(
            self.trials, left_on="Trial ID", right_on="Public Trial ID"
        )

    def run(self, save: bool = False) -> pd.DataFrame:
        """Runs the data pipeline.

        This method runs the entire data pipeline, including loading data,
        preprocessing, joining with item information, calculating results,
        and optionally saving the output to a file.

        Args:
            save: Whether to save the output to a file. Defaults to False.

        Returns:
            Final processed data.
        """
        print(f"Running data pipeline for {self.trial_name}")
        data = self.raw_data.copy()
        data = self.preprocess_data(data)
        data = self.join_with_items(data)
        data = self.calculate_results(data)
        data = self.merge_with_trials(data)
        data = data[TRIAL_COLS]
        if save:
            data.to_csv(self.output_filepath, index=False)
            print(f"Saved to {self.output_filepath}")
        print("Complete!")
        return data


class NewTemplatePipeline(AbstractDataPipeline):
    """Pipeline for processing data from the new template."""

    def load_data(
        self, data_filepath: Path, sheet_name: int = 0, skiprows: int = 0
    ) -> pd.DataFrame:
        """Loads data from the specified CSV file.

        Args:
            data_filepath: Path to the data file.
            sheet_name: Sheet name or index to load. Defaults to 0.
            skiprows: Number of rows to skip at the start of the file. Defaults to 0.

        Returns:
            Loaded data.
        """
        # Read the CSV file into a DataFrame
        # With fix utf-8 encoding issue
        # TODO: Change to Excel
        if data_filepath.suffix == ".csv":
            data = pd.read_csv(data_filepath)
        elif data_filepath.suffix == ".xlsx" or data_filepath.suffix == ".xls":
            data = pd.read_excel(data_filepath)
        else:
            raise ValueError(f"Unsupported file type: {data_filepath.suffix}")

        # Find the index of the first completely empty row — formatted
        # so there's comments below the data
        first_empty_row_index = data[data.isna().all(axis=1)].index.min()

        # If an empty row is found, drop all rows below it
        if pd.notna(first_empty_row_index):
            data = data[:first_empty_row_index]
        return data

    def preprocess_data(self, data):
        """Preprocesses the data.

        Args:
            data: Data to preprocess.

        Returns:
            The preprocess data.
        """
        data = data.rename(
            columns={
                "Trial": "Trial ID",
            }
        )
        percentage_cols = [
            "% Residuals (Dry Weight)",
            "% Residuals (Wet Weight)",
            "% Residuals (Area)",
        ]
        data[percentage_cols] = data[percentage_cols].replace("no data", np.nan)
        # TODO: Depending data actually comes in, maybe we don't want to do it this way?
        data[percentage_cols] = (
            data[percentage_cols].replace("%", "", regex=True).astype(float)
            / 100
        )

        # Prefer dry weight to wet weight if available
        data["% Residuals (Mass)"] = data["% Residuals (Dry Weight)"].fillna(
            data["% Residuals (Wet Weight)"]
        )

        return data

    def join_with_items(self, data):
        """Join with the items table

        Args:
            data: Data to join.

        Returns:
            The joined data
        """
        return self.items.drop_duplicates(subset="Item Name").merge(
            data, on="Item Name"
        )


class CASP004Pipeline(AbstractDataPipeline):
    """Pipeline for processing CASP004 trial data."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initializes the CASP004Pipeline with the given parameters.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        # We are using the start weight specific to this trial
        # so drop the Start Weight column
        # Start weight is set in preprocess_data
        self.items = self.items.drop("Start Weight", axis=1)

    def load_data(
        self, data_filepath: Path, sheet_name: int = 0, skiprows: int = 0
    ) -> pd.DataFrame:
        """Loads data from the specified Excel file.

        Args:
            data_filepath (Path): Path to the data file.
            sheet_name (int, optional): Sheet name or index to load. Defaults to 0.
            skiprows (int, optional): Number of rows to skip at the start
                of the file. Defaults to 0.

        Returns:
            Loaded data.
        """
        return pd.read_excel(
            data_filepath, sheet_name=sheet_name, skiprows=skiprows
        )

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocesses the data.

        This method performs the following steps:
        - Filters observations to only include the "End" stage.
        - Excludes bags A-5 and A-6.
        - Takes the average of three weight observations.
        - Fills null values with zero (indicating full disintegration).
        - Maps start weights and item descriptions.
        - Ensures no null items after mapping.

        Args:
            data: Data to preprocess.

        Returns:
            Preprocessed data.
        """
        # Only use observations at the end
        data = data[data["Stage"] == "End"].copy()
        # Bags A-5 and A-6 were not found
        data = data[~data["Bag Id"].isin(["A-5", "A-6"])]

        data["Trial"] = data["Trial Id"]

        # Take the average of the three weight observations
        data["End Weight"] = data[["Weight 1", "Weight 2", "Weight 3"]].mean(
            axis=1
        )

        # Null values mean the item fully disintegrated
        data["End Weight"] = data["End Weight"].fillna(0)

        # Ok...we need to do some weird items work arounds here...this might work?
        casp004_items = pd.read_excel(
            self.data_filepath, sheet_name=2
        ).drop_duplicates(subset=["Item Name"])
        casp004_weights = casp004_items.set_index("Item Name")[
            "Weight (average)"
        ].to_dict()
        data["Start Weight"] = data["Product Name"].map(casp004_weights)
        # rename so this matches the other trials
        data["Item Description Refined"] = data["Product Name"]

        # TODO: Some of this should be in the abstract method...
        data["Item ID"] = (
            data["Item Description Refined"].str.strip().map(self.item2id)
        )
        # Prevent duplicate columns when merging with items
        data = data.rename(
            columns={
                "Item Description Refined": "Item Description Refined (Trial)"
            }
        )
        data["Trial ID"] = "CASP004-01"
        if data["Item ID"].isna().sum() > 0:
            raise ValueError("There are null items after mapping")

        return data

    def calculate_results(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates results from the data.

        This method calculates the percentage of residuals by mass and sets
        residuals by area to None.

        Args:
            data: Data to calculate results from.

        Returns:
            Data with calculated results.
        """
        data["End Weight"] = data[["Weight 1", "Weight 2", "Weight 3"]].mean(
            axis=1
        )
        data["End Weight"] = data["End Weight"].fillna(0)

        data["% Residuals (Area)"] = None
        data["% Residuals (Mass)"] = data["End Weight"] / data["Start Weight"]
        return data


class ClosedLoopPipeline(AbstractDataPipeline):
    """Pipeline for processing Closed Loop trial data."""

    def melt_trial(self, data: pd.DataFrame, value_name: str) -> pd.DataFrame:
        """Helper method to melt DataFrames.

        Args:
            data (pd.DataFrame): DataFrame to melt.
            value_name (str): Name of the value column after melting.

        Returns:
            Melted DataFrame.
        """
        item_ids = [
            "N",
            "O",
            "Q",
            "V",
            "B",
            "D",
            "H",
            "I",
            "J",
            "K",
            "K1",
            "K2",
            "K3",
            "N",
            "O",
            "P",
            "Q",
            "S",
            "V",
        ]
        return (
            data.melt(
                id_vars=["Trial ID", "Trial Stage", "Bag Set", "Bag Number"],
                value_vars=item_ids,
                var_name="Item ID",
                value_name=value_name,
            )
            .dropna(subset=[value_name])
            .reset_index(drop=True)
        )

    def load_data(
        self, data_filepath: Path, sheet_name: int = 0, skiprows: int = 0
    ) -> pd.DataFrame:
        """Loads data from the specified Excel file.

        Args:
            data_filepath: Path to the data file.
            sheet_name: Sheet name or index to load. Defaults to 0.
            skiprows: Number of rows to skip at the start of the file. Defaults to 0.

        Returns:
            Loaded and merged data.
        """
        df_weight = pd.read_excel(data_filepath, sheet_name=3, skiprows=2)
        weight_melted = self.melt_trial(df_weight, "% Residuals (Mass)")

        df_area = pd.read_excel(data_filepath, sheet_name=4, skiprows=2)
        df_area["Trial ID"] = df_area["Facility Name"].map(get_trial_to_id_map())
        area_melted = self.melt_trial(df_area, "% Residuals (Area)")

        return weight_melted.merge(
            area_melted,
            on=["Trial ID", "Trial Stage", "Bag Set", "Bag Number", "Item ID"],
            how="outer",
        )

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocesses the data.

        This method sets the item description to None and filters the data to
        only include the "Second Removal" stage.

        Args:
            data: Data to preprocess.

        Returns:
            Preprocessed data.
        """
        data["Item Description Refined (Trial)"] = None
        data = data[data["Trial Stage"] == "Second Removal"]
        return data


class PDFPipeline(AbstractDataPipeline):
    """Pipeline for processing PDF trial data."""

    def __init__(
        self,
        *args: Any,
        weight_col: str = "Residual Weight - Oven-dry",
        **kwargs: Any,
    ) -> None:
        """Initializes the PDFPipeline with the given parameters.

        Args:
            *args: Arbitrary non-keyword arguments.
            weight_col: Column name for the residual weight.
                Defaults to "Residual Weight - Oven-dry".
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.weight_col = weight_col

    def load_data(
        self, data_filepath: Path, sheet_name: int = 0, skiprows: int = 0
    ) -> pd.DataFrame:
        """Loads data from the specified Excel file.

        Args:
            data_filepath: Path to the data file.
            sheet_name: Sheet name or index to load. Defaults to 0.
            skiprows: Number of rows to skip at the start of the file. Defaults to 0.

        Returns:
            Loaded data.
        """
        return pd.read_excel(
            data_filepath, sheet_name=sheet_name, skiprows=skiprows
        )

    def join_with_items(self, data: pd.DataFrame) -> pd.DataFrame:
        """Joins the data with item information.

        This method maps item descriptions to item IDs and merges the data with
        item information, dropping any unnecessary columns.

        Args:
            data: Data to join.

        Returns:
            Data joined with item information.
        """
        # TODO: Merge on ID or should we just merge on description if we have it?
        data["Item ID"] = (
            data["Item Description Refined"].str.strip().map(self.item2id)
        )
        # Prevent duplicate columns when merging with items
        data = data.rename(
            columns={
                "Item Description Refined": "Item Description Refined (Trial)"
            }
        )
        drop_cols = ["Item Description From Trial"]
        data = data.drop(drop_cols, axis=1)
        if data["Item ID"].isna().sum() > 0:
            raise ValueError("There are null items after mapping")
        return self.items.merge(data, on="Item ID")

    def calculate_results(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculates results from the data.

        This method calculates the percentage of residuals by mass and sets
        residuals by area to None.

        Args:
            data: Data to calculate results from.

        Returns:
            Data with calculated results.
        """
        data["% Residuals (Mass)"] = data[self.weight_col] / (
            data["Start Weight"] * data["Number of Items per bag"]
        )
        data["% Residuals (Area)"] = None
        data["Trial"] = data["Trial ID"]
        return data


class CASP003Pipeline(PDFPipeline):
    """Pipeline for processing CASP003 trial data."""

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Preprocesses the data.

        This method filters out data where the trial bag color is blue, as
        items in blue bags were combined and impossible to separate.

        Args:
            data (pd.DataFrame): Data to preprocess.

        Returns:
            Preprocessed data.
        """
        return data[data["Trial Bag Colour"] != "Blue"]
