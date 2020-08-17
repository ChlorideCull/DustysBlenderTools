# Dusty's Blender Tools

My personal "swiss army knife".

## Features

* "Atlas selected into UDIMs" - Atlas multiple textures into a single UDIM texture set. Select objects, and run the operator, it will combine the textures from the materials on the objects.
* "Simplify materials" - Clean up materials by removing functionally equivalent ones. Useful after atlasing multiple textures into a single UDIM texture set, since you tend to end up with 10+ materials. 

## Caveats

* "Atlas selected into UDIMs"
    * Textures must be stored as PNGs (mostly due to laziness)
    * All materials must have normals and diffuse image textures (mostly due to laziness, again)
    
## Future features

* "Pack UDIM to single texture set" - generate a pair of optimized PNGs, packing UV islands. Mostly for Unity and other game engines.