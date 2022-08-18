@echo off
rem ********************************************************************
rem CopyKeyboardDotXML.bat
rem ======================
rem Batch file to copy the sample keyboard.xml to userdata
rem
rem 14/08/2010 J. Rennie
rem ********************************************************************

rem *** Get the date to backup the old keyboard.xml

for /f "tokens=1" %%i in ('date /t') do set THEDATE=%%i
set THEDAY=%THEDATE:~0,2%
set THEDATE=%THEDATE:~6,4%%THEDATE:~3,2%%THEDATE:~0,2%

rem *** Warn the user what we're about to do

echo This script will copy the sample keyboard.xml to:
echo %APPDATA%\Kodi\userdata\keymaps\keyboard.xml
echo.
echo If there is already a keyboard.xml it will be renamed keyboard.xml.%THEDATE%
echo.
echo Press control-C to abort or any key to continue
echo.
pause

rem *** Check we can find the keyboard.xml

set NEWKB=%0\..\keyboard.xml
set NEWKB=%NEWKB:"=%

if exist "%NEWKB%" goto foundnewkb
echo ERROR: Cannot find the new keyboard.xml to copy
echo Check keyboard.xml is in the same directory as %0
pause
exit
:foundnewkb

rem *** Check if we need to backup the old keyboard.xml

set OLDKB=%APPDATA%\Kodi\userdata\keymaps\keyboard.xml
if not exist "%OLDKB%" goto nooldkb

set OLDKBBACK=keyboard.xml.%THEDATE%
if not exist "%APPDATA%\Kodi\userdata\keymaps\%OLDKBBACK%" goto nooldkbback
del /F /Q "%APPDATA%\Kodi\userdata\keymaps\%OLDKBBACK%"
:nooldkbback

echo Renaming %OLDKB% to %OLDKBBACK%
rename "%OLDKB%" "%OLDKBBACK%"

pause
:nooldkb

rem *** Copy the new keyboard.xml

md "%APPDATA%\Kodi\userdata\keymaps" 1>NUL 2>&1
copy "%NEWKB%" "%OLDKB%"

echo Keyboard.xml copied to %OLDKB%

pause
