@echo off
echo ============================================================
echo  Speech Transcriber - Dependency Setup
echo ============================================================
echo.

echo Uninstalling any existing torch build (avoids dll conflicts)...
pip uninstall torch torchvision torchaudio -y 2>nul
echo.

echo Installing all dependencies (CPU-only PyTorch + Streamlit + Whisper + yt-dlp)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Install failed. Check the output above for details.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Setup complete! Run the app with:
echo    streamlit run app.py
echo ============================================================
pause
