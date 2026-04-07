"""
clean_data_updated.py
Reshape the EDGAR 2025 release into long-format CSVs for the dashboard.

Two source files are used:
  - EDGAR_2025_GHG_booklet_2025_fossilCO2only.xlsx → 4 fossil CO2 sheets
  - EDGAR_2025_GHG_booklet_2025.xlsx               → 2 LULUCF sheets only

Outputs (all written to data_2025/):
  totals.csv             — country totals 1970–2024
  sectors.csv            — country × 8 sectors 1970–2024
  per_gdp.csv            — carbon intensity 1990–2024
  per_capita.csv         — per-capita emissions 1970–2024
  lulucf_regions.csv     — land-use flux per macro-region (incl. computed Net)
  lulucf_countries.csv   — land-use flux per country (incl. computed Net)

Usage:
    python clean_data_updated.py
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data_2025")
FOSSIL = DATA_DIR / "EDGAR_2025_GHG_booklet_2025_fossilCO2only.xlsx"
GHG = DATA_DIR / "EDGAR_2025_GHG_booklet_2025.xlsx"

# Valid LULUCF sub-sectors (used to filter out misaligned rows in the source)
VALID_LULUCF_SECTORS = {
    "Deforestation", "Fires", "Forest Land", "Organic Soil", "Other Land",
}


def melt_wide(df, id_cols, value_name):
    """Melt a wide dataframe with year columns into long format."""
    year_cols = [c for c in df.columns if isinstance(c, (int, float))]
    long = df.melt(
        id_vars=id_cols,
        value_vars=year_cols,
        var_name="Year",
        value_name=value_name,
    )
    long["Year"] = long["Year"].astype(int)
    long = long.dropna(subset=[value_name])
    return long


def main():
    DATA_DIR.mkdir(exist_ok=True)

    # ---------- 1. Totals ----------
    df = pd.read_excel(FOSSIL, sheet_name="fossil_CO2_totals_by_country")
    totals = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "Emissions_Mt")
    totals = totals.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    totals.to_csv(DATA_DIR / "totals.csv", index=False)
    print(f"totals.csv             → {len(totals):>6} rows")

    # ---------- 2. Sectors ----------
    df = pd.read_excel(FOSSIL, sheet_name="fossil_CO2_by_sector_country_su")
    sectors = melt_wide(df, ["Substance", "Sector", "EDGAR Country Code", "Country"], "Emissions_Mt")
    sectors = sectors.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    sectors.to_csv(DATA_DIR / "sectors.csv", index=False)
    print(f"sectors.csv            → {len(sectors):>6} rows")

    # ---------- 3. Per GDP ----------
    df = pd.read_excel(FOSSIL, sheet_name="fossil_CO2_per_GDP_by_country")
    gdp = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "tCO2_per_kUSD")
    gdp = gdp.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    gdp.to_csv(DATA_DIR / "per_gdp.csv", index=False)
    print(f"per_gdp.csv            → {len(gdp):>6} rows")

    # ---------- 4. Per capita ----------
    df = pd.read_excel(FOSSIL, sheet_name="fossil_CO2_per_capita_by_countr")
    cap = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "tCO2_per_capita")
    cap = cap.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    cap.to_csv(DATA_DIR / "per_capita.csv", index=False)
    print(f"per_capita.csv         → {len(cap):>6} rows")

    # ---------- 5. LULUCF regions ----------
    df = pd.read_excel(GHG, sheet_name="LULUCF_macroregions")
    df = df.dropna(subset=["Macro-region", "Sector"])
    df = df[df["Substance"] == "CO2"]
    df = df[df["Sector"].isin(VALID_LULUCF_SECTORS)]
    lulucf_r = melt_wide(df, ["Sector", "Macro-region", "Substance"], "Emissions_Mt")
    lulucf_r = lulucf_r.drop(columns=["Substance"]).rename(columns={"Macro-region": "Region"})
    # Drop aggregate rows that aren't real macro-regions
    lulucf_r = lulucf_r[~lulucf_r["Region"].isin(["GLOBAL TOTAL", "EU27"])]
    # Compute Net (sum of all sub-sectors per region+year)
    net_r = (
        lulucf_r.groupby(["Region", "Year"])["Emissions_Mt"].sum().reset_index()
    )
    net_r["Sector"] = "Net"
    lulucf_r = pd.concat([lulucf_r, net_r[lulucf_r.columns]], ignore_index=True)
    lulucf_r.to_csv(DATA_DIR / "lulucf_regions.csv", index=False)
    print(f"lulucf_regions.csv     → {len(lulucf_r):>6} rows")

    # ---------- 6. LULUCF countries ----------
    df = pd.read_excel(GHG, sheet_name="LULUCF_countries")
    df = df.dropna(subset=["Country", "Sector"])
    df = df[df["Substance"] == "CO2"]
    df = df[df["Sector"].isin(VALID_LULUCF_SECTORS)]
    lulucf_c = melt_wide(
        df, ["Sector", "EDGAR Country Code", "Country", "Macro-region"], "Emissions_Mt",
    )
    lulucf_c = lulucf_c.rename(
        columns={"EDGAR Country Code": "ISO3", "Macro-region": "Region"}
    )
    # Compute Net per country
    net_c = (
        lulucf_c.groupby(["ISO3", "Country", "Region", "Year"])["Emissions_Mt"]
        .sum()
        .reset_index()
    )
    net_c["Sector"] = "Net"
    lulucf_c = pd.concat([lulucf_c, net_c[lulucf_c.columns]], ignore_index=True)
    lulucf_c.to_csv(DATA_DIR / "lulucf_countries.csv", index=False)
    print(f"lulucf_countries.csv   → {len(lulucf_c):>6} rows")


if __name__ == "__main__":
    main()
