@echo off
setlocal enabledelayedexpansion

if "%~1" == "" goto usage
if "%~2" == "" goto usage

set "ERR_CONTENT=0"
set "ERR_DATE=0"
set "MISSING_COUNT=0"

REM パスの正規化（絶対パス化）
for %%A in ("%~1") do set "SRC_ROOT=%%~fA"
for %%A in ("%~2") do set "DEST_ROOT=%%~fA"

REM フォルダ末尾が \ なら除去（置換処理のため）
if "%SRC_ROOT:~-1%"=="\" set "SRC_ROOT=%SRC_ROOT:~0,-1%"
if "%DEST_ROOT:~-1%"=="\" set "DEST_ROOT=%DEST_ROOT:~0,-1%"

if not exist "%SRC_ROOT%\" (echo エラー: 比較元が見つかりません: %SRC_ROOT% & exit /b 1)
if not exist "%DEST_ROOT%\" (echo エラー: 比較先が見つかりません: %DEST_ROOT% & exit /b 1)

echo 比較を開始します...
echo 比較元: %SRC_ROOT%
echo 比較先: %DEST_ROOT%
echo --------------------------------------------------

REM 比較元の文字数を計算（パスの切り出しに使用）
set "TEMP_SRC=%SRC_ROOT%"
set "SRC_LEN=0"
:LEN_LOOP
if defined TEMP_SRC (
    set "TEMP_SRC=%TEMP_SRC:~1%"
    set /a SRC_LEN+=1
    goto :LEN_LOOP
)

for /f "delims=" %%F in ('dir "%SRC_ROOT%" /b /s /a-d') do (
    set "FULL_PATH=%%F"
    REM 文字列置換ではなく、文字数指定でカットすることで確実に相対パスを抽出
    set "REL_PATH=!FULL_PATH:~%SRC_LEN%!"
    set "D_FILE=%DEST_ROOT%!REL_PATH!"

    if not exist "!D_FILE!" (
        echo [存在せず] !REL_PATH!
        set /a MISSING_COUNT+=1
    ) else (
        REM 秒単位の日付比較
        for /f "usebackq" %%A in (`powershell -NoProfile -Command "(Get-Item -LiteralPath '%%F').LastWriteTime.ToString('yyyyMMddHHmmss')"`) do set "S_TIME=%%A"
        for /f "usebackq" %%A in (`powershell -NoProfile -Command "(Get-Item -LiteralPath '!D_FILE!').LastWriteTime.ToString('yyyyMMddHHmmss')"`) do set "D_TIME=%%A"

        if "!S_TIME!" neq "!D_TIME!" (
            set "S_D=!S_TIME:~0,4!/!S_TIME:~4,2!/!S_TIME:~6,2! !S_TIME:~8,2!:!S_TIME:~10,2!:!S_TIME:~12,2!"
            set "D_D=!D_TIME:~0,4!/!D_TIME:~4,2!/!D_TIME:~6,2! !D_TIME:~8,2!:!D_TIME:~10,2!:!D_TIME:~12,2!"
            echo [日付差異] !REL_PATH! (元:!S_D! 先:!D_D!)
            set /a ERR_DATE+=1
        )

        fc /b "%%F" "!D_FILE!" >nul
        if errorlevel 1 (
            echo [内容差異] !REL_PATH!
            set /a ERR_CONTENT+=1
        )
    )
)

echo --------------------------------------------------
echo 比較完了
echo 内容差異: %ERR_CONTENT% 件 / 日付差異: %ERR_DATE% 件 / 存在せず: %MISSING_COUNT% 件

if %ERR_CONTENT% equ 0 if %ERR_DATE% equ 0 if %MISSING_COUNT% equ 0 (
    echo 結果: すべて一致
) else (
    echo 結果: 不一致あり
)

REM プログラムの正常終了
endlocal
exit /b 0

:usage
echo 使用法: folder_compare.bat [比較元フォルダ] [比較先フォルダ]
exit /b 1