from bokeh.plotting import figure, show, output_file
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, WheelZoomTool, Dropdown,\
                         Paragraph, DataTable, ColumnDataSource, TableColumn, LinearScale, PanTool,\
                         SaveTool, HoverTool
from bokeh.tile_providers import Vendors, get_provider
from bokeh.resources import CDN
from bokeh.palettes import brewer
from bokeh.layouts import widgetbox, row, column
from bokeh.embed import file_html, components
from scipy.stats.kde import gaussian_kde
from shapely import wkt
import colorcet as cc

import pandas as pd
import numpy as np
import geopandas as gpd
import operator

import sys
import cenpy

__all__ = ['make_usage_map', 'write_standalone_usage_map', 'get_embedable_usage_map']

def get_filter_types(col_name):
  #TODO(brycew): is there a better way than hardcoding to columns?
  standard_name = col_name.lower()
  if standard_name == 'zip' or standard_name == 'state':
    return [('equals', operator.eq), 
            ('not equals', operator.ne)]
  elif standard_name == 'modtime':
    return [('less than', operator.lt),
            ('less than or equal to', operator.le),
            ('greater than', operator.gt),
            ('greater than or equal to', operator.ge)]
  else:
    return []

def make_usage_map(loc_df, col_name='zip', filters=[]):
  """Returns a bokeh layout, with a choropleth map of locations we've received
     Expects the dataframe to contain rows with a `col_name` column
     to_filters: should be an iterable, each element containing:
        * [0] is the name of the column to filter on, [1] is an operator to preform, and [2] is the name of the value to compare to
  """
  to_rm = loc_df[col_name].str.len() == 0
  loc_df = loc_df.drop(to_rm.index[to_rm])
  for it_filter in filters:
    to_rm = ~it_filter[1](loc_df[it_filter[0]], it_filter[2])
    loc_df = loc_df.drop(to_rm.index[to_rm])
  loc_df[col_name + '_counts'] = 1
  loc_df['Modtime'] = pd.to_datetime(loc_df['Modtime'])

  by_time = loc_df.set_index('Modtime')
  main_series = [x.timestamp() for x in by_time.index]
  all_series = {}
  for unit in set(by_time[col_name]):
    # Get only the submissions in the current geo unit, and then turn them into timestamps
    all_series[unit] = [x.timestamp() for x in by_time[(by_time[col_name] == unit)].index]

  loc_df = loc_df.groupby(col_name).agg({col_name + '_counts': 'sum',
                                         'state': 'first',
                                         'Modtime': 'max'}).reset_index(level=0)
  loc_df[col_name + '_percent'] = loc_df[col_name + '_counts'] / loc_df[col_name + '_counts'].sum()
  if col_name.lower() == 'zip':
    api_conn = cenpy.remote.APIConnection('DECENNIALSF12010') # short code for census product (TODO(brycew): how to find other short codes?)
    api_conn.set_mapservice('tigerWMS_Census2010') # other map services are at `cenpy.tiger.available()` (should match the census product)
    # Layer 8 should be the ZIP Code Tabulation Areas
    all_zip_codes = loc_df['zip'].to_list()
    full_where = ' or '.join(['ZCTA5={}'.format(x) for x in all_zip_codes])
    all_zip_shapes = api_conn.mapservice.query(layer=8, where=full_where)
    geo_loc_counts = all_zip_shapes.merge(loc_df, left_on='BASENAME', right_on='zip').drop(columns='Modtime')
    geo_loc_counts = geo_loc_counts.to_crs('EPSG:3857') # required for tile mapping
  else:
    # If not doing zip codes, you can use the State code to filter things down.
    # state_fips_code = cenpy.explorer.fips_table('STATE').set_index('State Abbreviation').loc['MA']['FIPS Code']
    print('ERROR: locations besides zips not supported right now')
    return None

  geosource = GeoJSONDataSource(geojson=geo_loc_counts.to_json())

  # Just a normal map
  TOOLTIPS = [(col_name, '@{}'.format(col_name)), ('Number of users', '@{}'.format(col_name + '_counts') + '{0}')]
  zoom_tool = WheelZoomTool(zoom_on_axis=False)
  tools = [PanTool(),zoom_tool,SaveTool()] 
  map_plot = figure(title='Submissions by ' + col_name, x_axis_type='mercator', y_axis_type='mercator', tooltips=TOOLTIPS, tools=tools)
  map_plot.sizing_mode = 'stretch_width'
  map_plot.toolbar.active_scroll = zoom_tool

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

  
  ridge_plots = figure(title='When did users submit?', x_axis_label='Date', y_axis_label='Count', x_axis_type='datetime', toolbar_location=None)
  ridge_plots.sizing_mode = 'stretch_width'
  ridge_plots.toolbar.active_drag = None
  ridge_plots.toolbar.active_scroll= None

  hist, edges = np.histogram(main_series, density=False, bins = 50)
  hist_df = pd.DataFrame({'amount': hist, 'left': pd.to_datetime(edges[:-1], unit='s'), 'right': pd.to_datetime(edges[1:], unit='s')})
  date_fmt_str = "%b %d, %y, %r"
  hist_df['interval'] = ["{} to {}".format(left.strftime(date_fmt_str), right.strftime(date_fmt_str)) for left, right in zip(hist_df["left"], hist_df["right"])]
  ridge_source = ColumnDataSource(hist_df)
  ridge_plots.quad(top='amount', bottom=0, left='left', right='right', fill_color='orange', line_color='black', alpha=0.8, source=ridge_source)
  hover = HoverTool(tooltips = [('Interval', '@interval'), ('Count', '@amount')])
  ridge_plots.add_tools(hover)

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

  layout = column(map_plot, ridge_plots, data_table)
  return layout
  # TODO(brycew): Alternatives: d3 to be fancier

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
  if len(argv) < 3:
    print('Need <input csv> <output_html>')
    return
  loc_df = pd.read_csv(argv[1], dtype='str')
  layout = make_usage_map(loc_df, 'zip', [('state', operator.eq, 'MA')])
  write_standalone_usage_map(layout, argv[2])

if __name__ == '__main__':
  main(sys.argv)
