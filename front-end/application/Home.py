# type:ignore

import streamlit as st
import datetime
import pickle
import os
from data_model import ChartData
import altair as alt
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.colors import n_colors
from wordcloud import WordCloud
from warnings import filterwarnings

filterwarnings('ignore')

st.set_page_config(
    page_title="Homepage",
    page_icon="smile",
    layout="wide"
)

############## FUNCTIONS HERE #######################
BASE_PATH = os.path.dirname(os.path.abspath(__name__))
MIN_DATE = datetime.datetime(2022, 10, 27)
MAX_DATE = datetime.datetime.today() - datetime.timedelta(days=1)
DEFAULT_DATE = MAX_DATE
# st.write(MAX_DATE)

@st.cache
def load_tickers():
    # Gets the first 100 labels from sp500 ticker file
    x = os.path.join(BASE_PATH, "./data/sp100.pickle")
    with open(x, "rb") as file:
        return pickle.load(file)

#@st.experimental_singleton
def get_chart_data_obj():
    obj = ChartData(BASE_PATH)
    return obj

#####################################################

st.title("AWS Data Pipeline for Twitter Data")
st.caption("Lambton College - Pulkit, Zarna, Yasin, Deep, Nikita")

## Configuring the sidebar, to act as a settings pane
with st.sidebar:
    st.header("Index")
    st.markdown("[Section 1](#section-1)")
    st.markdown("- [Metrics](#section-1)")
    st.markdown("- [Trending Stocks](#section-1)")
    st.markdown("[Section 2](#section-1)")
    st.markdown("- [Text](#section-1)")
    st.markdown("- [Ticker Trends](#section-1)")
    st.markdown("-----")
    refresh_page = st.columns([1,30,1])[1].button("Refresh Page 🔁", help="Refreshes the page by pulling data and updating charts")


########################### CHARTS ###################################

def plot_trending(data):
    fig = px.bar(data, y='TICKER', x='NUM_MENTIONS', title="Top ticker leaderboard", orientation="h")
    fig.update_layout({
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)'
})
    return fig

def plot_trending_2(data):
    data = data.assign(NUM_POSITVE=lambda x: x["NUM_POSITVE"]/x["NUM_MENTIONS"]\
        , NUM_NEGATIVE=lambda x: x["NUM_NEGATIVE"]/x["NUM_MENTIONS"]\
        , NUM_NEUTRAL=lambda x: x["NUM_NEUTRAL"]/x["NUM_MENTIONS"])
    fig = px.bar(data, y='TICKER', x=['NUM_NEGATIVE', 'NUM_POSITVE', 'NUM_NEUTRAL'], title="Number of positive, negative and neutral tweets", orientation="h")
    fig.update_layout({
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'paper_bgcolor': 'rgba(0,0,0,0)'
     })  
    return fig

def plot_recent_tweets_text(data):
    sentiment_ = {"POSITIVE": "green", "NEGATIVE": "red", "NEUTRAL": "lightskyblue"}
    x = list(map(lambda s: sentiment_[s], data.SENTIMENT))
    fig = go.Figure(data=[go.Table(
                            header=dict(
                                values=['<b>Tweet text for recent tweets</b>'],
                                line_color='white', fill_color='white',
                                align='center',font=dict(color='black', size=20)
                            ),
                            cells=dict(
                                values=[data.TEXT],
                                line_color=["white"],
                                fill_color=[x],
                                align='left', font=dict(color='black', size=13, family="lato"),
                                height=35
                                ))
                            ])
    
    fig.update_layout(margin=dict(l=10,r=30,t=3,b=10))
    return fig

charts = get_chart_data_obj()

with st.container():
    st.markdown("-----")
    st.header("Section 1")
    st.markdown("In the first section, we look at the trends and compare the different stocks based on <br>the number of mentions. We have built a leaderboard, and also charing the break-up of individual mentions into positive, negative and neutral tweets.")
    page_metrics_s2 = st.container()
    
# Containers to hold sub-sections for section 1    
con1 = st.empty().container()
con2 = st.empty().container()

with con1:
    st.subheader("Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tweets", 1000, 20)
    col2.metric("+ve Tweets", 200, 30)
    col3.metric("Neu Tweets", 50, -30)
    col4.metric("-ve Tweets", 50, 40)

with con2:
    st.subheader("Trending Stocks")
    # Controls for this section
    pm_month, pm_date, pm_time = None, None, None
    _1, _2, _3, _4 = st.columns(4)
    top = _1.selectbox("Top", [3, 5, 10, 15], 0) 
    aggregationType = _2.selectbox("AggregationType", ("All", "Monthly", "Daily", "Hourly"), 0)
    if aggregationType == "Monthly":
        _options = ["Current-0", "Current-1"]
        pm_month = _3.selectbox("Month", _options)
    elif aggregationType == "Daily":
        pm_date = _3.date_input("Date", DEFAULT_DATE,min_value=MIN_DATE, max_value=MAX_DATE)
    elif aggregationType == "Hourly":
        c1, c2 = st.columns(2)
        pm_date = _3.date_input("Date", DEFAULT_DATE, min_value=MIN_DATE, max_value=MAX_DATE)
        pm_time = _4.selectbox("Time", [f"{i}:00" for i in range(24)])
    pm_month_string, pm_date_string, pm_time_string = None, pm_date, pm_time # type:ignore
    if pm_month:
        pm_month_string = (MAX_DATE - datetime.timedelta(days=31*int(str(pm_month).split("-")[-1]))).strftime("%m")
    
    # Section logic  
    funcMap = {"Monthly": lambda x: charts.get_data_for_month(int(pm_month_string), top=x)}
    data = funcMap["Monthly"](int(top))
    
    tab1, tab2 = st.tabs(["Chart", "Data"])
    with tab1: 
        col1, col2 = st.columns([1, 1])
        with col1:
            st.plotly_chart(plot_trending(data), use_container_width=True)
        with col2:
            st.plotly_chart(plot_trending_2(data), use_container_width=True)
    with tab2:
        st.write(data)
        #st.download_button("Download", data)
    
   
with st.container():
    st.markdown("-----")
    st.header("Section 2")
    st.markdown("In the second section, we want to dive deeper into individual ticker symbols. We do so by asking user input for more than one TICKER symbol and show the vizualizations to compare.")
    page_metrics_s2 = st.container() 

con3 = st.empty().container()
con4 = st.empty().container()

with con3:
    st.subheader("Text data")
    _1, _2, _ = st.columns([1, 1, 2])
    top2 = _1.selectbox("Recent tweets", [10, 25, 50, 100, 500, 1000], 0, key="top2")
    ticker = _2.selectbox("Filter By Ticker", ["None"]+load_tickers(), 0)
    recent_tweets = charts.get_recent_tweets()
    
    tab1, tab2 = st.tabs(["Chart", "Data"])
    
    with tab1:
        col1, col2 = st.columns([2, 1.5])  
        col1.subheader("Wordcloud of these tweets")
        
        with col2:
            
            st.markdown("""
                    <style>
                        .cell-rect[style] {
                            opacity: 0.2 !important;
                        }
                    </style>
                    """, unsafe_allow_html=True)
            
            st.plotly_chart(plot_recent_tweets_text(recent_tweets))
            
        with col1:
            # Chart the wordcloud
            text = " ".join(recent_tweets.TEXT)
            w = WordCloud(background_color="grey", colormap="hot").generate(text)
            plt.figure(figsize=(5,20))
            fig, ax = plt.subplots()
            ax.imshow(w, interpolation="bilinear")
            ax.set_axis_off()      
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.pyplot()
    with tab2:
        st.write(recent_tweets)
        #st.download_button("Download", recent_tweets, key="recentTweets")
  
with con4:
    st.subheader("Ticker Trends")
    _1, _2, _ = st.columns([1, 1, 2])
    tick1 = _1.selectbox("Ticker (Primary)", load_tickers(), 0, key="tick1")
    tick2 = _2.selectbox("Ticker (Secondary)", ["None"]+load_tickers(), 0, key="tick2")
    
    st.radio("radio", ["X", "Y"]) 
    st.markdown('<style>div.Widget.row-widget.stRadio > div{flex-direction:row !important;}</style>', unsafe_allow_html=True)
        
        
        

        