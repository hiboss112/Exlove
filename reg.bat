@echo off
setlocal enabledelayedexpansion

echo === Exlove 레지스트리 설정 프로그램 ===
echo.

:: 관리자 권한 확인
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 관리자 권한으로 실행해주세요!
    echo 파일 우클릭 후 "관리자 권한으로 실행" 선택
    pause
    exit /b 1
)

:: 기존 키 삭제 (clean start)
reg delete "HKLM\SOFTWARE\idomnet" /f >nul 2>&1
reg delete "HKLM\SOFTWARE\WOW6432Node\idomnet" /f >nul 2>&1
reg delete "HKCU\SOFTWARE\idomnet" /f >nul 2>&1

echo 레지스트리 구조 생성 중...

:: HKEY_LOCAL_MACHINE (64bit)
echo HKLM 레지스트리 설정...
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: HKEY_LOCAL_MACHINE (32bit)
echo WOW6432Node 레지스트리 설정...
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: HKEY_CURRENT_USER
echo HKCU 레지스트리 설정...
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Username" /t REG_SZ /d "hiboss112" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "LastLoginTime" /t REG_SZ /d "2025-03-22 16:05:01" /f

:: 레지스트리 설정 확인
echo 레지스트리 설정 확인 중...

:: HKLM 확인
reg query "HKLM\SOFTWARE\idomnet\Exlove" >nul 2>&1
if errorlevel 1 (
    echo HKLM 레지스트리 설정 실패!
    echo 관리자 권한으로 다시 실행해주세요.
    pause
    exit /b 1
)

:: WOW6432Node 확인
reg query "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" >nul 2>&1
if errorlevel 1 (
    echo WOW6432Node 레지스트리 설정 실패!
    echo 관리자 권한으로 다시 실행해주세요.
    pause
    exit /b 1
)

:: HKCU 확인
reg query "HKCU\SOFTWARE\idomnet\Exlove" >nul 2>&1
if errorlevel 1 (
    echo HKCU 레지스트리 설정 실패!
    pause
    exit /b 1
)

echo.
echo 모든 레지스트리 설정이 완료되었습니다!
echo 게임을 실행해주세요.
pause
