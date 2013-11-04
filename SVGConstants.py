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
