@echo off
setlocal enabledelayedexpansion

rem Check if the correct number of arguments is provided

set BatchFileName=%~1
set BatchFilePath=%~dp1

echo %date% %time% 

if exist %BatchFilePath%config.txt (
    for /f "usebackq delims=" %%A in ("%BatchFilePath%config.txt") do (
        set line=%%A
        echo !line!
    )
) else (
    echo config.txt not found in %BatchFilePath%
    exit /b 1
)