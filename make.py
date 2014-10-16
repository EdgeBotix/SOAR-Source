# compiles the .py files in the stated directories

import os
import py_compile

for dir in ["libdw", "form", "soar", "soar/controls",\
            "soar/graphics", "soar/io", "soar/outputs",\
            "soar/serial"]:

  pyfiles = [file for file in os.listdir(dir) if file.endswith(".py")]

  for file in pyfiles:
    print 'compiling: ', dir+'/'+file
    py_compile.compile(dir+'/'+file)

