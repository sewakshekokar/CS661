import os
import pandas as pd

# Set file paths
INPUT_PATH = os.path.join("Datasets", "spread.csv")
OUTPUT_PATH = os.path.join("Datasets", "Daily Analysis","daily_analysis_data.csv")

def clean_temporal_data():
    print("📥 Loading spread.csv ...")
    df = pd.read_csv(INPUT_PATH)

    # Convert date to datetime and sort
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by=["country", "date"])

    # Remove aggregate regions (not actual countries)
    aggregates = ["World", "Asia", "Europe", "Africa", "North America", "South America", "Oceania", "European Union"]
    df = df[~df["country"].isin(aggregates)]

    # Ensure total columns have no NaN
    df["total_cases"] = df["total_cases"].fillna(0)
    df["total_deaths"] = df["total_deaths"].fillna(0)

    #  Calculate interpolated values
    df["new_cases_calc"] = df.groupby("country")["total_cases"].diff().fillna(0)
    df["new_deaths_calc"] = df.groupby("country")["total_deaths"].diff().fillna(0)

    #  Fill only where value is zero
    df["new_cases"] = df["new_cases"].mask(df["new_cases"] == 0, df["new_cases_calc"])
    df["new_deaths"] = df["new_deaths"].mask(df["new_deaths"] == 0, df["new_deaths_calc"])

    #  Clip to ensure no negative values
    df["new_cases"] = df["new_cases"].clip(lower=0)
    df["new_deaths"] = df["new_deaths"].clip(lower=0)

    #  Drop helper columns
    df.drop(columns=["new_cases_calc", "new_deaths_calc"], inplace=True)

    #  Drop per-million columns if present
    df.drop(columns=["new_cases_per_million", "new_deaths_per_million"], errors="ignore", inplace=True)

    #  Save cleaned dataset
    os.makedirs("Datasets", exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Cleaned daily analysis data saved to {OUTPUT_PATH}")

# ✅ Fix entry point
if __name__ == "__main__":
    clean_temporal_data()