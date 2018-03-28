#!/usr/bin/python3

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import State, Input, Output
import datetime
import pandas as pd
import plotly.graph_objs as go
from pytrends.request import TrendReq
import requests

# initialize pytrends API
pytrends = TrendReq(hl='en-US', tz=360)

# get list of coins from cryptocompare API
try:
    coin_list = [(k, v['CoinName']) for k, v in requests.get('https://www.cryptocompare.com/api/data/coinlist/').json()['Data'].items()]
except KeyError:
    coin_list = []

coin_list.sort(key=lambda coin: coin[1].lower())

app = dash.Dash()

app.layout = html.Div([
    html.H1('CryptoTrends'),
    dcc.Input(
        placeholder='Enter a search term...',
        type='text',
        id='search-term'
    ),
    dcc.Dropdown(
        id='coin-selection',
        options=[{'label': '{0} ({1})'.format(j, i) , 'value': i} for i, j in coin_list]
    ),
    html.Button('Search', id='search-button'),
    html.Div(id='graph-output')
])

@app.callback(
    Output('graph-output', 'children'),
    [Input('search-button', 'n_clicks')],
    [State('search-term', 'value'), State('coin-selection', 'value')])
def update_graph(n_clicks, search_term, coin_selection):
    if search_term and coin_selection:
        # query google trends API
        pytrends.build_payload([search_term], cat=0, timeframe='today 5-y', geo='', gprop='')
        google_trends_df = pytrends.interest_over_time()

        if google_trends_df.empty:
            return ['No Results Found']

        # query cryptocompare API
        req = requests.get('https://min-api.cryptocompare.com/data/histoday?fsym=' + coin_selection + '&tsym=USD&allData=true').json()
        
        try:
            cryptocompare_df = pd.DataFrame(req['Data'])
        except KeyError:
            return ['No Results Found']

        if cryptocompare_df.empty:
            return ['No Results Found']

        # get max price of coin
        try:
            max_price = cryptocompare_df['high'].max()
        except KeyError:
            return ['No Results Found']

        # create graph
        return [dcc.Graph(
            id='graph',
            figure={
                'data': [
                    # create google trends graph
                    go.Scatter(
                        x=[i.date().strftime('%Y-%m-%d') for i in google_trends_df.index],
                        y=[i for i in google_trends_df[search_term]],
                        name='Popularity',
                        yaxis='y2'
                    ),
                    # create cryptocompare price graph
                    go.Scatter(
                        x=[datetime.datetime.utcfromtimestamp(i).strftime('%Y-%m-%d') for i in cryptocompare_df['time']],
                        y=[i for i in cryptocompare_df['high']],
                        name='Price'
                    )
                ],
                'layout': go.Layout(
                    xaxis={'title': 'Date'},
                    yaxis={'title': 'Price'},
                    yaxis2={'title': 'Popularity', 'side': 'right', 'overlaying': 'y'}
                )
            }
        )]
    else:
        return []

if __name__ == '__main__':
    app.run_server(debug=True)
