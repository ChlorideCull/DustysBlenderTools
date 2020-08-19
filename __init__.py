from . import atlas
from . import simplify_mats
from . import pack_udim
import bpy

bl_info = {
    "name": "Dusty's Blender Tools",
    "blender": (2, 80, 0),
    "category": "Object",
}


def register():
    bpy.utils.register_class(atlas.AtlasOperator)
    bpy.utils.register_class(simplify_mats.SimplifyMaterialsOperator)
    bpy.utils.register_class(pack_udim.PackUdimOperator)


def unregister():
    bpy.utils.unregister_class(atlas.AtlasOperator)
    bpy.utils.unregister_class(simplify_mats.SimplifyMaterialsOperator)
    bpy.utils.unregister_class(pack_udim.PackUdimOperator)

