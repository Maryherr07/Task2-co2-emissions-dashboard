# Data Cleaning Report

**Source:** `EDGARv7_0_FT2021_fossil_CO2_booklet_2022.xlsx` (EDGAR v7.0, European Commission Joint Research Centre)

## Issues identified

The original workbook contains five data sheets, all stored in **wide format** with one column per year. This format is convenient for human reading but unsuitable for charting libraries (Plotly, Streamlit), which expect long-format data with one row per observation. In addition, several sheets contained missing values and the LULUCF sheet had blank separator rows.

| Sheet | Original shape | Issue |
|---|---|---|
| `fossil_CO2_totals_by_country` | 213 rows × 55 cols | Wide format; 52 NaN cells (countries with incomplete history) |
| `fossil_CO2_by_sector_and_countr` | 1036 rows × 56 cols | Wide format; 5 sector rows per country; 520 NaN cells |
| `fossil_CO2_per_GDP_by_country` | 213 rows × 35 cols | Wide format; year range only 1990–2021; 416 NaN cells |
| `fossil_CO2_per_capita_by_countr` | 213 rows × 55 cols | Wide format; 156 NaN cells |
| `LULUCF by macro regions` | 70 rows × 34 cols | Wide format; 3 blank separator rows; 1990–2020 only |

## Modifications made

1. **Reshaped each sheet from wide to long format** using `pandas.melt()`. The year columns were combined into a single `Year` column and the values into a single value column (`Emissions_Mt`, `tCO2_per_kUSD`, or `tCO2_per_capita` depending on the sheet).
2. **Renamed `EDGAR Country Code` → `ISO3`** for clarity, since the codes follow the ISO 3166-1 alpha-3 standard.
3. **Dropped the `Substance` column**, which contained only the constant value `"CO2"` and added no information.
4. **Removed rows with NaN values** in the value column (these represent country–year combinations where data was unavailable, often before a country existed in its current form).
5. **For LULUCF only:** Removed 3 blank separator rows where `region` and `Sector` were both NaN. Renamed `region` → `Region` for consistency.
6. **Saved each cleaned sheet as a separate CSV** in `data/`, ready to be loaded by the dashboard.

## Resulting cleaned files

| File | Rows | Columns | Year range |
|---|---|---|---|
| `data/totals.csv` | 11,024 | ISO3, Country, Year, Emissions_Mt | 1970–2021 |
| `data/sectors.csv` | 53,352 | Sector, ISO3, Country, Year, Emissions_Mt | 1970–2021 |
| `data/per_gdp.csv` | 6,400 | ISO3, Country, Year, tCO2_per_kUSD | 1990–2021 |
| `data/per_capita.csv` | 10,920 | ISO3, Country, Year, tCO2_per_capita | 1970–2021 |
| `data/lulucf.csv` | 2,077 | Sector, Region, Year, Emissions_Mt | 1990–2020 |

## What was *not* modified

- **Country names** were preserved exactly as in the source (EDGAR/EC short-name conventions).
- **Numerical values** were not transformed, normalized, or aggregated. All units remain as in the original dataset.
- **The original Excel file is included unmodified** in the project for reference.

## Notes on data limitations

- The per-GDP sheet starts in 1990 rather than 1970, so analyses combining per-GDP with other metrics are constrained to 1990 onwards.
- The LULUCF sheet uses **macro regions** rather than individual countries, which creates a granularity mismatch with the other four sheets. This is acknowledged in the dashboard design and report.
- LULUCF data ends in 2020 (one year earlier than the fossil-emissions sheets).
