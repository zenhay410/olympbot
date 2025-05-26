@echo off
echo 🔧 Установка зависимостей...
pip install -r requirements.txt

echo 📦 Парсим олимпиады...
python parcer.py

echo 🚀 Запускаем Telegram-бота...
start "" python bot.py

timeout /t 2 >nul

echo 🔔 Запускаем уведомлялку...
start "" python notifier.py

echo ✅ Всё запущено!
pause
