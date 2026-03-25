# Compostable Disintegration Analysis

## Project Background

The Compostable Field Testing Program (CFTP) is an international research platform providing field testing methods and kits for composters throughout North America to assess disintegration of certified compostable packaging and foodware, founded by the Compost Research & Education Foundation and BSIbio Packaging Solutions. The data submitted by facilities includes both disintegration data for the test items and composting conditions; one of the program's goals is to find correlations between different composting methodologies and the level of disintegration to enable education on the composting conditions required to break down compostable items. Facilities have historically submitted data in varying formats, so the DSI will help the CFTP create a database well-suited to the kinds of statistical analysis performed on composting data. CFTP will then standardize their data collection process so participating facilities adhere to best practices in both running experiments and in data collection. DSI has worked wtih CFTP to make the data available on a public results dashboard hosted at compostabletesting.org.

## Project Goals

The DSI will be extending a data pipeline to format data from new experiments into a consistent format and creating visualizations showing disintegration rates for different materials and composting methodology. We will also create a process for importing new trial data that CREF's partner facilities will use in future trials, and start building the infrastructure for a public-facing dashboard of data from composting trials.

## Pipeline
The data pipeline for this project does the following standardizes data from multiple facilities for display on a dashboard displaying decomposition rates of different compostable materials as well as operating conditions of the associated facilities.

Note: The pipeline was set up to handle multiple disparate files with varied input formats. Future data will come in a standardized format. The pipeline is left as one script for ease of iteration and refactoring later when the new data format is known.

### Quickstart

#### Data Files
Download the following files from the DSI Google Drive in the [Results Data for DSI - Raw uploads](https://drive.google.com/drive/folders/1B8aRIF1lWDKfeqlDTkG2y1ERZFD-A8JK?usp=sharing) and save them to ```data/```:

- [CFTP-TestItemInventory-Jan-2025.xlsx](https://docs.google.com/spreadsheets/d/1GgRFcWWcPEBfH6N4v15wiB_g4pGz_b9y/edit?gid=1380270313#gid=1380270313)
- [CFTP-TrialDetails-Oct22-2024.xlsx](https://docs.google.com/spreadsheets/d/1-djc8F_4fdzZOj3tXZSc1vDL0slUK02Q/edit?gid=1192858019#gid=1192858019)
- [CFTP_DisintegrationDataInput_Oct22-2024-partial.csv](https://drive.google.com/file/d/1QGCmImE8TIyBzD8JpqGo9TCN68k3Efc6/view?usp=drive_link)
- [CFTP Anonymized Data Compilation Overview - For Sharing](https://docs.google.com/spreadsheets/d/1GsbN9AexDb0j-Hqzz8z3kO4zC5v60ptx)
- [Donated Data 2023 - Compiled Facility Conditions for DSI](https://docs.google.com/spreadsheets/d/1-UGcOJ3Jy2Oe37hy9m8p2IjeHSTuBqeF)
- [Donated Data 2023 - Compiled Field Results for DSI](https://docs.google.com/spreadsheets/d/1XwYxdEhrpOxS6_nSf9yARWI-mLswrIBv)
- [CASP004-01 - Results Pre-Processed for Analysis from PDF Tables](https://docs.google.com/spreadsheets/d/1GfYaqgqx85qq5XM__0D1IfbMomGsLdmQ)
- [Compiled Field Results - CFTP Gathered Data](https://docs.google.com/spreadsheets/d/1EqRhb09hcXc9SW99vrj5aVUdYHicmUoU)
- [CFTP Test Item Inventory with Dimensions - All Trials.xlsx'](https://docs.google.com/spreadsheets/d/12deXRBI7_856FIuiu5ZgM_W19llAHD42/edit?usp=drive_link&ouid=102107591581911420296&rtpof=true&sd=true)
- [old_items.json](https://drive.google.com/file/d/11w1jwuF4Y3ZuBXppYWV11MKiDkXmsvOz/view?usp=sharing)
- [Item IDS for CASP004 CASP003.xlsx](https://docs.google.com/spreadsheets/d/1U8dds3eiUFNxQNzLYvYay1KxVqd9mpAR)

File paths for these sheets are all configured in ```scripts/constants.py``` and read in `DefaultDataFrames` in ```scripts/utils.py```


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
To run the pipeline:

```sh
python scripts/run-pipeline.py
```

Cleaned data files will be output in ```data/```. To update the files displayed on the dashboard, follow the instructions in [Updating the Dashboard Data](#updating-the-dashboard-data)

Updated pipeline templates should be added to `scripts/pipeline_templates.py` and added to the main pipeline function in `scripts/run-pipeline.py`

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
