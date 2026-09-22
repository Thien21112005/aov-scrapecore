@echo off
chcp 65001 > nul
title Lien Quan Mobile - Tool Tai Anh Tuong va Skin HD
echo Dang khoi dong giao dien do hoa (GUI)...
python main.py --gui
if %errorlevel% neq 0 (
    echo.
    echo [!] Gap loi khi khoi chay. Nhan phim bat ky de thoat...
    pause > nul
)
