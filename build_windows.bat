@echo off
REM Gera o app (pasta dist\Omega) e, se o Inno Setup 6 estiver instalado, o instalador Omega-Setup.exe
cd /d "%~dp0"
pip install -r requirements.txt pyinstaller || goto :err
pyinstaller --noconfirm --clean --windowed --name Omega --icon assets\icon.ico --add-data "assets;assets" omega.py || goto :err
where iscc >nul 2>nul
if %errorlevel%==0 (iscc installer\omega.iss) else (echo.& echo Instale o Inno Setup 6 ^(jrsoftware.org^) e rode de novo para gerar o Omega-Setup.exe)
goto :eof
:err
echo Falhou.
