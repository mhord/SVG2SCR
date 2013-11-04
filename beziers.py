import math

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
