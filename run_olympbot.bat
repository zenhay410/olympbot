@echo off
echo ===========================
echo Installing dependencies...
echo ===========================
pip install -r requirements.txt

echo ===========================
echo Running parser...
echo ===========================
python parcer.py

echo ===========================
echo Launching Telegram bot...
echo ===========================
start cmd /k "python bot.py"

timeout /t 2 >nul

echo ===========================
echo Launching notifier...
echo ===========================
start cmd /k "python notifier.py"

echo ===========================
echo All systems started successfully.
echo Keep this window open if you want to monitor.
echo ===========================

pause
