# Data Cleaning Report — 2025 Edition

**Source:**
1. `EDGAR_2025_GHG_booklet_2025_fossilCO2only.xlsx` (1.5 MB) — fossil CO₂ data
2. `EDGAR_2025_GHG_booklet_2025.xlsx` (4.5 MB) — full GHG file (LULUCF sheets only)

Both files are from the EDGAR 2025 release by the European Commission Joint Research Centre, available at https://edgar.jrc.ec.europa.eu/report_2025

## Note on data version

This is a **supplementary version** of the dataset. The original assignment provided the EDGAR 2022 release (`EDGARv7_0_FT2021_fossil_CO2_booklet_2022.xlsx`). On my own initiative, I also produced this version using the EDGAR 2025 release because it offers:

- **Three additional years** of data (extends through 2024 instead of 2021)
- **More granular sectors** (8 sectors instead of 5; previously vague "Other sectors" is split into Agriculture, Processes, Fuel Exploitation, and Waste)
- **Country-level LULUCF data** (the 2022 release only provided macro-region level)
- **Updated methodology** based on the 2025 IPCC guidelines

The original 2022-based version is preserved in the project folder as `data/`, `app.py`, and `clean_data.py`. The 2025 version is in `data_2025/`, `app_updated.py`, and `clean_data_updated.py`.

## Issues identified

The original sheets are stored in **wide format** (one column per year), which is unsuitable for plotting libraries that expect long-format input. Several sheets also contained NaN cells and structural quirks.

| Sheet | Source file | Original shape | Issues |
|---|---|---|---|
| `fossil_CO2_totals_by_country` | fossilCO2only | 214 × 58 | Wide format |
| `fossil_CO2_by_sector_country_su` | fossilCO2only | 1468 × 59 | Wide format; sheet name changed from 2022 |
| `fossil_CO2_per_GDP_by_country` | fossilCO2only | 212 × 38 | Wide; year range only 1990–2024 |
| `fossil_CO2_per_capita_by_countr` | fossilCO2only | 212 × 58 | Wide format |
| `LULUCF_macroregions` | full GHG | 98 × 38 | Wide; mixed substances (CO2 + CH4 + N2O); some misaligned rows |
| `LULUCF_countries` | full GHG | 1288 × 40 | Wide; mixed substances; no pre-computed Net column |

## Modifications made

1. **Reshaped each sheet from wide to long format** using `pandas.melt()`. Year columns become a single `Year` column; values become a single value column (`Emissions_Mt`, `tCO2_per_kUSD`, or `tCO2_per_capita`).
2. **Renamed `EDGAR Country Code` → `ISO3`** for clarity (codes follow ISO 3166-1 alpha-3).
3. **Renamed `Macro-region` → `Region`** in LULUCF data for column consistency.
4. **Dropped the `Substance` column** after using it as a filter (only kept `Substance == "CO2"` for LULUCF, since the source sheet mixes multiple greenhouse gases).
5. **Removed rows with NaN values** in the value columns.
6. **For LULUCF specifically:**
   - Filtered to keep only CO₂ rows
   - Filtered to keep only valid sub-sectors: Deforestation, Fires, Forest Land, Organic Soil, Other Land
   - Excluded structurally misaligned rows (some had region names in the Sector column)
   - Excluded `GLOBAL TOTAL` and `EU27` from regions since they're not mutually exclusive macro-regions
   - **Computed a "Net" sector** by summing all sub-sectors per region/country/year (the 2025 release no longer provides a pre-computed Net for individual gases)

## Resulting cleaned files (data_2025/)

| File | Rows | Year range | Purpose |
|---|---|---|---|
| `totals.csv` | 11,660 | 1970–2024 | Country totals |
| `sectors.csv` | 78,063 | 1970–2024 | 8 sectors × country × year |
| `per_gdp.csv` | 7,000 | 1990–2024 | Carbon intensity |
| `per_capita.csv` | 11,550 | 1970–2024 | Per-capita emissions |
| `lulucf_regions.csv` | 2,065 | 1990–2024 | Land-use flux per macro-region (incl. computed Net) |
| `lulucf_countries.csv` | 30,273 | 1990–2024 | Land-use flux per country (incl. computed Net) |

## What was *not* modified

- **Country and region names** preserved exactly as in the source (EDGAR/EC short-name conventions).
- **Numerical values** were not transformed, normalized, or aggregated, except for the explicit Net computation in LULUCF.
- **Both original Excel files** are included unmodified in the project for reference.
