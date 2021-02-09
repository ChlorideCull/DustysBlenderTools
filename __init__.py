from . import atlas
from . import simplify_mats
from . import pack_single_udim_operator
from . import pack_material_udims
from . import apply_operators
import bpy

bl_info = {
    "name": "Dusty's Blender Tools",
    "blender": (2, 91, 0),
    "category": "Object",
}


def register():
    bpy.utils.register_class(atlas.AtlasOperator)
    bpy.utils.register_class(simplify_mats.SimplifyMaterialsOperator)
    bpy.utils.register_class(pack_single_udim_operator.PackUdimOperator)
    bpy.utils.register_class(pack_material_udims.AtlasUdimMaterialsOperator)
    bpy.utils.register_class(apply_operators.ApplyOperatorsOperator)


def unregister():
    bpy.utils.unregister_class(atlas.AtlasOperator)
    bpy.utils.unregister_class(simplify_mats.SimplifyMaterialsOperator)
    bpy.utils.unregister_class(pack_single_udim_operator.PackUdimOperator)
    bpy.utils.unregister_class(pack_material_udims.AtlasUdimMaterialsOperator)
    bpy.utils.unregister_class(apply_operators.ApplyOperatorsOperator)


def view3d_object_draw(self: bpy.types.Menu, context):
    self.layout.operator("dusty.flatten_udims")
    self.layout.operator("dusty.atlas")
    self.layout.operator("dusty.applyoperators")


bpy.types.VIEW3D_MT_object.append(view3d_object_draw)
