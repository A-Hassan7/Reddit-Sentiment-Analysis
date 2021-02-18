import dash
import dash_core_components as dcc
import dash_html_components as html

from .header import header
from .search import search_bar
from .charts import wordcloud, sentiment_chart, submissions_table
from .store import store
from . import styles

layout = html.Div([
    header,
    search_bar,
    # data
    html.Div([
        dcc.Tabs([
            dcc.Tab([
                wordcloud
            ], label='WordCloud'),
            dcc.Tab([
                sentiment_chart
            ], label='Sentiment Plot'),
            dcc.Tab([
                submissions_table
            ], label='Submissions')
        ]),
    ], style=styles.charts_style),

    # hidden storage
    store
])
