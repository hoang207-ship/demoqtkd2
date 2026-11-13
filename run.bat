@echo off
chcp 65001 > nul
echo ========================================================
echo   KHỞI CHẠY AI AGENT B2B - CÔNG TY MINH AN (LOCALHOST)
echo ========================================================
echo.
echo Đang mở trình duyệt tại: http://localhost:8501 ...
echo.
start http://localhost:8501
.\.venv\Scripts\streamlit.exe run app.py --server.port 8501
pause

