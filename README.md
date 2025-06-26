# slack-migration-tool

# Slack Migrator

## Beschreibung
GUI-Tool zum Migrieren von Slack-Channels (Nachrichten, Threads, Dateien, Emojis).

## Setup

1. Python 3 installieren (macOS standardmäßig vorhanden).
2. Abhängigkeiten installieren:

# pip install -r requirements.txt

3. (Optional) Icon `icon.icns` ersetzen.

## Lokaler Build

```bash
pyinstaller --onefile --windowed --icon=icon.icns --osx-bundle-identifier=com.deinunternehmen.slackmigrator slack_gui_migrator.py

# Die .app erscheint in dist/.

Nutzung
App starten und Slack Token, Export-Ordner, Channel-Mapping eingeben.
