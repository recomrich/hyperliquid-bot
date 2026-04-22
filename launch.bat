@echo off
cd /d "C:\Users\rsser\hyperliquid-bot"

:: Lance le bot dans une fenêtre séparée
start "Hyperliquid Bot" cmd /k "python main.py"

:: Lance Claude Code dans une autre fenêtre
start "Claude Code" cmd /k "claude"
