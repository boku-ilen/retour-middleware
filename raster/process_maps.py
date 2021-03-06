import logging
import os
from urllib import request
from pathlib import Path
from urllib.error import HTTPError

import webmercator
from django.conf import settings

from landscapelab import utils
from location.models import Scenario
from raster import views

TILE_URL_FORMAT = "https://{}.tile.opentopomap.org/{}/{}/{}.png"
DEFAULT_LAYER = "opentopomap"
DEFAULT_ZOOM_FROM = 5
DEFAULT_ZOOM_TO = 22

# the format and location of the opentopomap raster pictures
TOPO_FILE = "/raster/{}/{}/{}/{}.png"


logger = logging.getLogger(__name__)


# method to fetch a complete pyramid within a given bounding box
def fetch_tiles(scenario_id, tile_url=TILE_URL_FORMAT, layer=DEFAULT_LAYER,
                zoom_from=DEFAULT_ZOOM_FROM, zoom_to=DEFAULT_ZOOM_TO):

    logger.info("fetch layer {} from {} (z: {} to {})".format(layer, tile_url, zoom_from, zoom_to))

    # fetch possible extent from scenario
    scenario = Scenario.objects.get(id=scenario_id)
    bounding_box = scenario.bounding_polygon.envelope
    logger.debug(bounding_box)

    min_x, min_y = bounding_box.centroid
    max_x, max_y = min_x, min_y
    for x, y in bounding_box.coords[0]:  # first of multiple geometries hold the bb
        if x < min_x:
            min_x = x
        if x > max_x:
            max_x = x
        if y < min_y:
            min_y = y
        if y > max_y:
            max_y = y

    # get all tiles in the available extent and zoomlevel
    for zoom in range(zoom_from, zoom_to):
        p_from = webmercator.Point(meter_x=min_x, meter_y=min_y, zoom_level=zoom)
        p_to = webmercator.Point(meter_x=max_x, meter_y=max_y, zoom_level=zoom)

        logger.info("getting all tiles with z {} for ({}, {}), ({}, {})".format(zoom, p_from.tile_x, p_from.tile_y,
                                                                                p_to.tile_x, p_to.tile_y))
        for y in range(p_to.tile_y, p_from.tile_y+1):
            for x in range(p_from.tile_x, p_to.tile_x+1):
                fetch_tile(tile_url, layer, x, y, zoom)


# this fetches a single tile and puts it into our source directory
def fetch_tile(tile_url, layer, x, y, zoom):

    file = utils.get_full_texture_path(TOPO_FILE.format(layer, zoom, x, y))

    if not Path(file).is_file():

        try:
            # create necessary subdirectories
            os.makedirs(Path(file).parent)
        except FileExistsError:
            pass  # skip if all paths are already there

        # make the request for the image and stores the raw answer into the file
        logger.debug("getting tile {} {}/{}-{}".format(layer, zoom, x, y))
        request_url = tile_url.format("b", zoom, x, y)
        try:
            request.urlretrieve(request_url, file)
        except HTTPError:
            logger.warning("Could not fetch {}".format(request_url))

    else:
        logger.debug("skipped tile {} {}/{}-{}".format(layer, zoom, y, x))


# get the filename based on tiles with the given coordinates
# and start fetching the map if it is still missing
# FIXME: propably to be deleted - old code?
def get_map_from_coords(tile_x: int, tile_y: int, zoom: int):

    filename = views.MAP_BASE.format(DEFAULT_LAYER, zoom, tile_x, tile_y)
    if not os.path.isfile(filename):
        if settings.DEBUG:
            fetch_tile(TILE_URL_FORMAT, DEFAULT_LAYER, tile_x, tile_y, zoom)
        else:
            filename = "None"  # TODO: we could try celery to fetch with delay

    return filename
