import os
import logging
import logging.config
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Load environment variables
database_config_path = Path('.') / '.env'
load_dotenv(dotenv_path=database_config_path)

# Load logging configurations
logging_config_path = Path('.') / 'log_config.yaml'
with open(logging_config_path, 'r') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

class PRAWConfig:
    """
    Set configuration variables from .env file
    """
    # PRAW credentials
    REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
    REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
    REDDIT_USER_AGENT = os.getenv('REDDIT_USER_AGENT')

class Loggers:
    """
    Provides pre-configured loggers
    """
    console = logging.getLogger('console')
    
