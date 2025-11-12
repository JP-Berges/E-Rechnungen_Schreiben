#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build-Script für Rechnungstool
==============================

Kompiliert das komplette Rechnungstool in eine ausführbare Datei
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

def build_rechnungstool():
    """Kompiliert das Rechnungstool"""
    print("🚀 RECHNUNGSTOOL KOMPILIERUNG")
    print("=" * 60)
    
    # Arbeitsverzeichnis
    work_dir = Path.cwd()
    print(f"📁 Arbeitsverzeichnis: {work_dir}")
    
    # Prüfe ob alle wichtigen Dateien vorhanden sind
    required_files = [
        "rechnungstool_menu.py",
        "rechnungstool_backend.py", 
        "unternehmen.csv"
    ]
    
    print("🔍 Prüfe erforderliche Dateien...")
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ FEHLER: {file} nicht gefunden!")
            return False
        else:
            print(f"✅ {file}")
    
    # Erstelle spec-Datei für erweiterte Konfiguration
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['rechnungstool_menu.py'],
    pathex=[],
    binaries=[],
    datas=[
        # KEINE Daten einbetten - sollen extern bearbeitbar bleiben
        # ('unternehmen.csv', '.'),  # <- Auskommentiert!
        # ('logo.png', '.'),         # <- Auskommentiert!
    ],
    hiddenimports=[
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib.pagesizes',
        'reportlab.lib.units',
        'pypdf',
        'csv',
        'json',
        'datetime',
        'hashlib',
        'xml.etree.ElementTree',
        'lxml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RechnungsTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    print("📝 Erstelle build-Konfiguration...")
    with open("rechnungstool.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    # PyInstaller Kommando - OHNE eingebettete Daten
    print("🔄 Starte Kompilierung...")
    # PyInstaller-Pfad für venv ermitteln
    pyinstaller_path = os.path.join(os.getcwd(), ".venv", "bin", "pyinstaller")
    if not os.path.exists(pyinstaller_path):
        # Fallback: System-PyInstaller versuchen
        pyinstaller_path = "pyinstaller"
    
    cmd = [
        os.path.join(work_dir, ".venv", "bin", "pyinstaller"),
        "--clean",
        "--onefile",
        "--name=RechnungsTool",
        # KEINE Daten einbetten - extern bearbeitbar lassen
        # "--add-data=unternehmen.csv:.",  # <- Entfernt!
        "--hidden-import=reportlab",
        "--hidden-import=pypdf", 
        "--hidden-import=lxml",
        "--hidden-import=xml.etree.ElementTree",
        # "--target-arch=universal2",  # Entfernt: Python ist kein fat binary
        "--codesign-identity=-",     # Ad-hoc Code Signing (x86_64 läuft via Rosetta auf Apple Silicon)
        "--console",
        "rechnungstool_menu.py"
    ]    # Logo NICHT einbetten - extern lassen
    print("ℹ️ Logo und CSV-Dateien bleiben extern bearbeitbar")
    
    print(f"🛠️ Kommando: {' '.join(cmd)}")
    print("⏳ Kompilierung läuft...")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Kompilierung erfolgreich!")
            
            # Erstelle Distributions-Ordner
            dist_dir = "RechnungsTool_Distribution"
            if os.path.exists(dist_dir):
                shutil.rmtree(dist_dir)
            os.makedirs(dist_dir)
            
            # Kopiere die Executable
            src_exe = os.path.join("dist", "RechnungsTool")
            dst_exe = os.path.join(dist_dir, "RechnungsTool")
            shutil.copy2(src_exe, dst_exe)
            
            # Executable ausführbar machen
            os.chmod(dst_exe, 0o755)
            
            # CSV-Dateien kopieren (extern bearbeitbar)
            for csv_file in ["unternehmen.csv", "kunden.csv", "rechnungsnummer.json"]:
                if os.path.exists(csv_file):
                    shutil.copy2(csv_file, dist_dir)
            
            # Rechnungen-Ordner erstellen
            rechnungen_dir = os.path.join(dist_dir, "Rechnungen")
            os.makedirs(rechnungen_dir, exist_ok=True)
            
            # Logo falls vorhanden
            logo_dateien = ["logo.png", "logo.jpg", "logo.jpeg"]
            for logo in logo_dateien:
                if os.path.exists(logo):
                    shutil.copy2(logo, dist_dir)
                    break
            
            # Verbesserte README mit Troubleshooting
            readme_content = """RECHNUNGSTOOL - PROFESSIONELLE RECHNUNGSERSTELLUNG
==================================================

⚠️  WICHTIG: NUR FÜR macOS (Apple Mac Computer)

SCHNELLSTART:
============
1. DOPPELKLICK auf 'RechnungsTool' 
2. Bei Warnung "Unbekannter Entwickler":
   → Rechtsklick → "Öffnen" → "Öffnen" bestätigen
3. Ihre Firmendaten in 'unternehmen.csv' eintragen
4. Optional: Logo als 'logo.png' hinzufügen

PROBLEMBEHEBUNG:
===============
Falls das Programm nicht startet:

🔧 LÖSUNG 1 - Sicherheitseinstellungen:
   Systemeinstellungen → Datenschutz & Sicherheit 
   → "Trotzdem öffnen" bei blockierter App

� LÖSUNG 2 - Terminal-Start (falls GUI nicht funktioniert):
   Terminal öffnen, dann eingeben:
   cd /Pfad/zum/RechnungsTool_Distribution
   ./RechnungsTool

🔧 LÖSUNG 3 - Quarantäne entfernen:
   Terminal: xattr -cr RechnungsTool

SYSTEMVORAUSSETZUNGEN:
=====================
✅ macOS 10.13 (High Sierra) oder neuer
✅ Intel Mac (x86_64) oder Apple Silicon (M1/M2/M3)

SUPPORT:
=======
Bei Problemen: jp.berges9@googlemail.com

© 2025 JP Engineering
"""
            with open(os.path.join(dist_dir, "README.txt"), "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            # Installationsscript für einfachere Weitergabe
            install_script = """#!/bin/bash
# Automatische Installation und Start des RechnungsTools

echo "🚀 RechnungsTool - Installation"
echo "=============================="

# Quarantäne entfernen (macOS Sicherheit)
echo "🔓 Entferne macOS-Quarantäne..."
xattr -cr ./RechnungsTool 2>/dev/null || true

# Ausführbar machen
echo "🔧 Setze Ausführungsrechte..."
chmod +x ./RechnungsTool

# Starten
echo "✅ Starte RechnungsTool..."
./RechnungsTool

echo "🎉 Installation abgeschlossen!"
"""
            
            install_path = os.path.join(dist_dir, "INSTALL_UND_STARTEN.sh")
            with open(install_path, "w") as f:
                f.write(install_script)
            os.chmod(install_path, 0o755)
            
            print(f"� Distribution erstellt in: {dist_dir}/")
            print("🎯 Für andere Macs: Ganzen Ordner weitergeben!")
            print("�️ Bei Problemen: INSTALL_UND_STARTEN.sh ausführen")
            return True
        else:
            print("❌ Kompilierung fehlgeschlagen!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei Kompilierung: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Starte Rechnungstool-Kompilierung...")
    
    if build_rechnungstool():
        print("\n🎉 ERFOLGREICH KOMPILIERT!")
        print("📦 Ihr Freunde können jetzt das RechnungsTool_Distribution Ordner verwenden!")
        print("💫 Keine Python-Installation bei Ihren Freunden erforderlich!")
    else:
        print("\n💥 KOMPILIERUNG FEHLGESCHLAGEN!")
        print("🔧 Bitte prüfen Sie die Fehlermeldungen oben.")