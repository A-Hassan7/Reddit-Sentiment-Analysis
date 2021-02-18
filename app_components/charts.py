import dash
import dash_core_components as dcc
import dash_html_components as html

from . import styles

wordcloud = html.Div([
    # max words
    html.Div([
        html.Label('Max Words'),
        dcc.Slider(
            id='max_words',
            min=10,
            max=60,
            step=10,
            marks={k: str(k) for k in range(10,110, 10)},
            value=30
        )
    ], style=styles.max_words_slider_style),

    dcc.Loading([
        html.Div([
            html.Div([
                # wordcloud image
                dcc.Graph(
                    id='wordcloud'
                )
            ], style={'padding': '20px'}),

            html.Div([
                # frequency distribution chart
                dcc.Graph(
                    id='freqdist'
                )
            ], style={'padding': '20px'}),
        ], style=styles.wordcloud_freqdist_style)
    ])
], style=styles.tab_content_style)


# sentiment chart
sentiment_chart = html.Div([

    # rolling window slider
    html.Div([
        html.Label('Sentiment Smoothness'),
        dcc.Slider(
            id='sentiment_smoothness',
            min=0,
            max=100,
            step=10,
            marks={k: str(k) for k in range(0,110, 10)},
            value=10
        )
    ], style=styles.max_words_slider_style),

    dcc.Loading([
        html.Div([
            dcc.Graph(
                id='sentiment'
            )
        ], style=styles.sentiment_chart_style)
    ])
], style=styles.tab_content_style)


submissions_table = html.Div(
    id='submissions_table',
    style=styles.submissions_table_style
)


def generate_table(dataframe, max_rows=1000000000):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col.replace('_', ' ').upper()) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])
