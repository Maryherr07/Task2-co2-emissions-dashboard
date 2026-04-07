# 🌍 Global CO2 Emissions Explorer

An interactive dashboard exploring fossil CO₂ emissions and land-use carbon flux from the EDGAR 2025 release (European Commission Joint Research Centre).

**Live dashboard:** _will be added after deployment_

Built for the **UC3DVS10 Data Visualisation** coursework (Task 2).

---

## What it shows

Five linked, interactive visualizations covering CO₂ emissions from 1970 to 2024:

1. **KPI metrics row** — global total, top emitter, and selected country with year-over-year change
2. **Choropleth world map** — total fossil CO₂ emissions by country
3. **Bubble scatter** — carbon intensity (CO₂/GDP) vs. per-capita emissions, colored by continent
4. **Sector breakdown** — 8 economic sectors for a selected country
5. **Trend line** — top emitters or custom country comparison over time
6. **LULUCF diverging bar** — land-use carbon sinks vs. sources, by macro-region or selected country

## Key interactions

- **Year slider** (1990–2024)
- **Continent filter** with auto-zoom on the map
- **Country drill-down** highlights the selected country across multiple charts
- **Trend chart modes:** top-N or custom country selection
- **Toggleable LULUCF view:** macro-regions or country-level breakdown
- **Click legend** entries to show/hide series; double-click to isolate
- **CSV download** for filtered data

## Required tools

- **Python 3.10 or newer**
- **pip**
- A modern web browser (Chrome, Firefox, Brave, Edge, Safari)

## Setup and run locally

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/co2-emissions-dashboard.git
cd co2-emissions-dashboard

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
streamlit run app_2025.py
```

The dashboard opens automatically at <http://localhost:8501>.

## Project structure

```
co2-emissions-dashboard/
├── app_2025.py                          # Main Streamlit dashboard (2025 data)
├── app.py                               # Original version (2022 data)
├── clean_data_2025.py                   # Cleaning script for 2025 data
├── clean_data.py                        # Cleaning script for 2022 data
├── requirements.txt                     # Python dependencies
├── README.md                            # This file
├── data_cleaning_report_2025.md         # Documentation of 2025 cleaning steps
├── data_cleaning_report.md              # Documentation of 2022 cleaning steps
├── data/                                # Original 2022 dataset + cleaned CSVs
│   ├── EDGARv7_0_FT2021_fossil_CO2_booklet_2022.xlsx
│   ├── totals.csv
│   ├── sectors.csv
│   ├── per_gdp.csv
│   ├── per_capita.csv
│   └── lulucf.csv
└── data_2025/                           # Updated 2025 dataset + cleaned CSVs
    ├── EDGAR_2025_GHG_booklet_2025_fossilCO2only.xlsx
    ├── EDGAR_2025_GHG_booklet_2025.xlsx
    ├── totals.csv
    ├── sectors.csv
    ├── per_gdp.csv
    ├── per_capita.csv
    ├── lulucf_regions.csv
    └── lulucf_countries.csv
```

## Data sources

- **Original (2022 release):** EDGAR v7.0 FT2021 fossil CO₂ booklet
- **Updated (2025 release):** EDGAR 2025 GHG booklet (full GHG + fossil CO₂ only versions)

Both produced by the European Commission Joint Research Centre.
Available at <https://edgar.jrc.ec.europa.eu/>

## License

Educational/coursework use. Underlying EDGAR data is released by the European Commission under CC BY 4.0.

## Built with

- **Streamlit** — dashboard framework
- **Plotly** — interactive charts
- **pandas** — data manipulation
