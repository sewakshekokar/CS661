import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
import os

vaccination_data = os.path.join("Datasets","Daily Analysis","daily_vaccinations_and_icu_all_countries_data.csv")
recovery_data = os.path.join("Datasets","Daily Analysis","active_cases_and_estimated_recovery_data.csv")
# Load vaccination and ICU data
@st.cache_data
def load_data():
    df = pd.read_csv(vaccination_data)
    df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data
def load_recovery_data():
    df = pd.read_csv(recovery_data)
    df["date"] = pd.to_datetime(df["date"])
    return df

# Load datasets
df = load_data()
recovery_df = load_recovery_data()

# Define global constants
MAX_DATE = datetime(2024, 1, 1).date()
exclude_keywords = [
    "World", "income", "countries", "region", "European Union", "Asia", "Africa",
    "America", "Oceania", "Other", "High-income", "Upper-middle", "Lower-middle",
    "Low-income", "International", "EU", "excl."
]

# Sidebar filter for date
st.sidebar.header("Filters")
vax_dates = sorted(df["date"].dt.date.unique())
selected_date = st.sidebar.date_input(
    "📅 Select a Date",
    value=min(MAX_DATE, max(vax_dates)),
    min_value=min(vax_dates),
    max_value=MAX_DATE
)

# Top 10 countries for selected date (non-aggregated)
df_filtered = df[df["date"].dt.date == selected_date].copy()
df_filtered = df_filtered[~df_filtered["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)]
top10_countries = df_filtered.nlargest(10, "daily_vaccinations")["country"]
df_top10 = df_filtered[df_filtered["country"].isin(top10_countries)]

# Compute monthly recovery stats
recovery_df["month"] = recovery_df["date"].dt.to_period("M").dt.to_timestamp()
monthly_avg = recovery_df.groupby(["month", "country"], as_index=False)["estimated_recovery_rate"].mean()
monthly_avg["estimated_recovery_rate_percent"] = monthly_avg["estimated_recovery_rate"] * 100
monthly_avg["month_str"] = monthly_avg["month"].dt.strftime("%Y-%m")

# App title
st.title("Daily Vaccination & Recovery Dashboard")

# ------------------------
#  Vaccination & ICU Charts
# ------------------------
if not df_top10.empty:
    st.subheader("Vaccination & ICU Snapshot (Top Countries)")
    
    vax_metrics = [
    ("daily_vaccinations", f"💉 Total Doses Given on {selected_date}", "Blues"),
    ("new_people_vaccinated", f"🧍 New People Vaccinated on {selected_date}", "Purples"),
    ("new_people_fully_vaccinated", f"✅ New Fully Vaccinated People on {selected_date}", "Greens"),
    ]


    for col, title, color in vax_metrics:
        top = df_top10.nlargest(10, col)
        if top[col].sum() > 0:
            fig = px.bar(
                top.sort_values(col),
                x=col, y="country",
                orientation="h",
                color=col,
                color_continuous_scale=color,
                title=title
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    
    if "daily_occupancy_icu" in df_top10.columns:
        icu_data = df_top10[df_top10["daily_occupancy_icu"].notna() & (df_top10["daily_occupancy_icu"] > 0)]

        if not icu_data.empty:
            st.subheader("🛏 ICU Occupancy (Top Countries)")

            top_icu = icu_data.sort_values("daily_occupancy_icu", ascending=False).head(10)

            fig_icu = px.bar(
                top_icu,
                x="daily_occupancy_icu",
                y="country",
                orientation="h",
                color="daily_occupancy_icu",
                color_continuous_scale="Reds",
                title=f"ICU Occupancy on {selected_date}"
            )
            fig_icu.update_layout(
                height=400,
                yaxis=dict(autorange="reversed")  # Highest ICU at top
            )
            st.plotly_chart(fig_icu, use_container_width=True)
        else:
            st.info("⚠ No ICU occupancy data available for the selected date.")
            
            
#  Grouped Bar Chart – Active vs Estimated Recovered (Clarified)
# -------------------------
st.subheader("📊 Active vs Recovered Cases by Country (Selected Date)")

recovery_snapshot = recovery_df[recovery_df["date"].dt.date == selected_date].copy()

bar_mode = st.radio("Select Data Mode", ["Top 10 Active Cases", "Custom Country Selection"], horizontal=True)

if bar_mode == "Custom Country Selection":
    custom_countries = st.multiselect(
       "Select countries for custom selection",
        options=sorted(recovery_snapshot["country"].unique()),
        default=["India", "United States", "Brazil"]
    )
    recovery_bar_data = recovery_snapshot[recovery_snapshot["country"].isin(custom_countries)]
else:
    non_aggregated = ~recovery_snapshot["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)
    recovery_bar_data = recovery_snapshot[non_aggregated].nlargest(10, "active_cases")

if not recovery_bar_data.empty:
    long_df = pd.melt(
        recovery_bar_data,
        id_vars=["country"],
        value_vars=["active_cases", "estimated_recovered"],
        var_name="Metric",
        value_name="Value"
    )

    # Custom tooltip notes
    hover_map = {
        "active_cases": "Real-time snapshot of currently infected individuals",
        "estimated_recovered": "Recovered estimate from cases ~14 days ago"
    }
    long_df["Metric Description"] = long_df["Metric"].map(hover_map)

    fig_grouped_bar = px.bar(
        long_df,
        x="country",
        y="Value",
        color="Metric",
        barmode="group",
        hover_data=["Metric Description"],
        title=f"Active Cases (Real-Time) vs Estimated Recovered (~14 Days Prior) – {selected_date}",
        color_discrete_map={
            "active_cases": "orange",
            "estimated_recovered": "green"
        }
    )

    fig_grouped_bar.update_layout(height=600, xaxis_title="Country", yaxis_title="People")
    st.plotly_chart(fig_grouped_bar, use_container_width=True)
else:
    st.info("ℹ No data available for the selected countries and date.")

# -------------------------
#Monthly Choropleth Map
# -------------------------
st.subheader("🌍 Monthly Animated Choropleth Map: Estimated Recovery Rate")

choropleth_data = monthly_avg.dropna(subset=["estimated_recovery_rate_percent"])
fig_map = px.choropleth(
    choropleth_data,
    locations="country",
    locationmode="country names",
    color="estimated_recovery_rate_percent",
    animation_frame="month_str",
    hover_name="country",
    color_continuous_scale="Greens",
    range_color=[0, 100],
    title="🗺 Monthly Recovery Rate by Country",
    labels={"month_str": "Date "}  # <--- This changes the slider label
)

fig_map.update_geos(showcoastlines=True, showframe=False, projection_type="natural earth")
fig_map.update_layout(margin=dict(l=40, r=40, t=60, b=20))
st.plotly_chart(fig_map, use_container_width=True)


# -------------------------
# Line Chart: Recovery Rate Over Time (with working slider preview)
# -------------------------
st.subheader("📈 Estimated Recovery Rate Over Time")

# Top 3 real countries by total cases
non_agg = recovery_df[~recovery_df["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)]
top3_countries = non_agg.groupby("country")["total_cases"].max().nlargest(3).index.tolist()

# Multiselect UI
# Multiselect UI with label for the "Estimated Recovery Rate Over Time" chart
selected_countries = st.multiselect(
    label="Select Countries to Visualize Recovery Rate",  # Added label argument
    options=sorted(recovery_df["country"].unique()),
    default=top3_countries
)


# Filter for selected countries and valid dates
line_df = recovery_df[
    (recovery_df["country"].isin(selected_countries)) &
    (recovery_df["date"].dt.date <= MAX_DATE) &
    ~recovery_df["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)
]

# Draw line chart with slider preview
if not line_df.empty:
    fig_line = go.Figure()

    for country in selected_countries:
        country_data = line_df[line_df["country"] == country]
        fig_line.add_trace(go.Scatter(
            x=country_data["date"],
            y=country_data["estimated_recovery_rate"],
            mode="lines+markers",
            name=country,
           
        ))

    fig_line.update_layout(
        title="Estimated Recovery Rate Over Time",
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]
            ),
            rangeslider=dict(visible=True),  #Enables preview in slider
            type="date"
        ),
        yaxis=dict(title="Recovery Rate", tickformat=".0%", range=[0, 1]),
        height=500,
        margin=dict(l=40, r=40, t=60, b=40),
        template="plotly_white"
    )

    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("⚠ No recovery data available for the selected countries.")
