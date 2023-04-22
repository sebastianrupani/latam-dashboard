import pandas as pd
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
from dash.dependencies import Output, Input, State

region_values = ['América Latina', 'América Latina y el Caribe']
data_dir = '/home/cefnam/Documents/proyectos/dashboard/data/' 
PBI_per_cap = pd.read_excel(data_dir + 'PBI_per_capita.ods')
PBI_total = pd.read_excel(data_dir + 'PBI_total.xlsx')
PBI_data = pd.concat([PBI_per_cap, PBI_total])
PBI_data = PBI_data[~PBI_data['País__ESTANDAR'].isin(region_values)]
PBI_data = PBI_data[PBI_data['País__ESTANDAR'] != 'Bahamas']
PBI_data['indicator'].replace(['Producto interno bruto (PIB) total anual por habitante a precios constantes en dólares',
                               'Producto interno bruto (PIB) total anual a precios constantes en dólares'],
                              ['Total GDP per inhabitant at constant prices in dollars',
                               'Total GDP at constant dollar prices'], inplace=True)
PBI_data['País__ESTANDAR'].replace(['Brasil', 'Perú', 'México', 'Panamá', 
                                    'Haití', 'República Dominicana', 'Belice',
                                    'Venezuela (República Bolivariana de)',
                                    'Bolivia (Estado Plurinacional de)'], 
                                      ['Brazil', 'Peru', 'Mexico', 'Panama', 
                                       'Haiti', 'Dominican Republic', 'Belize',
                                       'Venezuela', 'Bolivia'], inplace=True)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

app.layout = html.Div([
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='PBI_indicator_selector',
                        options=[{'label': indicator, 'value':indicator}
                                for indicator in PBI_data['indicator'].drop_duplicates().sort_values()],
                        value=PBI_data['indicator'].drop_duplicates().sort_values()[0]),
            dcc.Dropdown(id='PBI_year_selector',
                        value=2015,
                        options=[{'label': year, 'value':year}
                                for year in PBI_data['Años__ESTANDAR'].drop_duplicates().sort_values()]),
            dcc.Graph(
                id='PBI_map')
        ]),
        dbc.Col([
            dcc.Graph(
                id='PBI_bar')
        ])
    ])
])

@app.callback(Output('PBI_map', 'figure'),
              Input('PBI_indicator_selector', 'value'),
              Input('PBI_year_selector', 'value'))
def PBI_map_indicator_selector(indicator, year):
    PBI_indicator = PBI_data[PBI_data['indicator'] == indicator]
    PBI_indicator_year = PBI_indicator[PBI_indicator['Años__ESTANDAR'] == year]
    fig = px.choropleth(PBI_indicator_year, locationmode='country names',
                        locations='País__ESTANDAR', color='value',
                        color_continuous_scale="Viridis",
                        hover_name='País__ESTANDAR', hover_data='value',
                        height=900, width=800,
                        title=indicator)
    fig.layout.geo.lataxis.range = [-60, 40]
    fig.layout.geo.lonaxis.range = [-120, -30]
    return fig

@app.callback(Output('PBI_bar', 'figure'),
              Input('PBI_year_selector', 'value'))
def PBI_bar(year):
    GDP_per_cap = 'Total GDP per inhabitant at constant prices in dollars'
    GDP_total = 'Total GDP at constant dollar prices'
    PBI_year = PBI_data[PBI_data['Años__ESTANDAR'] == year]
    PBI_total = PBI_year[PBI_year['indicator'] == GDP_total]
    PBI_total.sort_values(by=['value'], ascending=False, 
                          inplace=True)
    fig = px.bar(PBI_total, x='País__ESTANDAR', y='value',
                 log_y=True)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)