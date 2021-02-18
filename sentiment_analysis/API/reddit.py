"""
RedditScraper is responsible for interfacing with and retrieving data from 
the PRAW and Pushshift API's.
"""

import pandas as pd
import praw
import requests
from praw.models import MoreComments
from tqdm import tqdm

from config import Loggers, PRAWConfig


class RedditAPI:
    """
    The RedditScraper class allows interaction with the Pushshift and PRAW API's.

    The Pushshift API allows us to get a large number of submissions for a given query.
    The PRAW API is then used to get the comments from each of those submissions.
    """

    def __init__(self):

        # Create praw.Reddit object with with reddit OAuth creds
        # Reddit application creds created at https://www.reddit.com/prefs/apps
        # Reddit class is a gateway to Reddit's API
        self.reddit = praw.Reddit(
            client_id=PRAWConfig.REDDIT_CLIENT_ID,
            client_secret=PRAWConfig.REDDIT_CLIENT_SECRET,
            user_agent=PRAWConfig.REDDIT_USER_AGENT
        )

        # Pushshift API endpoint for sumbissions
        self.submission_endpoint = "https://api.pushshift.io/reddit/search/submission/"
        
        self.logger = Loggers.console

    def get_submissions(self, params: dict) -> pd.DataFrame:
        """ Get submissions from Pushshift API

        Args:
            params (dict):
                Dictionary with request parameters as keys. full list of
                Pushshit parameters available at https://pushshift.io/api-parameters/

        Returns:
            [pd.DataFrame]: Pandas DataFrame of all submissions

        Note:
            Using sort parameters other than descending created_utc may
            result in unexpected behavior.
        """
        
        self.logger.info('Retrieving submissions based on search criteria')
        
        # check parameters
        params = self._check_params(params)
        
        ticker = params.pop('ticker')
        after = int(params['after'])
        before = int(params['before'])
        limit = int(params['limit'])
        pbar = tqdm(total=limit, desc='submissions')
        before_decay = 18000  # 18000s = 5hrs
        
        submissions = []
        # Request submissions
        while before > after and len(submissions) < limit:

            # Request and retrieve data in JSON format
            r = requests.get(url=self.submission_endpoint, params=params)
            
            # try to extract submissions
            try:
                data = r.json()['data']
                
                # Page to next set of submissions by setting before to
                # the last submissions created_utc
                params['before'] = data[-1]['created_utc']
                [submissions.append(post) for post in data]
                
                # Update progress bar
                pbar.update(len(data))
            
            # decrease before if no submissions found
            except IndexError:
                params['before'] -= before_decay
                
            except Exception as e:
                self.logger.warning(e, exc_info=True)
                break
                
        self.logger.info('%s submissions found', len(submissions))
        pbar.close()
        
        # convert submissions to dataframe and update scores
        if submissions:
            submissions = self._process_submissions(submissions, ticker)

        return submissions

    def get_comments(self, submission_ids: list) -> pd.DataFrame:
        """
        Returns list of top level comments in submission

        Args:
            submission_ids (list): list of submission_ids

        Returns:
            [pd.DataFrame]: Pandas DataFrame of all comments
        """

        comments = {
            'created_utc': [],
            'submission_id': [],
            'comment_id': [],
            'body': [],
            'score': []
        }

        self.logger.info('Retrieving comments for requested submissions')
        for submission_id in tqdm(submission_ids, desc='Getting comments'):

            # Catch bad ID's
            try:
                # Get submission instance from submission_id
                submission = self.reddit.submission(id=submission_id)
            except:
                self.logger.warning('Bad ID %s', submission_id)
                continue

            # Get top level comments
            for top_level_comment in submission.comments:
                # Ignore 'load more comments' and 'continue this thread' links
                if isinstance(top_level_comment, MoreComments):
                    continue

                # Append data to comments dictionary
                comments['created_utc'].append(top_level_comment.created_utc)
                comments['submission_id'].append(submission_id)
                comments['comment_id'].append(top_level_comment.id)
                comments['body'].append(top_level_comment.body)
                comments['score'].append(top_level_comment.score)

        # Convert comments to pandas DataFrame
        comments_df = pd.DataFrame(comments)
        comments_df['created_utc'] = pd.to_datetime(comments_df.created_utc, unit='s')
        
        return comments_df

    def _process_submissions(self, submissions, ticker):
        """
        Convert submissions to dataframe and update submission scores

        Args:
            submissions (list): list of submissions
            ticker (str): relevent ticker
        """
    	
    	# Convert submissions to pandas dataframe and add ticker
        submissions_df = pd.DataFrame(submissions)
        submissions_df['created_utc'] = pd.to_datetime(submissions_df.created_utc, unit='s')
        submissions_df['ticker'] = ticker
        
        # Get updated submission scores
        updated_scores = self.get_submission_details(
            submission_ids=submissions_df.id,
            fields=['id', 'score']
        )

        # Merge updated_scores on id
        submissions_df = pd.merge(
            left=submissions_df,
            right=updated_scores,
            on='id'
        )

        # Clean up
        submissions_df.drop('score_x', axis=1, inplace=True)
        submissions_df.rename(
            columns={'id': 'submission_id', 'score_y': 'score'},
            inplace=True
        )

        return submissions_df

    def get_subreddit_details(self, subreddits: list) -> pd.DataFrame:
        """
        Get information about a subreddit 

        Args:
            subreddit (list): list of strings with subreddit name
            
        Returns:
            [pd.DataFrame]: Subreddit details
        """

        # Subreddit attributes to collect
        subreddit_info = {
            'name': [],
            'subreddit_id': [],
            'subscribers': []
        }
        
        self.logger.info('Retrieving updated subreddit details')
        # Collect information about each subreddit given
        for subreddit in tqdm(subreddits, desc='subreddit'):
            # Find subreddit through PRAW
            sub = self.reddit.subreddit(subreddit)
            # Add data to dictionary
            subreddit_info['name'].append(subreddit)
            subreddit_info['subreddit_id'].append(sub.name)
            subreddit_info['subscribers'].append(sub.subscribers)

        return pd.DataFrame(subreddit_info)
    
    def get_submission_details(self, submission_ids: list, fields: list) -> pd.DataFrame:
        """
        Get information about submissions from PRAW API
        
        Args:
            submission_ids (list): stringed list of submission ids
            fields (list): stringed list of fields to get
            
        Returns:
            [pd.DataFrame]: Submission details
        """
        
        # Initialise dictionary from fields list
        submissions_info = {k:[] for k in fields}
        
        self.logger.info('Retrieving updated details for %s submissions', len(submission_ids))
        # Get information for each submission_id
        for submission_id in tqdm(submission_ids, desc='submissions'):
            # Create PRAW submission class
            submission = self.reddit.submission(id=submission_id)
            # Append required attribute from submission to the dictionary
            [submissions_info[attr].append(getattr(submission, attr)) for attr in fields]
            
        return pd.DataFrame(submissions_info)
    
    def get_comment_details(self, comment_ids: list, fields: list) -> pd.DataFrame:
        """
        Get informaiton for comments from PRAW API
        
        Args:
            comment_ids (list): stringed list of comment ids
            fields (list): stringed list of fields to get
            
        Returns:
            [pd.DataFrame]: Comment details
        """
        
        # Initialise dictionary from fields list
        comments_info = {k:[] for k in fields}
        
        self.logger.info('Retrieving updated details for %s comments', len(comment_ids))
        # Get informatino for each comment_id
        for comment_id in tqdm(comment_ids, desc='comments'):
            # Create PRAW comment class
            comment = self.reddit.comment(id=comment_id)
            # Append required attribute from comment to the dicionary
            [comments_info[attr].append(getattr(comment, attr)) for attr in fields]     

        return pd.DataFrame(comments_info)

    def _check_params(self, params: dict) -> dict:
        """
        Check if parameters are valid

        Args:
            params (dict): parameters dictionary
        """
        # Append created_utc to fields if not included
        if 'fields' in list(params.keys()):
            if 'created_utc' not in params['fields']:
                params['fields'].append('created_utc')

        return params
