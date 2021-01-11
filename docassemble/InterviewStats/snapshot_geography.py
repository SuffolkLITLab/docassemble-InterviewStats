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

from docassemble.base.util import log

import pandas as pd
import numpy as np
import geopandas as gpd
import operator
import timeit

import sys
import cenpy

__all__ = ['get_filters_from_strings', 'make_usage_map', 'write_standalone_usage_map', 'get_embedable_usage_map']

def get_filters_from_strings(filters):
  """
  Make binary operator functions from the given string.
  'eq' -> '=='
  'ne' -> '!='
  'lt' -> '<'
  'gt' -> '>'
  'any' -> always true
  For example:
  .. code-block:: python
  
     str_filters = [('state', 'eq', 'MA'), ('date', 'lt', datetime.date(2020, 3, 12)]
     filters = get_filters_from_strings(str_filters)
     # middle element in filters will now be binary operator function
     x = make_usage_map(df, col_name, filters)
  """
  filt_map = {'eq': operator.eq, 
              'ne': operator.ne, 
              'lt': operator.lt,
              'gt': operator.gt,
              'le': operator.le,
              'ge': operator.ge,
              'any': lambda x, y: operator.and_(x, np.full(x.shape, True))
             }
  return [(filt[0], filt_map[filt[1]], filt[2]) for filt in filters] 


def make_bokeh_map(geosource, geo_loc_counts, col_name='zip'):
  zoom_tool = WheelZoomTool(zoom_on_axis=False)
  tools = [PanTool(),zoom_tool,SaveTool()]
  TOOLTIPS = [(col_name, '@{}'.format(col_name)), 
              ('Number of users', '@{}'.format(col_name + '_counts') + '{0}')]
  map_plot = figure(title='Submissions by ' + col_name, 
                    x_axis_type='mercator', y_axis_type='mercator', 
                    tooltips=TOOLTIPS, tools=tools)
  map_plot.sizing_mode = 'stretch_width'
  map_plot.toolbar.active_scroll = zoom_tool

  # https://docs.bokeh.org/en/latest/docs/reference/tile_providers.html#bokeh-tile-providers
  map_plot.add_tile(get_provider(Vendors.CARTODBPOSITRON))

  # Settled on brewer for colors: https://colorbrewer2.org
  # Was considering `colorcet`, but https://arxiv.org/pdf/1509.03700v1.pdf says stick with brewer
  palette = list(reversed(brewer['YlGnBu'][5])) # Gets yellow as low and blue as high
  max_val = max(geo_loc_counts[col_name + '_counts'])
  color_mapper = LinearColorMapper(palette = palette, low = 0, high = max_val)
  map_plot.patches('xs', 'ys', source = geosource, 
                   fill_color = {'field': col_name + '_counts', 'transform': color_mapper},
                   line_color='black', line_width=0.5, fill_alpha=0.5)
  color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8, height =20,
                       border_line_color=None, location=(0, 0),
                       orientation = 'horizontal')
  map_plot.add_layout(color_bar, 'below')
  return map_plot
  

def make_bokeh_date_histogram(date_series):
  # Make a plot that handles making a histogram of submission times
  ridge_plots = figure(title='When did users submit?', x_axis_label='Date', y_axis_label='Count', x_axis_type='datetime', toolbar_location=None)
  ridge_plots.sizing_mode = 'stretch_width'
  ridge_plots.toolbar.active_drag = None
  ridge_plots.toolbar.active_scroll= None

  hist, edges = np.histogram(date_series, density=False, bins = 50)
  hist_df = pd.DataFrame({'amount': hist, 'left': pd.to_datetime(edges[:-1], unit='s'), 
                          'right': pd.to_datetime(edges[1:], unit='s')})
  fmt_str = "%b %d, %y, %r"
  hist_df['interval'] = ["{} to {}".format(left.strftime(fmt_str), right.strftime(fmt_str)) \
                         for left, right in zip(hist_df["left"], hist_df["right"])]
  ridge_source = ColumnDataSource(hist_df)
  ridge_plots.quad(top='amount', bottom=0, left='left', right='right', fill_color='orange',
                   line_color='black', alpha=0.8, source=ridge_source)
  hover = HoverTool(tooltips = [('Interval', '@interval'), ('Count', '@amount')])
  ridge_plots.add_tools(hover)
  return ridge_plots


def make_bokeh_table(geosource, col_name='zip'):
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
  return data_table


all_zip_shapes = gpd.GeoDataFrame()

  
def make_usage_map(loc_df, geo_col='zip', time_col='modtime', filters=[]):
  """
  Returns a bokeh layout, with a choropleth map of locations we've received
 Expects the dataframe to contain rows with a `geo_col` and `time_col` columns
     to_filters: should be an iterable, each element containing:
        * the name of the column to filter on
        * n operator to preform
        * the name of the value to compare to
  """
  global all_zip_shapes
  outer_start = timeit.time.time()
  to_rm = loc_df[geo_col].str.len() == 0
  loc_df = loc_df.drop(to_rm.index[to_rm])
  for it_filter in filters:
    to_rm = ~it_filter[1](loc_df[it_filter[0]], it_filter[2])
    loc_df = loc_df.drop(to_rm.index[to_rm])
  loc_df[geo_col + '_counts'] = 1
  loc_df[time_col] = pd.to_datetime(loc_df[time_col])

  agg_df = loc_df.groupby(geo_col).agg({geo_col + '_counts': 'sum',
                                        'state': 'first',
                                        'modtime': 'max'}).reset_index(level=0)
  agg_df[geo_col + '_percent'] = agg_df[geo_col + '_counts'] / agg_df[geo_col + '_counts'].sum()
  if geo_col.lower() == 'zip':
    agg_zip_codes = agg_df['zip']
    if all_zip_shapes.empty:
      need_to_grab = list(agg_zip_codes)
    else:
      need_to_grab = list(agg_zip_codes[~agg_zip_codes.isin(all_zip_shapes.BASENAME)])
    if len(need_to_grab):
      start = timeit.time.time()
      api_conn = cenpy.remote.APIConnection('DECENNIALSF12010') # short code for census product
      # other map services are at `cenpy.tiger.available()` (should match above)
      api_conn.set_mapservice('tigerWMS_Census2010') 
      full_where = ' or '.join(['ZCTA5={}'.format(x) for x in need_to_grab])
      # Layer 8 should be the ZIP Code Tabulation Areas
      new_zip_shapes = api_conn.mapservice.query(layer=8, where=full_where)
      all_zip_shapes = all_zip_shapes.append(new_zip_shapes)
      end = timeit.time.time()
      log('Grabbed {} zips in {} seconds'.format(len(new_zip_shapes), end - start))
    geo_loc_counts = all_zip_shapes.merge(agg_df, how='right',
                                  left_on='BASENAME', right_on='zip').drop(columns='modtime')
    geo_loc_counts = geo_loc_counts.to_crs('EPSG:3857') # required for tile mapping
  else:
    # If not doing zip codes, you can use the State code to filter things down.
    # fips = cenpy.explorer.fips_table('STATE').set_index('State Abbreviation').loc['MA']['FIPS Code']
    print('ERROR: locations besides zips not supported right now')
    return None
  outer_end = timeit.time.time()
  log('Processed zips in {} seconds'.format(outer_end - outer_start))

  start = timeit.time.time()
  geosource = GeoJSONDataSource(geojson=geo_loc_counts.to_json())
  map_plot = make_bokeh_map(geosource, geo_loc_counts, geo_col) 
  ridge_plots = make_bokeh_date_histogram([x.timestamp() for x in loc_df[time_col]])
  data_table = make_bokeh_table(geosource, geo_col)
  end = timeit.time.time()
  log('Made plots in {} seconds'.format(end - start))
  return column(map_plot, ridge_plots, data_table)


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
