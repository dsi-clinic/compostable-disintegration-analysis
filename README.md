# Compostable Disintegration Analysis

## Project Background

The Compostable Field Testing Program (CFTP) is an international research platform providing field testing methods and kits for composters throughout North America to assess disintegration of certified compostable packaging and foodware, founded by the Compost Research & Education Foundation and BSIbio Packaging Solutions. The data submitted by facilities includes both disintegration data for the test items and composting conditions; one of the program's goals is to find correlations between different composting methodologies and the level of disintegration to enable education on the composting conditions required to break down compostable items. Facilities have historically submitted data in varying formats, so the DSI will help the CFTP create a database well-suited to the kinds of statistical analysis performed on composting data. CFTP will then standardize their data collection process so participating facilities adhere to best practices in both running experiments and in data collection. DSI has worked wtih CFTP to make the data available on a public results dashboard hosted at compostabletesting.org.

## Project Goals

The DSI will be extending a data pipeline to format data from new experiments into a consistent format and creating visualizations showing disintegration rates for different materials and composting methodology. We will also create a process for importing new trial data that CREF's partner facilities will use in future trials, and start building the infrastructure for a public-facing dashboard of data from composting trials.

## Pipeline
The data pipeline standardizes CFTP field-trial data into three CSVs that the dashboard consumes: per-item disintegration results, per-trial average operating conditions, and time-series operating conditions. Reads a single consolidated workbook published by CFTP.

### Quickstart

#### Data file
The pipeline reads one file: `data/CFTP_FullDataSet_Lvl3.xlsx` (from the CFTP `_PRODUCTION DATA SETS (ACTIVE)` Drive folder). Save it to `data/`. No other inputs are required.

The file's tab names, column contracts, and filter rules are declared in [`pipeline_config.yaml`](./pipeline_config.yaml) at the repo root. To adapt to upstream column renames, edit the YAML — no code changes needed.

#### Legacy inputs
The previous multi-file pipeline (CASP004, ClosedLoop, PDFPipeline, etc.) and its source data have been moved to [`_archive/`](./_archive). Refer to git history if you need to compare behavior.


#### Docker
The pipeline runs in Docker. If you use VS Code, this is set up to run in a [dev container](https://code.visualstudio.com/docs/devcontainers/containers), so build the container the way you normally would. Otherwise, just build the Docker image from the ```Dockerfile``` in the root of the directory.

Run the following command in your terminal from the root of the repo to create Docker containers for the pipeline and dashboard:
```sh
docker-compose up
```

The pipeline will automatically run with the above command. If you want to make changes or run the pipeline interactively, you can do the following: in another terminal, run the following command to start an interactive session with the pipeline:
```sh
docker-compose exec pipeline sh
```

To stop the session, press `control`/`command` + `c` in the terminal where you ran the first command, `docker-compose up`.

Type `exit` in the terminal where you ran `docker-compose exec pipeline sh` to leave the interactive session.

The dashboard will run on your computer, you can view it by going to `http://localhost:3333/` in your web browser.
#### Running the Pipeline
The pipeline validates the input workbook (every sheet and required column declared in `pipeline_config.yaml` must be present), then writes three CSVs to both `data/` and `dashboard/data/`.

```sh
# Validate the input file without writing outputs
python scripts/run-pipeline.py --validate-only --verbose

# Full run
python scripts/run-pipeline.py --verbose
```

CLI flags:

| Flag | Purpose |
|---|---|
| `--config PATH` | Override the default `pipeline_config.yaml`. |
| `--input PATH` | Override `input_file` from the config. |
| `--output-dir PATH` | Override the primary output directory. |
| `--dashboard-dir PATH` | Override the dashboard output directory. |
| `--suffix STR` | Append a suffix to output filenames (e.g. `_test`). |
| `--validate-only` | Run validation and exit without writing CSVs. |
| `--verbose`, `-v` | Print per-stage row counts and distinct categorical values. |

Exit codes: `0` success, `1` validation/input failure, `2` unexpected error.

Outputs:
- `disintegration_data_all.csv` — joined per-item, per-trial disintegration data.
- `operating_conditions_avg.csv` — per-trial average temperature, moisture, and trial duration.
- `operating_conditions_full.csv` — long-form time-series across all operating-conditions sheets.

To update the files displayed on the dashboard, follow the instructions in [Updating the Dashboard Data](#updating-the-dashboard-data).

#### Configuring the pipeline
`pipeline_config.yaml` declares the contract with the input workbook:

- `input_file` — path to the workbook.
- `outputs` — output directories and CSV filenames.
- `sheets` — tab names and required columns for `TrialDetails`, `ItemInventory`, `DisintegrationData`. Validation fails with a list of every missing sheet or column.
- `operating_conditions` — list of operating-conditions sheets, the `Operating Condition` label to assign, and (for Temperature/Moisture) the `avg_column` name + optional `avg_window_days` for the per-trial average.
- `filters` — material-class exclusions, item-name exclusions, technology exclusions, outlier mass cutoff, and `include_timepoints` (set to `null` to include Midpoint rows alongside Final).
- `output_columns` — the exact column order for `disintegration_data_all.csv`. This is the dashboard schema contract; do not change without updating the dashboard.

## Dashboard
This is a [Next.js](https://nextjs.org/) project.

### Running the Dashboard
To run the dashboard locally, do **not** use the dev container!

#### Install Packages
Install packages:
```bash
npm install
```

#### Set up Environment Variables for Local Deployment
The dashboard expects a ```.env.local``` file in ```dashboard/``` with a [base64-encoded Google service account JSON](https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-base64-encode-and-decode-from-command-line/) (with permissions to access Cloud Storage buckets). This can be found in the UChicago Organization, DSI Folder, compostable project on GCP.

```
DATA_SOURCE=google
GOOGLE_APPLICATION_CREDENTIALS_BASE64=<base64-encoded-service-account.json>
```

#### Running the Server

To run the development server go into the `/dashboard` directory and then install the necessary packages using `npm install`.

Once the packages install you can run the development server using the following command:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Deploying the Dashboard
The dashboard is deployed via Vercel and is hosted on CFTP's site in an iframe.

Any update to the ```main``` branch of this repo will update the production deployment of the dashboard.

### Updating the Dashboard Data
If you rerun the pipeline, you need to update data files in Google Cloud Storage.

#### Google Cloud Storage
The dashboard pulls data from Google Cloud Storage via an API. Upload the following files to the root of the ```cftp_data``` storage bucket in the ```compostable``` project in the DSI account:
- ```disintegration_data_all.csv.csv```
- ```operating_conditions_avg.csv```
- ```operating_conditions_full.csv```

The `/test` page will show a preview of the files in the Google Cloud Storage bucket with the suffix `_test` (eg. `disintegration_data_all_test.csv`)

### Dashboard Structure

There are two dashboards. The dashboard located in ```page.js``` is the default one that is displayed on the CFTP site. There is also a proof of concept operating condition dashboard available at ```/operating-conditions```

#### Data
The dashboard loads via an API call in ```lib/data.js```. Data is managed in the same file. Menu options are fetched in ```page.js``` when the dashboard first loads.

#### Components
The dashboard consists of a [Plotly](https://plotly.com/javascript/) dash and various filters.

The main dashboard lives in ```components/Dashboard.js``` and the controls are in ```components/DashboardControls.js```.

The operating conditions dash is in one single component: ```componenents/OperatingConditionsDashboard.js```

#### API
The data for this project is sensitive, so it is accessed and aggregated via an API. There are endpoints for the trial data (```app/api/data/```), the options for populating the filter menus (```app/api/options```), and for the the operating conditions dash (```app/api/operating-conditions```).
