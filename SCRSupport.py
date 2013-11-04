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
