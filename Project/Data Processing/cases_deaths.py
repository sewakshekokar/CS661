import pandas as pd
import sys
import os
import pycountry_convert as pc
import pycountry

INPUT_DIR = r'Datasets'
OUTPUT_DIR = os.path.join('Datasets', 'Disease Spread')

CASES_DEATHS_FILE_PATH = os.path.join(INPUT_DIR,'cases_deaths.csv')
COUNTRIES_FILE_PATH = os.path.join(INPUT_DIR,'countries.csv')
CASES_FILE_PATH = os.path.join(OUTPUT_DIR,'cases.csv')
DEATHS_FILE_PATH = os.path.join(OUTPUT_DIR,'deaths.csv')

def get_continent(alpha_3_code):
    try:
        country = pycountry.countries.get(alpha_3=alpha_3_code)
        if not country:
            return None
        alpha_2_code = country.alpha_2
        
        continent_code = pc.country_alpha2_to_continent_code(alpha_2_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except Exception as e:
        return None

def get_values(row):
    lat = countries_df[countries_df['country']==row.iloc[0]]['latitude'].values[0]
    long = countries_df[countries_df['country']==row.iloc[0]]['longitude'].values[0]
    isocode = countries_df[countries_df['country']==row.iloc[0]]['isocode'].values[0]
    continent = get_continent(isocode)

    return pd.Series([lat, long, isocode, continent])


cases_deaths_df = pd.read_csv(CASES_DEATHS_FILE_PATH)

cases_deaths_df['country'] = cases_deaths_df['country'].replace('World excl. China, South Korea, Japan and Singapore',
                                                  'World excl. China South Korea Japan and Singapore')

cases_deaths_df['date'] = pd.to_datetime(cases_deaths_df['date'])
cases_deaths_df = cases_deaths_df[cases_deaths_df['date'] <= pd.to_datetime('2024-01-01')]
cases_deaths_df['new_cases'] = cases_deaths_df['new_cases'].ffill()
cases_deaths_df['new_deaths'] = cases_deaths_df['new_deaths'].ffill()
cases_deaths_df['new_cases_per_million'] = cases_deaths_df['new_cases_per_million'].ffill()
cases_deaths_df['new_deaths_per_million'] = cases_deaths_df['new_deaths_per_million'].ffill()

cases_deaths_df['total_cases'] = cases_deaths_df['total_cases'].ffill()
cases_deaths_df['total_deaths'] = cases_deaths_df['total_deaths'].ffill()
cases_deaths_df['total_cases_per_million'] = cases_deaths_df['total_cases_per_million'].ffill()
cases_deaths_df['total_deaths_per_million'] = cases_deaths_df['total_deaths_per_million'].ffill()


cases_columns = ['country', 'date'] + [i for i in cases_deaths_df.columns if 'cases' in i]
deaths_columns = ['country', 'date'] + [i for i in cases_deaths_df.columns if 'deaths' in i]

countries_df = pd.read_csv(COUNTRIES_FILE_PATH)
spread_df = cases_deaths_df[['country','date', 'new_cases','total_cases', 'new_deaths', 'total_deaths',
                             'new_cases_per_million', 'total_cases_per_million',
                             'new_deaths_per_million', 'total_deaths_per_million']]

cases_df = cases_deaths_df[cases_columns]
deaths_df = cases_deaths_df[deaths_columns]

cases_df[['latititude', 'longitude', 'isocode','continent']] = cases_df.apply(get_values, axis=1)
cases_df['date'] = cases_df['date'].astype('str').str.split().str[0]
cases_df.to_csv(CASES_FILE_PATH, index=False)
    
deaths_df[['latititude', 'longitude', 'isocode','continent']] = deaths_df.apply(get_values, axis=1)
deaths_df['date'] = deaths_df['date'].astype('str').str.split().str[0]
deaths_df.to_csv(DEATHS_FILE_PATH, index=False)






