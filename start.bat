@echo off
echo Запуск medcdss_api...
docker-compose up -d
echo Сервисы запущены.
echo Открываем Streamlit...
timeout /t 2 /nobreak >nul
start http://localhost:8501
echo API документация доступна по адресу: http://localhost:8000/docs
pause