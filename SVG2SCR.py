from HTMLParser import HTMLParser
import os, sys, re, math

## Filename specification section. Can be an absolute path, a relative path, or
##  by using sys.argv[1], can be a file which is dropped onto the script.
filename = sys.argv[1]
##filename = "filename_here.svg"

## this class represents the raw data plucked from the SVG file. 
class SVGPath:
    ## constructor- called whenever a copy of SVGPath is created.
    def __init__(self):
        self.xOffset = 0     ## Floating point values, in mm, of the offset of
        self.yOffset = 0     ##  the current path. Note that values in the SVG
                             ##  file are all given in px, and 1mm ~= 3.54px.
                             ##  This offset is ONLY local- there may be other
                             ##  offsets that get applied as well.
        self.pathType = []   ## Do we want to create a polygon or just a wire
                             ##  in the EAGLE script? Defined by whether the
                             ##  path is filled (fill color has no impact) or
                             ##  not.
        self.pathWeight = 0  ## Thickness of the line, in mm, to be created in
                             ##  the EAGLE script. Defined in the SVG file by
                             ##  the thickness of the path. 0 thickness is
                             ##  allowed.
        self.pathLayer = 1   ## The layer of the line in the EAGLE script. See
                             ##  EAGLE for more info on this; some common layers
                             ##  are 1 (top copper), 2 (bottom copper), 20
                             ##  (dimensions), 21 (top silk) and 22 (bottom
                             ##  silk). This data is encoded by the red value of
                             ##  the stroke- by default it will be set to 20, if
                             ##  the red value of the stroke is 0.
        self.path = []       ## This is a list containing the actual path data.
                             ##  we strip away all the white space and commas
                             ##  before packing it away here.

    ## display() is a handy little debugging tool that lets you print out the
    ##  packed values in an SVGPath class object.
    def display(self):
        print self.pathType[0], "Weight:", self.pathWeight, \
                "Layer:", self.pathLayer
        print "Offset:", self.xOffset, self.yOffset
        print self.path

## We use a re-defined instance of the HTMLParser class to scan the SVG doc and
##  make some sense of it. It turns out SVG stores all the data in the tag, so
##  there's no need to implement anything but a handle_starttag() function.
class SvgParser(HTMLParser):

    pathData = []   ## This empty list will be populated with SVGPath class
                    ##  objects as they are discovered in the SVG file.
    xOffset = 0     ## These values will be populated based on the information
    yOffset = 0     ##  found in the <g> tag (which defines the X and Y offset
                    ##  of all paths in a group), and a Y offset
                    ##  based on the dimensions of the document from the <svg>
                    ##  tag. NB- Inkscape puts the origin in the lower left but
                    ##  SVG treats the upper left as the origin; thus, to get
                    ##  the EAGLE path to look right, we have to multiply all
                    ##  Y coordinates by -1 and then add the Y dimension of the
                    ##  drawing as an offset. :-P

    ## Re-implement the handle_starttag function for our purposes. We're
    ##  interested in three tags: <path>, <g>, and <svg>. The <svg> tag contains
    ##  info on the size of the document, and that is important for reasons
    ##  discussed above. <g> contains info about groups, and while this script
    ##  assumes that none of the paths are in sub-groups, Inkscape creates one
    ##  big master group which it uses to define each layer, so we need to worry
    ##  about at least one (although we're going to say "no groups and one layer
    ##  only" in the spec for SVG files to run through this script). Finally,
    ##  <path> defines the actual path itself. All of these tags have all of
    ##  their "data" defined within the attributes ("attrs") of the tag itself,
    ##  so we only need to iterate over the list of attributes to figure out
    ##  what we need to do.
    def handle_starttag(self, tag, attrs):
        ## Following both logic and likely order-of-encounter in the document,
        ##  let's deal with the <svg> tag first:
        if tag == 'svg':
            ## attrs is a list of all the attributes contained within that tag.
            ##  Attributes typically take the form 'attr_name="attr_value"', and
            ##  attrs is a list of two-element lists, where element 0 of the
            ##  individual element in attrs is the attribute name and element 1
            ##  is the value associated with it, both expressed as a string
            ##  irrespective of the nature of the data. We will iterate over
            ##  this list, check for attributes we are interested in, and take
            ##  some action with those attributes.
            for i in attrs:
                ## We only really care about one thing in the <svg> tag: the
                ##  height of the document. We need to make that into a float
                ##  and subtract it from the overall yOffset because of the dumb
                ##  "lower-left" origin thing in Inkscape.
                if i[0] == 'height':
                    self.yOffset = self.yOffset - float(i[1])

        ## Next, let's handle the <g> tag. We only expect to see one of these-
        ##  if our users can't adhere to the spec that's not our problem. The
        ##  one we expect to see represents the supergroup that Inkscape uses
        ##  to define a "layer", and there will ALWAYS be at least one layer in
        ##  an Inkscape SVG.
        if tag == 'g':
            ## See above for a discussion of attrs and our iteration over it.
            for i in attrs:
                ## The attribute within <g> that we care about is a "transform"
                ##  of type "translate". The syntax for such a thing is
                ##  'transform="translate(x,y)". We first look for "transform"
                ##  in the name field of each item in the attrs list...
                if i[0] == "transform":
                    ## ...and then look to make sure it is a "translate"
                    ##  transform (other types of transforms are defined but
                    ##  disallowed by our specification; Inkscape doesn't appear
                    ##  to make heavy use of them anyway)...
                    if "translate" in i[1]:
                        ## ...and finally, pluck the numeric values out of the
                        ##  string, split them in two around the comma, and
                        ##  convert them to floating point.
                        self.xOffset = float(i[1][10:-1].split(',')[0])
                        self.yOffset = self.yOffset + \
                                float(i[1][10:-1].split(',')[1])

        ## Last of all we'll start discovering paths. Each path will have two,
        ##  maybe three, attributes that we are interested in: "d", "style", and
        ##  POSSIBLY a "transform" similar to the one discussed above.
        if tag == "path":
            ## With each new path we discover, we want to append the list of
            ##  paths that exists in this class to include one more. We'll
            ##  spend the rest of this path parsing session referring simply to
            ##  the last path in the list.
            self.pathData.append(SVGPath())
            ## See above for a discussion of attrs and our iteration over it.
            for i in  attrs:
                ## The meat is in the "d" attribute. This is the actual path
                ##  data and its format is too complex to get too into here.
                ##  Briefly, it will be a series of single-character commands
                ##  followed by numerical values seperated by either a space or
                ##  a comma. We want to parse each one of those items into its
                ##  own seperate list entry...
                if i[0] == "d":
                    ## ...so we use re.findall() (a function of the regular
                    ##  expression library, which is also too complex to get
                    ##  into here) to generate a list of items broken apart by
                    ##  commas or spaces, then we extend the empty path list
                    ##  with the values in that list. Shrewd observers will note
                    ##  that we've created another problem here- the items in
                    ##  that list are all strings, but we need at least some
                    ##  of them to be floating point values to express the
                    ##  coordinate data of each point. We'll cope with that
                    ##  later.
                    self.pathData[-1].path.extend(re.findall(r'[^,\s]+',i[1]))
                ## The "style" attribute defines thigs like opacity, line
                ##  weight, fill and line colors, etc etc. We use it to encode
                ##  the type of entity we're going to create (a polygon or an
                ##  outline, depending on whether the fill is "none" or not),
                ##  the line weight (directly converts to thickness in EAGLE),
                ##  and the layer it'll be drawn in (based on the red channel of
                ##  the RGB color of the stroke). The crappy thing is, the
                ##  attribute data is just one long string formatted as
                ##  "style1:value1;style2:value2;style3:value3" etc etc, so we
                ##  need to break it up a bit.
                if i[0] == "style":
                    ## Start with an empty list...
                    temp = []
                    ## ...and then populate it with the various items from the
                    ##  string by splitting them around the semicolons.
                    temp.extend(i[1].split(';'))
                    for i in temp:
                        ## "fill" tells us whether we're dealing with a
                        ##  polygon or just a path. If there's ANYTHING as a
                        ##  fill at all, we're treating it as a polygon. NB:
                        ##  the colon is included because there may be more than
                        ##  one style entry that contains the string "fill".
                        ##  This is true for all three of the style items we're
                        ##  looking for.
                        if "fill:" in i:
                            if (i != "fill:none"):
                                self.pathData[-1].pathType.append("POLYGON")
                            else:
                                self.pathData[-1].pathType.append("WIRE")
                        ## "stroke" encodes the layer in the red value.
                        if "stroke:" in i:
                            ## The red value is two characters buried in this
                            ##  string, and is expressed as a hex value, so we
                            ##  must first extract those characters and then
                            ##  convert them to a base 10 integer value.
                            self.pathData[-1].pathLayer = int(i[-6:-4],16)
                            ## A sanity check- if the user neglected to set a
                            ##  layer, be a pal and assume that "dimension" is a
                            ##  good layer to stick it on. This saves an error
                            ##  in EAGLE later.
                            if self.pathData[-1].pathLayer == 0:
                                self.pathData[-1].pathLayer = 20
                        ## "stroke-width" encodes the line thickness. The syntax
                        ##  here is "stroke-width:Npx" where 'N' represents a
                        ##  floating point number of arbitrary precision. We'll
                        ##  pluck the digits out of the middle of that string,
                        ##  convert to mm and store it away.
                                re.findall(r'\d+\.*\d*',i)[0]
                        if "stroke-width:" in i:
                            ##print re.findall(r'\d+\.*\d*',i)[0]
                            self.pathData[-1].pathWeight = \
                                    float(re.findall(r'\d+\.*\d*',i)[0])/3.54
                ## The last attribute in the <path> tag that we need to be
                ##  concerned with is "transform". There MAY not be a transform
                ##  attribute; in that case, we'll just never worry about it.
                ##  However, if there IS a transform attribute, we need to
                ##  account for that and store away the x and y offsets implied
                ##  by that transform. For more info on how this is done, see
                ##  the comments for the <g> tag above.
                if i[0] == "transform":
                    if "translate" in i[1]:
                        self.pathData[-1].xOffset = \
                                float(i[1][10:-1].split(',')[0])
                        self.pathData[-1].yOffset = \
                                float(i[1][10:-1].split(',')[1])
                        
## Okay, now we're done with the preliminaries. This is where the actual meat
##  of the operation occurs.

## this class represents the massaged data ready to be sent to EAGLE. 
class EAGLEPath:
    ## constructor- called whenever a copy of EAGLEPath is created.
    def __init__(self):
        self.pathType = []   ## "POLYGON" or "WIRE".
        self.pathWeight = 0  ## Thickness of the line, in mm, to be created in
                             ##  the EAGLE script. Defined in the SVG file by
                             ##  the thickness of the path. 0 thickness is
                             ##  allowed.
        self.pathLayer = 1   ## The layer of the line in the EAGLE script. See
                             ##  EAGLE for more info on this; some common layers
                             ##  are 1 (top copper), 2 (bottom copper), 20
                             ##  (dimensions), 21 (top silk) and 22 (bottom
                             ##  silk). This data is encoded by the red value of
                             ##  the stroke- by default it will be set to 20, if
                             ##  the red value of the stroke is 0.
        self.path = []       ## This is a list containing the actual points for
                             ##  the lines that will be drawn in EAGLE. All
                             ##  offsets will be applied before data goes in
                             ##  here- this is absolute coordinate data and each
                             ##  item in this list is one X Y pair.

## This class is implemented to create a list of points to interpolate a cubic
##  Bezier into a list of sub-lines. It takes as an argument to the
##  constructor the four points needed to calculate points within the curve,
##  approximates the length of the Bezier (the approximation method is detailed
##  at http://steve.hollasch.net/cgindex/curves/cbezarclen.html; it's the 
class cubicBezier:
    ## constructor
    def __init__(self, sp, h1, h2, ep):
        self.list = [sp]
        spx = sp[0]
        spy = sp[1]
        h1x = h1[0]
        h1y = h1[1]
        h2x = h2[0]
        h2y = h2[1]
        epx = ep[0]
        epy = ep[1]

        sph1 = math.sqrt(((spx-h1x)*(spx-h1x)) + ((spy-h1y)*(spy-h1y)))
        h1h2 = math.sqrt(((h1x-h2x)*(h1x-h2x)) + ((h1y-h2y)*(h1y-h2y)))
        h2ep = math.sqrt(((h2x-epx)*(h2x-epx)) + ((h2y-epy)*(h2y-epy)))
        spep = math.sqrt(((spx-epx)*(spx-epx)) + ((spy-epy)*(spy-epy)))

        L1 = sph1 + h1h2 + h2ep
        L0 = spep

        length = .5*L0 + .5*L1
        error = L1-L0
        
        point = [0,0]
        segments = int(math.ceil(length))
        if segments < 16:
            segments = 16
        p = 1.0/segments
        ##for pts in range(1,int(math.ceil(length))):
        for pts in range(1,segments+1):
            t = pts*p
            u = 1-t
            tt = t*t
            uu = u*u
            uuu = uu * u
            ttt = tt * t
            point[0]=((uuu*sp[0])+(3*uu*t*h1x)+(3*u*tt*h2x)+(ttt*epx))
            point[1]=((uuu*sp[1])+(3*uu*t*h1y)+(3*u*tt*h2y)+(ttt*epy))
            self.list.append([point[0],point[1]])

## This class is implemented to create a list of points to interpolate a 
##  quadratic Bezier into a list of sub-lines. It takes as an argument to the
##  constructor the three points needed to calculate points within the curve.
##  The method used to determine the length of the Bezier is detailed at
##  http://segfaultlabs.com/docs/quadratic-bezier-curve-length.
class quadBezier:
    ## constructor
    def __init__(self, sp, h1, ep):
        self.list = [sp]
        spx = sp[0]
        spy = sp[1]
        h1x = h1[0]
        h1y = h1[1]
        epx = ep[0]
        epy = ep[1]

        ax = sp[0] - 2*h1x + epx
        ay = sp[1] - 2*h1y + epy
        bx = -2*sp[0] + 2*h1x
        by = -2*sp[1] + 2*h1y
        A = 4*(ax*ax + ay*ay)
        B = 4*(ax*bx + ay*by)
        C = bx*bx + by*by

        Sabc = 2*math.sqrt(A+B+C)
        A2 = math.sqrt(A)
        A32 = 2*A*A2
        C2 = 2*math.sqrt(C)
        BA = B/A2

        length = ((A32*Sabc) + ((A2*B)*(Sabc-C2)) + 
                  ((4*C*A)-(B*B))*math.log(((2*A2)+BA+Sabc)/(BA+C2)))/(4*A32)
        
        point = [0,0]
        segments = int(math.ceil(length))
        if segments < 16:
            segments = 16
        p = 1.0/segments
        ##for pts in range(1,int(math.ceil(length))):
        for pts in range(1,segments+1):
            t = pts*p
            u = 1-t
            tt = t*t
            uu = u*u
            point[0]=((uu*sp[0])+(2*u*t*h1x)+(tt*epx))
            point[1]=((uu*sp[1])+(2*u*t*h1y)+(tt*epy))
            self.list.append([point[0],point[1]])

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

    
## Constants for the various letter commands one may find in a path. A path is
##  defined by a series of operations (each of which is defined by a single
##  character) along with a set of parameters for those operations. The number
##  of parameters is specific to each particular command, and parameters may
##  be seperated by whitespace or commas, although there is no requirement for
##  whitespace or a comma between commands and parameters.
MOVE            = 0     ## m (relative MOVETO)- lift the pen and put it here.
                        ##  When it appears as the first item in a path, this
                        ##  should be treated as absolute. After a MOVETO is
                        ##  executed, subsequent coordinate pairs should be
                        ##  treated as LINETO parameters; they will be absolute
                        ##  if the MOVETO was absolute or relative if the MOVETO
                        ##  was relative. However, if the MOVETO is absolute
                        ##  only because it was the first command in a path,
                        ##  these implicit LINETO points will be relative.
                        ##  After a MOVETO, the next two values give the x and y
                        ##  coordinates for the MOVETO.
MOVEABS         = 1     ## M (absolute MOVETO)- absolute version of MOVETO. 
                        ##  Absolute is misleading- this is absolute only after
                        ##  all previous translations have been applied.
LINE            = 2     ## l (relative LINETO)- can be omitted if the last
                        ##  command was a MOVETO. Otherwise, next two points are
                        ##  the x and y offset from the current pen position.
LINEABS         = 3     ## L (absolute LINETO)
LINEH           = 4     ## h (relative horizontal LINETO)- the next point is a
                        ##  horizontal offset from the current point.
LINEHABS        = 5     ## H (absolute horizontal LINETO)
LINEV           = 6     ## v (relative vertical LINETO)
LINEVABS        = 7     ## V (absolute vertical LINETO)
CURVE           = 8     ## c (relative cubic Bezier CURVETO)- the specifics of
                        ##  Bezier curves definition is too complex to go into
                        ##  here; we simply model them as straight lines (since
                        ##  EAGLE can't do Bezier curves anyway). Each Bezier
                        ##  in an SVG is defined by six parameters; the last two
                        ##  are the x and y of the end point.
CURVEABS        = 9     ## C (absolute cubic Bezier CURVETO)
SMOOTH          = 10    ## s (relative cubic Bezier SMOOTH CURVETO)- a simpler
                        ##  version of the full cubic CURVETO, this one only has
                        ##  four parameters per curve. The last two are x and y.
SMOOTHABS       = 11    ## S (absolute cubic Bezier SMOOTH CURVETO)
QUADRATIC       = 12    ## q (relative quadratic Bezier CURVETO)- takes four
                        ##  parameters; the last two are x and y.
QUADRATICABS    = 13    ## Q (absolute quadratic Bezier CURVETO)
SMOOTHQUAD      = 14    ## t (relative smooth quadratic Bezier CURVETO)- next
                        ##  two parameters are the next x and y.
SMOOTHQUADABS   = 15    ## T (absolute smooth quadratic Bezier CURVETO)
ARC             = 16    ## a (relative elliptical ARC)- defines an arc using
                        ##  the x and y radii, rotation, how much of a complete
                        ##  arc is drawn and which direction it is drawn in.
                        ##  As always, we only care about the x,y of the end
                        ##  of the arc, and those are the 6th and 7th
                        ##  parameters.
ARCABS          =17     ## A (absolute elliptical ARC)

pathList = []
for shape in parser.pathData:
    pathList.append(EAGLEPath())
    xOffset = shape.xOffset + parser.xOffset
    yOffset = shape.yOffset + parser.yOffset
    pathList[-1].pathType.extend(shape.pathType)
    pathList[-1].pathWeight = shape.pathWeight
    pathList[-1].pathLayer = shape.pathLayer
    ## This while loop looks awkward but there's a reason: we aren't going to
    ##  look at every item in the list, and sometimes we'll want to skip forward
    ##  by more items than others. Doing it this way lets us do that easily.
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

scriptName = filename[:-4] + ".scr"

with open(scriptName, 'w') as f:
    f.write("GRID MM;\n")
    f.write("SET WIRE_BEND 2;\n")
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
            shortPoint = ['{:.6f}'.format(point[0]), '{:.6f}'.format(point[1])]
            if shortPoint != lastPoint:
                f.write('(')
                f.write(shortPoint[0])
                f.write(' ')
                f.write(shortPoint[1])
                f.write(')\n')
                lastPoint = shortPoint
        point = path.path[0]
        shortPoint = ['{:.6f}'.format(point[0]), '{:.6f}'.format(point[1])]
        f.write('(')
        f.write(shortPoint[0])
        f.write(' ')
        f.write(shortPoint[1])
        f.write(')\n')
        
        f.write(';\n')
