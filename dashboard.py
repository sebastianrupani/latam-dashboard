import pandas as pd
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate

region_values = ['América Latina', 'América Latina y el Caribe']
data_dir = '/home/cefnam/Documents/proyectos/dashboard/data/' 
GDP_per_cap_str = 'Total GDP per inhabitant at constant prices in dollars'
GDP_total_str = 'Total GDP at constant dollar prices'
countries_spanish = ['Brasil', 'Perú', 'México', 'Panamá', 
                     'Haití', 'República Dominicana', 'Belice',
                     'Venezuela (República Bolivariana de)',
                     'Bolivia (Estado Plurinacional de)']
coutries_english =  ['Brazil', 'Peru', 'Mexico', 'Panama', 
                     'Haiti', 'Dominican Republic', 'Belize',
                     'Venezuela', 'Bolivia']

PBI_per_cap = pd.read_excel(data_dir + 'PBI_per_capita.ods')
PBI_total = pd.read_excel(data_dir + 'PBI_total.xlsx')

PBI_data_regions = pd.concat([PBI_per_cap, PBI_total])
PBI_data_regions['indicator'].replace(['Producto interno bruto (PIB) total anual por habitante a precios constantes en dólares',
                                       'Producto interno bruto (PIB) total anual a precios constantes en dólares'],
                                      [GDP_per_cap_str, GDP_total_str], inplace=True)

PBI_per_cap_data_regions = PBI_data_regions[PBI_data_regions['indicator'] == GDP_per_cap_str]
PBI_per_cap_data_regions['País__ESTANDAR'].replace(countries_spanish, coutries_english, inplace=True)

PBI_data = PBI_data_regions[~PBI_data_regions['País__ESTANDAR'].isin(region_values)]
PBI_data.sort_values(by=['País__ESTANDAR', 'Años__ESTANDAR'])
PBI_data = PBI_data[PBI_data['País__ESTANDAR'] != 'Bahamas']
PBI_data['indicator'].replace(['Producto interno bruto (PIB) total anual por habitante a precios constantes en dólares',
                               'Producto interno bruto (PIB) total anual a precios constantes en dólares'],
                              [GDP_per_cap_str, GDP_total_str], inplace=True)
PBI_data['País__ESTANDAR'].replace(countries_spanish, coutries_english, inplace=True)
PBI_data['Growth'] = PBI_data['value'].diff()

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
                id='PBI_bar'),
            html.Br(),
            dcc.Dropdown(id='PBI_country_selector',
                         multi=True, placeholder='Select Countries to view their GDP per capita timeline',
                         value=['Brazil', 'Mexico', 'Argentina', 'Colombia'],
                         options=[{'label': country, 'value':country}
                                 for country in PBI_per_cap_data_regions['País__ESTANDAR'].drop_duplicates().sort_values()]),
            dcc.Graph(
                id='PBI_per_cap_timeline'),
        ])
    ]),
    dcc.Dropdown(id='growth_year_selector',
                 multi=True,
                 value=[2011, 2012, 2013, 2014, 2015],
                 options=[{'label': years, 'value':years}
                          for years in PBI_data[PBI_data['Años__ESTANDAR'] != 1990]['Años__ESTANDAR'].drop_duplicates().sort_values()]),
    dcc.Graph(id='annual_growth_pie')
])

@app.callback(Output('PBI_map', 'figure'),
              Input('PBI_indicator_selector', 'value'),
              Input('PBI_year_selector', 'value'))
def PBI_map_indicator_selector(indicator, year):
    PBI_indicator = PBI_data[PBI_data['indicator'] == indicator]
    PBI_indicator_year = PBI_indicator[PBI_indicator['Años__ESTANDAR'] == year]
    fig = px.choropleth(PBI_indicator_year, locationmode='country names',
                        locations='País__ESTANDAR', color='value',
                        #color_continuous_scale="Viridis",
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
    PBI_total['País__ESTANDAR'].replace(['Dominican Republic', 
                                         'San Vicente y las Granadinas'], 
                                        ['Dominican Rep.', 'San Vte. y Granadinas'], 
                                        inplace=True)
    fig = px.bar(PBI_total, x='País__ESTANDAR', y='value',
                 log_y=True, color='value', height=600,
                 title=f'Total GDP at constant dollar prices - Year {year}')
    fig.layout.xaxis.title = None
    fig.layout.yaxis.title = None
    PBI_per_cap = PBI_year[PBI_year['indicator'] == GDP_per_cap]
    PBI_per_cap = PBI_per_cap[['País__ESTANDAR', 'value']]
    PBI_per_cap.rename(columns={'value': 'GDP_per_cap'}, inplace=True)
    PBI_per_cap['País__ESTANDAR'].replace(['Dominican Republic', 
                                           'San Vicente y las Granadinas'], 
                                          ['Dominican Rep.', 'San Vte. y Granadinas'], 
                                           inplace=True)
    #print('PBI_total shape: ' + PBI_total.shape)
    PBI_total = PBI_total.merge(right=PBI_per_cap, how='left', on='País__ESTANDAR')
    #print('PBI_total shape after merge: ' + PBI_total.shape)
    #print('Columns: ', PBI_total.columns)
    fig.add_trace(go.Scatter(x=PBI_total['País__ESTANDAR'], y=PBI_total['GDP_per_cap'], 
                             mode='lines+markers', 
                             line=dict(color='orange'), name='GDP per capita',
                             marker= dict(size=8, symbol='diamond',
                             color='yellow', line_width=2)))
    fig.update_layout(coloraxis_colorbar=dict(
                      title="Total GDP",
                      lenmode="pixels", len=300))
    return fig

@app.callback(Output('PBI_per_cap_timeline', 'figure'),
              Input('PBI_country_selector', 'value'))
def PBI_per_cap_country(country):
    my_plasma = ['#0d0887',  '#7201a8', '#fdca26', '#ed7953', '#bd3786', 
                 '#46039f', '#9c179e', '#d8576b','#fb9f3a', '#f0f921']
    if not country:
        raise PreventUpdate
    PBI_per_cap_country = PBI_per_cap_data_regions[PBI_per_cap_data_regions['País__ESTANDAR'].isin(country)]
    fig = px.area(PBI_per_cap_country, x='Años__ESTANDAR', y='value',
                  facet_col='País__ESTANDAR', facet_col_wrap=2,
                  color='País__ESTANDAR', color_discrete_sequence=my_plasma)
    return fig

@app.callback(Output('annual_growth_pie', 'figure'),
              Input('growth_year_selector', 'value'))
def annual_PBI_growth(years):
    if not years:
        raise PreventUpdate
    annual_PBI_change = PBI_data[(PBI_data['indicator'] == GDP_total_str) & (PBI_data['Años__ESTANDAR'].isin(years))]
    fig = px.pie(annual_PBI_change, values='Growth', names='País__ESTANDAR', color='País__ESTANDAR', 
                 facet_col='Años__ESTANDAR', facet_col_wrap=5, hole=0)
    return fig

    
if __name__ == '__main__':
    app.run_server(debug=True)