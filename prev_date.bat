@echo off
setlocal

rem 前日の年月日を YYYYMMDD 形式で取得するバッチファイル
set TARGET_DATE=20260119
for /f %%a in ('powershell -command "([datetime]('%TARGET_DATE%'.Insert(6,'/').Insert(4,'/'))).AddDays(-1).ToString('yyyyMMdd')"') do ( set YESTERDAY=%%a )
echo %YESTERDAY%