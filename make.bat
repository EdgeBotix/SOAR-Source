REM #!\bin\bash
@ECHO off
cls

SET DESTDIR=makedist

REM #clean up destination directory
REM ECHO ">> rm -fr %DESTDIR%\dist\*" 
REM DEL -fr %DESTDIR%\libdw\* %DESTDIR%\soar\* %DESTDIR%\form\* #DESTDIR\dist\*
REM DEL /F /S /Q %DESTDIR%\libdw\*.* %DESTDIR%\soar\*.* %DESTDIR%\form\*.* 
RMDIR /S /Q %DESTDIR%\libdw\ %DESTDIR%\soar\ %DESTDIR%\form\
MKDIR %DESTDIR%\libdw\ %DESTDIR%\soar\ %DESTDIR%\form\
MKDIR %DESTDIR%\soar\io %DESTDIR%\soar\graphics\ %DESTDIR%\soar\serial %DESTDIR%\soar\controls %DESTDIR%\soar\outputs %DESTDIR%\soar\worlds %DESTDIR%\soar\media

REM #create all the .pyc files, and move them to the appropriate dirs
REM #*code\ contains .py files. libdw\ soar\ & form\ are used to hold .pyc files
REM ECHO ">> python make.py"
C:\Python27\python make.py

REM ECHO "Moving files to %DESTDIR%\"
MOVE libdw\*.pyc          %DESTDIR%\libdw
MOVE form\*.pyc           %DESTDIR%\form
MOVE soar\*.pyc           %DESTDIR%\soar
MOVE soar\io\*.pyc        %DESTDIR%\soar\io
MOVE soar\graphics\*.pyc  %DESTDIR%\soar\graphics
MOVE soar\serial\*.pyc    %DESTDIR%\soar\serial
MOVE soar\controls\*.pyc  %DESTDIR%\soar\controls
MOVE soar\outputs\*.pyc   %DESTDIR%\soar\outputs
COPY soar\soar         	  %DESTDIR%\soar
REM XCOPY /E soar\worlds       %DESTDIR%\soar\worlds
REM XCOPY /E soar\media        %DESTDIR%\soar\media
COPY soar\worlds		  %DESTDIR%\soar\worlds
COPY soar\media			  %DESTDIR%\soar\media

REM #copy the __init__.py files to avoid python setup.py from complaining
COPY libdw\__init__.py %DESTDIR%\libdw\
COPY form\__init__.py  %DESTDIR%\form\
COPY soar\__init__.py  %DESTDIR%\soar\
COPY soar\io\__init__.py       %DESTDIR%\soar\io\
COPY soar\graphics\__init__.py %DESTDIR%\soar\graphics\
COPY soar\serial\__init__.py   %DESTDIR%\soar\serial\
COPY soar\controls\__init__.py %DESTDIR%\soar\controls\
COPY soar\outputs\__init__.py  %DESTDIR%\soar\outputs\

REM #perform the setup
REM ECHO ">> python setup.py sdist"
CD %DESTDIR%
C:\Python27\python setup.py sdist
DEL /F /S /Q MANIFEST

pause 
