import streamlit as st
from pathlib import Path
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from functools import reduce
import sys
import os
from scipy.signal import savgol_filter
# sys.path.append(str(Path(__file__).parent.parent.parent))

st.set_page_config(page_title="Excess Mortality Analysis", page_icon="📊", layout="centered")

@st.cache_data
def load_data():
      national_df = pd.read_csv(os.path.join('Datasets', 'Mortality_Analysis', 'national_data.csv'), parse_dates=['Date'])
      global_mean_df = pd.read_csv(os.path.join('Datasets', 'Mortality_Analysis', 'global_mean_data.csv'), parse_dates=['Date'])
      return national_df, global_mean_df

def savgol_filtering(df, window, poly):
      df = df.copy()
      for col in df.columns[1:]:
            if col != 'Date':
                  df[col] = savgol_filter(df[col], window, poly, mode='nearest')
      return df

def plot_figure(df, list_y, yaxis_title, x='Date', xaxis_title='Date', type='line'):
      if type == 'line':
            df = savgol_filtering(df, 64, 2)
            subfig = px.line(df.melt(id_vars=x, value_vars=list_y, var_name='Variable', value_name='Value'), x='Date', y='Value', color='Variable', labels={'Value': yaxis_title, 'Date': 'Date'}, height=500)
            subfig.update_layout(xaxis_title=xaxis_title, yaxis_title=yaxis_title)
      if type == 'bar':
            subfig = px.bar(df.melt(id_vars=x, value_vars=list_y, var_name='Variable', value_name='Value'), x=x, y='Value', color='Variable', barmode='group',  labels={'Value': yaxis_title, 'Date': xaxis_title}, height=500)
            subfig.update_layout(xaxis_title=xaxis_title, yaxis_title=yaxis_title)
      return subfig

def create_subplots(df, lol_y, list_ytitles, list_x, list_xtitles, num_rows=1, num_cols=2, title=None, legend_title=None, lx=0.3, ly=1.1, type='line'):
      num_figures = len(lol_y)
      fig = make_subplots(rows=num_rows, cols=num_cols, horizontal_spacing=0.15)
      fig_idx=0
      for i in range(num_rows):
            for j in range(num_cols):
                  if fig_idx>=num_figures:
                        break
                  subfig = plot_figure(df, lol_y[fig_idx], list_ytitles[fig_idx], list_x[fig_idx], list_xtitles[fig_idx], type=type)
                  for trace in subfig.data:
                        fig.add_trace(trace, row=i+1, col=j+1)
                  fig.update_yaxes(title_text=list_ytitles[fig_idx], row=i+1, col=j+1)
                  fig.update_xaxes(title_text=list_xtitles[fig_idx], row=i+1, col=j+1)
                  fig_idx+=1


      fig.update_layout(legend=dict(x=lx, y=ly, xanchor='center', yanchor='top', orientation='h'), title_text=legend_title, showlegend=True)
      fig.update_layout(height=num_rows*500)
      if title:
            fig.update_layout(title = title)
      return st.plotly_chart(fig, use_container_width=True)

def create_map(df, col, title=None):
      fig = px.choropleth(df, locations='Country', locationmode='country names', color=col, hover_name='Country', color_continuous_scale=px.colors.sequential.Plasma, title=title, labels={col: col})
      fig.update_geos(showcoastlines=True, coastlinecolor="Black", showland=True, landcolor="LightGray", showlakes=True, lakecolor="LightBlue")
      fig.update_coloraxes(colorbar_title=None)
      return st.plotly_chart(fig, use_container_width=True)

national_df, global_mean_df = load_data()
countries = national_df['Country'].unique()
features = national_df.columns[2:]

# Main container for visualization

st.title("Excess Mortality Analysis")
st.write("")
st.write("")

st.write("Existing datasets that maintain deaths counts due to COVID-19 often rely on official government statistics. The reliability of these statistitics is dependent on several factors like testing capacity, reporting practices, and the definition of COVID-19 deaths, inducing considerable variability across countries or administrations.")

with st.container():
      st.divider()
      col1, col2, col3 = st.columns(3)
      st.divider()
      with col1:
            st.metric("Total Reported Deaths per Million", value = f"{int(global_mean_df['Total Deaths per Million'].iloc[-1])}")  
      with col2:
            st.metric("Total Excess Deaths per Million", value = f"{int(global_mean_df['Cumulative Estimated Daily Excess Deaths per Million'].iloc[-1])}")
      with col3:
            st.metric("Excess Deaths to Reported Deaths", value = f"{round(global_mean_df['Cumulative Estimated Daily Excess Deaths per Million'].iloc[-1] / global_mean_df['Total Deaths per Million'].iloc[-1], 2)}")


st.write("Excess Mortality serves as a more reliable metric to assess the impact of COVID-19 by comparing the number of deaths during the pandemic to the expected number of deaths for the same period estimated from historical data. It accounts for misreporting and underreporting of COVID-19 deaths, providing a clearer picture of the pandemic's impact on mortality.")

st.header("Excess Mortality Trends")
st.write("")

with st.container():
      tab1, tab2, tab3, tab4, tab5 = st.tabs(["Reported and Excess Deaths", "Excess to Reported Deaths", "Reported CFR and Estimated CFR", "Excess Deaths Top & Bottom Nations", "Map Overlays"])

      with tab1:
            st.subheader("Reported and Excess Deaths & Cumulative Reported and Excess Deaths")
            st.write("")
            st.write('The following graphs compare the daily and cumulative deaths reported by the resprective countries over time to the estimated daily and cumulative excess deaths.')

            create_subplots(global_mean_df, lol_y=[['New Deaths per Million', 'Estimated Daily Excess Deaths per Million'], ['Total Deaths per Million', 'Cumulative Estimated Daily Excess Deaths per Million']],
                list_ytitles=['Deaths and Excess Mortality', 'Deaths and Excess Mortality'],
                list_x=['Date', 'Date'], list_xtitles=['Date', 'Date'],
                num_rows=1, num_cols=2, lx=0.5, ly=1.165, type='line')
      with tab2:
            st.subheader("Excess Death to Reported Deaths")
            st.write("")
            st.write("The following graph plots the ratio of cumulative excess deaths to the reported number of deaths over time.")
            create_subplots(global_mean_df[global_mean_df['Date']>=pd.to_datetime('2020-04-10')], lol_y = [['Cumulative Excess Deaths to Case Deaths']],
                        list_ytitles=['Cumulative Excess Deaths to Case Deaths'], list_x=['Date'], list_xtitles=['Date'],
                        num_rows=1, num_cols=1, lx=0.5, ly=1.165, type='line')         
      with tab3:
            st.subheader("Reported Case Fatality Rate and Estimated Case Fatality Rate")
            st.write("")
            st.write("The following graphs compare the estimated fatality rate to the fatality rate according to government-reported data")
            create_subplots(global_mean_df[(global_mean_df['Date']>=pd.to_datetime('2020-06-01'))& (global_mean_df['Date']<=pd.to_datetime('2023-10-01'))], lol_y=[['CFR', 'Estimated Daily CFR'], ['CFR', 'Estimated Cumulative CFR']],
                        list_ytitles=['CFR and Estimated Daily CFR', 'CFR and Estimated Cumulative CFR'], list_x=['Date', 'Date'], list_xtitles=['Date', 'Date'],
                              num_rows=1, num_cols=2, lx=0.21, ly=1.165, type='line')
      with tab4:
            st.subheader("Countrywise Top and Bottom Countries by Cumulaitve Excess Deaths per Million")
            st.write("")
            st.write("Below graph shows 20 countries with the most cumulative excess deaths per million as on 01-01-2024 and their respective reported total deaths.")
            create_subplots(national_df[national_df['Date']==national_df['Date'].max()].sort_values(by='Cumulative Estimated Daily Excess Deaths per Million', ascending=False).head(20),
                        lol_y=[['Cumulative Estimated Daily Excess Deaths per Million', 'Total Deaths per Million']],list_ytitles=['Cumulative Excess and Case Deaths per Million'], list_x = ['Country'], list_xtitles=['Country'],
                        num_rows=1, num_cols=1, lx=0.3, ly=1.165, type='bar')
            st.write("Below graph shows 20 countries with the least cumulative excess deaths per million as on 01-01-2024 and their respective reported total deaths.")
            create_subplots(national_df[national_df['Date']==national_df['Date'].max()].sort_values(by='Cumulative Estimated Daily Excess Deaths per Million', ascending=True).head(20),
                              lol_y=[['Cumulative Estimated Daily Excess Deaths per Million', 'Total Deaths per Million']],list_ytitles=['Cumulative Excess and Case Deaths per Million'], list_x = ['Country'], list_xtitles=['Country'],
                              num_rows=1, num_cols=1, lx=0.3, ly=1.165, type='bar')
      with tab5:
            st.subheader("Map Overlays")
            st.write("")
            st.write("Below map show the cumulative excess deaths per million as on 01-01-2024.")
            create_map(national_df[national_df['Date']==national_df['Date'].max()], col='Cumulative Estimated Daily Excess Deaths per Million', title='Cumulative Estimated Daily Excess Deaths per Million')
            st.write("Below map show the total reported case deaths per million as on 01-01-2024.")
            create_map(national_df[national_df['Date']==national_df['Date'].max()], col='Total Deaths per Million', title='Total Deaths per Million')
