import bpy.types


class SimpleMaterialDefinition:
    def __init__(self, diffuseTexture: bpy.types.Image, normalTexture: bpy.types.Image, metallicTexture: bpy.types.Image):
        self.diffuseTexture = diffuseTexture
        self.normalTexture = normalTexture
        self.metallicTexture = metallicTexture
