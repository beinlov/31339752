@echo off
echo Starting Log Processor with verbose logging...
cd /d "%~dp0backend\log_processor"
python main.py
pause
