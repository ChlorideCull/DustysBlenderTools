import bpy
from typing import List, Dict
import math
import shutil
import os
import logging
import re
from . import SimpleMaterialDefinition
from PIL import Image


log = logging.getLogger("DustyAtlas")


def get_texture_from_normal_node(node: bpy.types.ShaderNodeNormalMap):
    if node.type != "NORMAL_MAP":
        raise Exception("Node is not a normal map node.")
    if node.uv_map != '':
        raise Exception("Normal map node has a UV map set, which would break when atlasing without extra support.")
    color_input = node.inputs[1]
    if not color_input.is_linked:
        return None
    return get_texture_from_image_node(color_input.links[0].from_socket.node)


def get_texture_from_image_node(node: bpy.types.ShaderNodeTexImage):
    if node.type != "TEX_IMAGE":
        raise Exception("Node is not an image texture node.")
    return node.image


def get_texture_set_for_material(mat: bpy.types.Material):
    if not mat.use_nodes:
        raise Exception(f"Material '{mat.name}' doesn't use nodes - nodes are required.")

    output_node = None
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
            break
    if output_node is None:
        raise Exception(f"Material '{mat.name}' lacks a Material Output node.")
    if not output_node.inputs[0].is_linked:
        raise Exception(f"Material '{mat.name}' doesn't have a Surface output set up.")

    surface_node: bpy.types.Node = output_node.inputs[0].links[0].from_socket.node
    color_input = None
    normal_input = None
    for nodeInput in surface_node.inputs:
        if nodeInput.name == "Color" or nodeInput.name == "Base Color":
            color_input = nodeInput
        elif nodeInput.name == "Normal":
            normal_input = nodeInput
        if color_input is not None and normal_input is not None:
            break
    if color_input is None:
        raise Exception(f"Material '{mat.name}': Failed to find a (Base) Color input on the surface node.")

    color_texture = None
    if not color_input.is_linked:
        raise NotImplementedError()
    else:
        color_texture = get_texture_from_image_node(color_input.links[0].from_socket.node)

    normal_texture = None
    if normal_input is not None and normal_input.is_linked:
        normal_texture = get_texture_from_normal_node(normal_input.links[0].from_socket.node)

    return SimpleMaterialDefinition.SimpleMaterialDefinition(color_texture, normal_texture)


def merge_textures_udim_style(materials: Dict[str, SimpleMaterialDefinition.SimpleMaterialDefinition],
                              meshes: List[bpy.types.Mesh],
                              fileprefix: str,
                              directory: str):
    # UDIM style - each material gets placed on a grid, and UVs for each polygon gets offset to account for it.
    # + Simple, fast
    # - Waste of texture space since unused material space is left in
    tile_max_x = 10
    tile_max_y = math.ceil(len(materials)/tile_max_x)
    material_ids = [x for x in materials.keys()]

    # Tile the materials into UDIMs
    tile_map = {}
    for x in range(0, tile_max_x):
        tile_map[x] = {}
        for y in range(0, tile_max_y):
            tile_map[x][y] = None

    tile_map_lookup = {}
    for y in range(0, tile_max_y):
        for x in range(0, tile_max_x):
            material_index = (y * tile_max_x) + x
            if material_index < len(material_ids):
                tile_map[x][y] = material_ids[material_index]
                tile_map_lookup[material_ids[material_index]] = [x, y]

    # Map the UVs onto the UDIMs
    for mesh in meshes:
        if len(mesh.materials) == 0:
            continue  # Skip if no material slots exist on the mesh
        if len(mesh.uv_layers) == 0:
            raise Exception("Missing UV map!")
        for polygon in mesh.polygons:
            polygon_material_name = mesh.materials[polygon.material_index].name
            if polygon_material_name not in tile_map_lookup.keys():
                continue
            for loop_index in polygon.loop_indices:
                loop_uv = mesh.uv_layers[0].data[loop_index].uv
                mesh.uv_layers[0].data[loop_index].uv[0] = loop_uv[0] + tile_map_lookup[polygon_material_name][0]
                mesh.uv_layers[0].data[loop_index].uv[1] = loop_uv[1] + tile_map_lookup[polygon_material_name][1]

    # Generate two UDIM textures
    diffuse_textures = []
    for y in range(0, tile_max_y):
        for x in range(0, tile_max_x):
            if tile_map[x][y] is not None:
                diffuse_textures.append(materials[tile_map[x][y]].diffuseTexture)
    diffuse_texture = generate_udim_texture(f"{fileprefix}.Diffuse", directory, diffuse_textures)
    normal_textures = []
    for y in range(0, tile_max_y):
        for x in range(0, tile_max_x):
            if tile_map[x][y] is not None:
                normal_textures.append(materials[tile_map[x][y]].normalTexture)
    normal_texture = generate_udim_texture(f"{fileprefix}.Normal", directory, normal_textures)
    normal_texture.colorspace_settings.name = "Non-Color"
    normal_texture.colorspace_settings.is_data = True

    return diffuse_texture, normal_texture


def generate_udim_texture(name: str, path: str, textures: List[bpy.types.Image]):
    if len(textures) == 1:
        raise Exception("No point in creating UDIMs with a single image, is there?")
    if textures[0] is None:
        texture_size_x = 1
        texture_size_y = 1
        texture_name = "1001"
    else:
        texture_size_x = textures[0].size[0]
        texture_size_y = textures[0].size[1]
        texture_name = textures[0].name
    for texture in textures:
        if texture is None:
            continue
        if texture.is_dirty:
            raise Exception("Texture has unsaved changes, please save first.")
        if texture.filepath == "":
            raise Exception("Texture not saved, cannot use for tiling.")

    generated_image = bpy.data.images.new(name, texture_size_x, texture_size_y, alpha=True, tiled=True)
    generated_image.tiles[0].label = texture_name
    for tile_id in range(1, len(textures)):
        tile_label = str(tile_id)
        if textures[tile_id] is not None:
            tile_label = textures[tile_id].name
        generated_image.tiles.new(1001 + tile_id, label=tile_label)

    folder_path = bpy.path.abspath(path)
    try:
        os.mkdir(folder_path)
    except FileExistsError:
        pass

    for tile_id in range(0, len(textures)):
        texture = textures[tile_id]
        dest_path = os.path.join(folder_path, f"{name}.{1001 + tile_id}.png")
        if texture is None:
            with open(dest_path, mode="wb") as dest_file:
                # Single pixel PNG with #7F7FFF - couldn't be bothered to include it as a file.
                dest_file.write(b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a\x00\x00\x00\x0d\x49\x48\x44\x52\x00\x00\x00\x01'
                                b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90\x77\x53\xde\x00\x00\x00\x0c\x49\x44\x41'
                                b'\x54\x08\xd7\x63\xa8\xaf\xff\x0f\x00\x03\x7e\x01\xfe\x10\xb1\xfb\x65\x00\x00\x00'
                                b'\x00\x49\x45\x4e\x44\xae\x42\x60\x82')
        elif texture.file_format == "PNG":
            shutil.copy(bpy.path.abspath(texture.filepath), dest_path)
        else:
            im = Image.open(bpy.path.abspath(texture.filepath))
            im.save(dest_path, "PNG")
    generated_image.filepath = bpy.path.relpath(os.path.join(folder_path, f"{name}.1001.png"))
    generated_image.reload()
    return generated_image


def main(target_materials: List[bpy.types.Material], directory: str, fileprefix: str):
    material_definitions = {}
    for mat in target_materials:
        material_definitions[mat.name] = get_texture_set_for_material(mat)

    diffuse_udim_texture, normal_udim_texture = merge_textures_udim_style(material_definitions, bpy.data.meshes,
                                                                          fileprefix, directory)
    for mat in material_definitions.values():
        mat.diffuseTexture.user_remap(diffuse_udim_texture)
        if mat.normalTexture is not None:
            mat.normalTexture.user_remap(normal_udim_texture)


class AtlasOperator(bpy.types.Operator):
    """Atlas materials on selected objects into UDIMs"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "dusty.atlas"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Atlas selected into UDIMs"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    filename: bpy.props.StringProperty(subtype="FILE_NAME")

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
        materials = [context.blend_data.materials[k] for k in material_ids]

        filename_match = re.match(r"(\w+)\.\d+.\w+", self.filename)
        if not filename_match:
            self.report({'ERROR_INVALID_INPUT'}, f"Filename '{self.filename}' could not be used to generate a pattern, must be in the form of 'foo.1001.png'")
            return {'CANCELLED'}
        prefix = filename_match.group(1)

        main(materials, self.directory, prefix)
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
