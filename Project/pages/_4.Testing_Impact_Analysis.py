import streamlit as st
import pandas as pd
import plotly.express as px
# import seaborn as sns
# import matplotlib.pyplot as plt
import plotly.graph_objects as go
import itertools
import os
# import matplotlib.dates as mdates

# Configure the app
st.set_page_config(layout="wide")
st.title("🌐 Global COVID-19 Testing Dashboard")

# Load the dataset
@st.cache_data
def load_data():
    df = pd.read_csv(os.path.join("Datasets","Testing","Testing_Impact_Analysis.csv"), parse_dates=["date"])
    
    # Ensure numeric columns are correctly typed
    numeric_cols = [
        "new_tests_per_thousand", "total_tests", "total_tests_per_thousand",
        "total_cases", "total_cases_per_million",
        "total_deaths", "total_deaths_per_million",
        "new_cases_per_million", "new_deaths_per_million",
        "new_tests", "new_cases", "new_deaths"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    
    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("Filter Data")
countries = df["country"].dropna().unique()
selected_country = st.sidebar.selectbox("Select Country", sorted(countries))

# Set safe default dates
min_date = df["date"].min().date()
max_date = df["date"].max().date()
date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# Ensure date_range has 2 elements
if len(date_range) != 2:
    st.error("Please select a valid date range.")
    st.stop()

start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# Filter data once and reuse
filtered_df = df[(df["country"] == selected_country) &
                (df["date"] >= start_date) &
                (df["date"] <= end_date)].copy()

# Summary Metrics Section
st.markdown("## 📌 Global Summary (Cumulative)")

# Calculate cumulative global totals using 'new_' columns
total_tests = int(df["new_tests"].sum(skipna=True))
total_cases = int(df["new_cases"].sum(skipna=True))
total_deaths = int(df["new_deaths"].sum(skipna=True))

# Display the metrics
col1, col2, col3 = st.columns(3)
col1.metric("🧪 Total Tests", f"{total_tests:,}")
col2.metric("🦠 Total Cases", f"{total_cases:,}")
col3.metric("☠️ Total Deaths", f"{total_deaths:,}")

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs([
    "🌍 Global Overview",
    "🌐 Compare Multiple Countries",
    f"📊{selected_country} Country-Specific Insights",
    
])




# ======== Tab 1: Global Overview ========
with tab1:
    st.subheader("🌍 Global Overview")

    map_df = df.dropna(subset=["new_tests_per_thousand", "country"])

    fig2 = px.choropleth(
        map_df,
        locations="country",
        locationmode="country names",
        color="new_tests_per_thousand",
        hover_name="country",
        animation_frame=map_df["date"].dt.strftime("%Y-%m-%d"),
        color_continuous_scale="Plasma",
        title="🌐 COVID-19 Testing Intensity Over Time (Tests per 1,000 people)"
    )
    fig2.update_geos(
        showcoastlines=True, coastlinecolor="Black",
        showland=True, landcolor="LightGray",
        showcountries=True, countrycolor="Gray",
        showframe=False
    )
    fig2.update_layout(
        geo=dict(projection_type="natural earth"),
        coloraxis_colorbar=dict(title="Tests per 1,000 People"),
        width=1000, height=600,
        margin=dict(t=50, r=30, l=30, b=30)
    )
    if fig2.layout.updatemenus:
        fig2.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 100
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    The code plots an animated global choropleth map 
    showing how COVID-19 testing rates (tests per 1,000 people) 
    changed over time, using country-level data colored by testing intensity.""")




    # 🌍 COVID-19 Testing Efforts Across Continents

    st.markdown("### 🌍 COVID-19 Testing Efforts Across Continents")

    # Dropdown to select metric
    continent_metric = st.selectbox(
        "Select Metric to View by Continent:",
        options=["Total Tests", "Tests per Thousand", "Tests per Million"],
        index=0
    )

    # Prepare continent-level data
    continent_df = df.dropna(subset=["continent"]).copy()

    if continent_metric == "Total Tests":
        latest_tests = continent_df.groupby('country')["total_tests"].max().reset_index()
        latest_tests = latest_tests.merge(continent_df[['country', 'continent']].drop_duplicates(), on='country')
        continent_summary = latest_tests.groupby('continent')["total_tests"].sum().reset_index()
        continent_summary["Total Tests (Millions)"] = continent_summary["total_tests"] / 1e6
        y_col = "Total Tests (Millions)"
        y_label = "Total Tests (in Millions)"
    elif continent_metric == "Tests per Thousand":
        continent_summary = continent_df.groupby('continent')["total_tests_per_thousand"].mean().reset_index()
        y_col = "total_tests_per_thousand"
        y_label = "Tests per Thousand"
    else:  # Tests per Million
        continent_summary = continent_df.groupby('continent')["total_tests_per_thousand"].mean().reset_index()
        continent_summary["total_tests_per_million"] = continent_summary["total_tests_per_thousand"] * 1000
        y_col = "total_tests_per_million"
        y_label = "Tests per Million"

    # Bar Chart
    fig_continent = px.bar(
        continent_summary,
        x="continent",
        y=y_col,
        color="continent",
        labels={y_col: y_label, "continent": "Continent"},
        title=f"{y_label} by Continent",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_continent.update_layout(
        yaxis_tickformat=',',
        title_x=0.5,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )

    st.plotly_chart(fig_continent, use_container_width=True)

    st.markdown("""
    It helps users easily compare COVID-19 testing levels across continents and understand regional 
    differences in testing efforts during the pandemic.""")





    # Title
    st.markdown("### 🏅 Top Countries by Total COVID-19 Tests (Absolute)")

    # Now the select box just under the heading
    top_n = st.selectbox(
        "Select Top N Countries:",
        options=[10, 15,20,25],
        index=0
    )

    # Group and sort
    top_total_tests = df.groupby("country")["total_tests"].max().sort_values(ascending=False).head(top_n).reset_index()

    # Create the bar chart
    fig_bar1 = px.bar(
        top_total_tests, x="country", y="total_tests",
        title="",  # remove internal Plotly title since we use markdown heading
        text_auto=True,
        color="total_tests", 
        color_continuous_scale=[
            "#FFFFFF",  # white
            "#7FDBFF",  # light blue
            "#0074D9",  # medium blue
            "#001f3f"   # dark blue
        ]
    )

    # Show the chart
    st.plotly_chart(fig_bar1, use_container_width=True)
    st.markdown("""
    It identifies the top countries with the highest absolute number of COVID-19 tests, 
    helping highlight where the largest testing efforts occurred globally.""")


    # Title
    st.markdown("### 📏 Top Countries by Tests per 1,000 People")

    # Select box for Top N countries
    top_n_per_thousand = st.selectbox(
        "Select Top N Countries (Per 1,000 People):",
        options=[10, 15, 20, 25],
        index=0
    )

    # Group and sort
    top_per_thousand = df.groupby("country")["total_tests_per_thousand"].max().sort_values(ascending=False).head(top_n_per_thousand).reset_index()

    # Create the bar chart
    fig_bar2 = px.bar(
        top_per_thousand,
        x="country",
        y="total_tests_per_thousand",
        title="",  # Title handled by markdown
        text_auto=True,
        color="total_tests_per_thousand",
        color_continuous_scale="Greens"  # Shades of green
    )

    # Styling
    fig_bar2.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )

    # Display chart
    st.plotly_chart(fig_bar2, use_container_width=True)
    st.markdown("""
    It shows which countries conducted the most COVID-19 tests relative to their population size, 
    highlighting testing intensity and public health responsiveness and healthcare infrastructure..""")









    # Title
    st.markdown("### 🚨 Bottom Countries by Tests per 1,000 People")

    # Select box for Bottom N countries
    bottom_n_per_thousand = st.selectbox(
        "Select Bottom N Countries (Per 1,000 People):",
        options=[10, 15, 20, 25],
        index=0
    )

    # Group and sort
    bottom_per_thousand = df.groupby("country")["total_tests_per_thousand"].max().sort_values(ascending=True).head(bottom_n_per_thousand).reset_index()

    # Create the bar chart
    fig_bar3 = px.bar(
        bottom_per_thousand,
        x="country",
        y="total_tests_per_thousand",
        title="",  # Title handled by markdown
        text_auto=True,
        color="total_tests_per_thousand",
        color_continuous_scale="Reds_r"  # Reversed Reds: darker = lower value
    )

    # Styling
    fig_bar3.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white")
    )

    # Display chart
    st.plotly_chart(fig_bar3, use_container_width=True)
    st.markdown("""This visualization highlights countries with the lowest COVID-19 testing rates relative to their population, 
    revealing gaps in healthcare infrastructure.""")




    # Step 1: Replace NaNs with 0 in new_tests
    df["new_tests"] = df["new_tests"].fillna(0)

    # Step 2: Group by date and sum daily tests across all countries
    global_daily_tests = df.groupby("date")["new_tests"].sum().reset_index()

    # Step 3: Calculate cumulative tests
    global_daily_tests["cumulative_tests"] = global_daily_tests["new_tests"].cumsum()

    # Step 4: Plot
    fig_area = px.area(
        global_daily_tests, x="date", y="cumulative_tests",
        title="🧮 Global Cumulative Tests Over Time",
        labels={"cumulative_tests": "Cumulative Tests", "date": "Date"}
    )
    st.plotly_chart(fig_area, use_container_width=True)


    st.markdown("""To show the global scale and growth of COVID-19 testing during the pandemic.""")







    


# ======== Tab 2: Compare Multiple Countries ========
with tab2:
    st.subheader("🌐 Compare Testing Metrics Across Countries")

    compare_countries = st.multiselect(
        "Select Countries to Compare",
        sorted(df["country"].dropna().unique()),
        default=["India", "United States", "United Kingdom"]
    )

    # Exclude 'total_tests' and 'total_tests_per_thousand' from this section
    metric_option = st.selectbox(
        "Select a Metric to Compare",
        ["new_tests", "new_tests_per_thousand"]
    )

    # High-contrast color palette
    color_palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ]
    color_cycle = itertools.cycle(color_palette)

    if compare_countries and metric_option:
        fig_compare = go.Figure()
        for country in compare_countries:
            color = next(color_cycle)
            country_data = df[(df["country"] == country) & (df["date"].between(start_date, end_date))]
            fig_compare.add_trace(go.Scatter(
                x=country_data["date"],
                y=country_data[metric_option],
                mode='lines',
                name=country,
                line=dict(color=color)
            ))

        fig_compare.update_layout(
            title=f"📈 {metric_option.replace('_', ' ').title()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric_option.replace("_", " ").title(),
            legend_title="Country",
            hovermode="x unified"
        )
        st.plotly_chart(fig_compare, use_container_width=True)
    else:
        st.info("ℹ️ Select at least one country and a metric to view the comparison.")




    st.markdown("""Compare how COVID-19 testing rates changed over time across multiple countries to observe testing 
                trends and pandemic responses.""")
   
    # Total Tests Comparison Section
    if 'compare_countries' in locals() and compare_countries:
        st.subheader("🧪 Total Tests Over Time (All Selected Countries)")

        # New dropdown for selecting total test type
        total_metric_option = st.selectbox(
            "Select Total Tests Metric",
            ["total_tests", "total_tests_per_thousand"],
            index=0
        )

        fig_total_tests = go.Figure()
        color_cycle = itertools.cycle([
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
            "#f0a3a3", "#76d7c4", "#ff9b8d", "#f7b7a3"
        ])

        for country in compare_countries:
            color = next(color_cycle)
            country_data = df[(df["country"] == country) & (df["date"].between(start_date, end_date))]
            fig_total_tests.add_trace(go.Scatter(
                x=country_data["date"],
                y=country_data[total_metric_option],
                mode='lines+markers',
                name=country,
                line=dict(color=color, width=0.8),  # Slimmest line
                marker=dict(size=5, symbol="circle", line=dict(width=1.5, color=color))  # Optional: reduce marker size too
            ))


        fig_total_tests.update_layout(
            title=f"🧪 {total_metric_option.replace('_', ' ').title()} Over Time by Country",
            xaxis_title="Date",
            yaxis_title=total_metric_option.replace("_", " ").title(),
            legend_title="Country",
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(tickangle=45)
        )
        st.plotly_chart(fig_total_tests, use_container_width=True)
    else:
        st.warning("Please select at least one country to view total tests over time.")

    st.markdown("""This graph is used to compare COVID-19 testing trends across selected countries over time, 
                offering insights into absolute testing volumes or per capita testing rates.
    """)


# ======== Tab 3: Country-Specific Insights ========
with tab3:
    st.header(f"{selected_country} Country-Specific Insights")

    # Filter data based on selected country and date range
    country_data = filtered_df.copy()

    # Calculate metrics
    country_data["positivity_rate"] = country_data.apply(
        lambda row: row["new_cases"] / row["new_tests"]
        if pd.notnull(row["new_cases"]) and pd.notnull(row["new_tests"]) and row["new_tests"] > 0
        else None,
        axis=1
    )
    
    country_data["tests_per_case"] = country_data["new_tests"] / country_data["new_cases"]
    country_data["cases_per_test"] = country_data["new_cases"] / country_data["new_tests"]
    country_data["new_tests_7day_avg"] = country_data["new_tests"].rolling(window=7).mean()
    country_data["cases_7day_avg"] = country_data["new_cases"].rolling(7).mean()
    country_data["tests_7day_avg"] = country_data["new_tests"].rolling(7).mean()
    country_data["tests_per_case_7day"] = country_data["tests_per_case"].rolling(7).mean()
    country_data["cases_per_test_7day"] = country_data["cases_per_test"].rolling(7).mean()
    country_data["case_fatality_rate"] = (country_data["new_deaths"] / country_data["new_cases"]) * 100
    country_data["cases_change"] = country_data["new_cases"].pct_change()
    country_data["tests_change"] = country_data["new_tests"].pct_change()

    # Streamlit selector
    st.subheader("📊 COVID-19 Trends")

    view_option = st.radio(
        "Select data view for the graph below:",
        options=["7-Day Moving Average", "Daily Counts"],
        index=0,
        horizontal=True
    )

    # Ensure required moving averages exist
    country_data["cases_7day_avg"] = country_data["new_cases"].rolling(window=7).mean()
    country_data["tests_7day_avg"] = country_data["new_tests"].rolling(window=7).mean()
    country_data["deaths_7day_avg"] = country_data["new_deaths"].rolling(window=7).mean()

    # Choose columns based on selection
    if view_option == "7-Day Moving Average":
        y_cases = country_data["cases_7day_avg"]
        y_tests = country_data["tests_7day_avg"]
        y_deaths = country_data["deaths_7day_avg"]

        peak_data = country_data[
            (country_data["cases_7day_avg"] > country_data["cases_7day_avg"].quantile(0.75)) &
            (country_data["cases_7day_avg"].shift(1) < country_data["cases_7day_avg"]) &
            (country_data["cases_7day_avg"].shift(-1) < country_data["cases_7day_avg"])
        ]
    else:
        y_cases = country_data["new_cases"]
        y_tests = country_data["new_tests"]
        y_deaths = country_data["new_deaths"]

        peak_data = country_data[
            (country_data["new_cases"] > country_data["new_cases"].quantile(0.75)) &
            (country_data["new_cases"].shift(1) < country_data["new_cases"]) &
            (country_data["new_cases"].shift(-1) < country_data["new_cases"])
        ]

    # Plot
    fig_toggle = go.Figure()

    fig_toggle.add_trace(go.Scatter(x=country_data["date"], y=y_cases, name="Cases", line=dict(color="red")))
    fig_toggle.add_trace(go.Scatter(x=country_data["date"], y=y_tests, name="Tests", line=dict(color="blue")))
    fig_toggle.add_trace(go.Scatter(x=country_data["date"], y=y_deaths, name="Deaths", line=dict(color="orange")))

    if not peak_data.empty:
        fig_toggle.add_trace(go.Scatter(
            x=peak_data["date"],
            y=peak_data[y_cases.name],
            mode="markers",
            name="Peak Periods",
            marker=dict(color="yellow", size=10, symbol="diamond")
        ))

    fig_toggle.update_layout(
        title=f"📊 COVID-19 Trends in {selected_country} — {view_option}",
        hovermode="x unified",
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right", yanchor="bottom")
    )

    st.plotly_chart(fig_toggle, use_container_width=True)


    st.markdown("""This graph illustrates the COVID-19 trends in selected country, 
            showing the 7-day moving averages (or daily counts) of cases, tests, and deaths over time. 
            Peaks in cases are highlighted with yellow diamond markers to indicate periods of high transmission. 
            The graph helps visualize the relationship between testing levels, case counts, and mortality trends during 
            the pandemic.
    """)

    # Plot testing efficiency over time
    fig_efficiency = go.Figure()

    fig_efficiency.add_trace(go.Scatter(
        x=country_data["date"], 
        y=country_data["tests_per_case_7day"],
        name="Tests per Case (7-day avg)",
        line=dict(color="blue")
    ))

    fig_efficiency.add_trace(go.Scatter(
        x=country_data["date"], 
        y=country_data["cases_per_test_7day"],
        name="Positivity Rate (7-day avg)",
        yaxis="y2",
        line=dict(color="red")
    ))

    st.subheader("📉 Testing Efficiency Trends")
    fig_efficiency.update_layout(
        title=f"Trends in {selected_country}",
        yaxis=dict(title="Tests per Case"),
        yaxis2=dict(
            title="Positivity Rate (%)",
            overlaying="y",
            side="right",
            tickformat=".0%",
            domain=[0, 1],
        ),
        hovermode="x unified",
        legend_title="Metrics"
    )

    st.plotly_chart(fig_efficiency, use_container_width=True)

    st.markdown("""This graph shows the COVID-19 testing efficiency trends. 
                It compares the 7-day average number of tests performed per positive case (blue line) 
                against the positivity rate percentage (red line) over time. High "Tests per Case" 
                values suggest broader testing, while spikes in the "Positivity Rate" indicate periods of widespread infection. 
                The chart highlights how testing intensity and infection rates evolved during the pandemic.""")

    # Average Positivity Rate Donut Chart
    st.subheader("📌 Average Positivity Rate Donut Chart")
    avg_positive_rate = country_data["positivity_rate"].dropna().mean()

    if not pd.isna(avg_positive_rate):
        positive = round(avg_positive_rate * 100, 2)
        negative = round(100 - positive, 2)
        fig_pie = px.pie(
            names=["Positive", "Negative"],
            values=[positive, negative],
            hole=0.5,
            title=f"🧪 Avg. Positivity Rate in {selected_country}: {positive:.2f}%",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("⚠️ Insufficient data to compute positivity rate donut chart.")

    st.markdown("""This donut chart visualizes the average COVID-19 positivity rate over the entire selected period. 
            It shows the proportion of positive versus negative test results,
            A lower positivity rate generally indicates wider testing coverage and better outbreak control.""")


