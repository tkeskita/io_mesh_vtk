# VTK Import-Export Add-on for Blender

## Introduction

mesh_io_vtk is an add-on for ([Blender 2.8](https://www.blender.org/2-8)
for exporting mesh data in VTK ([Visualization ToolKit](https://www.vtk.org))
file format used widely in scientific computation applications.
Aim is first to create a small stand-alone import-export tool, and
extend from there towards a tool by which Blender could be used to
modify VTK mesh and data.

The add-on is currently under development. Currently supported features include

* ASCII legacy VTK file export
* Exports mesh (points and faces) and vertex colors as point data
