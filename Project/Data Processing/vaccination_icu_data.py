import pandas as pd
import os

# Set file paths
vax_path = os.path.join("Datasets", "vaccinations_global.csv")
hosp_path = os.path.join("Datasets", "hospital.csv")
output_path = os.path.join("Datasets","Daily Analysis", "daily_vaccinations_and_icu_all_countries_data.csv")

def clean_and_merge_data():
    print("📥 Loading vaccination and ICU data...")

    # Load datasets
    vax = pd.read_csv(vax_path)
    hosp = pd.read_csv(hosp_path)

    # ✅ Select necessary columns
    vax = vax[[
        "country", "date", "daily_vaccinations",
        "people_vaccinated", "people_fully_vaccinated", "people_unvaccinated"
    ]].copy()
    hosp = hosp[[
        "country", "date", "daily_occupancy_icu"
    ]].copy()

    # ✅ Convert date columns to datetime
    vax["date"] = pd.to_datetime(vax["date"])
    hosp["date"] = pd.to_datetime(hosp["date"])

    # ✅ Sort and calculate daily new vaccinations
    vax = vax.sort_values(by=["country", "date"])
    vax["new_people_vaccinated"] = vax.groupby("country")["people_vaccinated"].diff().fillna(0).clip(lower=0)
    vax["new_people_fully_vaccinated"] = vax.groupby("country")["people_fully_vaccinated"].diff().fillna(0).clip(lower=0)

    # ✅ Merge the datasets on country and date
    merged = pd.merge(vax, hosp, on=["country", "date"], how="outer")

    # ✅ Filter rows with valid daily_vaccinations
    cleaned = merged[merged["daily_vaccinations"].notna()].copy()

    # ✅ Save cleaned data
    os.makedirs("Datasets", exist_ok=True)
    cleaned.to_csv(output_path, index=False)
    print(f"✅ Cleaned data saved to: {output_path}")

# ✅ Fix entry point name check
if __name__ == "__main__":
    clean_and_merge_data()