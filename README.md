[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



# Reddit Sentiment Analyser
#### This project aims to analyse stock market sentiment on Reddit using Natural Language Processing.

## Motivation
* A large audience of retail traders organised in social media platforms such as reddit have the ability to influence stock prices.
* By analysing the sentiment of these traders through thier social media posts, it may be possible to anticipate stock market moves.
* [Bloomberg article on r/Wallstreetbets](https://www.bloomberg.com/news/articles/2020-02-26/reddit-s-profane-greedy-traders-are-shaking-up-the-stock-market)

## Features
* View a WordCloud and frequency distribution of the most mentioned words about a stock
* Analyse the sentiment of reddit submissions using the VADER model with a customised lexicon

## Data
 Reddit submissions are retrieved using the [Pushshift](https://github.com/pushshift/api) and [PRAW](https://github.com/praw-dev/praw) API's. The submission titles are preprocessed and analysed using [NLTK](https://github.com/nltk/nltk) for sentiment scores.

 ## Installation
```bash
git clone https://github.com/A-Hassan7/Reddit-Sentiment-Analysis.git

cd Reddit-Sentiment-Analysis

pip install -r requirements.txt
```

## Usage
run ```python app.py``` from the terminal then navitage to ```http://127.0.0.1:8050/``` in your browser.

## Note
* The app currently uses preloaded data. A future release will query the `RedditAPI` directly.

## Improvements
* Implament direct querying to the `RedditAPI`
* Migrate to an SQL database using [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) as an ORM
* Add more features! Dynamicly tune VADER, regress sentiment with closing prices, analyse selftext etc.
* Implament tests
