@echo off
setlocal enabledelayedexpansion

rem --- 設定 ---
set "BASE_DIR=base"
set "COMP_DIR=comp"
set "MOD_DIR=modified"
set "NEW_DIR=new"
set "DEL_DIR=deleted"

rem --- 保存先フォルダの作成 ---
if not exist "%MOD_DIR%" mkdir "%MOD_DIR%"
if not exist "%NEW_DIR%" mkdir "%NEW_DIR%"
if not exist "%DEL_DIR%" mkdir "%DEL_DIR%"

echo ========================================
echo 処理開始: ファイルの比較とコピー
echo ========================================

rem --- 1. 変更・変更なし・削除の判定 (baseを基準にループ) ---
for %%F in ("%BASE_DIR%\*") do (
    set "fname=%%~nxF"
    
    if exist "%COMP_DIR%\!fname!" (
        rem 両方に存在する場合、ハッシュ値を比較
        call :get_hash "%BASE_DIR%\!fname!" hash_base
        call :get_hash "%COMP_DIR%\!fname!" hash_comp
        
        if "!hash_base!"=="!hash_comp!" (
            echo [変更なし] !fname!
        ) else (
            echo [変更]     !fname! -^> %MOD_DIR% へコピー
            copy /y "%COMP_DIR%\!fname!" "%MOD_DIR%\" >nul
        )
    ) else (
        rem compに存在しない場合 (削除区分)
        echo [削除]     !fname! -^> %DEL_DIR% へファイル作成
        type nul > "%DEL_DIR%\!fname!"
    )
)

rem --- 2. 新規の判定 (compを基準にループ) ---
for %%F in ("%COMP_DIR%\*") do (
    set "fname=%%~nxF"
    if not exist "%BASE_DIR%\!fname!" (
        echo [新規]     !fname! -^> %NEW_DIR% へコピー
        copy /y "%COMP_DIR%\!fname!" "%NEW_DIR%\" >nul
    )
)

echo ========================================
echo 処理完了
pause
exit /b

:get_hash
for /f "skip=1" %%A in ('certutil -hashfile "%~1" MD5 ^| findstr /v "CertUtil"') do (
    set "%2=%%A"
    goto :eof
)