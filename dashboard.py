import pandas as pd
import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Output, Input, State
from dash.exceptions import PreventUpdate
import dashboard_utils as du

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
PBI_data_regions = PBI_data_regions.rename(columns={'País__ESTANDAR':'Country', 
                                                    'Años__ESTANDAR':'Year'})

PBI_per_cap_data_regions = PBI_data_regions[PBI_data_regions['indicator'] == GDP_per_cap_str]
PBI_per_cap_data_regions['Country'].replace(countries_spanish, coutries_english, inplace=True)

PBI_data = PBI_data_regions[~PBI_data_regions['Country'].isin(region_values)]
PBI_data.sort_values(by=['Country', 'Year'])
PBI_data = PBI_data[PBI_data['Country'] != 'Bahamas']
PBI_data['indicator'].replace(['Producto interno bruto (PIB) total anual por habitante a precios constantes en dólares',
                               'Producto interno bruto (PIB) total anual a precios constantes en dólares'],
                              [GDP_per_cap_str, GDP_total_str], inplace=True)
PBI_data['Country'].replace(countries_spanish, coutries_english, inplace=True)
PBI_data['Growth'] = PBI_data['value'].diff()

years_list = PBI_data['Year'].drop_duplicates().sort_values()
years_list = list(years_list)
growth_years_list = years_list[1:]
plasma0 = px.colors.sequential.Plasma[0]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])

app.layout = html.Div([
    html.H1('Latin America socioeconomic insights',
            style={
                'text-transform': 'uppercase',
                'font': 'calibri',
                'font-size': '60px',
                'font-weight': 'bold',
                'color': '#caf4fa',
                'background-color': '#0d0887',
                'text-align': 'center'
            }),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dcc.Dropdown(id='PBI_indicator_selector',
                        options=[{'label': indicator, 'value':indicator}
                                for indicator in PBI_data['indicator'].drop_duplicates().sort_values()],
                        value=PBI_data['indicator'].drop_duplicates().sort_values()[0],
                        style={'background-color': '#caf4fa',
                               'color': '#0d0887',
                               'border-color': '#0d0887'}),
            html.Br(),
            dcc.Slider(id='PBI_year_slider', min=years_list[0], 
                       max=years_list[-1], step=1, value=2015, 
                       marks={year: {'label': str(year), 
                                     'style': {'color': plasma0}} 
                                     for year in years_list[::3]},
                       tooltip={"placement": "bottom", 
                                "always_visible": True}),
            html.Br(),
            dcc.Graph(
                id='PBI_map'),
            dbc.ButtonGroup([  
                dbc.Button('GDP Map information', id='GDP_map_info_button',
                           style={'margin-left': '60px'}),
                dbc.Button(' GDP Map insights  ', id='GDP_map_insights_button',
                           style={'margin-left': '60px'})
            ])  
    ], lg=5),
        dbc.Col([
            dbc.Collapse(
                dcc.Markdown(
                    id='map_markdown', style={'padding-left': '80px',
                                              'marginTop': 100,
                                              'color': 'black'},
                ),
                id='GDP_map_collapse'
            ),
            dcc.Graph(
                id='PBI_bar'),
            dbc.Button('GDP Bar information', id='GDP_bar_info_button'),
            dbc.Collapse(html.P('Here goes GDP Bar information'),
                         id='GDP_bar_info_collapse'),
            html.Br(),
            dbc.Row(
                dbc.Col(
            dcc.Dropdown(id='PBI_country_selector',
                         multi=True, placeholder='Select Countries to view their GDP per capita timeline',
                         value=['Brazil', 'Mexico', 'Argentina', 'Colombia'],
                         options=[{'label': country, 'value':country}
                                 for country in PBI_per_cap_data_regions['Country'].drop_duplicates().sort_values()],
                        style={'background-color': '#caf4fa',
                               'color': '#0d0887',
                               'border-color': '#0d0887'}),
                lg={'size':7, 'offset':2})
            ),
            dcc.Graph(
                id='PBI_per_cap_timeline'),
        ], lg=7)
    ]),
    html.Br(),
    html.Br(),
    dbc.Row(
        dbc.Col([
            dcc.RangeSlider(min=growth_years_list[0], max=growth_years_list[-1], step=1, 
                            value=[growth_years_list[-4], growth_years_list[-1]], 
                            id='growth_year_slider',
                            tooltip={"placement": "bottom", 
                                     "always_visible": True},
                            marks={year: {'label': str(year), 
                                          'style': {'color': plasma0}} 
                                          for year in years_list[::3]}),
            dcc.Graph(id='annual_growth_pie')
        ], lg={'size':8, 'offset':2})
    )
], style={'backgroundColor': '#83aef2'})

@app.callback(Output('PBI_map', 'figure'),
              Input('PBI_indicator_selector', 'value'),
              Input('PBI_year_slider', 'value'))
def GDP_map_selector(indicator, year):
    PBI_indicator = PBI_data[PBI_data['indicator'] == indicator]
    PBI_indicator_year = PBI_indicator[PBI_indicator['Year'] == year]
    fig = px.choropleth(PBI_indicator_year, locationmode='country names',
                        locations='Country', color='value',
                        hover_name='Country', hover_data='value',
                        height=900, width=800,
                        title='<b>'+indicator+' - Year '+str(year)+'<b>')
    fig.layout.geo.lataxis.range = [-60, 40]
    fig.layout.geo.lonaxis.range = [-120, -30]
    fig.layout.geo.bgcolor = '#83aef2'
    fig.layout.paper_bgcolor = '#83aef2'
    fig.layout.geo.countrycolor = '#080808'
    fig.layout.geo.countrywidth = 3
    fig.update_layout(coloraxis_colorbar= {
        'title': '<b>'+'GDP'+'<b>'
    })
    fig.update_layout(title={
        'y': 0.95
    })
    return fig

@app.callback(Output('PBI_bar', 'figure'),
              Input('PBI_year_slider', 'value'))
def PBI_bar(year):
    GDP_per_cap = 'Total GDP per inhabitant at constant prices in dollars'
    GDP_total = 'Total GDP at constant dollar prices'
    PBI_year = PBI_data[PBI_data['Year'] == year]
    PBI_total = PBI_year[PBI_year['indicator'] == GDP_total]
    PBI_total.sort_values(by=['value'], ascending=False, 
                          inplace=True)
    PBI_total['Country'].replace(['Dominican Republic', 
                                         'San Vicente y las Granadinas'], 
                                        ['Dominican Rep.', 'San Vte. y Granadinas'], 
                                        inplace=True)
    fig = px.bar(PBI_total, x='Country', y='value',
                 log_y=True, color='value', height=600,
                 title='<b>'+f'Total GDP at constant dollar prices - Year {year}'+'<b>')
    fig.layout.xaxis.title = None
    fig.layout.yaxis.title = None
    fig.layout.plot_bgcolor = '#caf4fa'
    PBI_per_cap = PBI_year[PBI_year['indicator'] == GDP_per_cap]
    PBI_per_cap = PBI_per_cap[['Country', 'value']]
    PBI_per_cap.rename(columns={'value': 'GDP_per_cap'}, inplace=True)
    PBI_per_cap['Country'].replace(['Dominican Republic', 
                                           'San Vicente y las Granadinas'], 
                                          ['Dominican Rep.', 'San Vte. y Granadinas'], 
                                           inplace=True)
    #print('PBI_total shape: ' + PBI_total.shape)
    PBI_total = PBI_total.merge(right=PBI_per_cap, how='left', on='Country')
    #print('PBI_total shape after merge: ' + PBI_total.shape)
    #print('Columns: ', PBI_total.columns)
    fig.add_trace(go.Scatter(x=PBI_total['Country'], y=PBI_total['GDP_per_cap'], 
                             mode='lines+markers', 
                             line=dict(color='orange'), name='<b>GDP per capita<b>',
                             marker= dict(size=8, symbol='diamond',
                             color='yellow', line_width=2)))
    fig.update_layout(coloraxis_colorbar=dict(
                      title='<b>'+"Total GDP"+'<b>',
                      lenmode="pixels", len=300))
    fig.layout.paper_bgcolor = '#83aef2'
    return fig

@app.callback(Output('PBI_per_cap_timeline', 'figure'),
              Input('PBI_country_selector', 'value'))
def PBI_per_cap_country(country):
    my_plasma = ['#0d0887',  '#7201a8', '#fdca26', '#ed7953', '#bd3786', 
                 '#46039f', '#9c179e', '#d8576b','#fb9f3a', '#f0f921']
    if len(country) % 2 == 0:
        area_height = 100 * len(country)
    else:
        area_height= 100 * (len(country) + 1)
    if not country:
        raise PreventUpdate
    PBI_per_cap_country = PBI_per_cap_data_regions[PBI_per_cap_data_regions['Country'].isin(country)]
    fig = px.area(PBI_per_cap_country, x='Year', y='value',
                  facet_col='Country', facet_col_wrap=2,
                  height=area_height, color='Country',
                  color_discrete_sequence=my_plasma,
                  title='<b>Historical GDP per capita for each country<b>')
    fig.layout.paper_bgcolor = '#83aef2'
    fig.layout.plot_bgcolor = '#caf4fa'
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return fig

@app.callback(Output('annual_growth_pie', 'figure'),
              Input('growth_year_slider', 'value'))
def annual_PBI_growth(years):
    if not years:
        raise PreventUpdate
    years_range = list(range(years[0], years[-1]+1))
    annual_PBI_change = PBI_data[(PBI_data['indicator'] == GDP_total_str) & (PBI_data['Year'].isin(years_range))]
    annual_growth = annual_PBI_change[annual_PBI_change['Growth'] > 0]
    annual_growth.loc[annual_growth['Growth'] < 3000, 'Country'] = 'Other' # Represent only large countries
    annual_growth.sort_values('Year', inplace=True)
    extra_height = 300
    if len(years_range) > 4:
        if len(years_range) <= 8:
            extra_height = 500
        elif len(years_range) <= 12:
            extra_height = 1000
        elif len(years_range) <= 16:
            extra_height = 1500
        elif len(years_range) <= 20:
            extra_height = 2000
        elif len(years_range) <= 24:
            extra_height = 2500
        elif len(years_range) <= 28:
            extra_height = 3000
    
    if len(years_range) <= 4:
        width_fixer = 350*len(years_range)
    else:
        width_fixer =350*4

    my_plasma = ['#0d0887',  '#7201a8', '#fdca26', '#ed7953', '#bd3786', 
                 '#46039f', '#9c179e', '#d8576b','#fb9f3a', '#f0f921']
    
    fig = px.pie(annual_growth, values='Growth', names='Country', facet_col='Year',
                 facet_col_wrap=4, width=100+width_fixer, height=300+extra_height,
                 facet_col_spacing=.04, facet_row_spacing=.04, color_discrete_sequence=my_plasma)
    fig.layout.paper_bgcolor = '#83aef2'
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return fig

@app.callback(Output('GDP_map_collapse', 'is_open'),
              Output('map_markdown', 'children'),
              Input('GDP_map_info_button', 'n_clicks'),
              Input('GDP_map_insights_button', 'n_clicks'),
              State('GDP_map_collapse', 'is_open'))
def GDP_map_description(n, n_2, is_open):
    markdown = []
    markdown_info = du.GDP_map_information_markdown
    markdown_insights = du.GDP_map_insights_markdown
    if n:
        return not is_open, markdown_info
    if n_2:
        return not is_open, markdown_insights
    return is_open, markdown

"""
@app.callback(Output('GDP_map_collapse', 'is_open', allow_duplicate=True),
              Output('map_markdown', 'children', allow_duplicate=True),
              Input('GDP_map_insights_button', 'n_clicks'),
              State('GDP_map_collapse', 'is_open'))
def GDP_map_insights(n, is_open):
    markdown = ['This is a dummy markdown - Insights']
    if n:
        return not is_open, markdown
    return is_open, markdown"""

@app.callback(Output('GDP_bar_info_collapse', 'is_open'),
              Input('GDP_bar_info_button', 'n_clicks'),
              State('GDP_bar_info_collapse', 'is_open'))
def GDP_bar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
    
if __name__ == '__main__':
    app.run_server(debug=True)