import pandas as pd
import os

# File paths
spread_path = os.path.join("Datasets", "spread.csv")
output_path = os.path.join("Datasets", "active_cases_and_estimated_recovery_data.csv")

def compute_recovery_estimates():
    print("📥 Loading spread.csv and calculating active and recovery metrics...")

    # Load dataset
    df = pd.read_csv(spread_path)

    # Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort by country and date
    df = df.sort_values(by=["country", "date"])

    # Calculate active cases (approx.)
    df["active_cases"] = df["total_cases"] - df["total_deaths"]

    # Calculate total_cases_14_days_ago (lagged)
    df["total_cases_14_days_ago"] = df.groupby("country")["total_cases"].shift(14)

    # Estimate recovered
    df["estimated_recovered"] = (
        df["total_cases_14_days_ago"] - df["total_deaths"]
    ).clip(lower=0)

    # Estimate recovery rate
    df["estimated_recovery_rate"] = (
        df["estimated_recovered"] / df["total_cases_14_days_ago"]
    ).clip(upper=1.0)

    # Drop rows where lag data doesn't exist
    df = df.dropna(subset=["total_cases_14_days_ago"])

    # Save final selected columns
    final_df = df[[
        "country", "date", "total_cases", "total_deaths",
        "active_cases", "estimated_recovered", "estimated_recovery_rate"
    ]]

    os.makedirs("Datasets", exist_ok=True)
    final_df.to_csv(output_path, index=False)
    print(f"Processed file saved to: {output_path}")

if __name__ == "__main__":
    compute_recovery_estimates()