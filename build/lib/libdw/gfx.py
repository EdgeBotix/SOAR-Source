import util
from soar.io import io
import colors
import time

import sys
import gw
import dw
reload(dw)
import tk
# this file is for integrating graphics with soar, so we know tk has
# been inited.
tk.setInited()

import traceback

class PlotJob():
    def __init__(self, xname, yname, connectPoints,
                 xfunc=None, yfunc=None, 
                 xbounds='auto', ybounds='auto'):
        self.xname = xname
        self.xfunc = xfunc
        self.xbounds = xbounds
        self.yname = yname
        self.yfunc = yfunc
        self.ybounds = ybounds
        self.connectPoints = connectPoints
    def callFunc(self, func, inp):
        if func.func_code.co_argcount == 0:
            return func()
        elif func.func_code.co_argcount == 1:
            return func(inp)
        else:
            sys.stderr.write('Static plot function takes too many arguments')
            return 0.0

class RobotGraphics():
    connectPointsDef = False
    def __init__(self, drawSlimeTrail=False, sonarMonitor=False):
        """
        @param drawSlimeTrail: whether or not to draw slime trail when
        robot is stopped.  Setting drawSlimeTrail='Cheat' will use
        actual rather than sensed pose in the simulator.  Default is
        False.  @param sonarMonitor: whether or not to enable the
        sonar monitor.  Default is False.
        """
        self.tick = 0
        self.drawSlimeTrail = drawSlimeTrail
        self.slimeData = []
        self.slimeWindow = None
        self.plotJobs = []
        self.plotWindows = []
        self.plotWindowIdx = 0
        self.fileTasks = []
        self.plotData = {}
        self.plotData['clocktime'] = []
        self.plotData['step'] = []
        self.traceTasks = []
        self.windowSize = 500
        self.step = 0
        io.registerUserFunction('shutdown', self.reset)
        io.registerUserFunction('step', self.stepPlotting)
        io.registerUserFunction('brainStop', self.plot)
        if sonarMonitor:
            self.enableSonarMonitor()

    def __del__(self):
        if (self.slimeWindow): self.slimeWindow.destroy()
        self.closePlotWindows()

    def clearPlotData(self):
        # Added by lpk
        self.step = 0
        print 'clearing plot data'
        for k in self.plotData.keys():
            print '   key', k, len(self.plotData[k])
            self.plotData[k] = []

    def closePlotWindows(self):
        for w in self.plotWindows:
            w.destroy()
        self.plotWindows = []
    
    def tasks(self):
        return self.traceTasks

    def enableSonarMonitor(self):
        io.sonarMonitor(True)

    def addStaticPlotFunction(self, x=('step', None), y=('step', None),
                              connectPoints = connectPointsDef):
        """
        @param x: function to call for x-axis of static plot 
        @param y: function to call for y-axis of static plot 
        @param connectPoints: Boolean, whether or not to draw lines
        between the points.  Default is False.
        """
        (xname, xfunc)= x
        (yname, yfunc)= y
        if self.plotData.has_key(yname): yfunc = None
        if self.plotData.has_key(xname): xfunc = None
        if xfunc or yfunc:
            self.plotJobs.append(PlotJob(xname, yname, 
                                         connectPoints, 
                                         xfunc, yfunc))
        if yfunc: self.plotData[yname] = []
        if xfunc: self.plotData[xname] = []

    def addDynamicPlotFunction(self, y=('step', None)):
        """
        @param y: function to call for y-axis of dynamic plot
        """
        (name, func) = y
        io.addScopeProbeFunction(name, func)

    def addStaticPlotSMProbe(self, x=('step', None, None, None),
                             y=('step', None, None, None), 
                             connectPoints = connectPointsDef):
        """
        @param x: probe for x-axis of static plot
        @param y: probe for y-axis of static plot
        @param connectPoints: Boolean; whether or not to draw lines
        between the points.  Default is False.
        """
        (yname, ymachine, ymode, yvaluefun) = y
        (xname, xmachine, xmode, xvaluefun) = x
        if ymachine: self.addProbe(y)
        if xmachine: self.addProbe(x)
        self.plotJobs.append(PlotJob(xname, yname, connectPoints))
                                         
    def addDynamicPlotSMProbe(self, y=('step', None, None, None),
                              connectPoints = connectPointsDef):
        """
        @param y: probe for y-axis of dynamic plot
        """
        (yname, ymachine, ymode, yvaluefun) = y
        if ymachine: self.addProbe(y)
        io.addScopeProbeFunction(yname, lambda: self.recentPt(yname))

    def recentPt(self, name):
        try:
            if len(self.plotData[name]) > 0:
                return self.plotData[name][len(self.plotData[name])-1]
            else:
                return 0.0
        except KeyError:
            sys.stderr.write("Name not defined in gfx object: "+name)


    def reset(self):
        self.slimeData = []
        self.plotData.clear()
        self.plotData['clocktime'] = []
        self.plotData['step'] = []
        io.sonarMonitor(False)
        io.clearScope()

    def makeTraceFun(self, machineName, mode, valueFun, stream):
        def traceFun(x):
            stream.append(valueFun(x))
        return traceFun

    def setUpPlotting(self, dataProbes, plotTasks):
        for p in dataProbes:
            self.addProbe(p)
        for (xname, xbounds, yname, ybounds) in dataTasks:
            self.plotJobs.append(PlotJob(xname, yname, connectPoints,
                                         xbounds=xbounds,
                                         ybounds=ybounds))

    def addProbe(self, probe):
        (streamName, machineName, mode, valueFun) = probe
        stream = []
        if not self.plotData.has_key(streamName):
            self.plotData[streamName] = stream
        else:
            sys.stderr.write("Trying to add multiple probes w/ name:"+\
                                 streamName)
        self.traceTasks.append((machineName, mode,
                                self.makeTraceFun(machineName, mode,
                                                  valueFun, stream)))

    def stepPlotting(self):
        if self.drawSlimeTrail:
            odo = io.SensorInput(self.drawSlimeTrail=='Cheat').odometry
            self.slimeData.append(odo.xytTuple())
        self.plotData['clocktime'].append(time.time())
        self.plotData['step'].append(self.step)
        self.step += 1
        inp = io.SensorInput()
        for j in self.plotJobs:
            if j.xfunc: self.plotData[j.xname].append(j.callFunc(j.xfunc, inp))
            if j.yfunc: self.plotData[j.yname].append(j.callFunc(j.yfunc, inp))
                 
    def plot(self):
        if self.drawSlimeTrail:
            self.plotSlime()
        self.doDataPlotJobs()

    def doDataPlotJobs(self):
        self.timeData = self.plotData['clocktime'][:]
        self.stepData = self.plotData['step'][:]
        if len(self.stepData) == 0: return
        self.plotWindowIdx = 0
        for j in self.plotJobs:
            xdata = self.plotData[j.xname]
            ydata = self.plotData[j.yname]
            self.plotDataVersusData(xdata, j.xbounds, ydata, j.ybounds,
                                    j.yname+' versus '+j.xname, j.connectPoints)
        for j in self.plotJobs:
            self.plotData[j.xname] = []

    def plotDataVersusData(self, xData, xBounds, yData, yBounds, name,
                           connectPoints, windowSize = None):
        if not windowSize: windowSize = self.windowSize
        if len(xData) == 0:
            print 'X Data stream', name, 'empty:  skipping plot'
            return
        if len(yData) == 0:
            print 'Y Data stream', name, 'empty:  skipping plot'
            return

        (xLower, xUpper) = self.getBounds(xData, xBounds)
        (yLower, yUpper) = self.getBounds(yData, yBounds)
        
#        if len(self.plotWindows) > self.plotWindowIdx:
#            w = self.plotWindows[self.plotWindowIdx]
#            w.reopenWindow(windowSize, windowSize, 
#                           xLower, xUpper, yLower, yUpper, name)
#            self.plotWindowIdx += 1
#        else:
        w = gw.GraphingWindow(windowSize, windowSize, 
                              xLower, xUpper, yLower, yUpper, name)
        self.plotWindows.append(w)
        if connectPoints:
            w.graphContinuousSet(xData, yData)
        else:
            w.graphPointSet(xData, yData)

    def plotSlime(self):
        maxT = len(self.slimeData)
        if maxT == 0:
            print 'No slime to plot'
            return

        slimeX = [p[0] for p in self.slimeData]
        slimeY = [p[1] for p in self.slimeData]

        (xLower, xUpper, yLower, yUpper) = self.getEquallyScaledBounds(slimeX, 
                                                                       slimeY)
        xRange = xUpper - xLower
        yRange = yUpper - yLower

        if util.within(xRange, 0, 0.001):
            return

        if self.slimeWindow:
            self.slimeWindow.destroy()
        self.slimeWindow = dw.DrawingWindow(\
            self.windowSize, self.windowSize, xLower, xUpper, yLower, yUpper,
            'slime')
        # Draw dimensions
        self.slimeWindow.drawText(xLower + 0.1 * xRange, yLower + 0.05 * yRange,
                                  util.prettyString(xLower), color = "black")
        self.slimeWindow.drawText(xUpper - 0.1 * xRange, yLower + 0.05 * yRange,
                                  util.prettyString(xUpper), color = "black")
        self.slimeWindow.drawText(xLower + 0.05 * xRange, yLower + 0.1 * yRange,
                                  util.prettyString(yLower), color = "black")
        self.slimeWindow.drawText(xLower + 0.05 * xRange, yUpper - 0.1 * yRange,
                                  util.prettyString(yUpper), color = "black")
        # Draw axes
        xMin = min(slimeX)
        xMax = max(slimeX)
        yMin = min(slimeY)
        yMax = max(slimeY)

        self.slimeWindow.drawLineSeg(xMin, yMin, xUpper - 0.1 * xRange, yMin, 
                                     'gray')
        self.slimeWindow.drawLineSeg(xMin, yMin, xMin, yUpper - 0.1 * yRange, 
                                     'gray')

        # Draw slime
        for i in range(maxT):
            self.slimeWindow.drawRobot(slimeX[i], slimeY[i], 
                                       slimeX[i], slimeY[i],
                                       colors.RGBToPyColor(colors.HSVtoRGB(i*360.0/maxT, 1.0, 1.0)),
                                  2)

    def getBounds(self, data, bounds):
        if bounds == 'auto':
            upper = max(data)
            lower = min(data)
            if util.within(upper, lower, 0.0001):
                upper = 2*lower + 0.0001
            boundMargin = util.clip((upper - lower) * 0.1, 1, 100)
            return ((lower - boundMargin) , (upper + boundMargin))
        else:
            return bounds

    def getEquallyScaledBounds(self, xData, yData):
        xMax = max(xData)
        xMin = min(xData)
        yMax = max(yData)
        yMin = min(yData)
        xRange = xMax - xMin
        yRange = yMax - yMin
        if xRange > yRange:
            yMax = yMin + xRange
        else:
            xMax = xMin + yRange
        
        boundMargin = (xMax - xMin) * 0.1
        return (xMin - boundMargin , xMax + boundMargin,
                yMin - boundMargin, yMax + boundMargin)
