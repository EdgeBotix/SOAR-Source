"""
Utility procedures for manipulating colors
"""

from math import log, floor
import util

# h in [0, 360]
# s in [0, 1]
# v in [0, 1]

# returns values in [0,1]

def HSVtoRGB(h, s, v):
    """
    Convert a color represented in hue, saturation, value space into
    RGB space.
    @param h: hue, in range (0, 360)
    @param s: saturation, in range (0, 1)
    @param v: value, in range (0, 1)
    @returns: (r, g, b) with each value in the range (0, 1)
    """
    if s == 0:
        # achromatic (grey)
        return (v, v, v)
    else:
        h = h/60  # sector 0 to 5
	i = floor( h )
	f = h - i	# factorial part of h
	p = v * ( 1 - s )
	q = v * ( 1 - s * f )
	t = v * ( 1 - s * ( 1 - f ) )
        if i == 0:
            return (v, t, p)
        elif i == 1:
            return (q, v, p)
        elif i == 2:
            return (p, v, t)
        elif i == 3:
            return (p, q, v)
        elif i == 4:
            return (t, p, v)
        else:
            return (v, p, q)

redHue = 0.0
greenHue = 120.0
blueHue = 240.0
yellowHue = 60.0

def probToPyColor(p, uniformP = 0.5, upperVal = None):
    """
    Converts a probability to a Python color.  Probability equal to
    uniform converts to black.  Closer to 1 is brighter blue; closer
    to 0 is brighter red.
    @param p: probability value in range (0, 1)
    @param uniformP: probability value that will be colored black
    @param upperVal: in situations when there are lots of choices and
    so the highest reasonable value to occur is nowhere near 1, it can
    be useful to set this to the highest probability value you expect,
    in order to get some useful visual dynamic range.
    @returns: A Python color
    """

    if upperVal == None:
        upperVal = uniformP * 2
    if p > uniformP:
        return RGBToPyColor(HSVtoRGB(blueHue, 1.0,
                         min(1.0, ((p - uniformP)/(upperVal - uniformP))**0.5)))
    else:
        return RGBToPyColor(HSVtoRGB(redHue, 1.0,
                                     min(1.0, ((uniformP - p)/uniformP)**2)))


# Want 1, 1 when p = 0.5
# Want 1, 0 when p = 1
# Want 0, 1 when p = 0
def probToMapColor(p, hue = yellowHue):
    """
    @param p: probability value
    @returns: a  Python color that's good for mapmaking.  It's yellow
    when p = 0.5, black when p = 1, white when p = 1.
    """
    m = 0.51
    x = p - 0.5
    v = util.clip(2*(m - x), 0, 1)
    s = util.clip(2*(m + x), 0, 1)
    return RGBToPyColor(HSVtoRGB(hue, s, v))


def rootToPyColor(p, minV, maxV):
    """
    Color map for making root-locus plots
    """
    if p < 1:
        # v from 0.3 to 1 as p goes from 1 to minV
        return RGBToPyColor(HSVtoRGB(greenHue, 1.0,
                                     0.3 + 0.7*(1 - (p - minV)/(1 - minV))))
    else:
        # v from 0.2 to 1 as p goes from 1 to maxV
        return RGBToPyColor(HSVtoRGB(redHue, 1.0,
                                     0.2 + 0.8*(1 - (maxV - p)/(maxV - 1))))


def RGBToPyColor(colorVals):
    """
    @param colorVals: tuple (r, g, b) of values in (0, 1) representing
    a color in rgb space
    @returns: a python color string
    """
    (r, g, b) = [floor(c*255.99) for c in colorVals]
    return '#%02x%02x%02x' % (r, g, b)

def safeLog(v):
    """
    Log, but it returns -1000 for arguments less than or equal to 0.
    """
    if v > 0:
        return log(v)
    else:
        return -1000
