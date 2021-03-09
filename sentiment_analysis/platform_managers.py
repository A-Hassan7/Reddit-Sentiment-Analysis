"""
Classes to manage the data pipelines for each social media platform
"""

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from config import Loggers
from sentiment_analysis import utils
from sentiment_analysis._database import models
from sentiment_analysis.platform_api import RedditAPI
from sentiment_analysis.database_manager import DatabaseManager


class PlatformManager(ABC):
    """
    Abstract base class for platform managers
    """

    def __init__(self):
        self.database_manager = DatabaseManager()

    @abstractmethod
    def fetch_data(self):
        """
        Fetch submissions and comments from reddit. Perform sentiment
        analysis on the comments and insert the data into the database.
        """


class RedditManager(PlatformManager):
    """
    Keep Reddit submissions, comments and sentiment updated
    for each ticker that is tracked.

    TODO: Which tickers should be frequently updated?
            Screen for the most active tickers and maintain thier scores
            Where can we find list of the most populor tickers at the moment?

    Main usage:
        reddit_manager = RedditManager()
        # Fetch data
        reddit_manager.fetch_data(
            ticker='AAPL',
            limit=100,
            before=datetime(2021,1,30),
            after=datetime(2021,1,1),
            subreddits=['wallstreetbets', 'investing']
        )
        # Update existing data
        reddit_manager.update_submissions(['GE'], [datetime(2021, 1, 1), datetime(2021, 1, 30)])
    """

    def __init__(self):
        super().__init__()
        self.scraper = RedditAPI()
        self.logger = Loggers.console

    def update_subreddits(self, subreddits_list=None, update_all=False):
        """
        Update the subreddits table in the database by either adding
        new subreddits or updating existing subreddit stats.

        Args:
            subreddits_list (list, optional): 
                List of strings of subreddits. Defaults to None.
            update_all (bool, optional): 
                Updates all subreddits if True. Defaults to False.
        """

        # Get subreddits table from database
        stored_subreddits = self.database_manager.get_values(models.Subreddits)

        # Update all subreddits in subreddits table
        if update_all:
            # Get updated information
            updated_subreddits = self.scraper.get_subreddit_details(
                stored_subreddits.name
            )
            updated_subreddits = updated_subreddits[['name', 'subscribers']]
            updated_subreddits.subscribers.fillna(0, inplace=True)

            # Update values in table
            self.database_manager.update_table_values(
                model=models.Subreddits,
                values=updated_subreddits,
                on='name'
            )

        elif subreddits_list:
            # Find new subreddits
            existing_subs = list(stored_subreddits.name)
            new_subs = list(set(
                [sub for sub in subreddits_list if sub not in existing_subs]
            ))

            # If there are new subreddits, find details and add to database
            if new_subs:
                self.logger.info('Adding %s new subreddits', len(new_subs))

                # Get new sub information
                new_sub_info = self.scraper.get_subreddit_details(new_subs)
                new_sub_info.subscribers.fillna(0, inplace=True)
                # Insert new sub information to subreddit table in database
                self.database_manager.insert_values(
                    model=models.Subreddits,
                    values=new_sub_info
                )

    def process_submissions(self, submissions):
        """
        Processes submissions retreived from the PushShift API.
        The function updates the subreddits table, cleans and
        rearranged the columns.

        Args:
            submissions (pd.DataFrame): 
                Pandas DataFrame of submissions from PushShift API

        Returns:
            [pd.DataFrame]: returns dataframe of processed submissions
        """

        # Remove duplicate submissions
        submission_ids = self.database_manager.get_values(models.RedditSubmissions).submission_id
        submissions = submissions[~submissions.submission_id.isin(submission_ids)]

        if submissions.empty:
            self.logger.info("No new submissions found")
            return submissions

        else:
            self.logger.info(f'Processing %s new submissions', len(submissions))

            # Add new subreddits to subreddits table if needed
            self.update_subreddits(list(submissions.subreddit))

            # map subreddit name to subreddit id
            stored_subreddits = self.database_manager.get_values(models.Subreddits)
            submissions.loc[:, 'subreddit'] = submissions.subreddit.apply(
                lambda x: stored_subreddits.id[stored_subreddits.name == x].item()
            )
            submissions.rename(columns={'subreddit': 'subreddit_id'}, inplace=True)

            # Strip punctuation from title
            if hasattr(submissions, 'title'):
                submissions.loc[:, 'title'] = submissions.title.apply(
                    lambda x: utils.strip_punctuation(x).lower()
                )

            return submissions

    def process_comments(self, comments):
        """
        Process comments retreived from PushShift API.
        Clean the comments and add them to the database.

        Args:
            comments (pd.DataFrame): 
                Dataframe of comments that need to be processed
        """

        # Remove duplicate comments
        comment_ids = self.database_manager.get_values(models.RedditComments).comment_id
        comments = comments[~comments.comment_id.isin(comment_ids)]

        if comments.empty:
            self.logger.info("No new comments found")
            return comments

        else:
            self.logger.info('Processing %s new comments', len(comments))

            # Rename body column
            comments.rename(columns={'body': 'cleaned_comment'}, inplace=True)

            # Strip punctuation from title
            comments.loc[:, 'cleaned_comment'] = comments.cleaned_comment.apply(
                lambda x: utils.strip_punctuation(x).lower()
            )

            return comments

    def update_submissions(self, tickers, daterange):
        """
        Retreive and update details of submissions and thier comments
        for the specified tickers within the specified daterange.

        Args:
            tickers (list): List of string tickers
            daterange (list): datetime objects to specify data range
        """

        for ticker in tickers:

            self.logger.info('Getting submissions to update')

            # Get submission ids with the given ticker and daterange
            submission_ids = self.database_manager.get_values(
                model=models.RedditSubmissions,
                filters=[
                    models.RedditSubmissions.ticker == ticker,
                    models.RedditSubmissions.created_utc.between(*daterange)
                ]
            ).submission_id

            # Get updated submission information from scraper
            updated_submissions = self.scraper.get_submission_details(
                submission_ids=submission_ids,
                fields=['id', 'score']
            )
            updated_submissions.rename(columns={'id': 'submission_id'}, inplace=True)

            # Update scores in database
            self.database_manager.update_values(
                model=models.RedditSubmissions,
                values=updated_submissions,
                on='submission_id'
            )

            # Get comments for each submission and process them
            comments = self.scraper.get_comments(submission_ids)
            processed_comments = self.process_comments(comments)

            # Add new comments to the database
            if not processed_comments.empty:

                self.database_manager.insert_values(
                    model=models.RedditComments,
                    values=processed_comments
                )

            # Update details of existing comments
            old_comments = comments[~comments.comment_id.isin(processed_comments.comment_id)]
            if not old_comments.empty:

                self.update_comments(old_comments)

    def update_comments(self, comments):
        """
        Update the upvote score of each ticker given the specified daterange. 
        This may also update the sentiment score of the comment once the 
        sentiment analysis class is implamented.

        Args:
            Comments (pd.DataFrame): DataFrame of comments that need to be updated.
        """

        # Get updated comment information from scraper
        updated_comments = self.scraper.get_comment_details(
            comment_ids=list(comments.comment_id),
            fields=['id', 'score']
        )
        updated_comments.rename(columns={'id': 'comment_id'}, inplace=True)

        # Update the comment scores in the database
        self.database_manager.update_values(
            model=models.RedditComments,
            values=updated_comments,
            on='comment_id'
        )

    def fetch_data(self, ticker, limit, before, after, subreddits=''):
        """
        Get submissions and comments from reddit via RedditScraper
        and add new data to the database

        Args:
            ticker (str): ticker for which to fetch data
            limit (int): number of submissions to get (sorted by date desc)
            subreddits (str, optional): subreddits to get data from
        """

        # parameters
        fields = [
            'id',
            'created_utc',
            'subreddit',
            'title',
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
            'before': before.strftime('%s'),
            'after': after.strftime('%s'),
            # 'score': f'>{minimum_upvote}'
        }

        # Get submissions and process them
        submissions = self.scraper.get_submissions(params)
        processed_submissions = self.process_submissions(submissions)

        # Process comments if there are new submissions
        if not processed_submissions.empty:
            
            # Insert submissions into database
            self.database_manager.insert_values(
                model=models.RedditSubmissions,
                values=processed_submissions
            )

            # Get comments and process them
            comments = self.scraper.get_comments(
                list(processed_submissions.submission_id)
            )
            processed_comments = self.process_comments(comments)

            # Insert comments if there are new comments
            if not processed_comments.empty:

                # Insert comments into database
                self.database_manager.insert_values(
                    model=models.RedditComments,
                    values=processed_comments
                )


# reddit_manager = RedditManager()
# # Fetch data
# reddit_manager.fetch_data(
#     ticker='GME',
#     limit=20,
#     before=datetime(2021,3,8),
#     after=datetime(2021,2,1),
#     subreddits=['wallstreetbets', 'investing']
# )
# # Update existing data
# reddit_manager.update_submissions(['GME'], [datetime(2021, 3, 7), datetime(2021, 3, 8)])

