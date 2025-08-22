import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# Set page configuration
st.set_page_config(page_title="Daily Vaccination & Recovery Dashboard", layout="wide")

# Constants
DATA_FILE_PATH = os.path.join("Datasets","Daily Analysis","daily_analysis_data.csv")

@st.cache_data
def load_cleaned_temporal_data():
    df = pd.read_csv(DATA_FILE_PATH)
    df["date"] = pd.to_datetime(df["date"])
    exclude_keywords = [
        "World", "income", "countries", "region", "European Union", "Asia", "Africa",
        "America", "Oceania", "Other", "High-income", "Upper-middle", "Lower-middle",
        "Low-income", "International", "EU", "excl."
    ]
    df = df[~df["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)]
    return df

temporal_df = load_cleaned_temporal_data()



# Peak values with dates
peak_cases = temporal_df.loc[temporal_df.groupby("country")["new_cases"].idxmax()]
top10_cases_peak = peak_cases.nlargest(10, "new_cases")[["country", "new_cases", "date"]]
top10_cases_peak["date_str"] = top10_cases_peak["date"].dt.strftime("%Y-%m-%d")

peak_deaths = temporal_df.loc[temporal_df.groupby("country")["new_deaths"].idxmax()]
top10_deaths_peak = peak_deaths.nlargest(10, "new_deaths")[["country", "new_deaths", "date"]]
top10_deaths_peak["date_str"] = top10_deaths_peak["date"].dt.strftime("%Y-%m-%d")

# Pie Charts
col1, col2 = st.columns(2)
with col1:
    st.markdown("Top 10 Countries by Highest Daily New Cases")
    fig_peak_cases = px.pie(
        top10_cases_peak,
        names="country",
        values="new_cases",
        title="Highest Single-Day New Cases",
        color_discrete_sequence=px.colors.qualitative.Set3,
        custom_data=["date_str"]
    )
    fig_peak_cases.update_traces(
        hovertemplate="<b>%{label}</b><br>New Cases: %{value:,}<br>Date: %{customdata[0]}<extra></extra>"
    )
    st.plotly_chart(fig_peak_cases, use_container_width=True)

with col2:
    st.markdown("Top 10 Countries by Highest Daily New Deaths")
    fig_peak_deaths = px.pie(
        top10_deaths_peak,
        names="country",
        values="new_deaths",
        title="Highest Single-Day New Deaths",
        color_discrete_sequence=px.colors.qualitative.Set3,
        custom_data=["date_str"]
    )
    fig_peak_deaths.update_traces(
        hovertemplate="<b>%{label}</b><br>New Deaths: %{value:,}<br>Date: %{customdata[0]}<extra></extra>"
    )
    st.plotly_chart(fig_peak_deaths, use_container_width=True)


# Sidebar Filters
# -------------------------
with st.sidebar:
    st.header("Filters")

    # Filter valid dates
    valid_day_data = temporal_df.dropna(subset=["new_cases", "new_deaths"])
    valid_day_data = valid_day_data[(valid_day_data["new_cases"] > 0) | (valid_day_data["new_deaths"] > 0)]
    valid_dates = pd.to_datetime(valid_day_data["date"].unique()).date
    min_date = min(valid_dates)
    max_date = max(valid_dates)

    selected_date = st.date_input("📅 Select a Date", value=max_date, min_value=min_date, max_value=max_date)


    # Chart mode selection
    bubble_mode = st.radio(
        "🫧 Bubble Chart Mode",
        options=["All Countries", "Top 10 by New Cases", "Top 10 by New Deaths", "Custom Selection"],
        index=0
    )

    # Country list with optional aggregates
    exclude_keywords = [
        "World", "income", "countries", "region", "European Union", "Asia", "Africa",
        "America", "Oceania", "Other", "High-income", "Upper-middle", "Lower-middle",
        "Low-income", "International", "EU", "excl."
    ]

    full_country_list = sorted(pd.read_csv(DATA_FILE_PATH)["country"].unique())
    selected_countries = []

    if bubble_mode == "Custom Selection":
        default_top10_countries = top10_cases_peak["country"].tolist()
        selected_countries = st.multiselect(
            "🌍 Select Countries or Aggregated Regions",
            options=full_country_list,
            default=default_top10_countries
        )


# Bubble Chart
# -------------------------
st.subheader("🫧 New Cases vs New Deaths")

bubble_data = valid_day_data[valid_day_data["date"].dt.date == selected_date]

if bubble_mode == "Custom Selection":
    bubble_data = bubble_data[bubble_data["country"].isin(selected_countries)]
else:
    bubble_data = bubble_data[
        ~bubble_data["country"].str.contains('|'.join(exclude_keywords), case=False, na=False)
    ]
    if bubble_mode == "Top 10 by New Cases":
        bubble_data = bubble_data.nlargest(10, "new_cases")
    elif bubble_mode == "Top 10 by New Deaths":
        bubble_data = bubble_data.nlargest(10, "new_deaths")

if bubble_data.empty:
    st.warning("⚠ No data available for this selection on this date.")
else:
    fig_bubble = px.scatter(
        bubble_data,
        x="new_cases",
        y="new_deaths",
        size="new_cases",
        color="new_deaths",
        hover_name="country",
        color_continuous_scale="Reds",
        size_max=60,
        title=f"Date – {selected_date} ({bubble_mode})",
        labels={"new_cases": "New Cases", "new_deaths": "New Deaths"}
    )
    fig_bubble.update_layout(
        xaxis_title="New Cases",
        yaxis_title="New Deaths",
        height=600,
        margin=dict(l=80, r=40, t=60, b=40)
    )
    st.plotly_chart(fig_bubble, use_container_width=True)


# Bar Race Animation
# -------------------------
st.subheader("🎬Animation – New Cases & Deaths")

animation_end = selected_date
animation_end = pd.to_datetime(animation_end)


# Animation data is independent of sidebar filter
anim_data = temporal_df[temporal_df["date"] <= animation_end]

top10_cases_frames = (
    anim_data.sort_values(["date", "new_cases"], ascending=[True, False])
    .groupby("date").head(10)
)
top10_deaths_frames = (
    anim_data.sort_values(["date", "new_deaths"], ascending=[True, False])
    .groupby("date").head(10)
)
dates = top10_cases_frames["date"].sort_values().unique()

def build_adaptive_bar_race(df, value_col, title, color_scale):
    # Define bucket thresholds
    if value_col == "new_deaths":
        buckets = [10000, 50000, 100000, 250000]
    else:
        buckets = [10000,50000, 100000,150000,200000, 250000,300000,350000,400000,450000, 500000, 1000000, 2000000]

    # Start with the smallest bucket
    current_bucket_idx = 0
    current_bucket = buckets[current_bucket_idx]

    frames = []
    for date in dates:
        daily_data = df[df["date"] == date]
        max_val = daily_data[value_col].max()

        # Increase bucket only if the max_val crosses the current bucket
        if max_val > current_bucket and current_bucket_idx < len(buckets) - 1:
            while current_bucket_idx < len(buckets) - 1 and max_val > buckets[current_bucket_idx]:
                current_bucket_idx += 1
            current_bucket = buckets[current_bucket_idx]

        date_str = pd.to_datetime(str(date)).strftime('%Y-%m-%d')
        frames.append(
            go.Frame(
                data=[go.Bar(
                x=daily_data[value_col],
                y=daily_data["country"],
                orientation='h',
                marker=dict(color=daily_data[value_col], colorscale=color_scale),
                hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
                text=daily_data["country"],                 # <-- Only country name outside bar
                textposition="outside",
            )],

                name=date_str,
                layout=go.Layout(
                    xaxis=dict(range=[0, current_bucket])
                )
            )
        )

    # Initial frame uses the smallest bucket
    first_date = dates[0]
    init_data = df[df["date"] == first_date]
    first_date_str = pd.to_datetime(str(first_date)).strftime('%Y-%m-%d')

    fig = go.Figure(
        data=[go.Bar(
        x=init_data[value_col],
        y=init_data["country"],
        orientation='h',
        marker=dict(color=init_data[value_col], colorscale=color_scale),
        hovertemplate='%{y}: %{x:,.0f}<extra></extra>',
        width=0.7,
        text=init_data["country"],                 # <-- Only country name outside bar
        textposition="outside",
    )],

        layout=go.Layout(
            title=title,
            xaxis=dict(
            title=value_col.replace("_", " ").title(),
            tickformat="~s",
            range=[0, buckets[0]],
            fixedrange=True,
            showline=False,
            linewidth=2,
            linecolor='white',
            mirror=True
        ),

          yaxis=dict(
          title="",
          autorange="reversed",
          fixedrange=True,
          showticklabels=False,
          automargin=True,
          showline=False,
          linewidth=2,
          linecolor='white',
          mirror=True
        ),

            margin=dict(l=120, r=20, t=60, b=80),
            height=550,
            width=800,
            sliders=[dict(
                steps=[
                    dict(
                        method="animate",
                        args=[[pd.to_datetime(str(date)).strftime('%Y-%m-%d')], {"mode": "immediate"}],
                        label=pd.to_datetime(str(date)).strftime('%Y-%m-%d')
                    )
                    for date in dates
                ],
                transition={"duration": 0},
                x=0.1,
                xanchor="left",
                y=0,
                yanchor="top"
            )],
            updatemenus=[dict(
                type="buttons",
                direction="right",
                showactive=False,
                pad={"r": 10, "t": 10},
                x=0.5,
                y=1.25,
                xanchor="center",
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[None, {
                            "frame": {"duration": 300, "redraw": False},
                            "fromcurrent": True,
                            "transition": {"duration": 150}
                        }]
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], {
                            "mode": "immediate",
                            "frame": {"duration": 0, "redraw": False},
                            "transition": {"duration": 0}
                        }]
                    )
                ]
            )]
        ),
        frames=frames
    )
    return fig



fig_cases = build_adaptive_bar_race(
    top10_cases_frames, "new_cases", "Top 10 Countries by New Cases Over Time", "Blues"
)
fig_deaths = build_adaptive_bar_race(
    top10_deaths_frames, "new_deaths", "Top 10 Countries by New Deaths Over Time", "Reds"
)

st.plotly_chart(fig_cases, use_container_width=True)
st.plotly_chart(fig_deaths, use_container_width=True)

