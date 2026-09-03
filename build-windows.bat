@echo off
setlocal
cd /d "%~dp0"

echo === Philippine Cheque Writer — Windows build ===
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher "py" not found. Install Python 3.11+ from python.org
  pause
  exit /b 1
)

echo [1/4] Installing build dependencies...
py -3 -m pip install -q --upgrade pip
py -3 -m pip install -q -r requirements.txt "pyinstaller>=6.0"
if errorlevel 1 (
  echo Failed to install dependencies.
  pause
  exit /b 1
)

echo [2/4] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist\PhilippineChequeWriter rmdir /s /q dist\PhilippineChequeWriter
if exist dist\PhilippineChequeWriter-Portable.zip del /f /q dist\PhilippineChequeWriter-Portable.zip

echo [3/4] Building app with PyInstaller...
py -3 -m PyInstaller --noconfirm packaging\cheque_writer.spec
if errorlevel 1 (
  echo PyInstaller build failed.
  pause
  exit /b 1
)

echo [4/4] Creating portable ZIP...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\PhilippineChequeWriter\*' -DestinationPath 'dist\PhilippineChequeWriter-Portable.zip' -Force"
if errorlevel 1 (
  echo ZIP step failed, but the folder dist\PhilippineChequeWriter may still be usable.
)

echo.
where iscc >nul 2>&1
if errorlevel 1 (
  echo Portable build ready:
  echo   dist\PhilippineChequeWriter\PhilippineChequeWriter.exe
  echo   dist\PhilippineChequeWriter-Portable.zip
  echo.
  echo Optional: install Inno Setup, then run:
  echo   iscc packaging\cheque_writer.iss
  echo to create dist\PhilippineChequeWriter-Setup.exe
) else (
  echo Building Setup installer with Inno Setup...
  iscc packaging\cheque_writer.iss
  if errorlevel 1 (
    echo Inno Setup compile failed. Portable ZIP is still available.
  ) else (
    echo Setup installer ready: dist\PhilippineChequeWriter-Setup.exe
  )
)

echo.
echo Done. Copy the ZIP or Setup.exe to the other PC.
pause
