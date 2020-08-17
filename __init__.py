from . import atlas
import bpy

bl_info = {
    "name": "Dusty's Blender Tools",
    "blender": (2, 80, 0),
    "category": "Object",
}


def register():
    bpy.utils.register_class(atlas.AtlasOperator)


def unregister():
    bpy.utils.unregister_class(atlas.AtlasOperator)

