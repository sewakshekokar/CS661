# Importing necessary libraries
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import warnings
from functools import reduce
import sys
import pycountry

sys.path.append(str(Path(__file__).parent.parent))

import config

dataset_pathfiles= [i for i in list((config.PROJECT_DIR/ 'Primary_Datasets_Raw').iterdir()) if str(i).endswith('.csv')]

cases_deaths_df = pd.read_csv(dataset_pathfiles[0]).drop(columns=['days_since_0_1_total_deaths_per_million', 'days_since_100_total_cases_and_5m_pop', 'total_deaths_last12m', 'total_deaths_per_100k_last12m', 'total_deaths_per_million_last12m', 'weekly_cases', 'weekly_deaths', 'weekly_pct_growth_cases', 'weekly_pct_growth_deaths', 'biweekly_cases', 'biweekly_deaths', 'biweekly_pct_growth_cases', 'biweekly_pct_growth_deaths', 'weekly_cases_per_million', 'weekly_deaths_per_million', 'biweekly_cases_per_million', 'biweekly_deaths_per_million', 'total_deaths_per_100k', 'new_deaths_per_100k', 'new_cases_7_day_avg_right', 'cfr_short_term', 'days_since_100_total_cases', 'days_since_5_total_deaths', 'days_since_1_total_cases_per_million', 'new_deaths_7_day_avg_right', 'new_cases_per_million_7_day_avg_right', 'new_deaths', 'cfr_100_cases', 'new_deaths_per_million_7_day_avg_right', 'new_deaths_per_100k_7_day_avg_right', 'new_cases', 'total_cases', 'total_deaths'])
excess_mortality_economist_df = pd.read_csv(dataset_pathfiles[1]).drop(columns=['cumulative_estimated_daily_excess_deaths', 'cumulative_estimated_daily_excess_deaths_ci_95_top', 'cumulative_estimated_daily_excess_deaths_ci_95_bot', 'estimated_daily_excess_deaths', 'estimated_daily_excess_deaths_ci_95_top', 'estimated_daily_excess_deaths_ci_95_bot', 'cumulative_estimated_daily_excess_deaths_last12m', 'cumulative_estimated_daily_excess_deaths_per_100k_last12m', 'cumulative_estimated_daily_excess_deaths_ci_95_bot_last12m', 'cumulative_estimated_daily_excess_deaths_ci_95_bot_per_100k_last12m', 'cumulative_estimated_daily_excess_deaths_ci_95_top_last12m', 'cumulative_estimated_daily_excess_deaths_ci_95_top_per_100k_last12m'])
country_list = [country.name for country in pycountry.countries]
cases_deaths_df = cases_deaths_df[cases_deaths_df['country'].isin(country_list)]
excess_mortality_economist_df = excess_mortality_economist_df[excess_mortality_economist_df['country'].isin(country_list)]

df_list = [cases_deaths_df, excess_mortality_economist_df]

def processor(df):
      # Check if the 'date' column has type 'datetime64[ns]' and if not, convert it to datetime
      min_date, max_date ='2019-01-01', '2024-01-01'
      if 'date' in df.columns:
            if df['date'].dtype != 'datetime64[ns]':
                  df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
      else:
            if df['Date'].dtype != 'datetime64[ns]':
                  df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
      
      print("-" * 60)
      print(f"Initial non-null values: {df.notnull().sum().sum()}, Total values: {df.size}, Percent non-null values: {df.notnull().sum().sum() / df.size * 100:.2f}%")
      
      if 'date' in df.columns:
            df = df[df['date'].between(min_date, max_date)]
      else:
            df = df[df['Date'].between(min_date, max_date)]

      if ('country' in df.columns) or ('Country' in df.columns):
            if 'country' in df.columns:
                  for country in tqdm(df['country'].unique()):
                        mask = df['country'] == country
                        df.loc[mask] = df.loc[mask].infer_objects(copy=False).interpolate(method='linear', limit_direction='both', axis=0)
            else:
                  for country in tqdm(df['Country'].unique()):
                        mask = df['Country'] == country
                        df.loc[mask] = df.loc[mask].infer_objects(copy=False).interpolate(method='linear', limit_direction='both', axis=0)

      else:
            df = df.infer_objects(copy=False).interpolate(method='linear', limit_direction='both', axis=0)
      
      print(f"Final non-null values: {df.notnull().sum().sum()}, Total values: {df.size}, Percent non-null values: {df.notnull().sum().sum() / df.size * 100:.2f}%\n")
      return df

with warnings.catch_warnings():
      warnings.simplefilter("ignore", FutureWarning)
      for i in range(len(df_list)):
            df_list[i] = processor(df_list[i])
      
      df_merged = reduce(lambda left, right: pd.merge(left, right, on=['country', 'date'], how='outer'), df_list)
      df_merged = processor(df_merged)

df_merged[['cumulative_estimated_daily_excess_deaths_per_100k', 'cumulative_estimated_daily_excess_deaths_ci_95_top_per_100k', 'cumulative_estimated_daily_excess_deaths_ci_95_bot_per_100k', 'estimated_daily_excess_deaths_per_100k', 'estimated_daily_excess_deaths_ci_95_top_per_100k', 'estimated_daily_excess_deaths_ci_95_bot_per_100k']] = df_merged[['cumulative_estimated_daily_excess_deaths_per_100k', 'cumulative_estimated_daily_excess_deaths_ci_95_top_per_100k', 'cumulative_estimated_daily_excess_deaths_ci_95_bot_per_100k', 'estimated_daily_excess_deaths_per_100k', 'estimated_daily_excess_deaths_ci_95_top_per_100k', 'estimated_daily_excess_deaths_ci_95_bot_per_100k']]*10
df_merged.columns = ['Country', 'Date', 'New Cases per Million', 'New Deaths per Million', 'Total Cases per Million', 'Total Deaths per Million', 'CFR', 'Cumulative Estimated Daily Excess Deaths per Million', 'Cumulative Estimated Daily Excess Deaths CI 95 Top per Million', 'Cumulative Estimated Daily Excess Deaths CI 95 Bot per Million', 'Estimated Daily Excess Deaths per Million', 'Estimated Daily Excess Deaths CI 95 Top per Million', 'Estimated Daily Excess Deaths CI 95 Bot per Million']
df_merged['Cumulative Excess Deaths to Case Deaths'] = df_merged['Cumulative Estimated Daily Excess Deaths per Million']/ df_merged['Total Deaths per Million'].where((df_merged['Total Deaths per Million'].notna()) & (df_merged['Total Deaths per Million'] !=0))

df_merged = df_merged.drop(columns=["New Cases per Million", "Total Cases per Million", 'Estimated Daily Excess Deaths CI 95 Top per Million', 'Estimated Daily Excess Deaths CI 95 Bot per Million', 'Cumulative Estimated Daily Excess Deaths CI 95 Top per Million', 'Cumulative Estimated Daily Excess Deaths CI 95 Bot per Million'])

df_merged.to_csv(config.DATASET_DIR / 'national_data.csv', index = False, date_format='%Y-%m-%d')
df_global_mean = df_merged.drop(columns=['Country']).groupby(['Date']).mean().reset_index()

df_global_mean = processor(df_global_mean)

df_global_mean['Cumulative Mean Excess Deaths to Case Deaths'] = (df_global_mean['Cumulative Estimated Daily Excess Deaths per Million']/ df_global_mean['Total Deaths per Million']).where((df_global_mean['Total Deaths per Million'].notna()) & (df_global_mean['Total Deaths per Million'] !=0))
df_global_mean['Cumulative Excess Deaths to Case Deaths'] = (df_global_mean['Cumulative Estimated Daily Excess Deaths per Million']/ df_global_mean['Total Deaths per Million']).where((df_global_mean['Total Deaths per Million'].notna()) & (df_global_mean['Total Deaths per Million'] !=0))
df_global_mean['Estimated Daily CFR'] = (df_global_mean['Estimated Daily Excess Deaths per Million']* df_global_mean['CFR']/ df_global_mean['New Deaths per Million']).where((df_global_mean['New Deaths per Million'].notna()) & (df_global_mean['New Deaths per Million'] !=0))
df_global_mean['Estimated Cumulative CFR'] = (df_global_mean['Cumulative Estimated Daily Excess Deaths per Million']* df_global_mean['CFR']/ df_global_mean['Total Deaths per Million']).where((df_global_mean['Total Deaths per Million'].notna()) & (df_global_mean['Total Deaths per Million'] !=0))
df_global_mean.interpolate(method='linear', limit_direction='both',inplace=True)

df_global_mean.to_csv(config.DATASET_DIR / 'global_mean_data.csv', index = False, date_format='%Y-%m-%d')