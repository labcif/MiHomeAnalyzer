pyinstaller --noconfirm --onefile --console  "MiHomeForensics.py"
ren dist output
rmdir /s /q build
del *.spec
pause
