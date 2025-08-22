import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.signal import savgol_filter

# ---------- Load Cleaned Data ----------
data_path = os.path.join("Datasets", "Mobility Analysis", "cleaned_data.parquet")
merged_df = pd.read_parquet(data_path)
merged_df["month"] = merged_df["date"].dt.to_period("M").astype(str)
merged_df["year"] = merged_df["date"].dt.year


st.title("Mobility Analysis")
# ---------- Sidebar ----------
st.sidebar.title("Filters")
min_date = merged_df["date"].min()
max_date = merged_df["date"].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)
# Filter merged_df based on selected date range
merged_df = merged_df[
    (merged_df["date"] >= pd.to_datetime(date_range[0])) &
    (merged_df["date"] <= pd.to_datetime(date_range[1]))
]

# ---------- Tabs ----------
global_tab, top_tab, single_tab, multi_tab,  = st.tabs(["🌍 Global Overview", "🌟 Top Countries", "🏳️ Single Country", "🌐 Multi-Country"])

# ---------- Global Overview ----------
with global_tab:
    st.info("Note: Google Mobility data was discontinued after October 15, 2022. Values may appear flat beyond this point due to no new updates.")
    st.subheader("1. Line Chart – Global Average Mobility Index Over Time")
    st.write("This line chart shows how the average global mobility index changed over time, reflecting the impact of global COVID-19 waves and policy changes on human movement.")
    global_avg_mobility = merged_df.groupby("date")["trend"].mean().reset_index()
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=global_avg_mobility["date"], y=global_avg_mobility["trend"],
                                  mode="lines", name="Mobility Index"))
    fig_line.update_layout(
        xaxis_title="Date",
        yaxis_title="Average Mobility Index (%)",
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )
    st.plotly_chart(fig_line, use_container_width=True)

    st.subheader("2. Bar Chart – Year-wise Global Average Mobility Index Comparison")
    st.write("This bar chart compares average global mobility by year, helping us observe year-over-year shifts due to lockdowns, reopenings, and vaccination rollouts.")
    yearly_avg_mobility = merged_df.groupby("year")["trend"].mean().reset_index()
    fig_bar = px.bar(
        yearly_avg_mobility,
        x="year",
        y="trend",
        text_auto=True,
        labels={"trend": "Mobility Index (%)", "year": "Year"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("3. Treemap – Mobility under Combined Government Policies")
    st.write("This treemap visualizes countries based on average mobility and combined policy stringency, highlighting how stronger restrictions typically correlate with reduced mobility.")
    # Define relevant columns
    policy_cols = [
        "c1m_school_closing", "c2m_workplace_closing",
        "c6m_stay_at_home_requirements", "c7m_restrictions_on_internal_movement"
    ]
    # Filter valid data
    treemap_data = merged_df.dropna(subset=["country", "trend"] + policy_cols)
    # Group and calculate policy strength
    treemap_grouped = treemap_data.groupby("country").agg({
        "trend": "mean",
        "c1m_school_closing": "mean",
        "c2m_workplace_closing": "mean",
        "c6m_stay_at_home_requirements": "mean",
        "c7m_restrictions_on_internal_movement": "mean"
    }).reset_index()
    treemap_grouped["policy_score"] = (
        treemap_grouped["c1m_school_closing"] +
        treemap_grouped["c2m_workplace_closing"] +
        treemap_grouped["c6m_stay_at_home_requirements"] +
        treemap_grouped["c7m_restrictions_on_internal_movement"]
    )
    # --- Zoom-In Slider ---
    min_score = int(treemap_grouped["policy_score"].min())
    max_score = int(treemap_grouped["policy_score"].max())
    score_range = st.slider(
        "Select Policy Strength Score Range (Zoom In)",
        min_value=min_score,
        max_value=max_score,
        value=(min_score, max_score)
    )
    filtered_data = treemap_grouped[
        (treemap_grouped["policy_score"] >= score_range[0]) &
        (treemap_grouped["policy_score"] <= score_range[1])
    ]
    fig_treemap = px.treemap(
        filtered_data,
        path=["country"],
        values="trend",
        color="policy_score",
        color_continuous_scale="Reds",
        labels={
            "trend": "Avg Mobility (%)",
            "policy_score": "Policy Strength Score"
        }
    )
    st.plotly_chart(fig_treemap, use_container_width=True)


# ---------- Top Countries ----------
with top_tab:
    # Selector inside the tab
    top_n = st.selectbox(
        "Select number of top countries to display",
        options=[5, 10, 15, 20, 25, 30],
        index=1  # Default is 10
    )

    st.subheader(f"1. Pareto Chart – Mobility in Top {top_n} Countries by COVID-19 Cases")
    st.write("This dual-axis Pareto chart highlights countries with the highest number of COVID-19 cases and compares their mobility patterns to observe possible correlations between mobility and infection spread.")
    # Filter out aggregates like continents
    country_level_df = merged_df[~merged_df["country"].str.contains("World|Asia|Africa|Europe|America|Oceania", case=False)]
    # Group and prepare data
    pareto_data = country_level_df.groupby("country", as_index=False).agg({
        "new_cases": "sum",
        "trend": "mean"
    }).rename(columns={"trend": "mobility_index"})
    pareto_data = pareto_data.dropna(subset=["new_cases", "mobility_index"])
    pareto_data["mobility_index"] = pareto_data["mobility_index"].round(2)
    # Sort and select top N
    top_cases_df = pareto_data.sort_values(by="new_cases", ascending=False).head(top_n)
    # Create Pareto chart
    fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
    # Bar: New Cases (Left Y-Axis)
    fig_pareto.add_trace(
        go.Bar(
            x=top_cases_df["country"],
            y=top_cases_df["new_cases"],
            name="New Cases",
            # text=top_cases_df["new_cases"].apply(lambda x: f"{x:,}"),
            # textposition="auto",
            marker_color="#1f77b4",
            hovertemplate="%{x}<br>New Cases: %{y:,}"
        ),
        secondary_y=False,
    )
    # Line: Mobility Index (Right Y-Axis)
    fig_pareto.add_trace(
        go.Scatter(
            x=top_cases_df["country"],
            y=top_cases_df["mobility_index"],
            name="Mobility Index",
            mode="lines+markers+text",
            # text=top_cases_df["mobility_index"].apply(lambda x: f"{x:.2f}%"),
            # textposition="top center",
            line=dict(color="#ff7f0e"),
            hovertemplate="%{x}<br>Mobility Index: %{y:.2f}%"
        ),
        secondary_y=True,
    )
    # Layout
    fig_pareto.update_layout(
        xaxis_title="Country",
        yaxis_title="Total COVID-19 Cases",               # Left Y-axis
        yaxis2_title="Avg. Mobility Index (%)",           # Right Y-axis
        legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"),
        margin=dict(t=50, b=50)
    )
    st.plotly_chart(fig_pareto, use_container_width=True)

    st.subheader(f"2. Funnel Chart – Top {top_n} Countries Ranked by Mobility Index")
    st.write("This funnel chart ranks countries purely based on their average mobility index, revealing which populations had the most movement freedom regardless of their case counts.")
    # Group and prepare mobility data
    mobility_data = country_level_df.groupby("country", as_index=False)["trend"].mean()
    mobility_data = mobility_data.dropna()
    mobility_data = mobility_data[mobility_data["trend"] > 0]
    mobility_data = mobility_data.sort_values(by="trend", ascending=False).head(top_n)
    mobility_data["trend"] = mobility_data["trend"].round(2)
    # Funnel chart
    fig_funnel = px.funnel(
        mobility_data,
        x="trend",
        y="country",
        labels={"trend": "Mobility Index (%)", "country": "Country"},
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

# ---------- Single Country ---------- with smoothing filter
with single_tab:
    st.info("Note: Google Mobility data was discontinued after October 15, 2022. Values may appear flat beyond this point due to no new updates.")
    
    countries_available = merged_df["country"].dropna().unique()
    selected_country = st.selectbox(
        "Select a Country",
        options=sorted(countries_available),
        index=list(sorted(countries_available)).index("United States") if "United States" in countries_available else 0
    )
    country_df = merged_df[merged_df["country"] == selected_country].copy()

    # Set index to date
    country_df = country_df.set_index("date")

    # Keep only numeric columns for resampling
    numeric_cols = ["trend", "new_cases"]
    country_df_numeric = country_df[numeric_cols]
    # Resample to daily, take mean, interpolate
    country_df_numeric = country_df_numeric.resample('D').mean().interpolate()

    # Reset index
    country_df_numeric = country_df_numeric.reset_index()

    # Apply Savitzky-Golay smoothing only if enough points
    if len(country_df_numeric) > 7:
        country_df_numeric["trend_smoothed"] = savgol_filter(country_df_numeric["trend"], window_length=7, polyorder=2)
    else:
        country_df_numeric["trend_smoothed"] = country_df_numeric["trend"]

    apply_smoothing = st.checkbox("Show Smoothed Mobility Trend", value=False)

    st.subheader(f"1. Dual Axis Chart – Mobility Index vs New COVID-19 Cases in {selected_country}")
    st.write("This chart overlays mobility trends with new COVID-19 cases for the selected country, helping us identify whether movement patterns align with surges or declines in infection rates.")
    fig_single_country = make_subplots(specs=[[{"secondary_y": True}]])
    # Mobility Index (left y-axis)
    fig_single_country.add_trace(
        go.Scatter(
            x=country_df_numeric["date"],
            y=country_df_numeric["trend_smoothed"] if apply_smoothing else country_df_numeric["trend"],
            name="Mobility Index (Smoothed)" if apply_smoothing else "Mobility Index",
            mode="lines",
            line=dict(color="green" if apply_smoothing else "blue"),
            hovertemplate="%{x}<br>Mobility Index: %{y:.2f}%"
        ),
        secondary_y=False
    )
    # New Cases (right y-axis)
    fig_single_country.add_trace(
        go.Scatter(
            x=country_df_numeric["date"],
            y=country_df_numeric["new_cases"],
            name="New Cases",
            mode="lines",
            line=dict(color="firebrick"),
            hovertemplate="%{x}<br>New Cases: %{y:,}"
        ),
        secondary_y=True
    )
    fig_single_country.update_layout(
        xaxis_title="Date",
        yaxis_title="Mobility Index (%)",
        yaxis2_title="New COVID-19 Cases",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=50, b=50)
    )
    st.plotly_chart(fig_single_country, use_container_width=True)

# ---------- Multi-Country ----------
with multi_tab:
    st.info("Note: Google Mobility data was discontinued after October 15, 2022. Values may appear flat beyond this point due to no new updates.")
    countries_available = merged_df["country"].dropna().unique()
    multi_countries = st.multiselect(
        "Select Countries to Compare",
        options=sorted(countries_available),
        default=["United States", "India", "Brazil"]
    )
    if multi_countries:
        # Extract unique years for filtering
        merged_df["year"] = merged_df["date"].dt.year
        years = sorted(merged_df["year"].dropna().unique())
        # Filter data for selected countries
        filtered = merged_df[merged_df["country"].isin(multi_countries)]
        
        st.subheader("1. Line Chart – Yearly Mobility Trend")
        st.write("This multi-country line chart compares mobility trends across years, revealing how movement patterns evolved across different stages of the pandemic.")
        # Resample or aggregate monthly if needed
        filtered["month"] = filtered["date"].dt.to_period("M").astype(str)
        # Group by month and country to get average monthly mobility
        monthly_trend = (
            filtered.groupby(["month", "country"], as_index=False)["trend"]
            .mean()
            .rename(columns={"trend": "Mobility Index (%)"})
        )
        fig = px.line(
            monthly_trend,
            x="month",
            y="Mobility Index (%)",
            color="country",
            markers=True,
            labels={"month": "Year", "country": "Country"}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("2. Bar Chart – Average Annual Mobility Comparison")
        st.write("This bar chart compares the selected countries' average mobility in a specific year, revealing how different regions responded to the pandemic in terms of movement restrictions.")
        selected_year = st.selectbox("Select Year", years, index=years.index(2021) if 2021 in years else 0)
        # Filter further by selected year
        filtered_year = filtered[filtered["year"] == selected_year]
        avg_mobility = (
            filtered_year.groupby("country", as_index=False)["trend"]
            .mean()
            .rename(columns={"trend": "avg_mobility"})
        )
        avg_mobility["avg_mobility"] = avg_mobility["avg_mobility"].round(2)
        avg_mobility = avg_mobility.sort_values(by="avg_mobility", ascending=False)
        fig_bar = px.bar(
            avg_mobility,
            x="country",
            y="avg_mobility",
            text="avg_mobility",
            labels={"avg_mobility": "Mobility Index (%)", "country": "Country"},
            title=f"Average Mobility Index in {selected_year} by Country",
            color="country",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_bar.update_traces(textposition="auto")
        fig_bar.update_layout(
            xaxis_title="Country",
            yaxis_title="Mobility Index (%)",
            xaxis_tickangle=-45,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Please select multiple countries from the sidebar.")
