import bpy
from .pack_udim import calc_pack_items, pack_udim_btree


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

        calced = calc_pack_items([space_data.image])
        pack_udim_btree(calced, self.filepath)
        return {'FINISHED'}


def image_menu_draw(self: bpy.types.Menu, context):
    self.layout.operator("dusty.packudim")


bpy.types.IMAGE_MT_image.append(image_menu_draw)  # Add to the "Image" menu in the Image Editor
