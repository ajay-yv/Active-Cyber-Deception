@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" goto help

set "PYTHON_BIN=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_BIN%" set "PYTHON_BIN=python"

set "ATTACK=%~1"
set "COUNT_ARG="
set "TARGET_ARG="

if "%ATTACK%"=="1" (
    set "ATTACK=patient"
    set "COUNT_ARG=--patient P-01"
    if not "%~2"=="" (
        if "%~2:~0,4%"=="http" (
            set "TARGET_ARG=--target %~2"
        )
    )
    goto run
)

if "%ATTACK%"=="patient" (
    set "ATTACK=patient"
    if not "%~2"=="" (
        if "%~2:~0,4%"=="http" (
            set "TARGET_ARG=--target %~2"
            set "COUNT_ARG=--patient P-01"
        ) else (
            set "COUNT_ARG=--patient %~2"
        )
    ) else (
        set "COUNT_ARG=--patient P-01"
    )
    if not "%~3"=="" set "TARGET_ARG=--target %~3"
    goto run
)

if not "%~2"=="" set "COUNT_ARG=--count %~2"
if not "%~3"=="" set "TARGET_ARG=--target %~3"

:run
%PYTHON_BIN% "%~dp0tools\security_simulator.py" --attack %ATTACK% %COUNT_ARG% %TARGET_ARG%
goto :eof

:help
echo ======================================================================
echo          Healthcare Cyber Deception - Terminal Attack Runner
echo ======================================================================
echo Usage:
echo   attack.bat ^<attack_type^> [count_or_patient_id] [target_url]
echo.
echo Single Patient Commands (Requires 1 Patient Data):
echo   attack.bat 1                - Hack exactly 1 patient record (returns 1 synthetic twin)
echo   attack.bat patient P-01     - Hack specific patient P-01 (returns 1 synthetic twin)
echo   attack.bat exfiltration 1   - Exfiltrate 1 patient record
echo.
echo Bulk Attack Types:
echo   sqli                - SQL injection database dump probe
echo   enumeration         - Sequential patient record harvesting
echo   exfiltration        - Bulk patient records extraction
echo   brute-force         - Password guessing authentication attack
echo   credential-stuffing - Multi-account credential replay attack
echo   traversal           - Path/Directory traversal probe
echo   api-abuse           - High-frequency endpoint flooding
echo   session-abuse       - Forged session and invalid token replay
echo.
echo Examples:
echo   attack.bat 1
echo   attack.bat patient P-01
echo   attack.bat exfiltration 1
echo   attack.bat exfiltration 5
echo   attack.bat sqli
echo   attack.bat brute-force 3
echo ======================================================================
