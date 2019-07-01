# VTK Import-Export Add-on for Blender

## Introduction

mesh_io_vtk is an add-on for ([Blender 2.8](https://www.blender.org/2-8)
for importing and exporting mesh data in
VTK ([Visualization ToolKit](https://www.vtk.org))
file format used widely in scientific computation applications.

Aim is first to create a stand-alone import-export tool which supports
VTK polydata (including vertices, edges and polygon surface meshes).
My hope is to extend import-export for VTK unstructured grids
(polyhedron volume meshes), to allow Blender to be used to create and
modify volume meshes.

The add-on is currently under development. Currently supported features include

* ASCII legacy VTK file import (VTK polydata support only)
* ASCII legacy VTK file export (VTK polydata support only)
* Exports mesh (points and faces) and vertex colors as VTK color scalar data
