import dash
import dash_core_components as dcc
import dash_html_components as html

store = html.Div([
    html.Div(id='submissions_store'),
    html.Div(id='stock_price_store'),
    html.Div(id='preprocessed_text_store'),
    html.Div(id='unprocessed_text_store')
], style={'display': 'none'})
