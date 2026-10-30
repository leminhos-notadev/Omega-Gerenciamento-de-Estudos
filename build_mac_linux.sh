#!/bin/sh
# macOS: gera Omega.app + Omega.dmg   |   Linux: gera dist/Omega + Omega-linux.tar.gz
cd "$(dirname "$0")"
pip install -r requirements.txt pyinstaller || exit 1
if [ "$(uname)" = "Darwin" ]; then
  pyinstaller --noconfirm --clean --windowed --name Omega --icon assets/icon.icns --add-data "assets:assets" omega.py || exit 1
  hdiutil create -volname Omega -srcfolder dist/Omega.app -ov -format UDZO Omega.dmg
else
  pyinstaller --noconfirm --clean --windowed --name Omega --add-data "assets:assets" omega.py || exit 1
  tar -czf Omega-linux.tar.gz -C dist Omega
fi
