from datetime import datetime

import pandas as pd
from pandas_datareader import data

from sentiment_analysis.API.reddit import RedditAPI


def merge_sentiment_submissions(
    sentiment_scores: list,
    text: list,
    submissions: pd.DataFrame,
    on: str
    ) -> pd.DataFrame:
    """
    Merge sentiment scores from SentimentAnalyser.sentiment_scores with
    reddit submissions from API.reddit.RedditAPI

    Args:
        sentiment_scores (list): sentiment scores list
        text (list): text used to generate sentiment scores
        submissions (pd.DataFrame): submissions from reddit API
        
    Note: It is assumed that sentiment scores and text are correctly ordered
    """
    
    # create dataframe with text and its corresponding sentiment score
    text_sentiment = pd.DataFrame(
        zip(text, sentiment_scores),
        columns=[on, 'sentiment_score']
    )
    
    # merge with submissions
    merged = pd.merge(
        left=submissions,
        right=text_sentiment,
        on=on
    ).sort_values('created_utc')
    
    return merged

def get_data(
    ticker: str,
    limit: int,
    subreddits: list,
    before: str,
    after: str,
    minimum_upvote: int
    ) -> pd.DataFrame:
    """
    Retrieve submissions from RedditAPI using predefined parameters

    Args:
        ticker (str): ticker to search for
        limit (int): maximum number of submissions to return
        subreddits (list): list of subreddits to search from
        before (datetime): maximum submission date
        minimum_upvote (int): filter submissions with minimum_upvote or more

    Returns:
        pd.DataFrame: submissions
    """
    
    reddit = RedditAPI()
    
    # convert date to epoch format for Pushshift API
    before = datetime.strptime(before[:10], '%Y-%M-%d').strftime('%s')
    after = datetime.strptime(after[:10], '%Y-%M-%d').strftime('%s')
    
    # parameters
    fields = [
        'id',
        'created_utc',
        'subreddit',
        'title',
        'selftext',
        'score'
    ]

    params = {
        'ticker': ticker,
        'title': ticker,
        'sort_type': 'created_utc',
        'sort': 'desc',
        'limit': limit,
        'fields': fields,
        'subreddit': subreddits,
        'before': before,
        'after': after,
        'score': f'>{minimum_upvote}'
    }
    
    # get submissions
    submissions = reddit.get_submissions(params)
    
    # get historical stock price data
    price_data = data.DataReader(
        name=ticker,
        data_source='yahoo',
        start=submissions.created_utc.min().date(),
        end=submissions.created_utc.max().date(),
    )
    
    return submissions, price_data
