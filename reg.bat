@echo off
setlocal enabledelayedexpansion

echo === Exlove 레지스트리 자동 설정 프로그램 ===
echo.

:: 관리자 권한 확인
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 관리자 권한이 필요합니다.
    echo 스크립트를 관리자 권한으로 다시 실행해주세요.
    pause
    exit /b 1
)

:: 현재 시간과 유저는 고정값 사용
set "FIXED_TIME=2025-03-22 15:51:22"
set "FIXED_USER=hiboss112"

echo 레지스트리 설정을 적용합니다...

:: HKEY_LOCAL_MACHINE 설정
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: WOW6432Node 설정
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: HKEY_CURRENT_USER 설정 (시간과 유저 정보 포함)
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Username" /t REG_SZ /d "%FIXED_USER%" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "LastLoginTime" /t REG_SZ /d "%FIXED_TIME%" /f

echo.
echo 레지스트리 설정이 완료되었습니다.
echo 게임을 실행해주세요.
pause
