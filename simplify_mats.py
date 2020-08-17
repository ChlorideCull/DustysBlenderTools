from typing import List
import bpy
import json
import hashlib


def hash_node(node: bpy.types.Node):
    inputs = {}
    for inp in node.inputs:
        if inp.is_linked:
            inputs[inp.name] = "LINKED"
        else:
            try:
                inputs[inp.name] = f"{inp.default_value}"
            except AttributeError:
                inputs[inp.name] = "UNKNOWN"
    outputs = {}
    for outp in node.outputs:
        if outp.is_linked:
            outputs[outp.name] = "LINKED"
        else:
            try:
                outputs[outp.name] = f"{outp.default_value}"
            except AttributeError:
                outputs[outp.name] = "UNKNOWN"
    extradata = {}
    if isinstance(node, bpy.types.ShaderNodeTexImage):
        extradata["IMG"] = node.image.name
        extradata["INTERP"] = node.interpolation
        extradata["PROJ"] = node.projection
        extradata["PROJB"] = node.projection_blend
        extradata["TEXM"] = node.texture_mapping.mapping
    elif isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
        extradata["DIST"] = node.distribution
        extradata["SUBSM"] = node.subsurface_method
    return hashlib.sha1(json.dumps({
        "type": node.type,
        "inputs": inputs,
        "outputs": outputs,
        "extra": extradata
    }).encode("UTF-8")).hexdigest()


def hash_node_tree(node_tree: bpy.types.NodeTree):
    # We hash materials by their node tree, containing:
    # * Node types in the tree
    # * Configuration of individual nodes
    # * Links between nodes
    node_map = {}
    node_links = []
    for node in node_tree.nodes:
        node_map[node.name] = hash_node(node)
    for link in node_tree.links:
        node_links.append(f"{node_map[link.from_node.name]}.{link.from_socket.name} - {node_map[link.to_node.name]}.{link.to_socket.name}")
    node_links.sort()
    node_list = [x for x in node_map.values()]
    node_list.sort()
    return hashlib.sha1(json.dumps({
        "nodes": node_list,
        "links": node_links
    }).encode("UTF-8")).hexdigest()


def simplify_materials(mats: List[bpy.types.Material]):
    mat_hashes = {}
    remap_count = 0
    for mat in mats:
        if not mat.use_nodes:
            continue
        node_tree_hash = hash_node_tree(mat.node_tree)
        if node_tree_hash not in mat_hashes:
            mat_hashes[node_tree_hash] = mat
        else:
            mat.user_remap(mat_hashes[node_tree_hash])
            remap_count += 1
    return remap_count


class SimplifyMaterialsOperator(bpy.types.Operator):
    """Simplify materials, removing functionally equivalent ones."""
    bl_idname = "dusty.simplifymats"
    bl_label = "Simplify materials"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):        # execute() is called when running the operator.
        remap_count = simplify_materials(context.blend_data.materials)
        self.report({'INFO'}, f"Removed {remap_count} materials.")
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.
