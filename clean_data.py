"""
clean_data.py — Reshape the EDGAR CO2 workbook into long-format CSVs.

Usage:
    python clean_data.py

Reads:
    data/EDGARv7_0_FT2021_fossil_CO2_booklet_2022.xlsx
Writes:
    data/totals.csv
    data/sectors.csv
    data/per_gdp.csv
    data/per_capita.csv
    data/lulucf.csv
"""

import pandas as pd
from pathlib import Path

SRC = Path("data/EDGARv7_0_FT2021_fossil_CO2_booklet_2022.xlsx")
OUT = Path("data")
OUT.mkdir(exist_ok=True)


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
    # 1. Totals by country
    df = pd.read_excel(SRC, sheet_name="fossil_CO2_totals_by_country")
    totals = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "Emissions_Mt")
    totals = totals.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    totals.to_csv(OUT / "totals.csv", index=False)
    print(f"totals.csv      → {len(totals):>6} rows")

    # 2. Sectors
    df = pd.read_excel(SRC, sheet_name="fossil_CO2_by_sector_and_countr")
    sectors = melt_wide(df, ["Substance", "Sector", "EDGAR Country Code", "Country"], "Emissions_Mt")
    sectors = sectors.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    sectors.to_csv(OUT / "sectors.csv", index=False)
    print(f"sectors.csv     → {len(sectors):>6} rows")

    # 3. Per GDP
    df = pd.read_excel(SRC, sheet_name="fossil_CO2_per_GDP_by_country")
    gdp = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "tCO2_per_kUSD")
    gdp = gdp.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    gdp.to_csv(OUT / "per_gdp.csv", index=False)
    print(f"per_gdp.csv     → {len(gdp):>6} rows")

    # 4. Per capita
    df = pd.read_excel(SRC, sheet_name="fossil_CO2_per_capita_by_countr")
    cap = melt_wide(df, ["Substance", "EDGAR Country Code", "Country"], "tCO2_per_capita")
    cap = cap.rename(columns={"EDGAR Country Code": "ISO3"}).drop(columns=["Substance"])
    cap.to_csv(OUT / "per_capita.csv", index=False)
    print(f"per_capita.csv  → {len(cap):>6} rows")

    # 5. LULUCF
    df = pd.read_excel(SRC, sheet_name="LULUCF by macro regions")
    df = df.dropna(subset=["region", "Sector"])
    lulucf = melt_wide(df, ["Sector", "region", "substance"], "Emissions_Mt")
    lulucf = lulucf.drop(columns=["substance"]).rename(columns={"region": "Region"})
    lulucf.to_csv(OUT / "lulucf.csv", index=False)
    print(f"lulucf.csv      → {len(lulucf):>6} rows")


if __name__ == "__main__":
    main()
