# MAIN CODE
from datetime import datetime
from time import sleep

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Set the page layout to be wide
st.set_page_config(layout="wide")

# Load data with caching
@st.cache_data
def load_data():
    """
    This function loads the main COVID-19 vaccination data from a CSV file, 
    converts the 'date' column to datetime type, and returns the dataframe.
    """
    df = pd.read_csv(os.path.join('Datasets','Vaccination','final.csv'))
    df['date'] = pd.to_datetime(df['date'])
    return df

# Load the manufacturer data with caching
@st.cache_data
def load_manufacturer_data():
    """
    This function loads the manufacturer data from a CSV file, 
    converts the 'date' column to datetime type, and returns the dataframe.
    """
    manu_df = pd.read_csv(os.path.join('Datasets','Vaccination','vaccinations_manufacturer.csv'))
    manu_df['date'] = pd.to_datetime(manu_df['date'])
    return manu_df

# Process data based on filters 
def process_data(df, start_date, end_date):
    """
    This function filters the main data by the selected date range and 
    returns the filtered dataframe along with the latest data for each country.
    """
    filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    latest_df = filtered_df.sort_values('date').groupby('country').last().reset_index()
    return filtered_df, latest_df

# Load initial data
df = load_data()
manu_df = load_manufacturer_data()

# Get country lists
main_countries = ['World'] + sorted(df[df['country'] != 'World']['country'].unique())
manu_countries = sorted(manu_df['country'].unique())

# Date range selector (slider to pick the date range)
min_date = df['date'].min().to_pydatetime()
max_date = df['date'].max().to_pydatetime()
start_date, end_date = st.sidebar.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date)
)

# Sidebar controls for filtering
st.sidebar.header("Filters")
selected_country = st.sidebar.selectbox(
    "Select primary Region/Country/Economy ",
    main_countries,
    format_func=lambda x: f"{x}{'*' if x in manu_countries else ''}",
    index=main_countries.index("United States") if "United States" in main_countries else 0
)

compare_countries = st.sidebar.multiselect(
    "Compare Regions/Countries/Economies", 
    [c for c in main_countries if c != 'World'],
    default=["United States", "India", "China", "Russia"]
)



# Process data based on date selection
filtered_df, latest_df = process_data(df, start_date, end_date)

# Main content
st.title("🌍 COVID-19 Vaccination Dashboard")

# Display main metrics columns
country_data = latest_df[latest_df['country'] == selected_country]
total_vax = country_data['total_vaccinations_interpolated'].values[0]
people_vax = country_data['people_vaccinated_interpolated'].values[0]
boosters = country_data['total_boosters_interpolated'].values[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(f"💉 Total Vaccinations ({selected_country})", f"{total_vax:,.0f}")
with col2:
    st.metric(f"💉 People Vaccinated ({selected_country})", f"{people_vax:,.0f}")
with col3:
    st.metric(f"💉 Total Boosters ({selected_country})", f"{boosters:,.0f}")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["Global Patterns", "Country Analysis", "Comparative View", "Vaccine Manufacturers"])

with tab1:
    st.header("Global Patterns")
    map_layout = dict(
        height=500,  
        margin=dict(l=0, r=0, t=40, b=0),  
        geo=dict(showframe=False, showcoastlines=True),
        coloraxis_colorbar=dict(
            thickness=20,
            lenmode='fraction',
            len=0.9,
            title_font=dict(size=14),
            tickfont=dict(size=12))
    )

    # Total Cases by Country (Choropleth map)
    st.subheader("1. Total Cases by Country")
    fig2 = px.choropleth(latest_df,
                        locations="country",
                        locationmode="country names",
                        labels={"country":"Country ","total_cases":"Total Cases"},
                        color="total_cases",
                        hover_name="country",
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=(0, 104e6))
    fig2.update_layout(**map_layout)
    fig2.update_layout(coloraxis_colorbar=dict(
        title="Cases",
        tickvals=[0, 25e6, 50e6, 75e6, 100e6],
        ticktext=["0M", "25M", "50M", "75M", "100M"]
    ))
    st.plotly_chart(fig2, use_container_width=True)

    # Total People Vaccinated by Country (Choropleth map)
    st.subheader("2. Total People Vaccinated by Country")
    fig1 = px.choropleth(latest_df,
                        locations="country",
                        locationmode="country names",
                        labels={"country":"Country ","people_vaccinated_interpolated":"Total People Vaccinated (Atleast 1 Dose)"},
                        color="people_vaccinated_interpolated",
                        hover_name="country",
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=(0, 1.5e9))
    fig1.update_layout(**map_layout)
    fig1.update_layout(coloraxis_colorbar=dict(
        title="Vaccinations",
        tickvals=[0, 0.3e9, 0.6e9, 0.9e9, 1.2e9, 1.5e9],
        ticktext=["0B", "0.3B", "0.6B", "0.9B", "1.2B", "1.5B"]
    ))
    st.plotly_chart(fig1, use_container_width=True)

    # Total Deaths by Country (Choropleth map)    
    st.subheader("3. Total Deaths by Country")
    fig3 = px.choropleth(latest_df,
                        locations="country",
                        locationmode="country names",
                        labels={"country":"Country ","total_deaths":"Total Deaths"},
                        color="total_deaths",
                        hover_name="country",
                        color_continuous_scale=px.colors.sequential.Plasma,
                        range_color=(0, 1.2e6))
    fig3.update_layout(**map_layout)
    fig3.update_layout(coloraxis_colorbar=dict(
        title="Deaths",
        tickvals=[0, 3e5, 6e5, 9e5, 1.2e6],
        ticktext=["0L", "3L", "6L", "9L", "12L"]
    ))
    st.plotly_chart(fig3, use_container_width=True)

    # Top Regions section
    st.subheader("4. Top Regions by Total Vaccinations")
    
    # Define categories
    CONTINENTS = ['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania']
    INCOME_GROUPS = [
        'High-income countries', 'Low-income countries',
        'Lower-middle-income countries', 'Upper-middle-income countries'
    ]
    SPECIAL_GROUPS = ['World', 'European Union (27)']

    # Region type selector
    region_type = st.radio(
        "Select Region Type:",
        ["Country", "Continent", "Income Group"],
        horizontal=True,
        key="region_type"
    )
    
    # Filter data based on selection
    if region_type == "Country":
        # Exclude all non-country entities
        filtered_data = latest_df[~latest_df['country'].isin(CONTINENTS + INCOME_GROUPS + SPECIAL_GROUPS)]
    elif region_type == "Continent":
        filtered_data = latest_df[latest_df['country'].isin(CONTINENTS)]
    else:  # Income Group
        filtered_data = latest_df[latest_df['country'].isin(INCOME_GROUPS)]

    # Get top entries (up to 10)
    top_regions = filtered_data.nlargest(10, 'total_vaccinations_interpolated')
    num_top = len(top_regions)  # Get actual number of entries

    # Create and display the chart
    fig = px.bar(
        top_regions,
        x='country',
        y='total_vaccinations_interpolated',
        title=f'Top {num_top} {region_type}s by Total Vaccinations',  # Dynamic title
        labels={'total_vaccinations_interpolated': 'Total Vaccinations',"country":"Country "}
    )
    st.plotly_chart(fig, use_container_width=True, key='top_vaccinations')


with tab2:    
    # Filter data for the selected country
    country_df = filtered_df[filtered_df['country'] == selected_country]
    
    # Vaccination Progress Over Time (Line chart)
    st.subheader(f"1. Vaccination Progress in {selected_country}")
    # Rename columns for better display in the chart
    renamed_df = country_df.rename(columns={
        'people_vaccinated_interpolated': 'People with At Least One Dose',
        'people_fully_vaccinated_interpolated': 'Fully Vaccinated People',
        'total_boosters_interpolated': 'People Who Received a Booster'
    })
    fig1 = px.line(
        renamed_df,
        x='date',
        y=['People with At Least One Dose', 'Fully Vaccinated People', 'People Who Received a Booster'],
        labels={'value': 'Number of People', 'variable': 'Vaccination Status', 'date': 'Date'},
        color_discrete_map={
            'People with At Least One Dose': '#1f77b4',
            'Fully Vaccinated People': '#ff7f0e',
            'People Who Received a Booster': '#2f7f0e'
        }
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Rename columns for better display in the rolling trends chart
    renamed_df = country_df.rename(columns={
        'rolling_vaccinations_6m': '6-Month Rolling Vaccinations',
        'rolling_vaccinations_9m': '9-Month Rolling Vaccinations',
        'rolling_vaccinations_12m': '12-Month Rolling Vaccinations'
    })

    st.subheader(f"2. Vaccination Rates Analysis in {selected_country}")

    # Define friendly label mappings for better readability
    x_axis_labels = {
        'daily_people_vaccinated_smoothed_per_hundred': 'Daily People Vaccinated per 100 People',
        'people_vaccinated_interpolated': 'Total People Vaccinated (At Least One Dose)',
        'people_fully_vaccinated_interpolated': 'Total Fully Vaccinated'
    }

    y_axis_labels = {
        'new_cases': 'New Cases per Day',
        'new_deaths': 'New Deaths per Day',
        'weekly_cases_per_million': 'Weekly Cases per Million',
        'weekly_deaths_per_million': 'Weekly Deaths per Million'
    }

    # Selection widgets with readable labels
    col1, col2 = st.columns(2)
    with col1:
        x_metric = st.selectbox("X-Axis Metric:", options=list(x_axis_labels.keys()), format_func=lambda x: x_axis_labels[x])
        
    with col2:
        y_metric = st.selectbox("Y-Axis Metric:", options=list(y_axis_labels.keys()), format_func=lambda x: y_axis_labels[x])

    # Create scatter plot with trendline
    hover_df = country_df.copy()
    hover_df['formatted_date'] = hover_df['date'].dt.strftime('%Y-%m-%d')

    fig_correlation = px.scatter(
        hover_df,
        x=x_metric,
        y=y_metric,
        trendline="lowess",
        hover_data={
            "formatted_date": True,
            x_metric: True,
            y_metric: True,
            "date": False  # hide raw date
        },
        labels={
            x_metric: x_axis_labels[x_metric],
            y_metric: y_axis_labels[y_metric],
            "formatted_date": "Date"
        }
    )
    st.plotly_chart(fig_correlation, use_container_width=True)

with tab3:
    # Check if countries are selected for comparison
    if not compare_countries:
        st.warning("Please select at least one country to compare")
    else:
        compare_df = latest_df[latest_df['country'].isin(compare_countries)]
        trend_df = filtered_df[filtered_df['country'].isin(compare_countries)]
        
        st.subheader("1. Vaccination Volume Comparison")
        col1, col2 = st.columns(2)
        with col1:
            fig_total = px.bar(compare_df, x='country', y='total_vaccinations_interpolated',
                             labels={'total_vaccinations_interpolated': 'Total Vaccinations',
                                    'country': 'Country'},
                             title='Total Administered Vaccinations')
            st.plotly_chart(fig_total, use_container_width=True)
        
        with col2:
            fig_people = px.bar(compare_df, x='country', y='people_vaccinated_interpolated',
                              labels={'people_vaccinated_interpolated': 'People Vaccinated',
                                     'country': 'Country'},
                              title='People Vaccinated (At Least 1 Dose)')
            st.plotly_chart(fig_people, use_container_width=True)

        st.subheader("2. Daily Vaccination Rate Trends")
        trend_options = {
            'daily_vaccinations_smoothed': 'Daily Vaccinations',
            'daily_people_vaccinated_smoothed': 'People Receiving 1st Dose',
            'daily_people_vaccinated_smoothed_per_hundred': 'Vaccinations per 100 People/Day',
            'daily_vaccinations_smoothed_per_million': 'Vaccinations per Million/Day'
        }
        selected_trend = st.selectbox("Select Trend Metric:", options=list(trend_options.keys()),
                                    format_func=lambda x: trend_options[x])
        
        fig_trend = px.line(trend_df, x='date', y=selected_trend, color='country',
                          labels={'date': 'Date', selected_trend: trend_options[selected_trend]})
        st.plotly_chart(fig_trend, use_container_width=True)

with tab4:
    # Check if selected country has manufacturer data  
    if selected_country not in manu_countries:
        st.warning(f"No manufacturer data available for {selected_country} (* = has manufacturer data)")
        st.write("**Available countries with manufacturer data:**")
        cols = st.columns(4)
        for idx, country in enumerate(manu_countries):
            with cols[idx % 4]:
                st.markdown(f"• {country}")
    else:
        manu_filtered = manu_df[(manu_df['date'] >= start_date) & (manu_df['date'] <= end_date)]
        country_data = manu_filtered[manu_filtered['country'] == selected_country]
       
        # Vaccine Market Share in the selected country (Pie chart)
        st.subheader(f"1. Vaccine Market Share in {selected_country}")
        if not country_data.empty:
            # Get the latest data for each vaccine
            latest_data = country_data.sort_values('date').groupby('vaccine').last().reset_index()
            # Calculate total vaccinations across all vaccines
            total_vaccinations = latest_data['total_vaccinations'].sum()
            # Step 1: Calculate percentage share for each vaccine
            latest_data['percentage'] = (
                latest_data['total_vaccinations'] / total_vaccinations * 100
            ).round(1)
            # Step 2: Create custom label with value and percentage
            latest_data['label'] = latest_data.apply(
                lambda row: f"{row['vaccine']}: {row['total_vaccinations']:,} ({row['percentage']}%)",
                axis=1
            )
            # Step 3: Create pie chart
            fig_pie = px.pie(
                latest_data,
                names='vaccine',
                values='total_vaccinations',  # Used to size the slices
                hole=0.3,
                labels={'total_vaccinations': 'Total Vaccinations', 'percentage': 'Percentage','vaccine':'Vaccine'},
                hover_data=['percentage']     # Tooltip will include the percentage
            )
            # Show label inside each slice (value + percent + custom label)
            fig_pie.update_traces(
                text=latest_data['label'],
                textinfo='label+percent+value'
            )
            # Step 4: Display chart in Streamlit
            st.plotly_chart(fig_pie, use_container_width=True)

        # Vaccine Distribution over Time (Bar chart)
        st.subheader(f"2. Vaccine Distribution over Time in {selected_country}")
        if not country_data.empty:
            # Step 1: Total vaccinations per vaccine across countries
            vaccine_order = country_data.groupby('vaccine')['total_vaccinations'].sum().sort_values().index.tolist()
            # Step 2: Create faceted bar chart (one subplot per country)
            fig = px.bar(
                country_data,
                x='date',
                y='total_vaccinations',
                color='vaccine',
                labels={'total_vaccinations': 'Total Vaccinations', 'date': 'Date','vaccine':'Vaccine'},
                barmode='stack',
                title='',
                category_orders={'vaccine': vaccine_order}
            )
            # Step 3: Format date on x-axis
            fig.update_layout(
                xaxis=dict(tickformat="%d-%b-%Y", tickangle=45),
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)

        # Manufacturer-Specific Analysis (Line chart)
        st.subheader(f"3. Manufacturer-Specific Analysis over Time in {selected_country}")
        
        # Get unique manufacturers for the selected country
        manufacturers = country_data['vaccine'].unique().tolist()
        
        # Manufacturer selection
        selected_manufacturers = st.multiselect(
            "Select Vaccine Manufacturers",
            options=manufacturers,
            default=["Pfizer/BioNTech", "Moderna"],
            help="Choose manufacturers to compare"
        )
        
        if selected_manufacturers:
            # Filter data for selected manufacturers
            filtered_data = country_data[country_data['vaccine'].isin(selected_manufacturers)]
            # Vaccine distribution by manufacturer (Line chart)
            fig_trend = px.line(
                    filtered_data,
                    x='date',
                    y='total_vaccinations',
                    color='vaccine',
                    markers=True,
                    labels={'total_vaccinations': 'Total Vaccinations', 'date': 'Date','vaccine':'Vaccine'},
                    title=f'Vaccination Progress by Manufacturer'
                )
            st.plotly_chart(fig_trend, use_container_width=True)

                
            # Raw data view
            with st.expander("View Raw Manufacturer Data"):
                st.dataframe(filtered_data.sort_values('date', ascending=False))



# Footer
st.markdown("---")
st.markdown("Data Source: [Our World in Data](https://ourworldindata.org/covid-vaccinations)")
