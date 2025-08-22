import streamlit as st
import pandas as pd
import plotly.express as px
import os
import numpy as np

DEATHS_FILE_PATH = os.path.join('Datasets','Disease Spread','deaths.csv')
CASES_FILE_PATH = os.path.join('Datasets','Disease Spread','cases.csv')

############# Loading CSV file and Caching them #####################################
def load_spread_df(path):
    spread_df = pd.read_csv(path)
    column_names = spread_df.columns.to_list()
    column_names = [i.replace("_"," ").title() for i in column_names]
    spread_df.columns = column_names
    return spread_df

def load_choropleth_df(df):
    choropleth_df = df.dropna()
    choropleth_df['Date'] = pd.to_datetime(choropleth_df['Date'])
    choropleth_df['year_month'] = choropleth_df['Date'].dt.to_period('M')
    choropleth_df = choropleth_df.groupby(['Country', 'year_month']).last().reset_index()
    choropleth_df.drop('year_month', axis=1, inplace=True)
    choropleth_df['Date'] = choropleth_df['Date'].dt.date
    return choropleth_df

################## Overview ###################################
@st.fragment
def continents_charts(cases_df, deaths_df):
    st.subheader("COVID-19 Impact by Continents")
    continents = ['Asia','Europe','North America', 'South America', 'Africa', 'Oceania']

    # cases_df = cases_df.dropna(subset=['Continent'])
    cases_df = cases_df[cases_df['Country'].isin(continents)].reset_index(drop=True)
    deaths_df = deaths_df[deaths_df['Country'].isin(continents)].reset_index(drop=True)

    col1, col2 = st.columns(2)
    with col1:
        st.radio(
                "Select the type of graph:",
                options=['Pie Chart', 'Bar Graph'],
                horizontal= True,
                index=0,
                key='overview_continents_graph_type'
            )
    with col2:
        if st.session_state.overview_continents_graph_type == 'Bar Graph':
            st.checkbox(
                    'Make the graphs realtive to population.',
                    value = False,
                    key='overview_continents_rel2pop',
                )
    
    col1, col2 =st.columns(2)
    with col1:
        title = "COVID-19 Cases by Continent"
        if st.session_state.overview_continents_graph_type == 'Pie Chart':
            fig = px.pie(cases_df,
                        names = "Country",
                        values= "Total Cases",
                        title= title,
                        )
        else:
            fig = px.bar(cases_df, 
                        x='Country', 
                        y='Total Cases' if not st.session_state.overview_continents_rel2pop else 'Total Cases Per Million', 
                        title=title,
                        labels={'Country': 'Continent'},
                    )
        st.plotly_chart(fig)
    with col2:
        title = "COVID-19 Deaths by Continent"
        if st.session_state.overview_continents_graph_type == 'Pie Chart':
            fig = px.pie(deaths_df,
                        names = "Country",
                        values= "Total Deaths",
                        title= title,
                        )
        else:
            fig = px.bar(deaths_df, 
                        x='Country', 
                        y='Total Deaths' if not st.session_state.overview_continents_rel2pop else 'Total Deaths Per Million', 
                        title=title,
                        labels={'Country': 'Continent'},
                    )
        st.plotly_chart(fig)

@st.fragment
def top_n_countries(cases_df, deaths_df):
    st.subheader("COVID-19 Top Countries Impacted")

    cases_df = cases_df.dropna(subset=['Isocode','Continent']).reset_index(drop=True)
    deaths_df = deaths_df.dropna(subset=['Isocode','Continent']).reset_index(drop=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.selectbox(
            "Choose the region",
            options=['World'] + list(cases_df['Continent'].unique()),
            index =0,
            key='overview_countries_region'
        )
    with col2:
        st.number_input(
            "Choose the number of countries",
             min_value=2, 
             max_value=8,
             value=2,
             key = "overview_contries_num")
    with col3:
        st.radio(
                "Select the type of graph:",
                options=['Pie Chart', 'Bar Graph'],
                index=0,
                horizontal= True,
                key='overview_contries_graph_type'
            )
    with col4:
        if st.session_state.overview_contries_graph_type == 'Bar Graph':
            st.checkbox(
                    'Make the graphs realtive to population.',
                    value = False,
                    key= 'overview_contries_rel2pop'
                )
    if st.session_state.overview_countries_region!= 'World':
        cases_df = cases_df[cases_df['Continent'] == st.session_state.overview_countries_region]
        deaths_df = deaths_df[deaths_df['Continent'] == st.session_state.overview_countries_region]

    col1, col2 =st.columns(2)
    with col1:
        title = "COVID-19 Cases by Country"
        if st.session_state.overview_contries_graph_type == 'Pie Chart':
            values = 'Total Cases'
            fig = px.pie(cases_df.sort_values(by=values, ascending = False).iloc[:st.session_state.overview_contries_num],
                        names = "Country",
                        values= values,
                        title= title,
                        )
        else:
            values = 'Total Cases' if not st.session_state.overview_contries_rel2pop else 'Total Cases Per Million'
            fig = px.bar(cases_df.sort_values(by=values, ascending = False).iloc[:st.session_state.overview_contries_num], 
                        x='Country', 
                        y=values, 
                        title=title,
                    )
        st.plotly_chart(fig)
    with col2:
        title = "COVID-19 Deaths by Country"
        if st.session_state.overview_contries_graph_type == 'Pie Chart':
            values = "Total Deaths"
            fig = px.pie(deaths_df.sort_values(by=values, ascending = False).iloc[:st.session_state.overview_contries_num],
                        names = "Country",
                        values= values,
                        title= title,
                        )
        else:
            values = 'Total Deaths' if not st.session_state.overview_contries_rel2pop else 'Total Deaths Per Million'
            fig = px.bar(deaths_df.sort_values(by=values, ascending = False).iloc[:st.session_state.overview_contries_num], 
                        x='Country', 
                        y=values, 
                        title=title,
                    )
        st.plotly_chart(fig)

def overview(cases_df, deaths_df):
    # st.subheader('Overview')
    total_cases = 773956770 
    total_deaths = 7016159
    case_fatality_rate = (total_deaths/total_cases)*100
    
    col1, col2, col3 = st.columns(3)
    
    col1.metric(label="Total COVID-19 Cases", value=f"{total_cases:,}")
    col2.metric(label="Total COVID-19 Deaths", value=f"{total_deaths:,}")
    col3.metric(label="Case Fatality Rate", value= f"{case_fatality_rate:.6f}%")
    
    continents_charts(cases_df.groupby('Country').tail(1).reset_index(drop=True),
                     deaths_df.groupby('Country').tail(1).reset_index(drop=True))
    top_n_countries(cases_df.groupby('Country').tail(1).reset_index(drop=True),
                     deaths_df.groupby('Country').tail(1).reset_index(drop=True))


############ Choropleth Animation #############################
@st.fragment
def choropleth_animation(cases_df, deaths_df):
    
    st.subheader("Choropleth Animation of Global and Regional Spread of the Disease Over Time")
     
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox(
            "Choose the scope.",
            ['World', 'Asia','Europe','Africa', 'North America', 'South America'],
            index = 0,
            key = 'map_scope'
        )

    with col2:
        st.selectbox(
            "Choose the metric.",
            ['Total Cases','Total Deaths'],
            index = 0,
            key = 'map_metric',
        )
    with col3:
        st.checkbox(
            'Make the graphs relative to population',
            value = False,
            key = 'map_rel2pop',
        )

    parameter = st.session_state.map_metric
    if st.session_state.map_rel2pop:
        parameter = parameter + " Per Million"

    dataframe = cases_df if st.session_state.map_metric == 'Total Cases' else deaths_df
    if st.session_state.map_scope=='World':
        range_color = [0,dataframe[parameter].quantile(0.95)]
    else:
        temp_df = dataframe[dataframe['Continent'] == st.session_state.map_scope]
        range_color = [0,temp_df[parameter].quantile(0.95)]
    fig = px.choropleth(
                data_frame= dataframe,
                locations='Isocode',
                color = parameter,
                hover_name='Country',
                color_continuous_scale='Greens',
                animation_frame='Date',
                title=f'{parameter} Over Time For {st.session_state.map_scope.title()}',
                range_color=range_color,
                scope=st.session_state.map_scope.lower(),
    )
    fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 300
    fig.layout.updatemenus[0].buttons[0].args[1]['transition']['duration'] = 0
    fig.update_layout(
        width=1500,  
        height = 500,
        margin=dict(l=0, r=0, t=50, b=0) 
    )
    st.plotly_chart(fig,use_container_width=False)

########################### Graphs ###############################
@st.fragment
def time_series_continents(cases_df, deaths_df):

    st.subheader("Timeseries Analysis-Continent Wise")
    st.multiselect(
            "Select the continents",
            ['World','Asia','Europe','North America', 'South America', 'Africa', 'Oceania'],
            default=['World','Asia','Europe'],
            key = 'time_series_continents',
        )
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.selectbox(
        "Choose the metric",
        ['Cases','Deaths'],
        index= 0,
        key = 'time_series_continents_metric'
        )
    with col2:
        st.selectbox(
            'Choose the interval',
            options=['Daily', 'Weekly','Biweekly','Cummulative'],
            index=0,
            key = 'time_series_continents_interval',
        )

    with col3:
        st.checkbox(
            'Make the graphs relative to population',
            value = False,
            key = 'time_series_continents_rel2pop',
        )
    
    with col4:
        if st.session_state.time_series_continents_interval == 'Cummulative':
            st.checkbox(
                "Use Log Scale", 
                value= False,
                key = 'time_series_continents_use_log',)

    parameter = st.session_state.time_series_continents_metric
    if st.session_state.time_series_continents_interval == 'Daily':
        parameter = 'New ' + parameter
    elif st.session_state.time_series_continents_interval == 'Weekly':
        parameter = 'Weekly ' + parameter
    elif st.session_state.time_series_continents_interval == 'Biweekly':
        parameter = 'Biweekly ' + parameter
    else:
        parameter = 'Total ' + parameter

    if st.session_state.time_series_continents_rel2pop:
        parameter = parameter + " Per Million"

    use_log = False if not st.session_state.time_series_continents_interval == "Cummulative" else st.session_state.time_series_continents_use_log
    dataframe = cases_df if st.session_state.time_series_continents_metric == 'Cases' else deaths_df

    fig = px.line(dataframe[dataframe["Country"].isin(st.session_state.time_series_continents)],
                x = 'Date',
                y=parameter,
                color='Country',
                log_y= use_log)
    
    fig.update_layout(xaxis_title = "Date", yaxis_title = parameter, hovermode='x unified')
    st.plotly_chart(fig)

@st.fragment
def time_series_countries(cases_df, deaths_df):
    st.subheader("Timeseries Analysis-Country Wise")
    continents = ['Asia','Europe','North America', 'South America', 'Africa', 'Oceania']
    countries = [country for country in cases_df['Country'].unique() if country not in continents]

    st.multiselect(
            "Select the countries",
            countries,
            default=['World'],
            key = 'time_series_countries',
        )
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.selectbox(
        "Choose the metric",
        ['Cases','Deaths'],
        index= 0,
        key = 'time_series_metric'
        )
    with col2:
        st.selectbox(
            'Choose the interval',
            options=['Daily', 'Weekly','Biweekly','Cummulative'],
            index=0,
            key = 'time_series_interval',
        )

    with col3:
        st.checkbox(
            'Make the graphs relative to population',
            value = False,
            key = 'time_series_rel2pop',
        )
    
    with col4:
        if st.session_state.time_series_interval == 'Cummulative':
            st.checkbox(
                "Use Log Scale", 
                value= False,
                key = 'time_series_use_log',)

    parameter = st.session_state.time_series_metric
    if st.session_state.time_series_interval == 'Daily':
        parameter = 'New ' + parameter
    elif st.session_state.time_series_interval == 'Weekly':
        parameter = 'Weekly ' + parameter
    elif st.session_state.time_series_interval == 'Biweekly':
        parameter = 'Biweekly ' + parameter
    else:
        parameter = 'Total ' + parameter

    if st.session_state.time_series_rel2pop:
        parameter = parameter + " Per Million"

    use_log = False if not st.session_state.time_series_interval == "Cummulative" else st.session_state.time_series_use_log
    dataframe = cases_df if st.session_state.time_series_metric == 'Cases' else deaths_df

    fig = px.line(dataframe[dataframe["Country"].isin(st.session_state.time_series_countries)],
                x = 'Date',
                y=parameter,
                color='Country',
                log_y= use_log)
    
    fig.update_layout(xaxis_title = "Date", yaxis_title = parameter, hovermode='x unified')
    st.plotly_chart(fig)

def plot_graph(cases_df, deaths_df):
    time_series_continents(cases_df,deaths_df)
    time_series_countries(cases_df,deaths_df)
    


    cases_100_df = cases_df[cases_df['Days Since 100 Total Cases']==0]
    cases_100_df = cases_100_df.dropna(subset=['Isocode']).reset_index(drop=True)[['Date','Country','Continent']]
    cases_1_per_million_df = cases_df[cases_df['Days Since 1 Total Cases Per Million']==0]
    cases_1_per_million_df = cases_1_per_million_df.dropna(subset=['Isocode']).reset_index(drop=True)[['Date','Country','Continent']]
    deaths_5_df = deaths_df[deaths_df['Days Since 5 Total Deaths']==0]
    deaths_5_df = deaths_5_df.dropna(subset=['Isocode']).reset_index(drop=True)[['Date','Country','Continent']]
    deaths_0_1_per_million_df = deaths_df[deaths_df['Days Since 0 1 Total Deaths Per Million']==0]
    deaths_0_1_per_million_df = deaths_0_1_per_million_df.dropna(subset=['Isocode']).reset_index(drop=True)[['Date','Country','Continent']]

    st.subheader("Timeline of Countries Reaching 100 Cases Threshold")
    fig = px.strip(cases_100_df,
                   x="Date",
                   y="Country",
                   color='Continent'
                   )
    st.plotly_chart(fig)

    st.subheader("Timeline of Countries Reaching 1 Case Per Million Population Threshold")
    fig = px.strip(cases_1_per_million_df,
                x="Date",
                y="Country",
                color='Continent'
                )
    st.plotly_chart(fig)

    st.subheader("Timeline of Countries Reaching 5 Deaths Threshold")
    fig = px.strip(deaths_5_df,
                x="Date",
                y="Country",
                color='Continent'
                )
    st.plotly_chart(fig)

    st.subheader("Timeline of Countries Reaching 0.1 Deaths Per Million Population Threshold")
    fig = px.strip(deaths_0_1_per_million_df,
                x="Date",
                y="Country",
                color='Continent'
                )
    st.plotly_chart(fig)


######################### Main Code ###################### 
# Showing the title
title = "Analysis of Disease Spread"
st.set_page_config(page_title = title,layout='wide')
st.title(title)

if 'cases_df' not in st.session_state:
    st.session_state.cases_df = load_spread_df(CASES_FILE_PATH)

if 'deaths_df' not in st.session_state:
    st.session_state.deaths_df = load_spread_df(DEATHS_FILE_PATH)

if'choropleth_cases_df' not in st.session_state:
    cases_df_temp = st.session_state.cases_df.copy()
    cases_df_temp = cases_df_temp[['Date','Country','Total Cases','Total Cases Per Million','Isocode','Continent']]
    st.session_state.choropleth_cases_df = load_choropleth_df(cases_df_temp)

if'choropleth_deaths_df' not in st.session_state:
    deaths_df_temp = st.session_state.deaths_df.copy()
    deaths_df_temp = deaths_df_temp[['Date','Country','Total Deaths','Total Deaths Per Million','Isocode','Continent']]
    st.session_state.choropleth_deaths_df = load_choropleth_df(deaths_df_temp)

tabs = st.tabs(['Overview', 'Map Visualization','Timeline Plots'])

with tabs[0]:
    overview(st.session_state.cases_df, st.session_state.deaths_df)
    pass
with tabs[1]:
    choropleth_animation(st.session_state.choropleth_cases_df, st.session_state.choropleth_deaths_df)
with tabs[2]:    
    plot_graph(st.session_state.cases_df, st.session_state.deaths_df)
    pass
