import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
# ------------------- Page Config -------------------
st.set_page_config(
    page_title="India COVID-19 Dashboard",
    layout="wide",
    page_icon="🦠"
)

# ------------------- Data Loading Functions -------------------
@st.cache_data
def load_covid_data():
    file_path = os.path.join("Datasets", "Impacts_in_India", "statewise_daily_totals.csv")
    return pd.read_csv(file_path, parse_dates=['Date'], dayfirst=True)

@st.cache_data
def load_population_data():
    file_path = os.path.join("Datasets", "Impacts_in_India", "population_india_census2011.csv")
    pop = pd.read_csv(file_path)
    pop['Density'] = pop['Density'].str.extract(r'(\d+)').astype(float)
    return pop

@st.cache_data
def load_district_data():
    data_path = os.path.join("Datasets", "Impacts_in_India", "cleaned_data.csv")
    centroid_path = os.path.join("Datasets", "Impacts_in_India", "district wise centroids.csv")
    df = pd.read_csv(data_path, parse_dates=["Date"])
    centroids = pd.read_csv(centroid_path)
    return df, centroids

@st.cache_data 
def load_age_data():
    file_path = os.path.join("Datasets", "Impacts_in_India", "agegender_cleaneddata.csv")
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["age", "gender", "current_status"])
    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df = df.dropna(subset=["age"])
    df["age_group"] = df["age"].apply(lambda x: "< 40" if x < 40 else "40 - 60" if x <= 60 else "> 60")
    return df


# ------------------- Main App -------------------
st.title("📊 India COVID-19 Comprehensive Dashboard")
st.markdown("### A comprehensive view of COVID-19 statistics across India")

tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Overall & Statewise",
    "🧑👥🧑 Population Analysis",
    "🗺️ District Classification", 
    "👫 Age/Gender Analysis"
])

# ------------------- Tab 1: Original app1 + app2 + app3 -------------------
with tab1:
    # ---------- From app1.py ----------
    st.title("🫧 COVID-19 Animated Bubble Chart (India - Statewise)")
    st.markdown("An animated view of how different states fared over time.")

    df = load_covid_data()
    states = sorted(df['State'].unique())
    default_states = ["Tamil Nadu", "Uttar Pradesh", "West Bengal", "Gujarat"]
    selected_states = st.multiselect("🎯 Filter States:", states, default=default_states)

    # Axis selectors
    x_metric = st.selectbox("📅 Select X-axis Metric:", ["Date", "Confirmed", "Recovered", "Deceased"], index=0)
    y_metric = st.selectbox("📈 Select Y-axis Metric:", ["Confirmed", "Recovered", "Deceased"], index=1)

    filtered_df = df[df['State'].isin(selected_states)]

    # Ensure Date column is in datetime format
    filtered_df['Date'] = pd.to_datetime(filtered_df['Date'])

    # Calculate axis ranges
    x_range = [filtered_df[x_metric].min(), filtered_df[x_metric].max()] if x_metric != "Date" else [filtered_df['Date'].min(), filtered_df['Date'].max()]
    y_range = [0, filtered_df[y_metric].max() * 1.1]

    # Create animated scatter plot
    fig = px.scatter(
        filtered_df,
        x=x_metric,
        y=y_metric,
        animation_frame="Date",
        animation_group="State",
        size="Deceased",
        color="State",
        hover_name="State",
        size_max=50,
        range_x=x_range,
        range_y=y_range,
        title=f"COVID-19 Bubble Chart: {x_metric} vs {y_metric}"
    )

    # Keep animation speed same
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 200 / 7

    st.plotly_chart(fig, use_container_width=True)

    
    # ---------- From app2.py ----------
    st.title("📊 India COVID-19 Daily Totals")
    st.markdown("Stacked bar chart of daily total Confirmed, Recovered, and Deceased cases aggregated across all states.")

    # Group data
    daily = df.groupby("Date")[["Confirmed", "Recovered", "Deceased"]].sum().reset_index()

    # Define more vibrant and visually appealing colors
    colors = {"Confirmed": "#FF6F61",   # Soft coral red for Confirmed
            "Recovered": "#4CAF50",   # Vibrant green for Recovered
            "Deceased": "#FFEB3B"}   # Bright yellow for Deceased

    # Create the figure
    fig = go.Figure()

    # Add bars for each category
    fig.add_trace(go.Bar(
        x=daily["Date"],
        y=daily["Confirmed"],
        name="Confirmed",
        marker_color=colors["Confirmed"],
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Confirmed: %{y:,}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=daily["Date"],
        y=daily["Recovered"],
        name="Recovered",
        marker_color=colors["Recovered"],
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Recovered: %{y:,}<extra></extra>"
    ))

    fig.add_trace(go.Bar(
        x=daily["Date"],
        y=daily["Deceased"],
        name="Deceased",
        marker_color=colors["Deceased"],
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Deceased: %{y:,}<extra></extra>"
    ))

    # Styling the layout
    fig.update_layout(
        barmode="stack",  # Stacking the bars
        title="📅 COVID-19 Daily Case Totals in India",
        xaxis_title="Date",
        yaxis_title="Number of Cases",
        template="plotly",  # Light mode template
        bargap=0.05,
        # plot_bgcolor="white",  # Set background color to white
        # paper_bgcolor="white",  # Set paper color to white
        # font=dict(color="black"),  # Set font color to black for visibility
        showlegend=True,
        legend=dict(
            title="Case Type",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)



    # ---------- From app3.py ----------
    st.title("🦠 COVID-19 Confirmed Cases - Animated Race Chart")

    col1, col2 = st.columns(2)
    with col1:
        range_type = st.selectbox("📊 Select Range Type:", ["Top N States", "Bottom N States"])
    with col2:
        n = st.slider("Select N", 3, 20, 10)

    df_cumulative = df.pivot(index="Date", columns="State", values="Confirmed").fillna(0)
    selected_states = df_cumulative.iloc[-1].sort_values(
        ascending=(range_type == "Bottom N States")
    ).head(n).index.tolist()

    df_long = df_cumulative[selected_states].reset_index().melt(
        id_vars="Date", var_name="State", value_name="Confirmed"
    )

    fig = px.bar(
        df_long,
        x="Confirmed",
        y="State",
        color="State",
        animation_frame=df_long["Date"].dt.strftime("%Y-%m-%d"),
        animation_group="State",
        orientation="h",
        range_x=[0, df_long["Confirmed"].max() * 1.2],
        title="📊 COVID-19 Confirmed Cases in India (Animated)",
        text="Confirmed"
    )

    fig.update_layout(
        yaxis={"categoryorder": "total descending"},
        updatemenus=[
            {
                "buttons": [
                    {
                        "args": [None, {
                            "frame": {"duration": 50, "redraw": True},
                            "transition": {"duration": 25},
                            "fromcurrent": True
                        }],
                        "label": "Play",
                        "method": "animate"
                    },
                    {
                        "args": [None, {
                            "frame": {"duration": 0, "redraw": False},
                            "transition": {"duration": 0}
                        }],
                        "label": "Pause",
                        "method": "animate"
                    }
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 87},
                "showactive": False,
                "type": "buttons",
                "x": 0.1,
                "xanchor": "right",
                "y": 0.1,
                "yanchor": "top"
            }
        ]
    )

    st.plotly_chart(fig, use_container_width=True)



# --# ------------------- Tab 2: Original app4 + app6 with state selection -------------------
with tab2:
    # State selection (keep this section identical)
    pop_data = load_population_data()
    covid_latest = load_covid_data().groupby("State").last().reset_index()
    merged = pd.merge(covid_latest, pop_data, on="State")
    
    all_states = merged['State'].unique().tolist()
    mandatory = ["Maharashtra", "Kerala", "Uttar Pradesh"]
    others = [s for s in all_states if s not in mandatory]
    default = mandatory + pd.Series(others).sample(4).tolist()[:7]
    
    selected_states = st.multiselect(
        "Select States:", 
        all_states,
        default=default,
        key="pop_states"
    )
    filtered_df = merged[merged['State'].isin(selected_states)]

    # Modified layout for side-by-side comparisons
    st.markdown('<div class="main-title">📊 COVID-19 Impact Analysis</div>', unsafe_allow_html=True)
    
    metrics = [
        ('Confirmed', 'Plasma', 'Confirmed Cases'),
        ('Recovered', 'Viridis', 'Recovered Cases'), 
        ('Deceased', 'Reds', 'Deceased Cases')
    ]
    
    for metric, color_scale, title in metrics:
        st.markdown(f'<div class="section-title">📈 {title}</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(
                filtered_df, x='Population', y=metric, color=metric,
                size='Population', log_x=True, hover_name='State',
                color_continuous_scale=color_scale,
                title=f'{title} vs Population'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                filtered_df, x='Density', y=metric, color=metric,
                size='Population', log_x=True, hover_name='State',
                color_continuous_scale=color_scale,
                title=f'{title} vs Population Density'
            )
            st.plotly_chart(fig, use_container_width=True)
# ------------------- Tab 3: Original app5.py -------------------  
with tab3:
    st.title("🗺️ COVID-19 District Zone Classification - May 2021")
    
    # Load the data
    df, centroids = load_district_data()
    
    # Filter data for May 2021
    df_may = df[(df['Date'].dt.month == 5) & (df['Date'].dt.year == 2021)]
    
    # Get max values for each district
    district_max = df_may.groupby("District")[['Confirmed', 'Recovered', 'Deceased']].max().reset_index()
    dist_merged = pd.merge(district_max, centroids, on="District")
    
    # Classify the districts based on the number of confirmed cases
    dist_merged['Classification'] = dist_merged['Confirmed'].apply(
        lambda c: 'Red' if c >= 20000 else 'Orange' if c >= 5000 else 'Green'
    )
    
    # Concatenate Confirmed, Recovered, and Deceased for hover info
    dist_merged['hover_data'] = (
        "<b>" + dist_merged['District'] + "</b><br>" +  # Bold the district name
        "Classification: " + dist_merged['Classification'] + "<br>" +
        "Latitude: " + dist_merged['Latitude'].astype(str) + "<br>" +
        "Longitude: " + dist_merged['Longitude'].astype(str) + "<br>" +
        "Confirmed: " + dist_merged['Confirmed'].astype(str) + "<br>" +
        "Recovered: " + dist_merged['Recovered'].astype(str) + "<br>" +
        "Deceased: " + dist_merged['Deceased'].astype(str)
    )
    
    # Create the scatter mapbox plot
    fig = px.scatter_mapbox(
        dist_merged,
        lat="Latitude",
        lon="Longitude",
        color="Classification",
        color_discrete_map={'Red': 'red', 'Orange': 'orange', 'Green': 'green'},
        mapbox_style="open-street-map",
        hover_name="District",  # Keep the district name for hover
        hover_data={"hover_data": True},  # Use the new hover data field
        zoom=3.5,
        height=700
    )
    
    # Update hover template to show district name, classification, latitude, longitude, and cases in the desired order
    fig.update_traces(hovertemplate='%{customdata[0]}')  # Only show the custom hover data field
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("🔍 View Data Table"):
        st.dataframe(dist_merged.sort_values("Confirmed", ascending=False))




# ------------------- Tab 4: Original app9.py -------------------
with tab4:
    st.title("COVID-19 Age & Genderwise infection")
    df = load_age_data()
    grouped = df.groupby(["gender", "age_group", "current_status"]).size().reset_index(name="count")
    
    names = ["Total"]
    parents = [""]
    values = [grouped["count"].sum()]
    
    for gender in grouped["gender"].unique():
        gender_total = grouped[grouped["gender"] == gender]["count"].sum()
        names.append(gender)
        parents.append("Total")
        values.append(gender_total)
        
        for age_group in grouped["age_group"].unique():
            age_total = grouped[(grouped["gender"] == gender) & (grouped["age_group"] == age_group)]["count"].sum()
            label = f"{gender}-{age_group}"
            names.append(label)
            parents.append(gender)
            values.append(age_total)
            
            for status in grouped["current_status"].unique():
                status_total = grouped[(grouped["gender"] == gender) & (grouped["age_group"] == age_group) & (grouped["current_status"] == status)]["count"].sum()
                names.append(f"{label}-{status}")
                parents.append(label)
                values.append(status_total)
    
    fig = px.sunburst(
        names=names,
        parents=parents,
        values=values,
        title="COVID-19 Sunburst: Gender → Age Group → Status",
        height=750,
        color_discrete_sequence=px.colors.qualitative.Vivid  # More vibrant colors
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------- Footer -------------------
st.markdown("---")
st.markdown("<center style='color: grey;'>Task 6: Analyzing COVID-19 impact in India</center>", unsafe_allow_html=True)
