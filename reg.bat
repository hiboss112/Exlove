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

echo 레지스트리 초기화 중...

:: 먼저 HKCU 설정 (사용자별 설정)
echo HKCU 설정 중...
reg add "HKCU\SOFTWARE\idomnet" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKCU\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: 그 다음 HKLM 설정 (시스템 전역 설정)
echo HKLM 설정 중...
reg add "HKLM\SOFTWARE\idomnet" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: 마지막으로 WOW6432Node 설정
echo WOW6432Node 설정 중...
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "CompanyName" /t REG_SZ /d "idomnet" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "GameName" /t REG_SZ /d "Exlove" /f
reg add "HKLM\SOFTWARE\WOW6432Node\idomnet\Exlove" /v "Version" /t REG_SZ /d "1.0" /f

:: 설정 확인
echo 레지스트리 확인 중...
reg query "HKCU\SOFTWARE\idomnet\Exlove" >nul 2>&1
if errorlevel 1 (
    echo HKCU 레지스트리 설정 실패!
    pause
    exit /b 1
)

reg query "HKLM\SOFTWARE\idomnet\Exlove" >nul 2>&1
if errorlevel 1 (
    echo HKLM 레지스트리 설정 실패!
    pause
    exit /b 1
)

echo.
echo 레지스트리 설정 완료!
echo 게임을 실행해주세요.
pause
