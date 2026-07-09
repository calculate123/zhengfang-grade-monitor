@echo off
chcp 65001 >nul
echo ====================================
echo   成绩监控 - 打包为 EXE
echo ====================================
echo.

echo [1/3] 安装依赖...
pip install pyinstaller pynacl requests -q

echo [2/3] 打包中（约1分钟）...
pyinstaller --onefile --windowed --name "成绩监控" --add-data "monitor.py;." --add-data "requirements.txt;." app.py

echo [3/3] 完成！
echo.
echo EXE 文件位置: dist\成绩监控.exe
echo 文件大小:
dir "dist\成绩监控.exe" 2>nul
echo.
echo 将此文件发给同学即可，他们不需要安装 Python。
pause
