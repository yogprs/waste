@echo off
REM ==============================================================
REM Setup Script for waste-homeserver (Windows)
REM Requires: Python 3.10 installed and available via 'py -3.10'
REM ==============================================================

echo ============================================
echo   waste-homeserver - Windows Setup
echo ============================================
echo.

REM --- Check Python 3.10 via py launcher ---
py -3.10 --version >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=py -3.10
    for /f "tokens=*" %%i in ('py -3.10 --version 2^>^&1') do set PYVER=%%i
    echo [OK] %PYVER% ditemukan via py launcher.
    goto :setup
)

REM --- Fallback: check python command ---
python --version >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYVER=%%i
    echo %PYVER% | findstr /b "3.10" >NUL
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python
        echo [OK] Python %PYVER% ditemukan.
        goto :setup
    ) else (
        echo [ERROR] Python yang ditemukan adalah versi %PYVER%, bukan 3.10.x
        echo [INFO] Install Python 3.10 dari: https://www.python.org/downloads/release/python-31011/
        echo [INFO] Pastikan centang "Add to PATH" saat install.
        pause
        exit /b 1
    )
)

echo [ERROR] Python tidak ditemukan!
echo [INFO] Install Python 3.10 dari: https://www.python.org/downloads/release/python-31011/
echo [INFO] Pastikan centang "Add to PATH" saat install.
pause
exit /b 1

:setup

REM --- Create virtual environment ---
if not exist ".venv" (
    echo.
    echo [INFO] Membuat virtual environment dengan Python 3.10...
    %PYTHON_CMD% -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Gagal membuat virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment berhasil dibuat.
) else (
    echo [INFO] Virtual environment sudah ada, skip pembuatan.
)

REM --- Activate virtual environment ---
echo [INFO] Mengaktifkan virtual environment...
call .venv\Scripts\activate.bat

REM --- Upgrade pip ---
echo [INFO] Mengupgrade pip...
python -m pip install --upgrade pip

REM --- Install dependencies ---
echo.
echo [INFO] Menginstall dependencies (ini mungkin memakan waktu)...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Gagal menginstall beberapa dependencies!
    echo [INFO] Coba jalankan ulang script ini.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Setup selesai!
echo ============================================
echo.
echo Cara menjalankan:
echo   1. Aktifkan venv:  .venv\Scripts\activate
echo   2. Jalankan app:   python app.py
echo   3. Atau gunakan:   run_windows.bat
echo.
echo Aplikasi akan berjalan di: http://localhost:3000
echo.
pause
