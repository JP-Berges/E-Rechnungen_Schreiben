#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build-Script für Rechnungstool - Apple Silicon Native
====================================================

Kompiliert das Rechnungstool als natives ARM64 Binary für M1/M2/M3 Macs
ACHTUNG: Funktioniert nur auf Apple Silicon Macs!
"""

import os
import subprocess
import sys
import shutil
import platform
from pathlib import Path

def check_apple_silicon():
    """Prüft ob wir auf Apple Silicon laufen"""
    machine = platform.machine()
    print(f"🔍 Erkannte Architektur: {machine}")
    
    if machine != "arm64":
        print("⚠️  WARNUNG: Nicht auf Apple Silicon!")
        print("📱 Dieses Script funktioniert nur auf M1/M2/M3 Macs")
        print("🔄 Für Intel Macs: Verwenden Sie build_rechnungstool.py")
        
        antwort = input("🤔 Trotzdem fortfahren? (j/N): ").lower()
        return antwort in ['j', 'ja', 'y', 'yes']
    
    print("✅ Apple Silicon erkannt - natives ARM64 Build möglich!")
    return True

def build_rechnungstool_silicon():
    """Kompiliert das Rechnungstool als ARM64 Binary"""
    print("🚀 RECHNUNGSTOOL KOMPILIERUNG - APPLE SILICON NATIVE")
    print("=" * 65)
    
    if not check_apple_silicon():
        return False
    
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
    datas=[],
    hiddenimports=['reportlab', 'pypdf', 'lxml', 'xml.etree.ElementTree'],
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
    name='RechnungsTool_Silicon',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    print("📝 Erstelle Silicon-Build-Konfiguration...")
    with open("rechnungstool_silicon.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    # Ermittle Python-Pfad (venv oder system)
    if getattr(sys, 'frozen', False):
        python_exe = sys.executable
    elif hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # venv
        python_exe = os.path.join(sys.prefix, 'bin', 'python')
        pyinstaller_exe = os.path.join(sys.prefix, 'bin', 'pyinstaller')
    else:
        # system python
        python_exe = sys.executable
        pyinstaller_exe = 'pyinstaller'
    
    print(f"🐍 Python: {python_exe}")
    
    # PyInstaller Kommando - ARM64 spezifisch
    print("🔄 Starte ARM64-Kompilierung...")
    cmd = [
        pyinstaller_exe,
        "--clean",
        "--onefile", 
        "--name=RechnungsTool_Silicon",
        "--target-arch=arm64",  # Explizit ARM64
        "--codesign-identity=-",  # Ad-hoc signing
        "--hidden-import=reportlab",
        "--hidden-import=pypdf", 
        "--hidden-import=lxml",
        "--hidden-import=xml.etree.ElementTree",
        "--console",
        "rechnungstool_menu.py"
    ]
    
    print("ℹ️ ARM64-natives Binary für beste Performance auf Apple Silicon")
    print(f"🛠️ Kommando: {' '.join(cmd)}")
    print("⏳ Kompilierung läuft...")
    print("-" * 65)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ARM64-Kompilierung erfolgreich!")
            
            # Erstelle ARM64-Distributions-Ordner (GitHub Actions kompatibel)
            dist_dir = "RechnungsTool_Distribution_ARM64"
            if os.path.exists(dist_dir):
                shutil.rmtree(dist_dir)
            os.makedirs(dist_dir)
            
            # Kopiere die ARM64-Executable
            src_exe = os.path.join("dist", "RechnungsTool_Silicon")
            dst_exe = os.path.join(dist_dir, "RechnungsTool")  # Standardname für Konsistenz
            shutil.copy2(src_exe, dst_exe)
            
            # Executable ausführbar machen
            os.chmod(dst_exe, 0o755)
            
            # Prüfe Architektur des erstellten Binaries
            try:
                arch_result = subprocess.run(["file", dst_exe], capture_output=True, text=True)
                print(f"🔍 Binary-Architektur: {arch_result.stdout.strip()}")
            except:
                pass
            
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
            
            # Silicon-spezifische README
            readme_content = """RECHNUNGSTOOL - APPLE SILICON NATIVE
====================================

🚀 OPTIMIERT FÜR M1/M2/M3 MACS (ARM64)

Diese Version ist als natives ARM64-Binary kompiliert für:
✅ Beste Performance auf Apple Silicon Macs
✅ Geringerer Energieverbrauch
✅ Keine Rosetta 2 Emulation nötig

KOMPATIBILITÄT:
==============
✅ Apple Silicon (M1/M2/M3/M4) - NATIV
❌ Intel Macs - NICHT KOMPATIBEL!

Für Intel Macs verwenden Sie bitte:
→ RechnungsTool_Distribution (x86_64 Version)

SCHNELLSTART:
============
1. DOPPELKLICK auf 'RechnungsTool_Silicon'
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

🔧 LÖSUNG 2 - Terminal-Start:
   Terminal öffnen, dann:
   cd /Pfad/zum/RechnungsTool_Silicon_Native
   ./RechnungsTool_Silicon

🔧 LÖSUNG 3 - Quarantäne entfernen:
   Terminal: xattr -cr RechnungsTool_Silicon

SYSTEMVORAUSSETZUNGEN:
=====================
✅ macOS 11.0 (Big Sur) oder neuer
✅ Apple Silicon Mac (M1/M2/M3/M4)

SUPPORT:
=======
Bei Problemen: jp.berges9@googlemail.com

© 2025 JP Engineering - Apple Silicon Optimiert
"""
            
            with open(os.path.join(dist_dir, "README.txt"), "w", encoding="utf-8") as f:
                f.write(readme_content)
            
            # Silicon-Installationsscript
            install_script = """#!/bin/bash
# Apple Silicon Native Installation

echo "🚀 RechnungsTool - Apple Silicon Native Installation"
echo "=================================================="

# Architecture Check
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo "❌ FEHLER: Nicht auf Apple Silicon!"
    echo "📱 Diese Version funktioniert nur auf M1/M2/M3 Macs"
    echo "🔄 Für Intel Macs: Verwenden Sie die x86_64 Version"
    exit 1
fi

echo "✅ Apple Silicon erkannt"

# Quarantäne entfernen
echo "🔓 Entferne macOS-Quarantäne..."
xattr -cr ./RechnungsTool_Silicon 2>/dev/null || true

# Ausführbar machen
echo "🔧 Setze Ausführungsrechte..."
chmod +x ./RechnungsTool_Silicon

# Starten
echo "✅ Starte RechnungsTool (ARM64 nativ)..."
./RechnungsTool_Silicon

echo "🎉 Installation abgeschlossen!"
"""
            
            install_path = os.path.join(dist_dir, "INSTALL_UND_STARTEN.sh")
            with open(install_path, "w") as f:
                f.write(install_script)
            os.chmod(install_path, 0o755)
            
            print(f"📦 Apple Silicon Distribution erstellt: {dist_dir}/")
            print("🚀 Natives ARM64 Binary für optimale Performance!")
            print("📱 NUR für M1/M2/M3 Macs - Beste Performance!")
            print("⚡ Keine Rosetta 2 Emulation erforderlich")
            return True
            
        else:
            print("❌ ARM64-Kompilierung fehlgeschlagen!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei ARM64-Kompilierung: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Starte Apple Silicon Native Kompilierung...")
    
    if build_rechnungstool_silicon():
        print("\n🎉 APPLE SILICON BINARY ERFOLGREICH ERSTELLT!")
        print("🚀 Optimiert für M1/M2/M3 Macs - Beste Performance!")
        print("📦 Distribution bereit für Apple Silicon Macs!")
    else:
        print("\n💥 KOMPILIERUNG FEHLGESCHLAGEN!")
        print("🔧 Prüfen Sie die Fehlermeldungen oben.")
        print("💡 Tipp: Funktioniert nur auf Apple Silicon Macs!")