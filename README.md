SVG2SCR
=======

Converter for Inkscape SVG files into EAGLE shapes

This tool will take an Inkscape SVG dropped onto it and attempt to create an EAGLE script to draw
the shapes in the SVG file.

To use, make an Inkscape SVG of the desired shape(s). The tool will base the EAGLE script on any
path in the SVG file which is ungrouped and on Layer1. The line width used in the .scr file is
directly based on the line width of the path; the EAGLE layer is based on the red channel of the
stroke color. If any fill is present, the script will treat the shape as a polygon. Otherwise, it
will be treated as a simple line shape.

### Important!

This tool is kind of primitive. In order to get anything remotely resembling good results, you should
adhere to these guidelines when creating an SVG file to use with it:

- Don't group objects. Dealing with arbitrary depths of transformation is a bit much.
- Filled polygons should have one contiguous border; whitespace is a no-no.
- Make everything a path.
