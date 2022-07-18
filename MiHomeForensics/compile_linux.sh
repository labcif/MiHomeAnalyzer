#!/bin/bash
pyinstaller --noconfirm --onefile --console  "MiHomeForensics.py"
mv dist/ output/
rm -rf build
rm *.spec
read -p "Press enter to continue"
