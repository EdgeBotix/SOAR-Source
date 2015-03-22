 #############################soar/outputs/eBot.py#############################
# soar3.0
#  / outputs/eBot.py
# (C) 2014 EdgeBotix
################################################################################

####################################Imports#####################################
from time import *
import os
import sys
import math
from math import pi

if os.name == 'nt':
    try:
        import _winreg as winreg

    except:
        pass

from form.parallel import Stepper, SharedVar
from form.common import skip, clip, CancelGUIAction

debug = skip

#import traceback
#import getopt

#import traceback

#from Tkinter import *
#import Tkinter
#import tkMessageBox
#import serial

EBOT_POINTS = [(-0.04, -0.029),
               (-0.04, 0.005),
               (-0.016, 0.029),
               (0.016, 0.029),
               (0.04, 0.005),
               (0.04, -0.029), ]
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),
# (0.04   ,   -0.029),]


####################################Settings####################################
import form.settings as settings
import glob

MAX_TRANS, MAX_ROT = 0.5, 5
# these values match the default on the robots
#MAX_TRANS = 0.75
#MAX_ROT = 1.75 # on robot, 100 deg/s
METER_SCALE, RADIAN_SCALE = 0.001, 2 * pi / 4095.0


class Struct:
    def __init__(self, **entries): self.__dict__.update(entries)


Enum = Struct


# eBot Connection State
(
    STATE_NO_SYNC,
    STATE_SYNC,
    #STATE_FIRST_SYNC,
    #STATE_SECOND_SYNC,
    STATE_READY
) = range(3)

# eBot Connection Setup commands
# E, O
CMD_SYNC_SEND = Enum(
    CHECK1=0x45,
    CHECK2=0x4F,
)
# B, T
CMD_SYNC_RECV = Enum(
    CHECK1=0x42,
    CHECK2=0x54,
)

#eBot Commands - command to send data, or receive data
CMD = Enum(
    SEND=0x53,
    RECV=0x52,
    CLOSE=0x58,
    #CLOSE="PORT CLOSE",
)

# P2OS Command Argument Types
ArgType = Enum(
    ARGINT=0x3B,
    ARGNINT=0x1B,
    ARGSTR=0x2B,
)

# P2OS Commands
ArcosCmd = Enum(
    PULSE=0,
    OPEN=1,
    CLOSE=2,
    POLLING=3,
    ENABLE=4,
    SETA=5,
    SETV=6,
    SETO=7,
    MOVE=8,
    ROTATE=9,
    SETRV=10,
    VEL=11,
    HEAD=12,
    DHEAD=13,
    SAY=15,
    JOYREQUEST=17,
    CONFIG=18,
    ENCODER=19,
    RVEL=21,
    DCHEAD=22,
    SETRA=23,
    SONAR=28,
    STOP=29,
    DIGOUT=30,
    VEL2=32,
    GRIPPER=33,
    ADSEL=35,
    GRIPPERVAL=36,
    GRIPREQUEST=37,
    IOREQUEST=40,
    TTY2=42,
    GETAUX=43,
    BUMPSTALL=44,
    TCM2=45,
    JOYDRIVE=47,
    SONARCYCLE=48,
    HOSTBAUD=50,
    AUX1BAUD=51,
    AUX2BAUD=52,
    AUX3BAUD=53,
    E_STOP=55,
    M_STALL=56,
    GYROREQUEST=58,
    LCDWRITE=59,
    TTY4=60,
    GETAUX3=61,
    TTY3=66,
    GETAUX2=67,
    CHARGE=68,
    RESET=254,
    MAINTENANCE=255,
)


# ActiveRobots P2OS Interface
# Provides a python interface to an ActiveMedia Robot over an RS232 link.
class eBot:
    # Initialise connection to pioneer on specified port
    def __init__(self):
        try:
            from soar.serial import Serial
        except ImportError:
            print "You are missing some serial support libraries. Probably you are on windows and you need to get pywin32. Check out http://sourceforge.net/projects/pywin32/ for details."
            raise CancelGUIAction
        self.portName = -1
        self.sonarsChanged = [0, 0, 0, 0, 0, 0, 0, 0]  #Change to 6 after
        self.from_update = 0
        self.connectionState = STATE_NO_SYNC
        self.port = None
        self.lastxpos, self.lastypos = 0, 0
        self.storedsonars = SharedVar([0, 0, 0, 0, 0, 0, 0, 0])  #Change to 6 after
        self.trans, self.rot = SharedVar(0), SharedVar(0)
        self.odpose = SharedVar((0, 0, 0))
        self.stalled = SharedVar(False)
        self.analogInputs = SharedVar([0, 0, 0, 0])
        self.analogOut = SharedVar(0)
        self.asynchronous = True
        self.zero_recv_cnt = 0  # Added -> Not in pioneer
        self.setters = {"motorOutput": self.motorOutput,
                        "discreteMotorOutput": self.discreteMotorOutput,
                        "say": self.cmdSay,
                        "analogOutput": self.analogOutput,
                        "setMaxEffectiveSonarDistance": self.setMaxEffectiveSonarDistance,
                        "enableAccelerationCap": self.enableAccelerationCap,
                        "setMaxVelocities": self.setMaxVelocities}
        self.getters = {"pose": self.odpose.get,
                        "sonarDistances": self.storedsonars.get,
                        "stalled": self.stalled.get,
                        "analogInputs": self.analogInputs.get}
        debug("eBot variables set up", 2)
        self.serialReady = False

        try:
            self.connect(Serial)
            self.open()
            debug("Serial Connection started", 2)
            print "eBot connection successful"
        except:
            sys.stderr.write("Couldn't connect to eBot.\n")
            sys.stderr.write("- Check if eBot is on, paired and connected. If not, power up and try again. \n")
            #sys.stderr.write("- Check to see if COM port below is eBot. If not, remove device and try again. \n")
            debug("Could not open the serial port", 0)
            raise CancelGUIAction("Error opening serial port")

        app.soar.addFlowTriplet((self.startmoving, self.update, self.stopmoving))
        self.currentthread = None
        self.acceptMotorCmds = False
        self.startSerialThread()

    def destroy(self):
        self.stopSerialThread()
        sleep(0.2)
        if (self.serialReady):
            #self.cmdEnable(0)
            self.stopmoving()
            self.sendOutputs()
            self.sendPacket([CMD.CLOSE])
        #    self.flushSerialPort()
        try:
            self.port.close()
        except:
            pass
        app.soar.removeFlowTriplet((self.startmoving, self.update, self.stopmoving))

    # yes, this is repeated code, and should be neater.  you fix it.
    def initGlobals(self, dummy):
        self.stopSerialThread()
        sleep(0.2)
        #if self.serialReady:
            #self.cmdEnable(0)
            #self.stopmoving()
            #self.sendPacket([ArcosCmd.CLOSE])
        self.connectionState = STATE_NO_SYNC
        self.sonarsChanged = [0, 0, 0, 0, 0, 0, 0, 0]
        from soar.serial import Serial
        self.connect(Serial)
        self.open()
        #self.cmdEnable(1)
        self.startSerialThread()
        self.odpose.set((0.0, 0.0, 0.0))

    def getOpenPorts(self):
        """
            This Function Returns a list of tuples with the port number and its description. Used for Windows only
        """
        path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
        ports = []
        #maximum 256 entries, will break anyways
        for i in range(256):
            try:
                val = winreg.EnumValue(key, i)
                port = (str(val[1]) , str(val[0]))
                ports.append(port)
            except Exception:
                winreg.CloseKey(key)
                break
        #return ports
        #ports = getOpenPorts()
        devicePorts = []
        for port in ports:
            #Just because it is formatted that way...
            if 'BthModem' in port[1][8:] or 'VCP' in port[1][8:] or 'ProlificSerial'in port[1][8:]:
                devicePorts.append( (int(port[0][3:]) - 1))
        return devicePorts

    def connect(self, Serial):
        baudRate = 115200
        ports = []
        if os.name == "posix":
            if sys.platform == "linux2":
                #usbSerial = glob.glob('/dev/ttyUSB*')
                print "Support for this OS is under development."
            elif sys.platform == "darwin":
                ports = glob.glob('/dev/tty.eBot*')
                #usbSerial = glob.glob('/dev/tty.usbserial*')
            else:
                print "Unknown posix OS."
                sys.exit()
        elif os.name == "nt":
            ports = self.getOpenPorts()
            #ports = ['COM' + str(i + 1) for i in range(256)]
            #EBOT_PORTS = getEBotPorts()

        connect = 0
        ebot_ports = []
        ebot_names = []
        for port in ports:
            try:
                s = Serial(port, baudRate, timeout=1, writeTimeout=1)
                s._timeout = 1.0
                s._writeTimeout = 1.0
                #try:
                #    s.open()
                #except:
                #    continue
                line = "aaaa"
                while line[:2] != "eB":
                    if (s.inWaiting()>0):
                        line = s.readline()
                    s.write("<<1?")
                    sleep(0.5)

                    line = s.readline()
                    if (line[:2] == "eB"):
                        ebot_ports.append(port)
                        ebot_names.append(line)
                        connect = 1
                        self.port = s
                        self.portName = port
                        self.port._timeout = 1.0
                        self.port._writeTimeout = 1.0
                        self.port.flushInput()
                        self.port.flushOutput()
                if (line[:2] == "eB"):
                    break
                    #s.close()
#                    self.
            except:
                try:
                    if s.isOpen():
                        s.close()
                except:
                    pass

        if (connect == 0):
            try:
                self.port.close()
            except:
                pass
            #sys.stderr.write("Could not open serial port.  Is robot turned on and connected?\n")
            raise Exception("No Robot Found")



    # Open connection to robot
    def open(self):

        numAttempts = 3

        timeout = 5.0
        startt = time()
        while (self.connectionState != STATE_READY):
            if (self.connectionState == STATE_NO_SYNC):
                self.sendPacket([CMD_SYNC_SEND.CHECK1])
            elif (self.connectionState == STATE_SYNC):
                self.sendPacket([CMD_SYNC_SEND.CHECK2])
                self.connectionState = STATE_READY
                break
            #elif (self.connectionState == STATE_READY):
            #  pass

            try:
                pkt = self.recvPacket()
            except:
                if (self.connectionState == STATE_NO_SYNC and numAttempts >= 0):
                    numAttempts -= 1
                else:
                    self.port.close()
                    sys.stderr.write("Could not open serial port.  Is robot turned on and connected?\n")
                    raise Exception("No Robot Found")
                continue

            if (pkt[3] == CMD_SYNC_RECV.CHECK1):
                self.connectionState = STATE_SYNC
                # elif (pkt[3]==CMD_SYNC_RECV.CHECK2):
                #   self.connectionState = STATE_READY
            if (time() - startt) > timeout:
                self.port.close()
                sys.stderr.write("Robot needs to be reset.\n")
                raise Exception("Bad Robot State")

        sleep(.01)
        try:
            self.port.write('A')
        except:
            sys.stderr.write("Could not write to serial port.\n")
            self.serialReady = False
            app.soar.closeEBot()
            sys.stderr.write("Robot turned off or no longer connected.\nDead reckoning is no longer valid.\n")

        #changed = [0, 0, 0, 0, 0, 0]
        #while 0 in changed:
        #    #self.cmdPulse()
        #    self.sipRecv()
        #    self.storedsonars.get()
        #    changed = [changed[i] or self.sonarsChanged[i] for i in range(len(changed))]
        self.serialReady = True
        # turn on io packets
        #self.sendPacket([ArcosCmd.IOREQUEST,ArgType.ARGINT,2,0])

    def getPose(self):
        return self.odpose.get()

    def initGlobals(self):
      self.odpose.set(0.0, 0.0, 0.0)

    def flushSerial(self):
        self.port.flushInput()
        self.port.flushOutput()

    def setMaxEffectiveSonarDistance(self, d):
        pass

    def enableAccelerationCap(self, enable):
        if not enable:
            sys.stderr.write("Can't disable accleration cap on real robot.\n")

    def setMaxVelocities(self, maxTransVel, maxRotVel):
        global MAX_TRANS, MAX_ROT
        MAX_TRANS = maxTransVel
        MAX_ROT = maxRotVel
        if maxTransVel > 0.75:
            sys.stderr.write("Trying to set maximum translational velocity too high for real robot\n")
        if maxRotVel > 1.75:
            sys.stderr.write("Trying to set maximum rotational velocity too high for real robot\n")

    def enableTeleportation(self, prob, pose):
        sys.stderr.write("Enabling teleportation on real robot has no effect.\n")

    # Move by translating with velocity v (m/sec),
    # and rotating with velocity r (rad/sec)
    def motorOutput(self, v, w):
        #    traceback.print_stack()
        if self.acceptMotorCmds:
            self.trans.set(clip(v, -MAX_TRANS, MAX_TRANS))
            self.rot.set(clip(w, -MAX_ROT, MAX_ROT))
            if (not self.asynchronous):
                self.update()

    def analogOutput(self, v):
        self.analogOut.set(clip(v, 0.0, 10.0))

    # Move by translating with velocity v (m/sec),
    # and rotating with velocity r (deg/sec)
    # for dt seconds
    def discreteMotorOutput(self, v, w, dt):
        if self.acceptMotorCmds:
            self.motorOutput(v, w)
            sleep(dt)
            self.motorOutput(0, 0)

    def sendOutputs(self):
        data = [CMD.RECV]

        v = int(self.trans.get() * 1000.0)
        if (v >= 0):
            #data = [abs(v) & 0xFF, v >> 8, 0x01]
            data.append(abs(v)/256)
            data.append(abs(v)%256)
            data.append(0x01)
        else:
            #data = [abs(v) & 0xFF, v >> 8, 0x10]
            data.append(abs(v)/256)
            data.append(abs(v)%256)
            data.append(0x10)

        rv = int(self.rot.get() * 180 / pi)
        if (rv >= 0):
            data.append(abs(rv)/256)
            data.append(abs(rv)%256)
            data.append(0x01)
        else:
            data.append(abs(rv)/256)
            data.append(abs(rv)%256)
            data.append(0x10)
        self.sipSend(data)

    def sendMotorCmd(self):
        self.cmdVel(int(self.trans.get() * 1000.0))
        self.cmdRvel(int(self.rot.get() * 180 / pi))

    def sendDigitalOutCmd(self):
        # high order byte selects output bit for change
        # low order byte sets/resets bit
        data = [ArcosCmd.DIGOUT, ArgType.ARGINT,
                # convert 0-10 voltage to 0-255 value
                (int(math.floor((self.analogOut.get() * 25.5))) & 0xFF), 0xFF]
        self.sipSend(data)

    # update sonars, odometry and stalled
    def update(self, dummyparameter=0):
        if (self.serialReady):
            #self.sendPacket([CMD.RECV])
            #self.sendMotorCmd()
            #self.sendDigitalOutCmd()
            #   temp = self.port.inWaiting()

            self.sendOutputs()
            #sleep(.005)
            #self.sendPacket([CMD.SEND])
            sleep(.005)
            self.from_update = 1
            if (self.sipRecv() > 0):
                self.zero_recv_cnt = 0
            else:
                self.zero_recv_cnt += 1
                if (self.zero_recv_cnt > 400):
                    self.serialReady = False
                    app.soar.closeEBot()
                    sys.stderr.write("Robot turned off or no longer connected.\nDead reckoning is no longer valid.\n")

    # Calculate checksum on P2OS packet (see Pioneer manual)
    def calcChecksum(self, data):
        c = 0
        i = 3
        n = data[2] - ord('0') - 2
        while (n > 1):
            c += (data[i] << 8) | (data[i + 1])
            c = c & 0xFFFF
            n -= 2
            i += 2
        if (n > 0):
            c = c ^ data[i]
        return c

    def startmoving(self):
        self.acceptMotorCmds = True

    #    if (self.asynchronous):
    #      self.stopmoving()
    #      self.startSerialThread()

    def stopmoving(self):
        self.motorOutput(0.0, 0.0)
        self.acceptMotorCmds = False
        if (self.asynchronous):
            pass
        #      self.stopSerialThread()
        else:
            #self.sendMotorCmd()
            self.sendOutputs()

    def startSerialThread(self):
        self.flushSerial()
        self.currentthread = Stepper(self.update, 50)
        self.currentthread.start()

    def stopSerialThread(self):
        try:
            self.currentthread.stop()
        except AttributeError:
            pass

    # Send a packet to robot
    def sendPacket(self, data):
        #pkt = [0x3C,0x3C,len(data)+2]
        pkt = [0x3C, 0x3C, len(data)]
        for d in data:
            pkt.append(d)
        #pkt.append(0)
        #pkt.append(0)
        #chk = self.calcChecksum(pkt)
        #pkt[len(pkt)-2] = (chk>>8)
        #pkt[len(pkt)-1] = (chk&0xFF)
        s = reduce(lambda x, y: x + chr(y), pkt, "")
        try:
            self.port.write(s)
        except:
            sys.stderr.write("Could not write to serial port.\n")
            self.serialReady = False
            app.soar.closeEBot()
            sys.stderr.write("Robot turned off or no longer connected.\nDead reckoning is no longer valid.\n")
        sleep(0.008)

    # Block until packet recieved
    def recvPacket(self):
        timeout = 1.0
        data = [0, 0, 0]
        while (1):
            cnt = 0
            tstart = time()
            while (time() - tstart) < timeout:
                if (self.port.inWaiting() > 0):
                    data[2] = ord(self.port.read())
                    break
            if (time() - tstart) > timeout:
                raise Exception("Read timeout")
            if (data[0] == 0x3E and data[1] == 0x3E):
                break
            data[0] = data[1]
            data[1] = data[2]

        for d in range(data[2] - ord('0')):
            data.append(ord(self.port.read()))

            #if self.from_update:
            #crc = self.calcChecksum(data)
            #if data[len(data)-1]!=(crc&0xFF) or data[len(data)-2]!=(crc>>8):
            #    self.port.flushInput()
            #   raise Exception("Checksum failure")
            #if self.port.inWaiting() > 0:
            #    self.port.flushInput()
            #self.from_update=0
        return data

    # Send a packet
    def sipSend(self, data):
        if self.serialReady:
            self.sendPacket(data)

    # Receive all waiting packets.
    # returns the number of packets read
    def sipRecv(self):
        iters = 0
        if self.serialReady:
            while (self.port.inWaiting() > 0):
                try:
                    recv = self.recvPacket()
                except:
                    print 'no recv packet'
                    #continue
                    break
                iters += 1
                self.parseData(recv)
                # 0x3s means sip packet
                #if (recv[3]&0xF0)==0x30:
                #  self.parseSip(recv)
                # 0xF0 means io packet
                #elif recv[3]==0xF0:
                #  self.parseIO(recv)
        return iters

    def parseData(self, recv):
        # parse all data

        #    analogInputs = [0,0,0,0,0,0,0,0]
        #    bufferidx = 12
        #    for aninputidx in range(len(analogInputs)):
        #      analogInputs[aninputidx] = (recv[bufferidx] | recv[bufferidx+1]<<8)
        #      bufferidx += 2
        #    analogInputs = [a*10.0/1023.0 for a in analogInputs]
        #    self.analogInputs.set(analogInputs[4:len(analogInputs)])
        #
        dx = (recv[3] << 8) | (recv[4])  # mm
        dy = (recv[5] << 8) | (recv[6])  # mm
        #print 'dx: ', dx, 'dy: ', dy
        thpos = (recv[7] << 8) | (recv[8])  #
        stall = (recv[9])
        bump = (recv[10])
        sonars = [-1, -1, -1, -1, -1, -1]

        #Right Sonar
        sonars[4] = (recv[11] << 8) | (recv[12])
        #print 'Sonar 1: ', sonars[0]

        #Right Front Sonar
        sonars[3] = (recv[13] << 8) | (recv[14])
        #print 'Sonar 2: ', sonars[1]

        #Front Sonar
        sonars[2] = (recv[15] << 8) | (recv[16])
        #print 'Sonar 3: ', sonars[2]

        #Left Front Sonar
        sonars[1] = (recv[17] << 8) | (recv[18])
        #print 'Sonar 4: ', sonars[3]

        #Left Sonar
        sonars[0] = (recv[19] << 8) | (recv[20])
        #print 'Sonar 5: ', sonars[4]

        #Back Sonar
        sonars[5] = (recv[21] << 8) | (recv[22])
        #print 'Sonar 6: ', sonars[5]

        #for i in range(sonars):
        #  num = recv[23+3*i]s
        #  sonars[num] = recv[24+3*i] | (recv[25+3*i]<<8)
        #control     = recv[17] | (recv[18]<<8)
        #flags       = recv[19] | (recv[20]<<8)
        #compass     = recv[21]
        #lvel        = recv[9] | (recv[10]<<8)
        #rvel        = recv[11] | (recv[12]<<8)
        #battery     = recv[13]
        #indx = 23 + 3*sonarcount
        #gripstate   = recv[indx]
        #anport      = recv[indx+1]
        #analog      = recv[indx+2]
        #digin       = recv[indx+3]
        #digout      = recv[indx+4]
        #batteryx10  = recv[indx+5] | (recv[indx+6]<<8)
        #chargestate = recv[indx+7]

        # deal with the fact that x and y odometry roll over
        #dx, dy = xpos-self.lastxpos, ypos-self.lastypos
        #if dx > 60000:
        #  dx-=65536
        #elif dx < -60000:
        #  dx+=65536
        #if dy > 60000:
        #  dy-=65536
        #elif dy < -60000:
        #  dy+=65536
        lastpose = self.odpose.get()
        self.odpose.set((lastpose[0] + dx * METER_SCALE,
                         lastpose[1] + dy * METER_SCALE,
                         thpos * RADIAN_SCALE))
        #self.lastxpos, self.lastypos = xpos, ypos
        #self.battery = battery/10.0
        #stall = [( (stall&0x01) == 0x01 ), ( (stall&0x10) == 0x10 )]
        #bump = [( (bump&0x01) == 0x01 ), ( (bump&0xFE00) >> 9 )]
        self.stalled.set((stall != 0x00) or (bump != 0x00))
        storedsonars = self.storedsonars.get()
        for i in range(len(sonars)):
            if sonars[i] != -1:
                storedsonars[i] = sonars[i] * METER_SCALE;
                self.sonarsChanged[i] = 1
            else:
                self.sonarsChanged[i] = 0
                self.storedsonars.set(storedsonars)

    # Send a packet and receive a SIP response from the robot
    def sipSendReceive(self, data):
        self.sipSend(data)
        self.sipRecv()

    #  def cmdPulse(self):
    #    self.sipSendReceive([ArcosCmd.PULSE])

    #  def cmdPulseSend(self):
    #    self.sipSend([ArcosCmd.PULSE])

    def cmdEnable(self, v):
        #self.sendPacket([ArcosCmd.ENABLE, ArgType.ARGINT, v, 0])
        pass

    def cmdVel(self, v):
        absv = int(abs(v))
        if (v >= 0):
            data = [ArcosCmd.VEL, ArgType.ARGINT, absv & 0xFF, absv >> 8]
        else:
            data = [ArcosCmd.VEL, ArgType.ARGNINT, absv & 0xFF, absv >> 8]
        #    self.sipSendReceive(data)
        self.sipSend(data)


    #  def cmdVel2(self,l,r):
    #    self.sipSendReceive([ArcosCmd.VEL2,ArgType.ARGINT,int(r),int(l)])

    def cmdRvel(self, rv):
        absrv = abs(rv)
        if (rv >= 0):
            data = [ArcosCmd.RVEL, ArgType.ARGINT, absrv & 0xFF, absrv >> 8]
        else:
            data = [ArcosCmd.RVEL, ArgType.ARGNINT, absrv & 0xFF, absrv >> 8]
        #    self.sipSendReceive(data)
        self.sipSend(data)

    def cmdSay(self, note, duration):
        data = [ArcosCmd.SAY, ArgType.ARGSTR]
        for d in ("%s,%s" % (note, duration)):
            data.append(ord(d))
        data.append(0)
        #self.sendPacket(data)
