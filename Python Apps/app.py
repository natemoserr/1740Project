from dash import Dash, html, dcc, callback, Output, Input
import dash_ag_grid as dag
import pandas as pd
import plotly.express as px
from datetime import datetime 

import json

with open("pa_counties.geojson", "r") as f:
    pa_counties_geojson = json.load(f)



df = pd.read_csv("Filtered_TitleV_Permits.csv")

app = Dash(__name__)

df["Date Received"] = pd.to_datetime(df["Date Received"], errors="coerce")
df["Date Disposed"] = pd.to_datetime(df["Date Disposed"], errors="coerce")
df["Date Expires"] = pd.to_datetime(df["Date Expires"], errors="coerce")

today = datetime.now()
df["processing_days"] = (df["Date Disposed"] - df["Date Received"]).dt.days
df["backlogged"] = (
    (df["processing_days"] > 548) | 
    (df.loc[df["Date Disposed"].isna(), "Date Expires"] < today)
)
df["Disposition Year"] = df["Date Disposed"].dt.year

regional_backlog = (
    df[df["backlogged"]]
    .dropna(subset=["Disposition Year", "Region"])
    .groupby(["Disposition Year", "Region"])
    .size()
    .unstack(fill_value=0)
)

regional_backlog = regional_backlog.sort_index()
regional_backlog_display = regional_backlog.reset_index()

#create the plot
fig = px.line(
    regional_backlog,
    x=regional_backlog.index,
    y=regional_backlog.columns,
    title="Backlogged Permits by Region Over Time"
)

# Heatmap - Backlogged Permits by Region and Year

import plotly.express as px

heatmap_data = regional_backlog.T

fig_heatmap = px.imshow(
    heatmap_data,
    labels=dict(
        x="Disposition Year",
        y="Region",
        color="Backlogged Permits"
    ),
    title="Heatmap of Backlogged Permits by Region and Year",
    aspect="auto",
    color_continuous_scale="Blues"
)

# fig_heatmap.update_layout(
#     font=dict(x
#         family="Inter, Arial, sans-serif",
#         size=12,
#         color="#0072bc"
#     )
# )

#ig_heatmap.show()

# Aggregate total backlog by region
region_totals = (
    df[df["backlogged"]]
    .groupby("Region")
    .size()
    .reset_index(name="Total Backlogged Permits")
)

# Sort descending
region_totals = region_totals.sort_values(
    "Total Backlogged Permits", ascending=False
)

fig_ranked = px.bar(
    region_totals,
    x="Region",
    y="Total Backlogged Permits",
    color="Region",
    title="Total Backlogged Permits by Region (Ranked)",
    template="simple_white"
)

fig_ranked.update_layout(
    font=dict(
        family="Inter, Arial, sans-serif",
        size=12,
        color="#0072bc"
    ),
    xaxis_title="Region",
    yaxis_title="Number of Backlogged Permits",
    showlegend=False
)

backlog_by_year = (
    df[df["backlogged"]]
    .dropna(subset=["Disposition Year"])
    .groupby("Disposition Year")
    .size()
    .reset_index(name="Backlogged Permits")
    .sort_values("Disposition Year")
)

fig_year_bar = px.bar(
    backlog_by_year,
    x="Disposition Year",
    y="Backlogged Permits",
    title="Backlogged Permits by Year",
    template="simple_white"
)

fig_year_bar.update_layout(
    font=dict(
        family="Inter, Arial, sans-serif",
        size=12,
        color="#0072bc"
    ),
    xaxis_title="Disposition Year",
    yaxis_title="Number of Backlogged Permits"
)

facet_data = regional_backlog.reset_index().melt(
    id_vars="Disposition Year",
    var_name="Region",
    value_name="Backlogged Permits"
)

fig_facet = px.line(
    facet_data,
    x="Disposition Year",
    y="Backlogged Permits",
    facet_col="Region",
    facet_col_wrap=3,
    title="Backlogged Permits by Region (Faceted)",
    template="simple_white"
)

fig_facet.update_layout(
    font=dict(family="Inter, Arial, sans-serif", size=12, color="#0072bc")
)


county_backlog_pivot = (
    df[df["backlogged"]]
    .dropna(subset=["Disposition Year", "County"])
    .groupby(["Disposition Year", "County"])
    .size()
    .unstack(fill_value=0)
    .sort_index()
)

available_years = [int(year) for year in county_backlog_pivot.index]





# geojson_counties = {
#     feature["properties"]["county_nam"].strip().upper()
#     for feature in pa_counties_geojson["features"]
# }

# data_counties = set(county_region_map_data["County"].unique())

# missing_in_geojson = sorted(data_counties - geojson_counties)
# missing_in_data = sorted(geojson_counties - data_counties)

# print("Counties in data not matched in GeoJSON:")
# print(missing_in_geojson)

# print("\nCounties in GeoJSON not in data:")
# print(missing_in_data)


county_region_map_data = (
    df[["County", "Region"]]
    .dropna(subset=["County", "Region"])
    .drop_duplicates()
    .sort_values(["Region", "County"])
)

county_region_map_data["County"] = (
    county_region_map_data["County"]
    .astype(str)
    .str.strip()
    .str.upper()
)

county_region_map_data["Region"] = (
    county_region_map_data["Region"]
    .astype(str)
    .str.strip()
)



fig_pa_regions = px.choropleth(
    county_region_map_data,
    geojson = pa_counties_geojson,
    locations = "County",
    featureidkey="properties.county_nam",
    color = "Region",
    scope = "usa",
    title = "Counties by Region"
)

fig_pa_regions.update_geos(
    fitbounds = "locations",
    visible = False
)

fig_pa_regions.update_layout(
    font=dict(
        family = "Inter, Arial, sans-serif",
        size = 12,
        color ="#0072bc"
    )
)

region_totals_map = region_totals.copy()
region_totals_map["Region"] = (
    region_totals_map["Region"]
    .astype(str)
    .str.strip()
)

region_map_plot_data = county_region_map_data.merge(
    region_totals_map,
    on="Region",
    how = "left"
)

fig_pa_region_totals = px.choropleth(
    region_map_plot_data,
    geojson=pa_counties_geojson,
    locations="County",
    featureidkey="properties.county_nam",
    color="Region",
    hover_data=["Region", "Total Backlogged Permits"],
    scope="usa",
    title="Total Backlogged Permits by Region Across Pennsylvania",
    color_continuous_scale="Blues"
)

fig_pa_region_totals.update_traces(
    hovertemplate="<b>%{customdata[0]}</b><br>Total Backlogged Permits: %{customdata[1]}<extra></extra>"
)

fig_pa_region_totals.update_geos(
    fitbounds="locations",
    visible=False
)

fig_pa_region_totals.update_layout(
    font=dict(
        family="Inter, Arial, sans-serif",
        size=12,
        color="#0072bc"
    )
)





# #testing 
# print(county_region_map_data["County"].unique()[:10])
# print(pa_counties_geojson["features"][0]["properties"])



#turn code into a Dash App
app = Dash(__name__)

app.layout = html.Div([

    html.H1("Permit Backlog Dashboard"),

    html.H2("Original Permit Data"),
    dag.AgGrid(
        rowData=df.to_dict("records"),
        columnDefs=[{"field": i} for i in df.columns],
        style={"height": 300}
    ),

    html.H2("Regional Backlog Summary"),
    dag.AgGrid(
        rowData=regional_backlog_display.to_dict("records"),
        columnDefs=[{"field": i} for i in regional_backlog_display.columns],
        style={"height": 250}
    ),


    dcc.Graph(figure=fig),
    dcc.Graph(figure = fig_heatmap),
    dcc.Graph(figure = fig_ranked),
    dcc.Graph(figure = fig_year_bar),
    dcc.Graph(figure = fig_facet),
    

    html.H2("Backlogged Permits by County and Year"),

    # dcc.Dropdown(
    #     id="year-dropdown",
    #     options=[{"label": str(year), "value": year} for year in available_years],
    #     value=available_years[0],
    #     clearable=False,
    #     style={"width": "300px", "marginBottom": "20px"}
    # ),

    # dcc.Graph(id="county-year-graph"),

     html.H2("Backlogged Permits by County and Year (Slider)"),

    dcc.Slider(
    id="year-slider",
    min=min(available_years),
    max=max(available_years),
    step=None,
    marks={year: str(year) for year in available_years},
    value=available_years[0]
    ),
    dcc.Graph(id="county-year-graph"),

    html.H2("Pennsylvania Counties by Region"),
    dcc.Graph(figure=fig_pa_regions),

    html.H2("Pennsylvania Map of Total Backlogged Permits by Region"),
    dcc.Graph(figure=fig_pa_region_totals),


])

# @callback(
#     Output("county-year-graph", "figure"),
#     Input("year-dropdown", "value")
# )

@callback(
    Output("county-year-graph", "figure"),
    Input("year-slider", "value")
)
def updateCountyYearGraph(selectedYear):
    county_counts = county_backlog_pivot.loc[selectedYear].sort_values(ascending=False)

    figCountyYear = px.bar(
        x=county_counts.index,
        y=county_counts.values,
        title=f"Backlogged Permits by County in {selectedYear}",
        labels={"x": "County", "y": "Number of Backlogged Permits"},
        template="simple_white"
    )

    figCountyYear.update_layout(
        font=dict(
            family="Inter, Arial, sans-serif",
            size=12,
            color="#0072bc"
        ),
        xaxis_tickangle=-45
    )

    return figCountyYear

app.run(debug=True)


