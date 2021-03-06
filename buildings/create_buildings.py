import os, sys

print("Start create_buildings.py")

# FIXME: On Linux, I need to make several changes to the Python path here. This is
#  because we need both the Blender Python environment and the usual environment
#  which the server runs in.
#  The order of many of these statements (including 'import's) seems to be important
#  as well.
#  How can we generalize this?

# print("Fixing up the path")
#
# sys.path.remove('/usr/lib/python37.zip')
# sys.path.remove('/usr/lib/python3.7')
# sys.path.remove('/usr/lib/python3.7/lib-dynload')
# sys.path.remove('/usr/lib/python3/dist-packages')
#
# os.environ['MKL_THREADING_LAYER'] = 'GNU'
#
# sys.path.append('/home/karl/anaconda3/envs/boku/lib/python37.zip')
# sys.path.append('/home/karl/anaconda3/envs/boku/lib/python3.7')
# sys.path.append('/home/karl/anaconda3/envs/boku/lib/python3.7/lib-dynload')
# sys.path.append('/home/karl/anaconda3/envs/boku/lib/python3.7/site-packages')

print("Importing other libraries")
import numpy as np
import psycopg2
import bpy, bmesh
from enum import Enum
from math import *
from mathutils import Vector, Matrix

# FIXME: Is there a way to use Django and our landscapelab project here? (This script
#  is run as a subprocess!) Do we need to do more pythonpath trickery?
# import django
# from landscapelab.settings.local_settings import GDAL_LIBRARY_PATH
# from buildings.models import BuildingLayout

C = bpy.context
D = bpy.data

ASSET_TABLE_NAME = "assetpos_asset"
ASSET_POSITIONS_TABLE_NAME = "assetpos_assetpositions"
BUILDING_FOOTPRINT_TABLE_NAME = "buildings_buildingfootprint"

BUILDING_TEXTURE_FOLDER = 'facade'
BASEMENT_TEXTURE_FOLDER = 'basement'
ROOF_TEXTURE_FOLDER = 'roof'

BASEMENT_SIZE = 3
FLAT_ROOF_THRESHOLD = 2800

dir = os.path.dirname(D.filepath)
if dir not in sys.path:
    sys.path.append(dir)

# TODO: If we manage to import our landscapelab environment, we don't need this
#  manual db connection
db = {
    'NAME': 'retour-dev',
    'USER': 'retour',
    'PASSWORD': 'retour',
    'HOST': '141.244.151.130',
    'PORT': '5432'
}

print("Setting up directories")

# TODO: These will change - allow this to be set via script argument?
SERVER_WD= os.path.join('C:\\', 'landscapelab-dev', 'landscapelab-server', 'buildings')
TEXTURE_DIRECTORY = os.path.join(SERVER_WD, 'textures')
if not os.path.exists(TEXTURE_DIRECTORY):
    os.makedirs(TEXTURE_DIRECTORY)

# TODO: Get the path from the server; move it to the resources
OUTPUT_DIRECTORY = os.path.join(SERVER_WD, 'out')
if not os.path.exists(str(OUTPUT_DIRECTORY)):
    os.makedirs(OUTPUT_DIRECTORY)

print("Setup done")


class RoofType(Enum):
    FLAT = 0
    SIMPLE = 1
    HIP_ROOF = 2
    GABLE_ROOF = 3


# takes name footprint-vertices, building-height and texture name (optional)
# to create a new building and export it
def create_building(name, vertices, height, textures):

    # clear the scene and add z component to the received 2d vertices
    clear_scene()
    vertices = np.pad(np.asarray(vertices), (0, 1), 'constant')[:-1]

    # crate the base of the building and the roof
    basement = create_base_building_mesh(name, vertices, -BASEMENT_SIZE, textures, BASEMENT_TEXTURE_FOLDER)
    building = create_base_building_mesh(name, vertices, height, textures)
    roof = create_roof(name, vertices, height, textures)

    delete_bottom(building)
    delete_bottom(building, top_instead=True)
    delete_bottom(basement, top_instead=True)

    # export the scene to a gltf 2.0 file
    print('Output dir: {}'.format(OUTPUT_DIRECTORY))
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUTPUT_DIRECTORY, name))


# clears unwanted elements from the default scene
# and the leftovers from previous building exports
def clear_scene():

    for m in D.meshes:
        D.meshes.remove(m)
    for o in D.objects:
        D.objects.remove(o)
    for l in D.lights:
        D.lights.remove(l)
    for i in D.images:
        D.images.remove(i)
    for m in D.materials:
        D.materials.remove(m)
    for t in D.textures:
        D.textures.remove(t)
    for c in D.cameras:
        D.cameras.remove(c)


# creates a footprint and extrudes it upwards to get a cylindrical base of the building
def create_base_building_mesh(name, vertices, height, textures, key=BUILDING_TEXTURE_FOLDER):

    # create the building footprint
    [building, mesh, bm, footprint] = create_footprint(name, vertices)

    # extrude face to get roof
    roof = bmesh.ops.extrude_face_region(bm, geom=[footprint])

    # move the roof upwards, recalculate the face normals and finish edit
    bmesh.ops.translate(bm, vec=Vector((0, 0, height)), verts=[v for v in roof["geom"] if isinstance(v, bmesh.types.BMVert)]) # move roof up
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    finish_edit(bm, mesh)

    # add textures if possible
    if key in textures:
        # create and add material
        building_mat = create_material(textures[key])
        building.data.materials.append(building_mat)

        # set wall UVs
        set_wall_uvs(building)

    return building


# creates a decently looking roof on any building
# uses neat_roof() on buildings with 4 vertex footprint
def create_roof(name, vertices, height, textures):

    # create base face
    [roof, mesh, bm, footprint] = create_footprint(name+"_roof", vertices)
    bbox = get_bounding_box([v.co for v in footprint.verts])

    # select roof type and height
    roof_type, roof_height = select_roof(footprint, bm, height)

    # if footprint has 4 vertices use neat_roof()
    # otherwise use inset operator and push resulting face up
    if roof_type == RoofType.SIMPLE:
        neat_roof(footprint, bm, roof_height, mesh, height)
        delete_bottom(roof)

    elif roof_type == RoofType.FLAT:
        flat_roof(footprint, bm, roof_height, mesh, height)

    else:
        hip_roof(roof, footprint, bm, mesh, roof_height, height, bbox, name, vertices)

    # add textures if possible
    if ROOF_TEXTURE_FOLDER in textures:
        # create and add material
        roof_mat = create_material(textures[ROOF_TEXTURE_FOLDER])
        roof.data.materials.append(roof_mat)

        # set wall UVs
        # NOTE: for buildings with 4 vertices this will work perfectly
        # for other buildings this will distort the UVs
        # for pattern textures this is hardly noticable
        # but if for example a window is on the image, it will be noticably distorted
        # TODO create suitable function for buildings with more than 4 vertices
        set_wall_uvs(roof)

    return roof


# creates a new object and adds the footprint of a building as a face
# returns all necessary elements to continue editing the object
# NOTE: when caller is finished editing the footprint they should call finish_edit(bm, mesh)
def create_footprint(name, vertices):

    # instantiate mesh
    mesh = D.meshes.new('mesh')
    generated_object = D.objects.new(name, mesh)
    C.scene.collection.objects.link(generated_object)

    # set footprint active and enable edit mode
    C.view_layer.objects.active = generated_object
    bpy.ops.object.mode_set(mode='EDIT')

    # setup mesh and bm
    mesh = generated_object.data
    bm = bmesh.new()

    # add vertices to create footprint
    vert = []
    for v in vertices:
        vert.append(bm.verts.new(v))

    footprint = bm.faces.new(vert)

    return [generated_object, mesh, bm, footprint]


# updates mesh, frees bm and returns to object mode
def finish_edit(bm, mesh):

    bpy.ops.object.mode_set(mode='OBJECT')
    bm.to_mesh(mesh)
    bm.free()


def flat_roof(face, bm, roof_height, mesh, height):

    bmesh.ops.inset_individual(bm, faces=[face], thickness=0)
    bm.faces.ensure_lookup_table()
    top = bm.faces[0]

    bmesh.ops.translate(bm, vec=Vector([0, 0, 2]), verts=[v for v in top.verts])

    bmesh.ops.translate(bm, vec=Vector([0, 0, height]), verts=bm.verts)
    finish_edit(bm, mesh)


# from https://blender.stackexchange.com/questions/14136/trying-to-create-a-script-that-makes-roofs-on-selected-boxes
# only works on buildings with 4 vertex footprint
# sets a neat looking roof on top of the building
def neat_roof(face, bm, roof_height, mesh, building_height):

    if len(face.verts) == 4:
        ret = bmesh.ops.extrude_face_region(bm, geom=[face])
        vertices = [element for element in ret['geom'] if isinstance(element, bmesh.types.BMVert)]
        faces = [element for element in ret['geom'] if isinstance(element, bmesh.types.BMFace)]
        bmesh.ops.translate(bm, vec=face.normal * roof_height, verts=vertices)

        e1, e2, e3, e4 = faces[0].edges
        if (e1.calc_length() + e3.calc_length()) < (e2.calc_length() + e4.calc_length()):
            edges = [e1, e3]
        else:
            edges = [e2, e4]
        bmesh.ops.collapse(bm, edges=edges)

    bmesh.ops.translate(bm, vec=Vector([0, 0, building_height]), verts=bm.verts)
    finish_edit(bm, mesh)


def hip_roof(roof_object, footprint_face, bm, mesh, roof_height, positional_height, bbox, name, vertices):
    footprint_face.select = True
    bmesh.ops.translate(bm, vec=Vector([0, 0, positional_height]), verts=bm.verts)
    finish_edit(bm, mesh)

    bpy.ops.object.mode_set(mode='EDIT')

    # create roof form
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    roof_inset_amount = longest_edge(bm.verts) / 2
    bpy.ops.mesh.insetstraightskeleton(inset_amount=roof_inset_amount, inset_height=-roof_height, region=True, quadrangulate=True)

    # if flawed roof was created abort and create flat roof instead
    if not roof_generated_correctly(roof_object, bbox):
        print('WARNING: failed to create hip roof, resorting to flat roof')
        bpy.ops.mesh.delete(type='VERT')
        [roof_object, mesh, bm, footprint_face] = create_footprint(name + "_roof", vertices)
        flat_roof(footprint_face, bm, roof_height, mesh, positional_height)

    bpy.ops.object.mode_set(mode='OBJECT')
    delete_inner_faces(roof_object)


# selects a roof type and height based on a buildings footprint and height
def select_roof(footprint, bm, height):
    roof_type = RoofType.HIP_ROOF

    area = calc_area(footprint)
    print('area = {}'.format(area))

    # if area is big enough assume flat roof
    if area > FLAT_ROOF_THRESHOLD:
        return RoofType.FLAT, 0.5

    # if only 4 vertices use neat roof
    if len(bm.verts) is 4:
        roof_type = RoofType.SIMPLE

    if area > 200:
        roof_height = height * 0.5 + np.log(area)
    else:
        roof_height = 1

    return roof_type, roof_height


# checks if the roof was generated correctly by checking if all generated vertices lie within the bounding box
# this is necessary because the inset_straight_skeleton operator produces false results where vertices lie far away
# in very rare cases
def roof_generated_correctly(roof, bbox):
    vertices = vert_from_mesh(roof.data)
    x_min, y_min, x_max, y_max = bbox

    for v in vertices:
        if x_min <= v.x <= x_max:
            if y_min <= v.y <= y_max:
                continue
        return False

    return True


# deletes the bottom (or top if specified) face of any mesh (face where avg vertex z coordinate is lowest / highest)
def delete_bottom(obj, top_instead=False):

    comp = lambda a, b: a < b
    if top_instead:
        comp = lambda a, b: a > b

    # switch to edit mode and get bm
    C.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)

    # filter out lowest face
    low_f = [None, None]
    for f in bm.faces:
        h = 0
        for v in f.verts:
            h += v.co.z
        h /= len(f.verts)
        if low_f[1] is None or comp(h, low_f[1]):
            low_f[0] = f
            low_f[1] = h

    # delete lowest face and return to object mode
    bmesh.ops.delete(bm, geom=[low_f[0]], context='FACES')
    bpy.ops.object.mode_set(mode='OBJECT')


# deletes all horizontal faces that were generated within a volume
# (including a horizontal bottom face, excluding a horizontal top face)
# this is necessary since the operator inset straight skeleton sometimes generates such faces
def delete_inner_faces(obj):

    # swap to edit mode and setup inner face array
    C.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    inner_f = []

    # get max z value of object
    max_z = None
    for v in bm.verts:
        if max_z is None or max_z < v.co.z:
            max_z = v.co.z

    # find inner horizontal faces
    for f in bm.faces:
        face_height = None
        for v in f.verts:
            # only continue if height stays constant across all vertices
            if face_height is None or face_height == v.co.z:
                face_height = v.co.z
            else:
                face_height = None
                break

        # add to inner face list if height stayed constant and face is not top face
        if face_height is not None and face_height < max_z:
            inner_f.append(f)

    # delete inner faces and return to object mode
    bmesh.ops.delete(bm, geom=inner_f, context='FACES')
    bpy.ops.object.mode_set(mode='OBJECT')


# sets the uv coordinates for the wall faces of any general cylinder
def set_wall_uvs(object):

    # scene setup
    C.view_layer.objects.active = object
    bpy.ops.object.mode_set(mode='EDIT')

    # mesh setup
    mesh = object.data
    bm = bmesh.from_edit_mesh(mesh)

    # convenience variable
    uv_layer = bm.loops.layers.uv.verify()

    # iterates through all faces of the object
    # and sets the uv-coordinates for all wall faces
    for f in bm.faces:
        if face_is_wall(f):
            mean_z_value = face_mean(f)[2]
            upper, lower = [], []

            # split vertices in upper and lower parts
            for v in f.loops:
                if v.vert.co.z > mean_z_value:
                    upper.append(v)
                else:
                    lower.append(v)

            # decide how often the texture should repeat itself horizontally
            columns = max(float(1), vertex_distance(upper[0].vert, upper[1].vert) // 3)
            rows = max(float(1), min(vertex_distance(lower[0].vert, upper[0].vert), vertex_distance(lower[0].vert, upper[1].vert)) // 3)

            # find vertex below upper[0] and assign UVs accordingly
            if vertex_distance(upper[0].vert, lower[0].vert) < vertex_distance(upper[0].vert, lower[1].vert):
                upper[0][uv_layer].uv = Vector((0, rows))
                lower[0][uv_layer].uv = Vector((0, 0))
                upper[1][uv_layer].uv = Vector((columns, rows))
                lower[1][uv_layer].uv = Vector((columns, 0))
            else:
                upper[0][uv_layer].uv = Vector((0, rows))
                lower[1][uv_layer].uv = Vector((0, 0))
                upper[1][uv_layer].uv = Vector((columns, rows))
                lower[0][uv_layer].uv = Vector((columns, 0))

    # update mesh and return to object mode
    bmesh.update_edit_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')


# creates a new material with defined texture and returns it
def create_material(texture_name: str):

    # create material
    mat = D.materials.new(name=texture_name)
    mat.use_nodes = True

    # create and set texture_image with
    texture_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture_image.image = D.images.load(os.path.join(TEXTURE_DIRECTORY, texture_name))

    # get shader node of material and link texture to it's color property
    diff = mat.node_tree.nodes["Principled BSDF"]
    mat.node_tree.links.new(diff.inputs['Base Color'], texture_image.outputs['Color'])

    return mat


# returns true if the specified face is a wall with 4 vertices
def face_is_wall(f):

    if len(f.loops) is 4:
        mean_z = face_mean(f)[2]

        # determines if a face is a wall by checking
        # if the z distance of the first vertex to the face mean
        if abs(f.loops[0].vert.co.z - mean_z) > 0.1:
            return True

    return False


# calculates the mean point of
def face_mean(f):

    mean = np.zeros(3)
    if len(f.loops) > 0:
        for l in f.loops:
            c = l.vert.co
            mean = np.add(mean, np.array([c.x, c.y, c.z]))
        mean = np.divide(mean, len(f.loops))

    return mean.tolist()


# calculates the euclidean distance between two vertices
def vertex_distance(v1, v2):
    c1 = v1.co
    c2 = v2.co
    return sqrt(pow(c1.x - c2.x, 2) + pow(c1.y - c2.y, 2) + pow(c1.z - c2.z, 2))


# takes the vertices of a polygon in a list, computes the shortest edge and returns it's length
def shortest_edge(vertices):
    min_edge = float("inf")

    # iterates through all the vertices
    # calculates the distance to the next vertex
    # uses % operator in order to loop around and also consider the edge from last to first vertex
    for i in range(len(vertices)):
        d = vertex_distance(vertices[i], vertices[(i + 1) % len(vertices)])
        if d < min_edge:
            min_edge = d

    return d


# takes a list of vertices and finds
# the distance of the closest pair in the list
def shortest_vertex_distance(vertices):
    min_dist = float("inf")

    for i in range(len(vertices) - 1):
        for j in range(i + 1, len(vertices)):
            d = vertex_distance(vertices[i], vertices[j])
            if min_dist > d:
                min_dist = d

    return min_dist


# returns the distance of the longest edge
def longest_edge(vertices):
    max_dist = 0

    for i in range(len(vertices) - 1):
        d = vertex_distance(vertices[i], vertices[(i + 1) % len(vertices)])

        if max_dist < d:
            max_dist = d

    return max_dist


# approximates the building footprint area via bounding box
def calc_area(footprint):
    x_min, y_min, x_max, y_max = get_bounding_box([v.co for v in footprint.verts])

    w = x_max - x_min
    h = y_max - y_min

    return w * h


def get_bounding_box(vertices):
    x_min = y_min = x_max = y_max = None

    for v in vertices:
        if not x_min:
            x_min = x_max = v.x
            y_min = y_max = v.y

        else:
            x_min = min(x_min, v.x)
            x_max = max(x_max, v.x)
            y_min = min(y_min, v.y)
            y_max = max(y_max, v.y)

    print('bounding box data: {} {} {} {}'.format(x_min, y_min, x_max, y_max))
    return x_min, y_min, x_max, y_max


def vert_from_mesh(mesh_data):
    return (v.co for v in mesh_data.vertices)


# scans the texture folder
# creates a dictionary of lists where each subdirectory is a key
# each list contains all jpg image names of the corresponding direcotry
def get_images():

    img_ext = 'jpg'
    images = {}
    dirs = os.listdir(TEXTURE_DIRECTORY)

    # iterate through all directories
    for dir in dirs:
        dir_path = os.path.join(TEXTURE_DIRECTORY, dir)
        if os.path.isdir(dir_path):

            # add directory name as key to images
            images[dir] = []

            # add all files with correct extension to images[dir]
            files = os.listdir(dir_path)
            for file in files:
                if file.endswith(img_ext):
                    images[dir].append(file)

    print("images: {}".format(images))
    print("imagePath: {}".format(TEXTURE_DIRECTORY))
    return images


def main(arguments):

    print("Connecting to db...")

    images = get_images()
    conn = psycopg2.connect(host=db['HOST'], database=db['NAME'], user=db['USER'],
                            password=db['PASSWORD'], port=db['PORT'])
    cur = conn.cursor()

    print("Connected!")

    # goes through each argument
    # fetches the data for specified building
    # creates and exports it
    for a in arguments:

        print("Fetching the next result")

        # get building name and height
        # TODO: Replace with Django code if we can import the landscapelab environment!
        sql_request = 'SELECT n.name, h.height ' \
                      'FROM {ASSET} as n, (SELECT height FROM {BUILDING_FOOTPRINT} WHERE id = {argument_id}) as h ' \
                      'WHERE n.id IN ' \
                      '(SELECT asset_id FROM {ASSET_POSITIONS} WHERE id IN ' \
                      '(SELECT asset_id FROM {BUILDING_FOOTPRINT} WHERE id = {argument_id}));' \
            .format(
            ASSET=ASSET_TABLE_NAME,
            ASSET_POSITIONS=ASSET_POSITIONS_TABLE_NAME,
            BUILDING_FOOTPRINT=BUILDING_FOOTPRINT_TABLE_NAME,
            argument_id=a
        )

        cur.execute(sql_request)

        ret = cur.fetchone()
        name = ret[0]
        height = ret[1]

        # get building vertices
        # TODO: Replace with Django code if we can import the landscapelab environment!
        cur.execute('SELECT ST_x(geom), ST_y(geom) FROM'
                    '(SELECT (St_DumpPoints(vertices)).geom, height FROM {BUILDING_FOOTPRINT} where id = {argument_id}) as foo;'
            .format(
                BUILDING_FOOTPRINT=BUILDING_FOOTPRINT_TABLE_NAME,
                argument_id=a
            )
        )

        vertices = cur.fetchall()

        # delete last vertex since it is duplicate of first
        del vertices[-1]

        # select textures from the image pool
        textures = {}
        for key, value in images.items():
            if len(value) > 0:
                textures[key] = os.path.join(key, value[int(a) % len(value)])

        print("Creating the model")

        # create and export the building
        create_building(name, vertices, height, textures)

    cur.close()
    conn.close()


if __name__ == '__main__':
    arg = sys.argv
    arg = arg[arg.index('--') + 1:]
    main(arg)
