@echo off
setlocal

rem set check_date_yyyymmdd=20260103
set check_date_yyyymmdd=%1

:: PowerShellで日付として妥当かチェック
powershell -Command "[DateTime]::ParseExact('%check_date_yyyymmdd%', 'yyyyMMdd', $null)" >nul 2>&1

if %errorlevel% equ 0 (
    echo %check_date_yyyymmdd% は正しい日付です。
) else (
    echo %check_date_yyyymmdd% は不正な日付です。
)

pause