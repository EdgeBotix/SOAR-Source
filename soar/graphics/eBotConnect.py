import os
import glob
import sys
from time import *
import serial
from Tkinter import *
import Tkinter
import tkMessageBox


top = Tk()
top.title("eBot Selection")
top.geometry("210x280+200+200")
#top.size(width=200, height=100)
top.resizable(width=FALSE, height=FALSE)
top.grid()

var = StringVar()
label = Label(top, textvariable=var)
var.set("Select a connected eBot and click \"Ok\"")
label.pack(pady=5)

Lb1 = Listbox(top, bd=0)
Lb1.insert(1, "eBot #1")
Lb1.insert(2, "eBot #3")
Lb1.insert(3, "eBot #18")
Lb1.pack(pady=2)

def okCallBack():
    t = Lb1.curselection()
    s = "Selected eBot: #"
    s += str(int(t[0])+1)
    tkMessageBox.showinfo("eBot", s)
    top.destroy()

#B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack, variable=bPressed, onClick=1)
B = Tkinter.Button(top, width=20, text="Ok", command=okCallBack)
B.pack(side="bottom", pady=15)

top.mainloop()
