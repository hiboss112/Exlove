@echo off
setlocal enabledelayedexpansion

echo === Exlove 레지스트리 자동 설치 프로그램 ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한이 필요합니다.
    echo 스크립트를 관리자 권한으로 다시 실행해주세요.
    pause
    exit /b 1
)

:: 현재 스크립트 위치 확인
set "SCRIPT_DIR=%~dp0"

:: Exlove.exe 찾기
echo 게임 파일 검색 중...
for /f "delims=" %%i in ('dir /b /s "%SCRIPT_DIR%Exlove.exe" 2^>nul') do (
    set "INSTALL_PATH=%%~dpi"
    set "GAME_EXE=%%~fi"
    goto FOUND_EXE
)

:: 게임 파일을 찾지 못한 경우
echo Exlove.exe를 찾을 수 없습니다.
echo 이 스크립트를 게임 폴더나 상위 폴더에 위치시켜주세요.
pause
exit /b 1

:FOUND_EXE
:: 경로에서 마지막 백슬래시 제거
if "%INSTALL_PATH:~-1%"=="\" set "INSTALL_PATH=%INSTALL_PATH:~0,-1%"
set "DATA_PATH=%INSTALL_PATH%\Data"

:: 현재 사용자 이름 가져오기
set "USERNAME=%USERNAME%"

:: 현재 시간 가져오기 (UTC 형식)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set "YEAR=%datetime:~0,4%"
set "MONTH=%datetime:~4,2%"
set "DAY=%datetime:~6,2%"
set "HOUR=%datetime:~8,2%"
set "MINUTE=%datetime:~10,2%"
set "SECOND=%datetime:~12,2%"

echo 설치 정보:
echo 사용자: %USERNAME%
echo 게임 실행 파일: %GAME_EXE%
echo 설치 경로: %INSTALL_PATH%
echo 데이터 경로: %DATA_PATH%
echo 현재 시간: %YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%:%SECOND%
echo.

:: 레지스트리 설정
echo 레지스트리 설정을 적용합니다...

:: HKEY_LOCAL_MACHINE 설정
echo 시스템 레지스트리 설정 중...
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: WOW6432Node 설정
echo 32비트 호환성 레지스트리 설정 중...
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: HKEY_CURRENT_USER 설정
echo 사용자 레지스트리 설정 중...
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Username" /t REG_SZ /d "%USERNAME%" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "LastLoginTime" /t REG_SZ /d "%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%:%SECOND%" /f

echo.
echo 레지스트리 설정이 완료.
echo 게임을 실행.
pause