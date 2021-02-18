import dash
import dash_core_components as dcc
import dash_html_components as html

from . import styles

header = html.Div([
    dcc.Markdown('''
        # Reddit Sentiment Analyser
        *Source Code: https://github.com/A-Hassan7/Reddit-Sentiment-Analysis*

        ###### Analyse Reddit sentiment for popular stocks using the Python Natural Language Toolkit (NLTK) 

    ''')
], style=styles.header_style)
