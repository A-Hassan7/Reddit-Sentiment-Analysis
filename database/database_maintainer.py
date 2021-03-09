import requests

import pandas as pd

from config import Loggers

from . import utils, models
from .database_manager import DatabaseManager


class DatabaseMaintainer:
    """
    The DatabaseMaintainer class provides methods to perform maintinance
    tasks on the database.
    
    TODO: Create function to schedule submission data update 
            (Use RedditManager.update_submissions)
    """

    def __init__(self):
        """Initialise class"""

        self.database_manager = DatabaseManager()
        self.sec_companies_url = "https://www.sec.gov/files/company_tickers.json"
        self.logger = Loggers.console

    def update_companies(self):
        """
        Updates the companies table with new data from the SEC
        """

        self.logger.info("retrieving companies data from %s", self.sec_companies_url)
        # Retrieve securities data from the SEC
        r = requests.get(self.sec_companies_url)
        companies_info = pd.DataFrame(r.json()).transpose()

        self.logger.info("cleaning data")
        # drop duplicate tickers and rename columns
        companies_info = companies_info.drop_duplicates('ticker')
        companies_info.rename(columns={'cik_str': 'cik'}, inplace=True)

        # strip punctuation from title
        # punctuation causes errors in postgresql
        companies_info['title'] = companies_info.title.apply(
            lambda x: utils.strip_punctuation(x).title()
        )

        # insert dataframe into database
        self.database_manager.insert_values(
            model=models.Companies,
            values=companies_info
        )
        
        self.logger.info("Companies table update complete")

# database_maintainer = DatabaseMaintainer()
# database_maintainer.update_companies()