import dash
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output


import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from welly import Well, Project
import pandas as pd
import os
import glob

import json

app = dash.Dash(__name__)

# load well data as a welly project
# # looks into root folder or subdirectories for LAS files
data_folder = r'Data/'
asps = []
for root, dirs, files in os.walk(data_folder):
    asps += glob.glob(os.path.join(root, '*.LAS'))

list_of_wells = [Well.from_las(file) for file in asps]
p = Project(list_of_wells)

well_names = [w.name for w in p]
dropdown_options = [{'label': n, 'value': i} for i,  n in enumerate(well_names)]

# load well data and plots from Doug 
# /Notebooks/dashwellviz WellLog example.ipynb
w = Well.from_las('Data/Poseidon1Decim.LAS')
df = w.df()

# Generate Vp and Vs from DTco and DTsm
df['Vp'] = (1000000 / df['DTCO']) / 3.281
df['Vs'] = (1000000 / df['DTSM']) / 3.281
df['Vp_max'] = df['Vp'].max() + 200

# make cross plot 
cross_plot = go.Figure(data=go.Scatter(
    x = df['Vp'],
    y = df['Vs'],
    mode='markers',
    opacity=0.7,
    marker=dict(
        size=8,
        color=df['NPHI'], #set color equal to a variable
        colorscale='turbid', # one of plotly colorscales
        line=dict(
            color='black',
            width=1
        ),
        showscale=True
    )
))
cross_plot.update_xaxes(title_text='Vp')
cross_plot.update_yaxes(title_text='Vs')
cross_plot.update_layout(template='plotly_white', height=800, width=800, title_text="Vp Vs Xplot - coloured by GR")

# make log tracks
log_plot = make_subplots(rows=1, cols=3, subplot_titles=("Vp","Vs", "Rho"), shared_yaxes=True)

log_plot.add_trace(
    go.Scatter(x=df['Vp'], y=df.index),
    row=1, col=1,
)

log_plot.add_trace(
    go.Scatter(x=df['Vs'], y=df.index),
    row=1, col=2
)

# log_plot.add_trace(
#     go.Scatter(x=df['HROM'], y=df.index), 
#     row=1, col=3
# )

log_plot.update_yaxes(range=[5000, 4400])
log_plot.update_layout(template='plotly_white', height=1000, width=600, title_text="Vp Vs Rho Subplots")

# Create app layout
app.layout = html.Div([
    html.Div(
        className="app-header",
        children=[
            html.Div(className='header', children=[
                html.Div(className='logo_txt', children=[
                    html.Img(src='./assets/img/swung_round_no_text.png', height='75px', className='logo_img'),
                    html.Div('Dash Viz', className="app-header--title")
                ]),
                html.Div(className='project-subtitle', children=['A Transform 2020 Project'])
            ])
        ]
    ),


    html.Div(className='page', children=[
        html.Div(className='sidebar', children=[
            html.H1('Sidebar'),
            'Configuration tools (dropdowns etc.) can go in here)',
            dcc.Dropdown(id='well-selector-dropdown', 
                        placeholder="Select a well",
                        options=dropdown_options),
            '------- Debuging Text --------',
            html.Pre(id='active-well', children=[])
        ]),
        html.Div([
            html.H1('Well Plots Can Go Here'),
            html.Div(className='well-plot-container', children=[
                dcc.Graph(id='log-plot', figure=log_plot) 
            ]),
        ]),
        
        html.Div(className='other-plot-container', children=[
            html.H1('Other Plots Can Go Here'),
            'cross plots, maps, etc',
            dcc.Graph(id='cross-plot', figure=cross_plot)

        ]),
    ]),
    html.Div(id='well-data-container', children=[], style={'display': 'none'}),
])


@app.callback(Output("active-well", "children"),
 [Input("well-selector-dropdown", "value")])
def update_active_well_name(well_number):
    w = p[well_number]
    data = dict(name=w.name, curves=list(w.data.keys()))

    return json.dumps(data)

@app.callback(Output("well-data-container", "children"),
 [Input("well-selector-dropdown", "value")])
def update_well_data(well_number):
   
    w = p[well_number]
    df = w.df()

    # Generate Vp and Vs from DTco and DTsm
    df['Vp'] = (1000000 / df['DTCO']) / 3.281
    df['Vs'] = (1000000 / df['DTSM']) / 3.281
    df['Vp_max'] = df['Vp'].max() + 200

    return df.to_json()


@app.callback(Output("log-plot", "figure"),
 [Input("well-data-container", "children")])
def update_log_tracks_plot(df_json):

    df = pd.read_json(df_json)

    # make log tracks
    log_plot = make_subplots(rows=1, cols=3, subplot_titles=("Vp","Vs", "Rho"), shared_yaxes=True)

    log_plot.add_trace(
        go.Scatter(x=df['Vp'], y=df.index),
        row=1, col=1,
    )

    log_plot.add_trace(
        go.Scatter(x=df['Vs'], y=df.index),
        row=1, col=2
    )

    log_plot.add_trace(
        go.Scatter(x=df['HROM'], y=df.index), 
        row=1, col=3
    )

    log_plot.update_yaxes(range=[5000, 4400])
    log_plot.update_layout(template='plotly_white', height=1000, width=600, title_text="Vp Vs Rho Subplots")

    return log_plot


@app.callback(Output("cross-plot", "figure"),
 [Input("well-data-container", "children")])
def update_cross_plot(df_json):

    df = pd.read_json(df_json)

    # make cross plot 
    cross_plot = go.Figure(data=go.Scatter(
        x = df['Vp'],
        y = df['Vs'],
        mode='markers',
        opacity=0.7,
        marker=dict(
            size=8,
            color=df['NPHI'], #set color equal to a variable
            colorscale='turbid', # one of plotly colorscales
            line=dict(
                color='black',
                width=1
            ),
            showscale=True
        )
    ))
    cross_plot.update_xaxes(title_text='Vp')
    cross_plot.update_yaxes(title_text='Vs')
    cross_plot.update_layout(template='plotly_white', height=800, width=800, title_text="Vp Vs Xplot - coloured by GR")

    return cross_plot

if __name__ == '__main__':
    app.run_server(debug=True)