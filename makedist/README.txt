Open a terminal window, navigate to the directory where you placed the 
libdw-2013-1.tar.gz file by typing a command of the form

> cd ~/Desktop

(assuming you place the file in ~/Desktop.)

Unpack the modules by typing

> tar xvzf libdw-2013-1.tar.gz

Then change directories and do the installation with

> cd libdw
> sudo python2.7 setup.py install

You can now delete all of the files created by this operation 
(i.e., ~/Desktop/libdw-2013-1.tar.gz and its associated directory tree). 

You should now be able to run soar by typing soar at a terminal command prompt. 

