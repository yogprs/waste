@echo off
REM ==============================================================
REM Run Script for waste-homeserver (Windows)
REM ==============================================================

echo ============================================
echo   waste-homeserver - Starting...
echo ============================================

REM --- Check virtual environment ---
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment belum dibuat!
    echo [INFO] Jalankan setup_windows.bat terlebih dahulu.
    pause
    exit /b 1
)

REM --- Activate and run ---
call .venv\Scripts\activate.bat

REM --- Check .env file ---
if not exist ".env" (
    echo [WARNING] File .env tidak ditemukan!
    echo [INFO] Buat file .env dengan isi:
    echo   DATABASE_URL=your_supabase_url
    echo   DATABASE_KEY=your_supabase_key
    echo.
)

echo [INFO] Menjalankan aplikasi...
echo [INFO] Akses di: http://localhost:3000
echo [INFO] Tekan Ctrl+C untuk menghentikan.
echo.

python app.py
