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
