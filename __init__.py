# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Inspired by official Blender add-ons: object_print3d_utils and io_mesh_stl

# <pep8 compliant>

bl_info = {
    "name": "VTK Surface Mesh Import-Export",
    "author": "Tuomo Keskitalo",
    "version": (0, 2, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export > VTK",
    "description": "Import-Export of VTK (Visualization ToolKit) polydata (surface mesh) files",
    "wiki_url": "https://github.com/tkeskita/io_mesh_vtk",
    "support": 'COMMUNITY',
    "category": "Import-Export",
}


if "bpy" in locals():
    import importlib
else:
    import math
    import bpy
    from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
    )
    from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        axis_conversion,
    )
    #from . import (
    #    ui,
    #)

# Set up logging of messages using Python logging
# Logging is nicely explained in:
# https://code.blender.org/2016/05/logging-from-python-code-in-blender/
# To see debug messages, configure logging in file
# $HOME/.config/blender/{version}/scripts/startup/setup_logging.py
# add there something like:
# import logging
# logging.basicConfig(format='%(funcName)s: %(message)s', level=logging.DEBUG)
import logging
l = logging.getLogger(__name__)

@orientation_helper(axis_forward='Y', axis_up='Z')
class ExportVTK(bpy.types.Operator, ExportHelper):
    '''Save active object mesh and vertex data to VTK file'''
    bl_idname = "export_mesh.vtk"
    bl_label = "Export VTK Polydata"

    filename_ext = ".vtk"
    filter_glob: StringProperty(default="*.vtk", options={'HIDDEN'})

    def execute(self, context):
        import itertools
        from mathutils import Matrix

        ob = context.active_object
        ascii_write_vtk(self.filepath, ob.data)
        return {'FINISHED'}


class ImportVTK(bpy.types.Operator, ImportHelper):
    '''Import VTK file as mesh object'''
    bl_idname = "import_mesh.vtk"
    bl_label = "Import VTK Polydata"

    filename_ext = ".vtk"
    filter_glob: StringProperty(default="*.vtk", options={'HIDDEN'})

    def execute(self, context):
        ascii_read_vtk(self)
        return {'FINISHED'}


def menu_import(self, context):
    self.layout.operator(ImportVTK.bl_idname, text="VTK Polydata (.vtk)")

def menu_export(self, context):
    self.layout.operator(ExportVTK.bl_idname, text="VTK Polydata (.vtk)")

classes = (
    ExportVTK,
    ImportVTK,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_export.remove(menu_export)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


if __name__ == "__main__":
    register()



def ascii_write_vtk(filepath, obdata):
    '''ASCII VTK Polydata writer'''
    
    with open(filepath, 'w') as data:
        fw = data.write
        fw(vtk_header(obdata.name))

        # Points
        fw("DATASET POLYDATA\n")
        fw("POINTS " + str(len(obdata.vertices)) + " float\n")
        for v in obdata.vertices:
            fw("%f %f %f\n" % (v.co[0], v.co[1], v.co[2]))

        # Faces
        fw("POLYGONS " + str(len(obdata.polygons)) + " " + \
            str(sum([1 + len(p.vertices) for p in obdata.polygons])) + "\n")
        for f in obdata.polygons:
            row = str(len(f.vertices))
            for v in f.vertices:
                row += " " + str(v)
            fw(row + "\n")

        # Vertex colors
        for c in obdata.vertex_colors:
            fw("POINT_DATA " + str(len(obdata.vertices)) + "\n")
            fw("COLOR_SCALARS " + str(c.name) + " 4\n")

            # Blender saves vertex colors per each face loop
            # -> There can be several colors per vertex.
            # For now this algorithm takes color from first matching face loop.
            for i in range(0, len(obdata.vertices)):
                found = False
                for p in obdata.polygons:
                    if found:
                        continue
                    for li in p.loop_indices:
                        if i == obdata.loops[li].vertex_index:
                            v = c.data[li].color
                            fw("%f %f %f %f\n" % (v[0], v[1], v[2], v[3]))
                            found = True
                            continue

def ascii_read_vtk(self):
    '''ASCII VTK Polydata reader'''

    points = [] # List of X, Y and Z coordinates for VTK points
    polygons = [] # List of number of points and point indices for polygons

    [ob, points, polygons] = ascii_read_vtk_get_data(self)
    if not points or not polygons or not ob:
        l.info("No points imported")
        return None

    l.debug("Number of points data read: %d" % len(points))
    l.debug("Number of polygons data read: %d" % len(polygons))

    create_verts_and_faces(ob, points, polygons)


def ascii_read_vtk_get_data(self):
    '''Get data from ASCII VTK Polydata file. Returns mesh object, list of
    points and list of polygons.
    '''

    import re
    data = open(self.filepath, 'r')
    ascii = False # Flag to mark "ASCII" entry in file
    mode = "" # Mode of number import (POINTS, POLYGONS, COLOR_SCALARS)
    dataset = "" # Type of dataset (POLYDATA)
    points = [] # List of X, Y and Z coordinates for VTK points
    polygons = [] # List of number of points and point indices for polygons
    ob = None # Mesh object for the final data

    for line in data:
        line = line.rstrip() # Remove trailing characters

        # Skip comment lines
        if re.search(r'^\s*\#', line):
            l.debug("got comment line")
            continue

        # String lines. Note: re.M is required to match line end with '$'
        regex = re.search(r'^([\ \w]+)$', line, re.M)
        if regex:
            s = str(regex.group(1))
            if s == "ASCII":
                l.debug("got ascii")
                ascii = True
                continue
            if s == "DATASET POLYDATA":
                l.debug("got polydata")
                dataset = "POLYDATA"
                continue
            if s == "DATASET UNSTRUCTURED_GRID":
                l.debug("got unstructured_grid")
                self.report({'ERROR'}, "Unstructured Grid import isn't supported!")
                return None, None, None
            if re.search(r"^POINTS", s):
                l.debug("got points")
                mode = "POINTS"
                continue
            if re.search(r"^POLYGONS", s):
                l.debug("got polygons")
                mode = "POLYGONS"
                continue
            if re.search(r"^SCALARS", s):
                l.debug("got scalars")
                self.report({'WARNING'}, "Import may be partial: SCALARS is not implemented.")
                return ob, points, polygons
                mode = "SCALARS"
                continue
            if re.search(r"^COLOR_SCALARS", s):
                l.debug("got color scalars")
                self.report({'WARNING'}, "Import may be partial: COLOR_SCALARS is not implemented.")
                return ob, points, polygons
                mode = "COLOR_SCALARS"
                continue

            # Use first non-keyword match as name for the object
            if not 'name' in locals() and re.search(r'[a-zA-Z]?', line):
                name = s
                l.debug("got name %s" % name)

                if name in bpy.data.objects:
                    l.debug("Delete existing object " + name)
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.data.objects[name].select_set(True)
                    bpy.ops.object.delete()

                l.debug("Create new mesh object " + name)
                mesh_data = bpy.data.meshes.new(name)
                ob = bpy.data.objects.new(name, mesh_data)
                bpy.context.scene.collection.objects.link(ob)
                continue

        # Numerical data lines
        regex = re.search(r'^([dDeE\s\d\.\-]+)$', line, re.M)
        if regex:

            # Exit if no mode is specified for numerical data
            if mode == "":
                self.report({'WARNING'}, "Import may be partial: Found numerical data before DATASET")
                return ob, points, polygons

            # Exit if no ASCII entry has been found in file at this point
            if not ascii:
                self.report({'ERROR'}, "This is not an ASCII VTK file, stopping.")
                return None, None, None

            s = str(regex.group(1))
            numbers = s.split()
            # l.debug("got %d numbers" % len(numbers))

            for x in numbers:
                if mode == "POINTS":
                    points.append(float(x))
                elif mode == "POLYGONS":
                    polygons.append(int(x))
                elif mode == "COLOR_SCALARS":
                    return ob, points, polygons
                else:
                    self.report({'WARNING'}, "Import may be partial: Got unsupported mode " + mode)
                    return ob, points, polygons

    return ob, points, polygons

def create_verts_and_faces(ob, points, polygons):
    '''Create vertices and faces to object ob from point list and polygons list'''

    verts = [] # list of x, y, z point coordinate triplets
    faces = [] # list of vertice indices for faces

    # TODO: Find better way of conversion, these are ugly.

    # Convert list of point coordinates into triplets
    triplet = []
    for x in points:
        triplet.append(x)
        if len(triplet) == 3:
            verts.append(tuple(triplet))
            triplet=[]

    # Convert list of vertex indices into face vertex index list
    ilist = []
    i = 0
    for x in polygons:
        if i == 0:
            np = int(x)
            i += 1
        else:
            ilist.append(int(x))
            i += 1
            if i == np + 1:
                faces.append(tuple(ilist))
                i = 0
                ilist = []

    # Create vertices and faces into mesh object
    ob.data.from_pydata(verts, [], faces)


def vtk_header(name):
    '''Generate VTK header'''
    h = "# vtk DataFile Version 4.2\n"
    h += name + "\n"
    h += "ASCII\n"
    return h
