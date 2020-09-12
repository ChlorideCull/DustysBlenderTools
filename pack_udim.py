from typing import List, Dict
import os
import re
import bpy
from .binary_tree_packer import pack_items_binary_tree, NodePackerItem, PackerResult
from .NotifyUserException import NotifyUserException
from PIL import Image


class PackCalculation:
    def __init__(self, udims: List[bpy.types.Image], packresult: PackerResult, files: Dict[str, Dict[str, Image.Image]]):
        self.udims = udims
        self.packed_result = packresult
        self.files = files


def calc_pack_items(udims: List[bpy.types.Image]):
    items_to_pack: List[NodePackerItem] = []
    files = {}

    for udim in udims:
        first_udim = False
        if len(items_to_pack) == 0:
            first_udim = True
        files[udim.name] = {}
        filepath = bpy.path.abspath(udim.filepath)
        dirpath, filename = os.path.split(filepath)
        filename_match = re.match(r"(\w+)\.\d+.(\w+)", filename)
        if not filename_match:
            raise NotifyUserException(
                f"'{udim.filepath}' could not be used to generate a pattern, files must be in the form of 'foo.1001.png'")

        for tile in udim.tiles:
            tile_filename = os.path.join(dirpath, f"{filename_match.group(1)}.{tile.number}.{filename_match.group(2)}")
            tile_image: Image.Image = Image.open(tile_filename)
            files[udim.name][f"{tile.number}"] = tile_image
            if first_udim:
                items_to_pack.append(NodePackerItem(f"{tile.number}", tile_image.width, tile_image.height))

    pack_result = pack_items_binary_tree(items_to_pack)

    return PackCalculation(udims, pack_result, files)


def pack_udim_btree(pack_calc: PackCalculation, target_abspath: str):
    for udim in pack_calc.udims:
        output_image = Image.new("RGBA", (pack_calc.packed_result.w, pack_calc.packed_result.h), (0, 0, 0, 0))
        for item in pack_calc.packed_result.items:
            if item.fit is None:
                raise Exception(f"Failed to pack {item.identity}")
            file = pack_calc.files[udim.name][item.identity]
            if file.width != item.w or file.height != item.h:
                file = file.resize((item.w, item.h))
            output_image.paste(file, (item.fit.x, item.fit.y))
        if len(pack_calc.udims) == 1:
            output_image.save(target_abspath)
        else:
            output_image.save(os.path.join(target_abspath, f"{udim.name}.png"))
