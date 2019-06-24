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
    "name": "VTK Import-Export",
    "author": "Tuomo Keskitalo",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import-Export > VTK",
    "description": "Import-Export of VTK (Visualization ToolKit, www.vtk.org) files",
    "wiki_url": "https://github.com/tkeskita/mesh_io_vtk",
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


@orientation_helper(axis_forward='Y', axis_up='Z')
class ExportVTK(bpy.types.Operator, ExportHelper):
    '''Save active object mesh and vertex data to VTK file'''
    bl_idname = "export_mesh.vtk"
    bl_label = "Export VTK"

    filename_ext = ".vtk"
    filter_glob: StringProperty(default="*.vtk", options={'HIDDEN'})

    #use_bin: BoolProperty(
    #        name="Binary",
    #        description="Export in binary VTK format",
    #        default=False,
    #)

    def execute(self, context):
        import itertools
        from mathutils import Matrix

        ob = context.active_object
        ascii_write_vtk(self.filepath, ob.data)
        return {'FINISHED'}


def menu_import(self, context):
    self.layout.operator(ImportVTK.bl_idname, text="VTK (.vtk)")

def menu_export(self, context):
    self.layout.operator(ExportVTK.bl_idname, text="VTK (.vtk)")

classes = (
    ExportVTK,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(menu_export)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()


def ascii_write_vtk(filepath, obdata):
    '''ASCII VTK writer'''
    
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


def vtk_header(name):
    '''Generate VTK header'''
    h = "# vtk DataFile Version 4.2\n"
    h += name + "\n"
    h += "ASCII\n"
    return h
