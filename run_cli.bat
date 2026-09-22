@echo off
chcp 65001 > nul
title Lien Quan Mobile - Tool Tai Anh Tuong va Skin HD (CLI)
python cli.py
if %errorlevel% neq 0 (
    echo.
    echo [!] Nhan phim bat ky de thoat...
    pause > nul
)
