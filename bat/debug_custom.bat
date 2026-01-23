@echo off
setlocal enabledelayedexpansion

:: --- 設定エリア ---
set "SOURCE_DIR=%~dp0target"
echo [WATCH] SOURCE_DIR is now: !SOURCE_DIR!
set "LOG_FILE=%~dp0sort_log.txt"
set "TIMESTAMP=%date% %time%"

title ファイル仕分けスクリプト - Running...

echo ============================================
echo  File Organizer Starting...
echo  Time: %TIMESTAMP%
echo ============================================

:: 対象フォルダがない場合は作成して終了
if not exist "%SOURCE_DIR%" (
    echo [ERROR] 対象フォルダ "%SOURCE_DIR%" が見つかりません。
    echo フォルダを作成して再実行してください。
    pause
    exit /b
)

:: ログ初期化
echo --- Execution at %TIMESTAMP% --- >> "%LOG_FILE%"

:: --- メイン処理 ---
pushd "%SOURCE_DIR%"

for %%F in (*) do (
    if not "%%~nxF"=="%~nx0" (
        set "FILE_EXT=%%~xF"
        echo [WATCH] FILE_EXT is now: !FILE_EXT!
        
        if "!FILE_EXT!"=="" (
            set "DEST_DIR=no_extension"
        ) else (
            set "DEST_DIR=!FILE_EXT:~1!"
        )

        call :MoveFile "%%F" "!DEST_DIR!"
    )
)

popd

echo ============================================
echo  処理が完了しました。詳細はログを確認してください。
echo ============================================
pause
exit /b

:: --- サブルーチン (ファイル移動) ---
:MoveFile
set "FILENAME=%~1"
set "FOLDER=%~2"

if not exist "%FOLDER%" (
    mkdir "%FOLDER%"
    echo [%TIME%] Created directory: %FOLDER% >> "%LOG_FILE%"
)

move "%FILENAME%" "%FOLDER%\" >nul
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] %FILENAME% -^> %FOLDER%
    echo [%TIME%] MOVED: %FILENAME% to %FOLDER% >> "%LOG_FILE%"
) else (
    echo [FAILED]  %FILENAME%
    echo [%TIME%] ERROR: Failed to move %FILENAME% >> "%LOG_FILE%"
)
goto :eof