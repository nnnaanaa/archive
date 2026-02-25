@echo off
setlocal enabledelayedexpansion

:: --- ここに比較したい2つのファイルのパスを記述してください ---
set "FILE1=large_file_finder.py"
set "FILE2=large_file_finder.py"
:: --------------------------------------------------------

echo [比較開始]
echo ファイル1: %FILE1%
echo ファイル2: %FILE2%
echo -------------------------------------------------------

:: ファイルの存在チェックを事前に行う
if not exist "%FILE1%" (echo エラー: ファイル1が見つかりません。& pause & exit /b)
if not exist "%FILE2%" (echo エラー: ファイル2が見つかりません。& pause & exit /b)

:: サブルーチンを呼び出してハッシュを取得
call :GetHash "%FILE1%" HASH1
call :GetHash "%FILE2%" HASH2

:: 結果の表示
echo MD5 (1): %HASH1%
echo MD5 (2): %HASH2%
echo -------------------------------------------------------

:: 比較判定
if /i "%HASH1%"=="%HASH2%" (
    echo 【 判定：一致 ◎ 】
) else (
    echo 【 判定：不一致 × 】
)

echo.
pause
exit /b

:: --- 以下、ハッシュ取得用の共通関数（サブルーチン） ---
:GetHash
:: %1 はファイルパス、%2 は結果を格納する変数名
for /f "tokens=* skip=1" %%a in ('certutil -hashfile "%~1" MD5') do (
    set "temp_hash=%%a"
    :: 2行目を取得した時点でループを抜ける（CertUtilの成功メッセージを無視するため）
    set "%~2=!temp_hash: =!"
    exit /b
)