from HTMLParser import HTMLParser
from SVGPath import SVGPath
import re

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
                    ## Sometimes, particularly with files that come from Adobe
                    ##  illustrator, the height will be denoted with a trailing
                    ##  "px". If that's the case, we need to ignore it.
                    if "px" in i[1]:
                        self.yOffset = self.yOffset - float(i[1][0:-2])
                    else:
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

                    ## Some tools do not add spaces or commas around the
                    ## command characters. This re.sub command is supposed
                    ## to resolve this.
                    temp = re.sub(r"(M|L|H|V|C|S|Q|T|A|Z)", r" \1 ", i[1],
                                    flags=re.IGNORECASE)

                    ## Some tools do not separate numbers followed by a negative
                    ## number. This re.sub command is supposed to resolve this
                    ## specific issue.
                    temp = re.sub(r"([0-9]+)(-[0-9+])", r"\1 \2", temp)

                    self.pathData[-1].path.extend(re.findall(r'[^,\s]+',temp))
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
                                self.pathData[-1].pathType="POLYGON"
                            else:
                                self.pathData[-1].pathType="WIRE"
                        ## "stroke" encodes the layer in the red value.
                        if "stroke:" in i:
                            ## The red value is two characters buried in this
                            ##  string, and is expressed as a hex value, so we
                            ##  must first extract those characters and then
                            ##  convert them to a base 10 integer value.
                            ##  If the user hasn't made a stroke style yet, we
                            ##  need to catch that.
                            if "none" in i:
                                print "You didn't specify a stroke somewhere!"
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
