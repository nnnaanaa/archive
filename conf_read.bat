@echo off
rem =======================================================
rem conf_read.bat
rem 引数で指定されたテキストファイルを順次読み込み、
rem 「変数名,値,」の形式を環境変数として展開します。
rem 引数がない、またはファイルがない場合は 9999 を返します。
rem =======================================================

rem --- 追加：引数が一つも設定されていないかチェック ---
if "%~1"=="" (
    echo [Error] No arguments provided.
    exit /b 9999
)

:loop
rem すべての引数を処理し終えたら正常終了
if "%~1"=="" exit /b 0

rem ファイルが存在するか確認
if not exist "%~1" (
    echo [Error] File not found: %~1
    exit /b 9999
)

rem ファイルを1行ずつ読み込み、カンマ区切りでパース
for /f "usebackq tokens=1,2 delims=," %%a in ("%~1") do (
    if not "%%a"=="" (
        set %%a=%%b
    )
)

shift
goto :loop