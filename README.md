# Dusty's Blender Tools

My personal "swiss army knife".

## Features

* "Atlas selected into UDIMs" - Atlas multiple textures into a single UDIM texture set. Select objects, and run the operator, it will combine the textures from the materials on the objects.
* "Simplify materials" - Clean up materials by removing functionally equivalent ones. Useful after atlasing multiple textures into a single UDIM texture set, since you tend to end up with 10+ materials. 
* "Pack UDIM into single image" - Packs a UDIM image into a plain old PNG.
* "Atlas UDIMs on selected objects into PNGs" - Packs all UDIMs in materials into a set of PNGs, for non-UDIM rendering workflows.

## Caveats

* General
    * Most of this assumes you are using PNGs for textures.
    * Most of this assumes a normal map and diffuse image texture.
* "Atlas selected into UDIMs"
    * Textures must be stored as PNGs (mostly due to laziness)
* "Pack UDIM into single image"
    * Not very useful - it does not remap UVs or replace Image Textures used in materials. It's a WIP, basically.
    
## Future features

* "Pack UDIM to single texture set" - generate a pair of optimized PNGs, packing UV islands. Mostly for Unity and other game engines.