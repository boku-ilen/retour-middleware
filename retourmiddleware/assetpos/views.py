import json
import os.path

from django.http import JsonResponse
# from osgeo import gdal
from osgeo import ogr

from .util import *
# from .shp_reader import *
from .shp_to_json import get_trees


# Create your views here.
def index(request):
    if 'filename' not in request.GET:
        return JsonResponse({"Error": "no filename specified"})
    # get parameters
    filename = request.GET.get('filename')
    tree_multiplier = float(request.GET.get('tree_multiplier') if 'tree_multiplier' in request.GET else 0.5)
    place_border = str_to_bool(request.GET.get('place_border')) if 'place_border' in request.GET else True
    place_area = str_to_bool(request.GET.get('place_area')) if 'place_area' in request.GET else True
    area_percentage = float(request.GET.get('area_percentage') if 'area_percentage' in request.GET else 0.5)
    recalculate = str_to_bool(request.GET.get('recalc')) if 'recalc' in request.GET else False
    # save generator relevant parameters in dictionary
    modifiers = dict(
        tree_multiplier=tree_multiplier,
        place_border=place_border,
        place_area=place_area,
        area_percentage=area_percentage
    )

    # generate filenames
    BASE = os.path.dirname(os.path.abspath(__file__))
    gen_file_path = os.path.join(BASE, "generatedFiles", filename + "({}~{}~{}~{}).json".format(
        str(tree_multiplier).replace('.', '_'),
        place_border,
        place_area,
        str(area_percentage).replace('.', '_')
    ))
    file_path = os.path.join(BASE, "inputFiles", filename + ".shp")

    if os.path.isfile(gen_file_path) and not recalculate:
        print("opening ", gen_file_path)

        with open(gen_file_path) as f:
            data = json.load(f)
        return JsonResponse(data)
    elif os.path.isfile(file_path):
        print("opening %s" % file_path)

        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            return JsonResponse({"Error": "driver not available ESRI Shapefile"})

        data_set = driver.Open(file_path, 0)

        if data_set is None:
            return JsonResponse({"Error": "could not open " + file_path})
        else:
            print("opened %s" % file_path)
            data = get_trees(data_set, modifiers)

            print("saving data to file")
            with open(gen_file_path, 'w') as outfile:
                json.dump(data, outfile)

            print("returning json")
            # return JsonResponse(data, json_dumps_params={'indent': 2})
            return JsonResponse(data)
    else:
        return JsonResponse({"Error": "file %s.shp does not exist" % filename})
