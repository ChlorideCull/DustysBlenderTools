from typing import List
import bpy
import os
import math
from .pack_udim import calc_pack_items, pack_udim_btree, PackCalculation
from .atlas import get_texture_set_for_material
from .NotifyUserException import NotifyUserException


def map_uv(calc: PackCalculation, uv: List[float], tile_id: int):
    real_width = calc.packed_result.w
    real_height = calc.packed_result.h

    u_transformed = math.fmod(uv[0], 1)
    v_transformed = math.fmod(uv[1], 1)

    tile_pack = None
    for packed_item in calc.packed_result.items:
        if packed_item.identity != f"{tile_id}":
            continue
        tile_pack = packed_item
    if tile_pack is None:
        raise NotifyUserException(f"Failed to find tile '{tile_id}'")

    u_start = tile_pack.fit.x / real_width
    v_start = tile_pack.fit.y / real_height
    u_range = tile_pack.fit.w / real_width
    v_range = tile_pack.fit.h / real_height

    return [u_start + (u_transformed * u_range), v_start + (v_transformed * v_range)]


class AtlasUdimMaterialsOperator(bpy.types.Operator):
    """Atlas UDIM materials on selected objects into PNG textures"""
    bl_idname = "dusty.flatten_udims"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Atlas UDIMs on selected objects into PNGs"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    directory: bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):        # execute() is called when running the operator.
        material_ids = []
        selected_objects: List[bpy.types.Object] = context.selected_objects
        for obj in selected_objects:
            for matslot in obj.material_slots:
                if matslot.material.name not in material_ids:
                    material_ids.append(matslot.material.name)
        materials: List[bpy.types.Material] = [context.blend_data.materials[k] for k in material_ids]

        material_calculations = {}
        replacement_images = {}
        for mat in materials:
            texture_set = get_texture_set_for_material(mat)
            calculated = calc_pack_items([texture_set.normalTexture, texture_set.diffuseTexture])
            material_calculations[mat.name] = calculated
            pack_udim_btree(calculated, self.directory)
            for texture in calculated.udims:
                if texture.name not in replacement_images:
                    new_image = bpy.data.images.new(
                        f"{texture.name}_packed", calculated.packed_result.w, calculated.packed_result.h)
                    new_image.filepath = os.path.join(self.directory, f"{texture.name}.png")
                    new_image.source = "FILE"
                    new_image.colorspace_settings.is_data = texture.colorspace_settings.is_data
                    new_image.colorspace_settings.name = texture.colorspace_settings.name
                    new_image.reload()
                    replacement_images[texture.name] = new_image

        for mesh in bpy.data.meshes:
            if len(mesh.materials) == 0:
                continue  # Skip if no material slots exist on the mesh
            if len(mesh.uv_layers) == 0:
                raise Exception("Missing UV map!")
            for polygon in mesh.polygons:
                polygon_material_name = mesh.materials[polygon.material_index].name
                if polygon_material_name not in material_calculations.keys():
                    continue
                for loop_index in polygon.loop_indices:
                    loop_uv = mesh.uv_layers[0].data[loop_index].uv
                    udim_id = math.floor(1000 + (math.floor(loop_uv[0]) + 1) + (math.floor(loop_uv[1]) * 10))
                    mesh.uv_layers[0].data[loop_index].uv = map_uv(material_calculations[polygon_material_name],
                                                                   loop_uv, udim_id)

        for image_id in replacement_images.keys():
            bpy.data.images[image_id].user_remap(replacement_images[image_id])

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
