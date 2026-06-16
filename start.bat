@echo off
cd /d "%~dp0"
echo OPG Faulty Tooth Detection - http://localhost:4005
python flask_app.py
pause
