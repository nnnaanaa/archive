@echo off
setlocal enabledelayedexpansion

set "BASE_DIR=base"
set "COMP_DIR=comp"

echo ========================================
echo 比較開始: %BASE_DIR% vs %COMP_DIR%
echo ========================================

rem --- 1. 変更・変更なし・削除の判定 (baseを基準にループ) ---
echo [判定中...]
for %%F in ("%BASE_DIR%\*") do (
    set "fname=%%~nxF"
    
    if exist "%COMP_DIR%\!fname!" (
        rem 両方に存在する場合、ハッシュ値を比較
        call :get_hash "%BASE_DIR%\!fname!" hash_base
        call :get_hash "%COMP_DIR%\!fname!" hash_comp
        
        if "!hash_base!"=="!hash_comp!" (
            echo [変更なし] !fname!
        ) else (
            echo [変更]     !fname!
        )
    ) else (
        rem compに存在しない場合
        echo [削除]     !fname!
    )
)

rem --- 2. 新規の判定 (compを基準にループ) ---
for %%F in ("%COMP_DIR%\*") do (
    set "fname=%%~nxF"
    if not exist "%BASE_DIR%\!fname!" (
        echo [新規]     !fname!
    )
)

echo ========================================
echo 比較完了
pause
exit /b

:get_hash
for /f "skip=1" %%A in ('certutil -hashfile "%~1" MD5 ^| findstr /v "CertUtil"') do (
    set "%2=%%A"
    goto :eof
)