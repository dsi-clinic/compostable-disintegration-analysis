# %%
import pandas as pd
from constants import (
    APP_DATA_DIR,
    DATA_DIR,
    EXCLUDED_TECHNOLOGIES,
    OUTLIER_THRESHOLD,
    TRIAL_DATA_PATHS,
    USE_LEGACY_DATA_FORMATS,
)
from pipeline_template import (
    CASP003Pipeline,
    CASP004Pipeline,
    ClosedLoopPipeline,
    NewTemplatePipeline,
    PDFPipeline,
)
from utils import DefaultDataFrames, anonymize_brand, map_technology


def main(suffix: str = ""):
    default_dfs = DefaultDataFrames()

    trials_to_run = [
        NewTemplatePipeline(
            TRIAL_DATA_PATHS.get("NEW_TEMPLATE_PATH"),
            trial_name="OCT_22_PARTIAL",
        )
    ]

    if USE_LEGACY_DATA_FORMATS is True:
        trials_to_run.extend(
            [
                CASP004Pipeline(
                    TRIAL_DATA_PATHS.get("CASP004_PATH"),
                    sheet_name=1,
                    trial_name="casp004",
                ),
                ClosedLoopPipeline(
                    TRIAL_DATA_PATHS.get("TEN_TRIALS_PATH"),
                    trial_name="closed_loop",
                ),
                PDFPipeline(
                    TRIAL_DATA_PATHS.get("PDF_TRIALS"),
                    trial_name="ad001",
                    sheet_name=0,
                    skiprows=1,
                ),
                PDFPipeline(
                    TRIAL_DATA_PATHS.get("PDF_TRIALS"),
                    trial_name="wr001",
                    sheet_name=1,
                ),
                PDFPipeline(
                    TRIAL_DATA_PATHS.get("PDF_TRIALS"),
                    trial_name="casp001",
                    sheet_name=2,
                ),
                CASP003Pipeline(
                    TRIAL_DATA_PATHS.get("PDF_TRIALS"),
                    trial_name="casp003",
                    sheet_name=3,
                    weight_col="Final Residual Weight - wet - aggregate",
                ),
                PDFPipeline(
                    TRIAL_DATA_PATHS.get("PDF_TRIALS"),
                    trial_name="wr003",
                    sheet_name=4,
                    weight_col="Final Residual Weight - wet",
                ),
            ]
        )

    all_trials = pd.concat(
        [trial.run() for trial in trials_to_run], ignore_index=True
    )
    # Exclude mixed materials and multi-laminate pouches
    all_trials = all_trials[
        ~(all_trials["Material Class II"] == "Mixed Materials")
    ]
    all_trials = all_trials[
        ~(
            all_trials["Item Name"]
            == "Multi-laminate stand-up pounch with zipper"
        )
    ]
    # Exclude anything over 1000% as outlier
    all_trials = all_trials[
        all_trials["% Residuals (Mass)"] < OUTLIER_THRESHOLD
    ]
    # Map Trial IDs to the technology used in the trial
    all_trials["Technology"] = all_trials["Trial ID"].apply(map_technology)

    all_trials["Item Brand"] = all_trials["Item Brand"].apply(
        lambda brand: anonymize_brand(brand, default_dfs.brand_mapping)
    )
    # Ensure all Item Format columns are title case
    all_trials["Item Format"] = all_trials["Item Format"].str.title()

    # Filtering for only final timepoints
    # TODO: incorporate midpoint timepoints
    all_trials['Timepoint'] = all_trials['Timepoint'].replace("Endpoint", "Final")
    all_trials = all_trials[(
        all_trials["Timepoint"] == "Final"
    )]


    # CFTP as of 2025 is excluding AD data from the dashboard, may include in future
    all_trials = all_trials[
        ~all_trials["Technology"].isin(EXCLUDED_TECHNOLOGIES)
    ]

    # Make sure all trial IDs are represented in operating conditions
    unique_trial_ids = pd.DataFrame(
        all_trials["Trial ID"].unique(), columns=["Trial ID"]
    ).set_index("Trial ID")
    df_operating_conditions_avg = unique_trial_ids.merge(
        default_dfs.df_operating_conditions_avg,
        left_index=True,
        right_index=True,
        how="left",
    )
    df_operating_conditions = pd.concat(
        [default_dfs.df_temps, default_dfs.df_moisture, default_dfs.df_o2],
        axis=0,
    )
    for OUTPUT_DIR in [APP_DATA_DIR, DATA_DIR]:
        trials_outpath = OUTPUT_DIR / f"all_trials_processed{suffix}.csv"
        operating_conditions_avg_outpath = (
            OUTPUT_DIR / f"operating_conditions_avg{suffix}.csv"
        )
        operating_conditions_outpath = (
            OUTPUT_DIR / f"operating_conditions_full{suffix}.csv"
        )

        print(f"Saving data to {OUTPUT_DIR}")
        all_trials.to_csv(trials_outpath, index=False)
        df_operating_conditions_avg.to_csv(
            operating_conditions_avg_outpath,
            index_label="Trial ID",
        )
        df_operating_conditions.to_csv(
            operating_conditions_outpath,
            index=True,
            index_label="Time Step",
        )

    print("Complete!")


if __name__ == "__main__":
    main()
# %%
