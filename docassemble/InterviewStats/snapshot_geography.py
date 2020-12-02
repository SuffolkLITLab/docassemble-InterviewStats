from bokeh.plotting import figure, show, output_file
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, WheelZoomTool, Dropdown,\
                         Paragraph, DataTable, ColumnDataSource, TableColumn, LinearScale
from bokeh.tile_providers import STAMEN_TERRAIN, get_provider
from bokeh.resources import CDN
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column
from bokeh.embed import file_html
from shapely import wkt

import pandas as pd
import numpy as np
import geopandas as gpd

import sys

import pgeocode
from uszipcode import SearchEngine

def make_heatmap(loc_df, col_name='zip'):
  """Returns a bokeh layout, with a choropleth map of locations we've received
     Expects the dataframe to contain rows with a `col_name` column
  """
  to_rm = loc_df[col_name].str.len() == 0
  loc_df = loc_df.drop(to_rm.index[to_rm])
  loc_df[col_name + '_counts'] = 1
  loc_df = loc_df.groupby(col_name).sum().reset_index(level=0)
  loc_df[col_name + '_percent'] = loc_df[col_name + '_counts'] / loc_df[col_name + '_counts'].sum()
  if col_name.lower() == 'zip':

    nomi = pgeocode.Nominatim('us') # TODO(brycew): US assumption
    loc_df['geometry'] = loc_df[col_name].apply(
      lambda x: wkt.loads('POINT ({a.longitude} {a.latitude})'.format(a=nomi.query_postal_code(str(x))))
    )
    geo_loc_counts = gpd.GeoDataFrame(loc_df, geometry='geometry')
    geo_loc_counts.crs = 'EPSG:4326'
    geo_loc_counts = geo_loc_counts.to_crs('EPSG:3857') # required for tile mapping
    # How big should the dots be? Have the largest be 1 mile?
  else:
    print('ERROR: locations besides zips not supported right now')
    return None
  
  geo_loc_counts[col_name +'_sizes'] = np.interp(geo_loc_counts[col_name + '_counts'], (1, max(loc_df[col_name + '_counts'])), (10, 30), left=0)
  print(loc_df)
  print(geo_loc_counts)

  geosource = GeoJSONDataSource(geojson=geo_loc_counts.to_json())
  print(geosource)

  # Just a normal map
  map_plot = figure(title=col_name+'_heatmap')
  map_plot.sizing_mode = 'stretch_width'
  map_plot.toolbar.active_scroll = map_plot.select_one(WheelZoomTool)

  # https://docs.bokeh.org/en/latest/docs/user_guide/geo.html?highlight=geo
  # https://docs.bokeh.org/en/latest/docs/reference/tile_providers.html#bokeh-tile-providers
  tile_provider = get_provider(STAMEN_TERRAIN)
  map_plot.add_tile(tile_provider)

  map_plot.circle(x='x', y='y', size=col_name+'_sizes', color='red', source=geosource)

  # Make a table of the numerical values that we can sort by
  dt_columns = [
      TableColumn(field=col_name, title='title'),
      TableColumn(field=col_name + '_percent',
                  title='percent ' + col_name),
      TableColumn(field=col_name + '_counts', title='count ' + col_name)
  ]
  data_table = DataTable(source=geosource, columns=dt_columns)
  data_table.selectable = False
  data_table.editable = False
  data_table.scroll_to_selection = True
  data_table.reorderable = True
  data_table.sortable = True

  layout = row(map_plot, data_table)
  return layout
  #TODO(brycew): continue here, make the bokeh map, figure out how to display the html in-page?
  # Alternatives: d3 to be fancier

def write_heatmap_file(loc_df, output_file):
  layout = make_heatmap(loc_df, 'zip')
  html = file_html(layout, CDN, 'All Data')
  with open('{}'.format(output_file), 'w') as f:
    f.write(html)

def main(argv):
  if len(argv) > 3:
    print('Need <input csv> <output_html>')
  loc_df = pd.read_csv(argv[1], dtype='str')
  write_heatmap_file(loc_df, argv[2])

if __name__ == '__main__':
  main(sys.argv)