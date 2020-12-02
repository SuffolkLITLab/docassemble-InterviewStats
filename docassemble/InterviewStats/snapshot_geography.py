from bokeh.plotting import figure, show, output_file
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, WheelZoomTool, Dropdown,\
                         Paragraph, DataTable, ColumnDataSource, TableColumn, LinearScale
from bokeh.tile_providers import Vendors, get_provider
from bokeh.resources import CDN
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column
from bokeh.embed import file_html, components
from shapely import wkt

import pandas as pd
import numpy as np
import geopandas as gpd

import sys
import cenpy

__all__ = ['make_usage_map', 'write_standalone_usage_map']

def make_usage_map(loc_df, col_name='zip'):
  """Returns a bokeh layout, with a choropleth map of locations we've received
     Expects the dataframe to contain rows with a `col_name` column
  """
  to_rm = loc_df[col_name].str.len() == 0
  loc_df = loc_df.drop(to_rm.index[to_rm])
  loc_df[col_name + '_counts'] = 1
  loc_df = loc_df.groupby(col_name).sum().reset_index(level=0)
  loc_df[col_name + '_percent'] = loc_df[col_name + '_counts'] / loc_df[col_name + '_counts'].sum()
  if col_name.lower() == 'zip':
    api_conn = cenpy.remote.APIConnection('DECENNIALSF12010') # short code for census product (TODO(brycew): how to find other short codes?)
    api_conn.set_mapservice('tigerWMS_Census2010') # other map services are at `cenpy.tiger.available()` (should match the census product)
    # Layer 8 should be the ZIP Code Tabulation Areas
    all_zip_codes = loc_df['zip'].to_list()
    full_where = ' or '.join(['ZCTA5={}'.format(x) for x in all_zip_codes])
    print(full_where)
    all_zip_shapes = api_conn.mapservice.query(layer=8, where=full_where)
    geo_loc_counts = all_zip_shapes.merge(loc_df, left_on='BASENAME', right_on='zip')
    geo_loc_counts = geo_loc_counts.to_crs('EPSG:3857') # required for tile mapping
  else:
    # If not doing zip codes, you can use the State code to filter things down.
    # state_fips_code = cenpy.explorer.fips_table('STATE').set_index('State Abbreviation').loc['MA']['FIPS Code']
    print('ERROR: locations besides zips not supported right now')
    return None

  geosource = GeoJSONDataSource(geojson=geo_loc_counts.to_json())

  # Just a normal map
  TOOLTIPS = [('Zip', '@zip'), ('Number of users', '@{name}'.format(name=col_name + '_counts') + '{0.000}')]
  map_plot = figure(title='Usage map over ' + col_name, tooltips=TOOLTIPS)
  map_plot.sizing_mode = 'stretch_width'
  map_plot.toolbar.active_scroll = map_plot.select_one(WheelZoomTool)

  # https://docs.bokeh.org/en/latest/docs/user_guide/geo.html?highlight=geo
  # https://docs.bokeh.org/en/latest/docs/reference/tile_providers.html#bokeh-tile-providers
  map_plot.add_tile(get_provider(Vendors.CARTODBPOSITRON))

  # Settled on brewer for colors: https://colorbrewer2.org
  # Was considering `colorcet`, but https://arxiv.org/pdf/1509.03700v1.pdf suggests to stick with brewer and
  # use colorcet for geophysical exploration or medical images
  palette = list(reversed(brewer['YlGnBu'][5])) # Gets yellow as low and blue as high
  max_val = max(geo_loc_counts[col_name + '_counts'])
  color_mapper = LinearColorMapper(palette = palette, low = 0, high = max_val)
  map_plot.patches('xs', 'ys', source = geosource, fill_color = {'field': col_name + '_counts', 'transform': color_mapper},
                                   line_color='black', line_width=0.5, fill_alpha=0.5)
  color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8, height =20, border_line_color=None, location=(0, 0),
                       orientation = 'horizontal')
  map_plot.add_layout(color_bar, 'below')

  # Make a table of the numerical values that we can sort by
  dt_columns = [
      TableColumn(field=col_name, title=col_name),
      TableColumn(field=col_name + '_percent',
                  title='Percentage of users in ' + col_name),
      TableColumn(field=col_name + '_counts', title='Number of Users in ' + col_name)
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

def get_embedable_usage_map(layout):
  script, div = components(layout)
  # from https://docs.bokeh.org/en/latest/docs/user_guide/embed.html#components
  inline_cdn = """<script src="https://cdn.bokeh.org/bokeh/release/bokeh-2.2.3.min.js"
        crossorigin="anonymous"></script>
<script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-2.2.3.min.js"
        crossorigin="anonymous"></script>
<script src="https://cdn.bokeh.org/bokeh/release/bokeh-tables-2.2.3.min.js"
        crossorigin="anonymous"></script>
        """
  return script, div, inline_cdn

def write_standalone_usage_map(layout, output_file):
  html = file_html(layout, CDN, 'All Data')
  with open('{}'.format(output_file), 'w') as f:
    f.write(html)

def main(argv):
  if len(argv) > 3:
    print('Need <input csv> <output_html>')
  loc_df = pd.read_csv(argv[1], dtype='str')
  layout = make_usage_map(loc_df, 'zip')
  write_standalone_usage_map(layout, argv[2])

if __name__ == '__main__':
  main(sys.argv)
