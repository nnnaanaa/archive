@echo off
setlocal enabledelayedexpansion

set target_path=%~dp0
set target_conf_path=%~dp0
set target_bat=conf_read.bat
set target_conf1=conf1.txt
set target_conf2=conf2.txt
set target_conf3=conf3.txt
set target_conf4=conf4.txt

rem setting environment variables
call %target_path%%target_bat%
rem call %target_path%%target_bat% %target_conf_path%%target_conf1% %target_conf_path%%target_conf2% %target_conf_path%%target_conf3%
rem call %target_path%%target_bat% %target_conf_path%%target_conf1% %target_conf_path%%target_conf2% %target_conf_path%%target_conf3% %target_conf_path%%target_conf4%

set result=%errorlevel%
if %result% neq 0 (
    echo [Error] conf_read.bat failed with error code %result%
    exit /b %result%
)

rem test environment variables conf1.txt
echo %uselang1%
echo %uselang2%
echo %uselang3%
echo %uselang4%

rem test environment variables conf2.txt
echo %uselang5%
echo %uselang6%
echo %uselang7%
echo %uselang8%

rem test environment variables conf3.txt
echo %uselang9%
echo %uselang10%
echo %uselang11%
echo %uselang12%

exit /b 0