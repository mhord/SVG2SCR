from SVGPath import SVGPath
from SvgParser import SvgParser
from beziers import cubicBezier, quadBezier
from SCRSupport import EAGLEPath
from SVGConstants import *
import os, sys, re, math

## Filename specification section. Can be an absolute path, a relative path, or
##  by using sys.argv[1], can be a file which is dropped onto the script.
##filename = sys.argv[1]
filename = "SFE_Logo.svg"

f = open(filename, 'r')   ## Open the file in question.
svg_data = f.read()       ## Read the data into a holding structure.
f.close()                 ## Be a good resident of the OS and close the file.
parser = SvgParser()      ## Instantiate an object of the SvgParser class.
parser.feed(svg_data)     ## Run the data we collected from the file through
                          ##  the SvgParser we just created.

## Uncomment this during debugging to display the results of the parsing. Note
##  that a good file will produce a ridiculously large amount of data, since
##  the curves must be kept short to make modeling them as straight segments
##  aesthetically pleasing!

##print "Offset:", parser.xOffset, parser.yOffset
##for i in parser.pathData:
##    i.display()

## Okay, now we have a list of SVGPath objects, each of which contains the
##  information necessary to describe one path from the drawing, plus a couple
##  of sundry data points needed to properly describe the location of those
##  paths in an absolute coordinate system in EAGLE. We now have to interpret
##  that list from curves to endpoints of straight lines, and that's a bit of
##  more work.

pathList = []  ## This will become a list of items of type EAGLEPath, which is
               ##  effectively a list of points ready to get written to an SCR
               ##  file with minimum fuss.

## Here's our iteration across all the paths we picked out of the SVG file.
##  parser.pathData is a list of SVGPath objects; see the SVGPath file for deets
##  on that object.
for shape in parser.pathData:
    pathList.append(EAGLEPath())  ## Create a new EAGLEPath for this shape

    ## In a well-stuctured SVG (that is, one where all the objects are in one
    ##  group), there are two offsets: the total group offset and the offset of
    ##  each individual shape. We want to create a single offset for our start
    ##  point in the SCR file.
    xOffset = shape.xOffset + parser.xOffset
    yOffset = shape.yOffset + parser.yOffset
    ## We need to convert information from the SVGPath object to the
    ##  corresponding field in the EAGLEPath object that we just appended to the
    ##  pathList object.
    pathList[-1].pathType.extend(shape.pathType)
    pathList[-1].pathWeight = shape.pathWeight
    pathList[-1].pathLayer = shape.pathLayer

    ## This while loop looks awkward but there's a reason: we aren't going to
    ##  look at every item in the list, and sometimes we'll want to skip forward
    ##  by more items than others. Doing it this way lets us do that easily. Also,
    ##  if you *really* want to grok this, you'll need to read up on how SVG paths
    ##  are defined.
    i = -1
    while i < (len(shape.path)-1):
        i = i+1
        ## First let's parse out any actual commands. These only get sent ONCE
        ##  and then subsequent elements are treated as continuations of the last
        ##  command, so we need a way to track what the last command WAS. We'll
        ##  deal with non-command strings after we've handled the command cases.

        ## The model for this is simple: discover and set a mode, then grab the
        ##  data for the current mode, adjust it for offsets, create a
        ##  coordinate pair for the current EAGLE path and append it to the
        ##  list. Then, we jump to the next unknown parameter and go back to the
        ##  beginning of the while loop.
        if (shape.path[i] == 'm'):
            if i == 0:          ## When a relative MOVETO is first command in a
                mode = MOVEABS  ##  path, treat it as absolute, although any
                                ##  following parameters should be treated as
                                ##  relative LINETO parameters.
            else:
                mode = MOVE
            continue
        if (shape.path[i] == 'M'):
            mode = MOVEABS
            continue
        if (shape.path[i] == 'l'):
            mode = LINE
            continue
        if (shape.path[i] == 'L'):
            mode = LINEABS
            continue
        if (shape.path[i] == 'h'):
            mode = LINEH
            continue
        if (shape.path[i] == 'H'):
            mode = LINEHABS
            continue
        if (shape.path[i] == 'v'):
            mode = LINEV
            continue
        if (shape.path[i] == 'V'):
            mode = LINEVABS
            continue
        if (shape.path[i] == 'c'):
            mode = CURVE
            continue
        if (shape.path[i] == 'C'):
            mode = CURVEABS
            continue
        if (shape.path[i] == 's'):
            mode = SMOOTH
            continue
        if (shape.path[i] == 'S'):
            mode = SMOOTHABS
            continue
        if (shape.path[i] == 'q'):
            mode = QUADRATIC
            continue
        if (shape.path[i] == 'Q'):
            mode = QUADRATICABS
            continue
        if (shape.path[i] == 't'):
            mode = SMOOTHQUAD
            continue
        if (shape.path[i] == 'T'):
            mode = SMOOTHQUADABS
            continue
        if (shape.path[i] == 'a'):
            mode = ARC
            continue
        if (shape.path[i] == 'A'):
            mode = ARCABS
            continue
        if (shape.path[i] == 'z'):
            pathList[-1].path.append(pathList[-1].path[0])
            break
        if (shape.path[i] == 'Z'):
            pathList[-1].path.append(pathList[-1].path[0])
            break
        ## Okay, now let's deal with cases where we DON'T have a command, based on
        ##  what the most recent command seen was. Basically, we want to grab
        ##  x and y data, convert it to a float, adjust it for offset, convert
        ##  to mm, convert it into a two-element list and append that list to
        ##  the path[] element of the most recent entry in pathList[].
        if (mode == MOVE):
            cpx = (float(shape.path[i])/3.54) + cpx
            i = i+1
            cpy = (float(shape.path[i])/-3.54) + cpy
            pathList[-1].path.append([cpx,cpy])
            mode = LINE
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == MOVEABS):
            cpx = (float(shape.path[i]) + xOffset)/3.54
            i = i+1
            cpy = (float(shape.path[i]) + yOffset)/-3.54
            pathList[-1].path.append([cpx,cpy])
            if (i == 2):
                mode = LINE
            else:
                mode = LINEABS
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINE):
            cpx = (float(shape.path[i])/3.54) + cpx
            i = i+1
            cpy = (float(shape.path[i])/-3.54) + cpy
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINEABS):
            cpx = (float(shape.path[i]) + xOffset)/3.54
            i = i+1
            cpy = (float(shape.path[i]) + yOffset)/-3.54
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINEH):
            cpx = (float(shape.path[i])/3.54) + cpx
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINEHABS):
            cpx = (float(shape.path[i]) + xOffset)/3.54
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINEV):
            cpy = (float(shape.path[i])/-3.54) + cpy
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == LINEVABS):
            cpy = (float(shape.path[i]) + yOffset)/-3.54
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == CURVE):
            h1x = (float(shape.path[i])/3.54)+cpx
            h1y = (float(shape.path[i+1])/-3.54)+cpy
            h2x = (float(shape.path[i+2])/3.54)+cpx
            h2y = (float(shape.path[i+3])/-3.54)+cpy
            epx = (float(shape.path[i+4])/3.54)+cpx
            epy = (float(shape.path[i+5])/-3.54)+cpy
            curve = cubicBezier([cpx,cpy], [h1x,h1y], [h2x, h2y], [epx, epy])
            i = i + 5
            cpx = epx
            cpy = epy
            chqx = cpx
            chqy = cpy
            chcx = (2*cpx) - h2x
            chcy = (2*cpy) - h2y
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == CURVEABS):
            h1x = (float(shape.path[i]) + xOffset)/3.54
            h1y = (float(shape.path[i+1]) + yOffset)/-3.54
            h2x = (float(shape.path[i+2]) + xOffset)/3.54
            h2y = (float(shape.path[i+3]) + yOffset)/-3.54
            epx = (float(shape.path[i+4]) + xOffset)/3.54
            epy = (float(shape.path[i+5]) + yOffset)/-3.54
            curve = cubicBezier([cpx,cpy], [h1x,h1y], [h2x, h2y], [epx, epy])
            i = i + 5
            cpx = epx
            cpy = epy
            chqx = cpx
            chqy = cpy
            chcx = (2*cpx) - h2x
            chcy = (2*cpy) - h2y
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == SMOOTH):
            h1x = chcx
            h1y = chcy
            h2x = (float(shape.path[i+2])/3.54)+cpx
            h2y = (float(shape.path[i+3])/-3.54)+cpy
            epx = (float(shape.path[i+4])/3.54)+cpx
            epy = (float(shape.path[i+5])/-3.54)+cpy
            curve = cubicBezier([cpx,cpy], [h1x,h1y], [h2x, h2y], [epx, epy])
            i = i + 3
            cpx = epx
            cpy = epy
            chqx = cpx
            chqy = cpy
            chcx = (2*cpx) - h2x
            chcy = (2*cpy) - h2y
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == SMOOTHABS):
            h1x = chcx
            h1y = chcy
            h2x = (float(shape.path[i+2]) + xOffset)/3.54
            h2y = (float(shape.path[i+3]) + yOffset)/-3.54
            epx = (float(shape.path[i+4]) + xOffset)/3.54
            epy = (float(shape.path[i+5]) + yOffset)/-3.54
            curve = cubicBezier([cpx,cpy], [h1x,h1y], [h2x, h2y], [epx, epy])
            i = i + 3
            cpx = epx
            cpy = epy
            chqx = cpx
            chqy = cpy
            chcx = (2*cpx) - h2x
            chcy = (2*cpy) - h2y
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == QUADRATIC):
            h1x = (float(shape.path[i])/3.54)+cpx
            h1y = (float(shape.path[i+1])/-3.54)+cpy
            epx = (float(shape.path[i+2])/3.54)+cpx
            epy = (float(shape.path[i+3])/-3.54)+cpy
            curve = quadBezier([cpx,cpy], [h1x,h1y], [epx, epy])
            i = i + 3
            cpx = epx
            cpy = epy
            chqx = (2*cpx) - h1x
            chqy = (2*cpy) - h1y
            chcx = cpx
            chcy = cpy
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == QUADRATICABS):
            h1x = (float(shape.path[i]) + xOffset)/3.54
            h1y = (float(shape.path[i+1]) + yOffset)/-3.54
            epx = (float(shape.path[i+2]) + xOffset)/3.54
            epy = (float(shape.path[i+3]) + yOffset)/-3.54
            curve = quadBezier([cpx,cpy], [h1x,h1y], [epx, epy])
            i = i + 3
            cpx = epx
            cpy = epy
            chqx = (2*cpx) - h1x
            chqy = (2*cpy) - h1y
            chcx = cpx
            chcy = cpy
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == SMOOTHQUAD):
            h1x = chqx
            h1y = chqy
            epx = (float(shape.path[i])/3.54)+cpx
            epy = (float(shape.path[i+1])/-3.54)+cpy
            curve = quadBezier([cpx,cpy], [h1x,h1y], [epx, epy])
            i = i + 1
            cpx = epx
            cpy = epy
            chqx = (2*cpx) - h1x
            chqy = (2*cpy) - h1y
            chcx = cpx
            chcy = cpy
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == SMOOTHQUADABS):
            h1x = chqx
            h1y = chqy
            epx = (float(shape.path[i]) + xOffset)/3.54
            epy = (float(shape.path[i+1]) + yOffset)/-3.54
            curve = quadBezier([cpx,cpy], [h1x,h1y], [epx, epy])
            i = i + 1
            cpx = epx
            cpy = epy
            chqx = (2*cpx) - h1x
            chqy = (2*cpy) - h1y
            chcx = cpx
            chcy = cpy
            pathList[-1].path.extend(curve.list)
            continue
        if (mode == ARC):
            i = i+5
            cpx = (float(shape.path[i])/3.54) + cpx
            i = i+1
            cpy = (float(shape.path[i])/-3.54) + cpy
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue
        if (mode == ARCABS):
            i = i+5
            cpx = (float(shape.path[i]) + xOffset)/3.54
            i = i+1
            cpy = (float(shape.path[i]) + yOffset)/-3.54
            pathList[-1].path.append([cpx,cpy])
            chqx = cpx
            chqy = cpy
            chcx = cpx
            chcy = cpy
            continue

## By this point, we've parsed every shape we extracted from the SVG file. We can
##  now create a new EAGLE .scr file and start adding stuff to it.
scriptName = filename[:-4] + ".scr"

with open(scriptName, 'w') as f:
    ## Preliminaries. We *always* want to be drawing in mm, and wire bend 2 is the
    ##  "here-to-there" mode, rather than any default bends.
    f.write("GRID MM;\n")
    f.write("SET WIRE_BEND 2;\n")
    ## We now need to iterate over the EAGLE path list, setting layers and weights
    ##  and then creating points.
    for path in pathList:
        f.write("LAYER ")
        f.write('{}'.format(path.pathLayer))
        f.write(";\n")
        f.write(path.pathType[0])
        f.write(' {:.3f}'.format(path.pathWeight))
        f.write("\n")
        i = 0
        lastPoint = []
        for point in path.path:
            shortPoint = ['{:.2f}'.format(point[0]), '{:.2f}'.format(point[1])]
            if shortPoint != lastPoint:
                f.write('(')
                f.write(shortPoint[0])
                f.write(' ')
                f.write(shortPoint[1])
                f.write(')\n')
                lastPoint = shortPoint
        ## This last little if statement serves to close paths that may not
        ##  otherwise close, but only if they're polygons.
        if path.pathType == "POLYGON":
            point = path.path[0]
            shortPoint = ['{:.2f}'.format(point[0]), '{:.2f}'.format(point[1])]
            f.write('(')
            f.write(shortPoint[0])
            f.write(' ')
            f.write(shortPoint[1])
            f.write(')\n')
        
        f.write(';\n')
