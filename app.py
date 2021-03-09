import json
from datetime import timedelta
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots
from dash.dependencies import Input, Output, State
from pandas_datareader import data

import app_components.layout
import app_components.charts
from sentiment_analysis import utils
from sentiment_analysis.platform_managers import RedditManager
from sentiment_analysis.sentiment_analyser import SentimentAnalyser

sentiment_analyser = SentimentAnalyser()
reddit_manager = RedditManager()
reddit_data_path = Path('sentiment_analysis/reddit_data/')

app = dash.Dash(__name__)
server = app.server

app.layout = app_components.layout.layout

# get submissions and stock price data
@app.callback(
    [
        Output('submissions_store', 'children'),
        Output('stock_price_store', 'children'),
        Output('preprocessed_text_store', 'children'),
        Output('unprocessed_text_store', 'children'),
        Output('data_loading', 'debug')
    ],
    [
        Input('submit_button', 'n_clicks'),
        Input('minimum_upvote', 'value'),
        State('ticker_input', 'value'),
    ]
)
def get_data(submit, minimum_upvote, ticker):
    """
    Get Reddit submissions
    """
    
    # read in submissions
    submissions = pd.read_pickle(reddit_data_path / f'{ticker}.pkl')
    
    # filter submissions
    submissions = submissions[submissions.score >= minimum_upvote]

    # preprocess text for analysis
    text = submissions.title.tolist()
    preprocessed_text = sentiment_analyser.preprocess_text(text)
    
    # set dates for stock price data
    start = submissions.created_utc.min().date() - timedelta(weeks=2)1
    end = submissions.created_utc.max().date() + timedelta(weeks=2)

    # get historical stock price data
    price_data = data.DataReader(
        name=ticker,
        data_source='yahoo',
        start=start,
        end=end,
    )
    
    # convert to json for storage
    submissions = submissions.to_json(date_format='iso')
    price_data = price_data.to_json(date_format='iso')
    preprocessed_text = json.dumps(preprocessed_text)
    text = json.dumps(text)
    
    return [submissions, price_data, preprocessed_text, text, False]

# create wordcloud and freqdist
@app.callback(
    [
        Output('wordcloud', 'figure'),
        Output('freqdist', 'figure')
    ],
    [
        Input('preprocessed_text_store', 'children'),
        Input('max_words', 'value')
    ]
)
def generate_wordcloud_freqdist(preprocessed_text, max_words):
    """
    Create wordcloud and frequency distribution
    """
    
    # read preprocessed text
    preprocessed_text = json.loads(preprocessed_text)

    # create wordcloud
    wordcloud = sentiment_analyser.create_wordcloud(
        preprocessed_text,
        max_words=max_words
    )
    
    # create freqdist
    freqdist = sentiment_analyser.create_freqdist(
        preprocessed_text,
        max_words=max_words
    )

    # create wordcloud figure
    wordcloud_fig = px.imshow(wordcloud)
    wordcloud_fig.update_layout(
        width=500, 
        height=400, 
        margin=dict(l=2, r=2, b=2, t=2),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    wordcloud_fig.update_xaxes(showticklabels=False)
    wordcloud_fig.update_yaxes(showticklabels=False)
    wordcloud_fig.update_traces(hovertemplate=None, hoverinfo='skip')
    
    # create freqdist figure
    freqdist_fig = px.bar(freqdist, x='count', y='word')
    freqdist_fig.update_layout(
        width=400,
        height=400,
        margin=dict(l=10, r=10, b=10, t=10),
        paper_bgcolor='rgba(0,0,0,0)'
    )
    freqdist_fig.update_yaxes(autorange='reversed')

    return [wordcloud_fig, freqdist_fig]

# create sentiment chart and table
@app.callback(
    [
        Output('sentiment', 'figure'),
        Output('submissions_table', 'children')
    ],
    [
        Input('submissions_store', 'children'),
        Input('stock_price_store', 'children'),
        Input('preprocessed_text_store', 'children'),
        Input('unprocessed_text_store', 'children'),
        Input('sentiment_smoothness', 'value')
    ]
)
def generate_sentiment(
    submissions,
    stock_prices,
    preprocessed_text,
    unprocessed_text,
    window
    ):
    """
    Create rolling sentiment chart
    """
    
    # get submissions, stock prices, preprocessed and unprocessed text
    submissions = pd.read_json(submissions)
    stock_prices = pd.read_json(stock_prices).Close
    preprocessed_text = json.loads(preprocessed_text)
    unprocessed_text = json.loads(unprocessed_text)
    
    # get sentiment scores
    sentiment = sentiment_analyser.sentiment_score(
        preprocessed_text,
        customise_vader=True
    )
    
    # merge sentiment scores with submissions
    merged = utils.merge_sentiment_submissions(
        sentiment_scores=sentiment,
        text=unprocessed_text,
        submissions=submissions,
        on='title'
    )
    
    # calculate rolling sentiment
    merged['rolling_sentiment'] = merged.sentiment_score \
                                        .rolling(window) \
                                        .mean()

    # create rolling sentiment figure
    fig = plotly.subplots.make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=[f'Stock Price', 'Rolling Sentiment'],
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1
    )
    price_line = go.Scatter(
        x=stock_prices.index,
        y=stock_prices.values,
        mode='lines',
        name='close price'
    )
    sentiment_line = go.Scatter(
        x=merged.created_utc,
        y=merged.rolling_sentiment,
        mode='lines',
        name='rolling sentiment'
    )
    fig.add_trace(price_line, row=1, col=1)
    fig.add_trace(sentiment_line, row=2, col=1)
    fig.update_layout(
        width=800,
        height=800,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # create submissions table
    submissions_table = app_components.charts.generate_table(merged)
    
    return [fig, submissions_table]


if __name__ == "__main__":
    app.run_server(debug=True)
