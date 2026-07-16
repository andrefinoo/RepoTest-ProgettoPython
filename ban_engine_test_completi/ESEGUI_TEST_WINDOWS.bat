@echo off
setlocal

echo ========================================
echo  BAN ENGINE - VERIFICA COMPLETA
echo ========================================

py -m pytest -q
if errorlevel 1 goto errore

echo.
echo Test automatici superati.
echo.

py -m ban_engine --help
if errorlevel 1 goto errore

echo.
echo Avvio demo dry-run...
py -m ban_engine --log examples/auth.log --config examples/config.json --dry-run
if errorlevel 1 goto errore

echo.
echo ========================================
echo  TUTTI I CONTROLLI SONO PASSATI
echo ========================================
exit /b 0

:errore
echo.
echo ========================================
echo  CONTROLLO FALLITO
echo ========================================
exit /b 1
