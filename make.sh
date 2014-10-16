#!/bin/bash

DESTDIR=makedist

#clean up destination directory
echo ">> rm -fr $DESTDIR/dist/*" 
rm -fr $DESTDIR/libdw/* $DESTDIR/soar/* $DESTDIR/form/* #DESTDIR/dist/*
mkdir $DESTDIR/soar/io $DESTDIR/soar/graphics/ $DESTDIR/soar/serial $DESTDIR/soar/controls $DESTDIR/soar/outputs

#create all the .pyc files, and move them to the appropriate dirs
#*code/ contains .py files. libdw/ soar/ & form/ are used to hold .pyc files
echo ">> python make.py"
python make.py

echo ">> moving files to $DESTDIR/"
mv libdw/*.pyc          $DESTDIR/libdw/
mv form/*.pyc           $DESTDIR/form/
mv soar/*.pyc           $DESTDIR/soar/
mv soar/io/*.pyc        $DESTDIR/soar/io/
mv soar/graphics/*.pyc  $DESTDIR/soar/graphics/
mv soar/serial/*.pyc    $DESTDIR/soar/serial/
mv soar/controls/*.pyc  $DESTDIR/soar/controls/
mv soar/outputs/*.pyc   $DESTDIR/soar/outputs/
cp    soar/soar         $DESTDIR/soar/
cp -r soar/worlds       $DESTDIR/soar/
cp -r soar/media        $DESTDIR/soar/

#copy the __init__.py files to avoid python setup.py from complaining
cp libdw/__init__.py $DESTDIR/libdw/
cp form/__init__.py  $DESTDIR/form/
cp soar/__init__.py  $DESTDIR/soar/
cp soar/io/__init__.py       $DESTDIR/soar/io/
cp soar/graphics/__init__.py $DESTDIR/soar/graphics/
cp soar/serial/__init__.py   $DESTDIR/soar/serial/
cp soar/controls/__init__.py $DESTDIR/soar/controls/
cp soar/outputs/__init__.py  $DESTDIR/soar/outputs/

echo
#perform the setup
echo ">> python setup.py sdist"
cd $DESTDIR
python setup.py sdist
rm -f MANIFEST

