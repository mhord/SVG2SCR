SVG2SCR
=======

Converter for Inkscape SVG files into EAGLE shapes. Python 2.7.

Creates an EAGLE .scr file that will draw the paths found in an Inkscape SVG into any EAGLE document. To work properly, certain guidelines (described below) must be adhered to in creation of the images to be imported.

Other drawing programs (CorelDraw, Adobe Illustrator, etc) do not generate compatible SVG files; importing a pdf into Inkscape that was exported from another program is often the best way to ensure that it will work.

####Usage:
1. Fill of path determines whether polygon in EAGLE will be filled or not.
2. Width of stroke determines width of stroke in EAGLE; this can be zero.
3. Red channel of stroke color determines layer of polygon in EAGLE; for example, make the red channel 21 to draw polygon in the top silk (tPlace) layer in a .brd file, or 94 to draw in Symbol layer on a schematic.
4. Polygons are drawn 1:1 with the paths in the original SVG.
5. The lower left of the SVG frame is the 0,0 origin of the EAGLE drawing.

####Notes on file setup:
1. Negative space is not allowed.
2. No groups should be present in the file.
3. Close all paths.
4. Use the "Break Apart" command to make smaller paths out of larger paths.

Check out the Wiki for a walk-through of how to make a nicely compatible SVG file.
