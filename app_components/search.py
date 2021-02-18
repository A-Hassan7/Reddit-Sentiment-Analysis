from datetime import datetime, timedelta

import dash
import dash_core_components as dcc
import dash_html_components as html

from . import styles

search_bar = html.Div([
    
    html.Div([
        html.H3('Search', style={'textAlign': 'center', 'fontSize': 20})
    ]),
    
    html.Hr(),
    
    html.Div([
        # ticker input
        html.Label('Ticker', className='control_label'),
        dcc.Dropdown(
            id='ticker_input',
            options=[
                {'label': 'TSLA', 'value': 'TSLA'},
                {'label': 'GME', 'value': 'GME'},
                {'label': 'AAPL', 'value': 'AAPL'},
                {'label': 'AMZN', 'value': 'AMZN'},
                {'label': 'FB', 'value': 'FB'},
                {'label': 'SPY', 'value': 'SPY'}


            ], value='TSLA')
    ], style=styles.input_form_style),
        
    html.Br(),
    
    dcc.Loading([
        html.Div([
            html.Div([
            # submit button
            html.Button(
                'Submit',
                id='submit_button',
            )
        ], style=styles.input_form_style),
    ])], id='data_loading'),
    
    html.Br(),
    
    html.Div([
        # mimimum upvote
        html.Label('Minimum Upvote'),
        dcc.Slider(
            id='minimum_upvote',
            min=0,
            max=50,
            step=10,
            marks={
                0: '0',
                10: '10',
                20: '20',
                30: '30',
                40: '40',
                50: '50'
            },
            value=0
        )
    ], style={'textAlign': 'center'})
], style=styles.search_bar_style)
