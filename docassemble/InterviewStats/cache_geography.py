import cenpy
import requests
import geopandas as gpd
from functools import reduce
import numpy as np
import os
from pathlib import Path

try:
    from docassemble.base.util import log
except:
    log = print


def download_file(url: str, local_file: str) -> str:
    """
    Download a file from an arbitrary URL to a local file
    """
    # https://stackoverflow.com/a/16696317
    log('Downloading {} to {}'.format(url, local_file))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with local_file.open(mode='wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_file


def get_fips_code(state_abbrev: str) -> str:
    """
    Gets the FIPS (Federal Information Processing Standards) code for a state
    abbreviation, like 'MA'.
    """
    if state_abbrev.lower() == 'us':
        return 'us'
    states = cenpy.explorer.fips_table('STATE')
    return states[states['State Abbreviation'] == state_abbrev.upper()].iat[0, 1]


base_url = 'https://www2.census.gov/geo/tiger/GENZ2019/shp/'


def get_boundary_file(state_abbrev: str, layer_type: str, resolution: str='500k') -> str:
    return 'cb_2019_{}_{}_{}.zip'.format(
        get_fips_code(state_abbrev), layer_type, resolution)


def saved_dir() -> Path:
    cdir = Path(__file__).resolve().parent
    return cdir.joinpath('data/sources')


def download_shapes(state_abbrev: str, layer_type: str, resolution: str='500k') -> bool:
    """
    See https://www2.census.gov/geo/tiger/GENZ2019/2019_file_name_def.pdf?#
    for layer type (entity name)
    """
    base_name = get_boundary_file(state_abbrev, layer_type, resolution)
    to_save_dir = saved_dir()
    if not to_save_dir.exists():
        to_save_dir.mkdir(parents=True, exist_ok=True)
    download_file(base_url + base_name, to_save_dir.joinpath(base_name))
    return True


def get_zips() -> gpd.GeoDataFrame:
    full_file_path = saved_dir().joinpath(get_boundary_file('us', 'zcta510'))
    if not full_file_path.exists():
        log("{} doesn't exist, downloading".format(full_file_path))
        download_shapes('us', 'zcta510')
    # TODO(brycew): consider a bounding box: it's 2x as fast with one, but
    # trying to read bounding boxes from a different shp file is slower
    return gpd.read_file('zip://' + str(full_file_path))


def get_tracts(state_abbrevs):
    # TODO(brycew): finish
    all_state_path = saved_dir().joinpath(get_boundary_file('us', 'state', '20m'))
    # if not Path(all_state_path).exists():
    #  download_shapes('us', 'state')
    full_file_path = saved_dir().joinpath(get_boundary_file('us', 'tract'))
    if not full_file_path.exists():
        download_shapes('us', 'tract')
    #state_shapes = gpd.read_file('zip://' + all_state_path)
    # bounds = tuple(reduce(lambda l1, l2: np.minimum(l1, l2),
    #                      state_shapes['geometry'].bounds[['minx', 'miny']].values)) + \
    #         tuple(reduce(lambda l1, l2: np.maximum(l1, l2),
    #                      state_shapes['geometry'].bounds[['maxx', 'maxy']].values))
    return None
