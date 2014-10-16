import os
import glob
import sys
from time import *
import serial
from Tkinter import *
import Tkinter
import tkMessageBox
if os.name == 'nt':
    try:
        import _winreg as winreg

    except:
        pass

class eBotConnect:
    def __init__(self):
        #self.windowHeight = 350 # 220
        #self.windowWidth = 450 # 350
        #app.top.protocol('WM_DELETE_WINDOW', self.exit)

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

        ebot_ports = []
        ebot_names = []
        for port in ports:
            try:
                s = serial.Serial(port, 115200, timeout=1, writeTimeout=1)
                s.write("?")
                sleep(0.5)
                line = s.readline()
                if (line[:4] == "eBot"):
                    ebot_ports.append(port)
                    ebot_names.append(line)
                    s.close()
            except:
                try:
                    if s.isOpen():
                        s.close()
                except:
                    pass

        if (len(ebot_ports) == 0):
            # RAISE RAISE EXCEPTION
            sys.stderr.write("Could not find eBot.  Is robot turned on and connected?\n")
            tkMessageBox.showinfo("Connection Error", "No eBot connected. Please make sure eBot is on and paired.")
        else:
            bPressed = 0
            top = Tk()
            top.title("eBot Selection")
            top.geometry("250x280+200+200")
            top.size(width=200, height=100)
            top.resizable(width=FALSE, height=FALSE)
            top.grid()

            #var = StringVar()
            #label = Label(top, textvariable=var)
            #var.set("Select a connected eBot and click \"Ok\"")
            #label.pack(pady=5)

            #Lb1 = Listbox(top, bd=0, font="verdana")
            #for i in range(len(ebot_names)):
            #    Lb1.insert(i+1, ebot_names[i])
            #Lb1.pack(pady=2)

            #def okCallBack():
            #    tkMessageBox.showinfo("Hello Python", "Hello World")
            #    self.destroy()

            ##B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack, variable=bPressed, onClick=1)
            #B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack)
            #B.pack(side="bottom", pady=15)

            top.mainloop()

    #### For windows only ########
    def getOpenPorts(self):
        """
            This Function Returns a list of tuples witht the port number
            and its description.
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

    def getSelectedPort(self):
        return -1
   #def getEBotPort(self):
   #        ports = []
   #        if os.name == "posix":
   #            if sys.platform == "linux2":
   #                #usbSerial = glob.glob('/dev/ttyUSB*')
   #                print "Support for this OS under development."
   #            elif sys.platform == "darwin":
   #                ports = glob.glob('/dev/tty.eBot*')
   #                #usbSerial = glob.glob('/dev/tty.usbserial*')
   #            else:
   #                print "Unknown posix OS."
   #                sys.exit()
   #        elif os.name == "nt":
   #            ports = self.getEBotPort()
   #            #ports = ['COM' + str(i + 1) for i in range(256)]
   #            #EBOT_PORTS = getEBotPorts()
#
   #        ebot_ports = []
   #        ebot_names = []
   #        for port in ports:
   #            try:
   #                s = serial.Serial(port, 115200, timeout=1, writeTimeout=1)
   #                s.write("BOT?")
   #                sleep(0.5)
   #                line = s.readline()
   #                if (line[:4] == "eBot"):
   #                    ebot_ports.append(port)
   #                    ebot_names.append(line)
   #                    s.close()
   #            except:
   #                try:
   #                    if s.isOpen():
   #                        s.close()
   #                except:
   #                    pass
#
   #        if (len(ebot_ports) == 0):
   #            # RAISE RAISE EXCEPTION
   #            sys.stderr.write("Could not find eBot.  Is robot turned on and connected?\n")
   #        else:
   #            bPressed = 0
   #            #top = Tk()
   #            #top.title("eBot Selection")
   #            #top.geometry("250x280+200+200")
   #            ##top.size(width=200, height=100)
   #            #top.resizable(width=FALSE, height=FALSE)
   #            #top.grid()
   ##
   #            #var = StringVar()
   #            #label = Label(top, textvariable=var)
   #            #var.set("Select a connected eBot and click \"Ok\"")
   #            #label.pack(pady=5)
   ##
   #            #Lb1 = Listbox(top, bd=0, font="verdana")
   #            #for i in range(len(ebot_names)):
   #            #    Lb1.insert(i+1, ebot_names[i])
   #            #Lb1.pack(pady=2)
   ##
   #            #def okCallBack():
   #            #    tkMessageBox.showinfo("Hello Python", "Hello World")
   #            #    self.destroy()
   ##
   #            ##B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack, variable=bPressed, onClick=1)
   #            #B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack)
   #            #B.pack(side="bottom", pady=15)
   ##
   #            #top.mainloop()
   ##
   #            #sleep(20)
   #            #top.destroy()
   #           # self.portName = ebot_ports[0]
                #settings.SERIAL_PORT_NAME =self.portName