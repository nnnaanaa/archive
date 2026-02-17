@echo off
setlocal enabledelayedexpansion

:: --- 設定エリア ---
set TARGET_DIR=P:\batch\archive\date
set TARGET_DATE=20260401
:: -----------------

set PREV_DATE=なし

:: フォルダ名を取得し、昇順（古い順）にループ処理
for /f "tokens=*" %%f in ('dir /b /ad /on "%TARGET_DIR%"') do (
    
    :: 指定された日付と同じになったら、ループを抜ける
    if "%%f"=="%TARGET_DATE%" (
        goto :RESULT
    )
    
    :: 指定日より前であれば、そのフォルダ名を変数に上書きしていく
    :: （最終的に、指定日の直前の日付が変数に残る）
    set PREV_DATE=%%f
)

:RESULT
echo 指定基準日: %TARGET_DATE%
echo １つ前の日: %PREV_DATE%

:: 後の処理で使う場合は、この変数 %PREV_DATE% を利用してください
pause