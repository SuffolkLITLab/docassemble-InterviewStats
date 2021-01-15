import cenpy
import requests
import geopandas as gpd
from functools import reduce
import numpy as np
import os
from pathlib import Path


def download_file(url, local_filename):
  # https://stackoverflow.com/a/16696317
  with requests.get(url, stream=True) as r:
    r.raise_for_status()
    with open(local_filename, 'wb') as f:
      for chunk in r.iter_content(chunk_size=8192):
        f.write(chunk)
  return local_filename


def get_fips_code(state_abbrev):
  if state_abbrev.lower() == 'us':
    return 'us'
  state_table = cenpy.explorer.fips_table('STATE')
  return state_table[state_table['State Abbreviation'] == state_abbrev.upper()].iat[0, 1]


base_url = 'https://www2.census.gov/geo/tiger/GENZ2019/shp/'


def saved_dir():
  cdir = os.path.dirname(os.path.abspath(__file__))
  return os.path.join(cdir, 'data/shapes')


def get_boundary_file(state_abbrev, layer_type, resolution='500k'):
  return 'cb_2019_{}_{}_{}.zip'.format(
    get_fips_code(state_abbrev), layer_type, resolution)


def download_shapes(state_abbrev, layer_type, resolution='500k'):
  """
  See https://www2.census.gov/geo/tiger/GENZ2019/2019_file_name_def.pdf?#
  for layer type (entity name)
  """
  base_name = get_boundary_file(state_abbrev, layer_type, resolution)
  download_file(base_url + base_name, os.path.join(saved_dir(), base_name))
  return True


def get_zips():
  # Download the rough US state shapes: saves time later when loading from file
  full_file_path = os.path.join(saved_dir(), get_boundary_file('us', 'zcta510'))
  if not Path(full_file_path).exists():
      download_shapes('us', 'zcta510')
  # TODO(brycew): consider a bounding box: it's 2x as fast with one, but trying to read and grab
  # bounding boxes from a different shape file is slower
  return gpd.read_file('zip://' + full_file_path)

  def get_tracts(state_abbrevs):
    # TODO(brycew): finish
    all_state_path = os.path.join(saved_dir(), get_boundary_file('us', 'state', '20m'))
    #if not Path(all_state_path).exists():
    #  download_shapes('us', 'state')
    full_file_path = os.path.join(saved_dir(), get_boundary_file('us', 'tract'))
    if not Path(full_file_path).exists():
        download_shapes('us', 'tract')
    #state_shapes = gpd.read_file('zip://' + all_state_path)
    #bounds = tuple(reduce(lambda l1, l2: np.minimum(l1, l2),
    #                      state_shapes['geometry'].bounds[['minx', 'miny']].values)) + \
    #         tuple(reduce(lambda l1, l2: np.maximum(l1, l2),
    #                      state_shapes['geometry'].bounds[['maxx', 'maxy']].values))     
    return None


  



