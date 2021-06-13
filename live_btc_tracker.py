import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json


#Get the initial data ready
coin_info = json.loads(requests.get('https://api.coincap.io/v2/rates').content).get('data')
curr_rate = 0
for coin in coin_info:
    if(coin.get('symbol')=='BTC'):
        curr_rate = float(coin.get('rateUsd'))
df_line = pd.DataFrame([[datetime.utcnow(),curr_rate ]],columns=['time', 'rate'])
last_update_time = datetime.utcnow()


#Create the dash app, and define its layout
app = dash.Dash()
server = app.server
app.layout = html.Div(children=[
    html.H1(
        children='BTC Live Conversion Rate',
        style={
            'textAlign': 'center'
        }
    ),
    
    html.H3(
        id='last_update_time',
        style={
            'textAlign': 'center'
        }
    ),
    
    html.H1(
        children="   ",
        style={
            'textAlign': 'center'
        }
    ),
    html.Div(children=[
        html.Div(children=[
            html.H3(id='rate_text', children ='Latest BTC-USD Rate',  style={'textAlign': 'center'}),
            html.H1(id='rate',  style={'textAlign': 'center','bottomMargin':50})],
            style={"border":"2px black solid"}),
        html.Div(children=[
            dcc.Graph(id='plot')],
            style={"border":"2px black solid"})],
        style = {'width': '100%', 'height': '90%', 'float': 'left', 'display': 'inline-block', "border":"2px black solid"}),
    dcc.Interval(
        id='interval-component',
        interval=5000, # 5000 milliseconds = 5 seconds
        n_intervals=0),
    html.Div(id='intermediate-value', children=df_line.to_json(date_format='iso', orient='split'), style={'display': 'none'})
])


#Callback to update the invisible intermediate-value element
@app.callback(Output('intermediate-value', 'children'), [Input('interval-component', 'n_intervals')],
              [State('intermediate-value', 'children')])
def clean_data(value, json_old):
    df_old = pd.read_json(json_old, orient='split')
    coin_info = json.loads(requests.get('https://api.coincap.io/v2/rates').content).get('data')
    curr_rate = 0
    for coin in coin_info:
        if(coin.get('symbol')=='BTC'):
            curr_rate = float(coin.get('rateUsd'))
     
    df_curr = pd.DataFrame([[datetime.utcnow(),curr_rate ]],columns=['time', 'rate'])
    df_new = df_old.append(df_curr,ignore_index=True)
    #return latest 100 entries
    return df_new.tail(100).to_json(date_format='iso', orient='split')



#Callback to update the last-update-time element
@app.callback(Output('last_update_time', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_time(n):
    return 'Last update time (UTC): {}'.format(datetime.utcnow())


#Callback to update the latest rate value
@app.callback(Output('rate', 'children'),
              [Input('intermediate-value', 'children')])
def update_rate(jsonified_data):
    df = pd.read_json(jsonified_data, orient='split')
    curr_rate = df.tail(1)['rate'].max()

    return curr_rate


#Callback to update the line-graph
@app.callback(Output('plot', 'figure'),
              [Input('intermediate-value', 'children')])
def update_realtime_fig(json1):
    df_go = pd.read_json(json1, orient='split').tail(500)
    fig = make_subplots()
    fig.add_trace(go.Scatter(x=df_go['time'], y=df_go['rate'],
                        mode='lines+markers',
                        name='Devices'))
    fig.update_layout(
        title_text="Rate in last 100 readings", uirevision="Don't change"
    )
    fig.update_yaxes(title_text="Rate", secondary_y=False)
    return fig

if __name__ == '__main__':
    app.run_server()

