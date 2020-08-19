from typing import List
import os
import re
import bpy
from .binpacker import pack_items, PackItem
from .binary_tree_packer import pack_items_binary_tree, NodePackerItem
from .NotifyUserException import NotifyUserException
from PIL import Image


def pack_udim(udim: bpy.types.Image, target_abspath: str):
    items_to_pack: List[PackItem] = []
    files = {}

    filepath = bpy.path.abspath(udim.filepath)
    dirpath, filename = os.path.split(filepath)
    filename_match = re.match(r"(\w+)\.\d+.(\w+)", filename)
    if not filename_match:
        raise NotifyUserException(f"'{udim.filepath}' could not be used to generate a pattern, files must be in the form of 'foo.1001.png'")

    for tile in udim.tiles:
        tile_filename = os.path.join(dirpath, f"{filename_match.group(1)}.{tile.number}.{filename_match.group(2)}")
        tile_image: Image.Image = Image.open(tile_filename)
        files[f"{tile.number}"] = tile_image
        items_to_pack.append(PackItem(f"{tile.number}", tile_image.width, tile_image.height))

    pack_grid = pack_items(items_to_pack)
    output_image = Image.new("RGBA", (pack_grid.width, pack_grid.height), (0, 0, 0, 0))
    x_offset = 0
    y_offset = 0
    for row in pack_grid.tiles:
        for tile in row.tiles:
            output_image.paste(files[tile.identity], (x_offset, y_offset))
            x_offset += files[tile.identity].width
        x_offset = 0
        y_offset += row.height
    output_image.save(os.path.join(dirpath, target_abspath))


def pack_udim_btree(udim: bpy.types.Image, target_abspath: str):
    items_to_pack: List[NodePackerItem] = []
    files = {}

    filepath = bpy.path.abspath(udim.filepath)
    dirpath, filename = os.path.split(filepath)
    filename_match = re.match(r"(\w+)\.\d+.(\w+)", filename)
    if not filename_match:
        raise NotifyUserException(f"'{udim.filepath}' could not be used to generate a pattern, files must be in the form of 'foo.1001.png'")

    for tile in udim.tiles:
        tile_filename = os.path.join(dirpath, f"{filename_match.group(1)}.{tile.number}.{filename_match.group(2)}")
        tile_image: Image.Image = Image.open(tile_filename)
        files[f"{tile.number}"] = tile_image
        items_to_pack.append(NodePackerItem(f"{tile.number}", tile_image.width, tile_image.height))

    pack_result = pack_items_binary_tree(items_to_pack)
    output_image = Image.new("RGBA", (pack_result.w, pack_result.h), (0, 0, 0, 0))
    for item in pack_result.items:
        if item.fit is None:
            print(f"{item.identity} was not fit, skipping")
            continue
        print(f"{item.identity}, {item.w}x{item.h} fit into {item.fit.w}x{item.fit.h}, offset {item.fit.x}x{item.fit.y}")
        output_image.paste(files[item.identity], (item.fit.x, item.fit.y))
    output_image.save(os.path.join(dirpath, target_abspath))


class PackUdimOperator(bpy.types.Operator):
    """Pack the selected UDIM image into a single, non-UDIM image"""
    bl_idname = "dusty.packudim"
    bl_label = "Pack UDIM into single image"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    @classmethod
    def poll(cls, context):
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceImageEditor):
            return False
        if space_data.image.source != "TILED":
            return False
        if space_data.image.is_dirty:
            return False
        if len(space_data.image.packed_files) > 0:
            return False
        return True

    def execute(self, context):
        space_data = context.space_data
        if not isinstance(space_data, bpy.types.SpaceImageEditor):
            self.report({'ERROR'}, "Can only run in an Image Editor context")
            return {'CANCELLED'}
        if space_data.image.source != "TILED":
            self.report({'ERROR'}, "Can't pack a UDIM if it's not a UDIM, you know.")
            return {'CANCELLED'}
        if space_data.image.is_dirty:
            self.report({'ERROR'}, "Can't pack a dirty file, changes must be saved first.")
            return {'CANCELLED'}
        if len(space_data.image.packed_files) > 0:
            self.report({'ERROR'}, "Can't work on packed files.")
            return {'CANCELLED'}

        pack_udim_btree(space_data.image, self.filepath)
        return {'FINISHED'}


def image_menu_draw(self: bpy.types.Menu, context):
    self.layout.operator("dusty.packudim")


bpy.types.IMAGE_MT_image.append(image_menu_draw)  # Add to the "Image" menu in the Image Editor
