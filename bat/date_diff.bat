@echo off
setlocal

:: --- 設定エリア ---
set DATE1=20260401
set DATE2=20260202
:: -----------------

echo 比較開始: %DATE1% と %DATE2%

:: PowerShellを呼び出して日付の差を計算
for /f %%a in ('powershell -command "& { $d1 = [datetime]::ParseExact('%DATE1%', 'yyyyMMdd', $null); $d2 = [datetime]::ParseExact('%DATE2%', 'yyyyMMdd', $null); Write-Host ([math]::Abs(($d1 - $d2).Days)) }"') do (
    set DIFF=%%a
)

echo.
echo 二つの日付の差は %DIFF% 日です。
pause