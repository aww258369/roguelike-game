@echo off
chcp 65001 >nul
title 轮回之战
echo ===============================
echo   轮回之战 — Roguelike 生存
echo ===============================
echo.
echo  WASD 移动 · F1 作弊菜单
echo  打怪升级 · 选天赋 · 挑战 Boss
echo.
echo  启动中...
start "" "D:\Python312\pythonw.exe" "D:\游戏\roguelike\main.py"
ping 127.0.0.1 -n 3 >nul
exit
