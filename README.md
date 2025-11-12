# RechnungsTool - Professionelle deutsche Rechnungserstellung

[![Build Status](https://github.com/JP-Berges/E-Rechnungen_Schreiben/actions/workflows/build.yml/badge.svg)](https://github.com/JP-Berges/E-Rechnungen_Schreiben/actions)
[![Latest Release](https://img.shields.io/github/v/release/JP-Berges/E-Rechnungen_Schreiben)](https://github.com/JP-Berges/E-Rechnungen_Schreiben/releases)
[![macOS](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](https://github.com/JP-Berges/E-Rechnungen_Schreiben/releases)

**Erstellen Sie deutsche Rechnungen schnell und einfach - mit automatischer PDF- und XRechnung-Generierung!**

![RechnungsTool Demo](https://via.placeholder.com/800x400/1e1e2e/cdd6f4?text=RechnungsTool+Demo)

## 🚀 Features

- ✅ **Deutsche Standards**: DIN 5008, § 14 UStG konforme Rechnungen
- ✅ **Dual-Output**: PDF für Versand + XRechnung-XML für öffentliche Auftraggeber  
- ✅ **Kleinunternehmer**: Automatische MwSt-Behandlung nach § 19 UStG
- ✅ **Smart-Nummern**: Datumsbasierte Rechnungsnummern (YYYY-MM-DD-##)
- ✅ **Logo-Support**: Automatische Logo-Erkennung und Einbindung
- ✅ **Universal**: Native Builds für Intel und Apple Silicon Macs

## 📦 Download

**[→ Neueste Version herunterladen](https://github.com/JP-Berges/E-Rechnungen_Schreiben/releases/latest)**

### Verfügbare Builds:
- **🖥️ Intel Macs** → `RechnungsTool-Intel-macOS.zip`
- **🚀 Apple Silicon (M1/M2/M3)** → `RechnungsTool-AppleSilicon-macOS.zip`

> **💡 Tipp:** Nicht sicher welcher Mac? Die Intel-Version läuft auf allen Macs!

## 🛠️ Installation

1. **Download** der entsprechenden ZIP-Datei
2. **Entpacken** durch Doppelklick
3. **Starten** mit `INSTALL_UND_STARTEN.sh` oder direkt `RechnungsTool`
4. Bei macOS-Warnung: **Rechtsklick** → "Öffnen"

### Bei Problemen:
```bash
# Quarantäne entfernen
xattr -cr RechnungsTool

# Terminal-Start
./RechnungsTool
```

## 📋 Schnellstart

1. **Firmendaten** in `unternehmen.csv` eintragen
2. **Logo** als `logo.png` hinzufügen (optional)
3. **Programm starten** 
4. **Kunden anlegen** über Menü
5. **Rechnung erstellen** → PDF + XML automatisch generiert!

## 🎯 Beispiel-Output

### PDF-Rechnung:
- DIN 5008 Layout mit Faltmarken
- Deutsche Zahlenformatierung (1.234,56 €)
- Automatische MwSt-Berechnung
- Professionelles Design mit Logo

### XRechnung-XML:
- EN 16931 konform
- PEPPOL kompatibel
- Für öffentliche Auftraggeber
- Elektronische Übermittlung

## 🏗️ Entwicklung

### Lokaler Build

```bash
# Repository klonen
git clone https://github.com/JP-Berges/E-Rechnungen_Schreiben.git
cd E-Rechnungen_Schreiben

# Python Environment erstellen
python3 -m venv .venv
source .venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
pip install pyinstaller

# Build ausführen
python build_rechnungstool.py        # Intel/Universal
python build_apple_silicon.py        # Apple Silicon (nur auf M1/M2/M3)
```

### GitHub Actions

**Automatische Builds** für beide Architekturen:

- **Push zu main** → Development Builds
- **Version Tag** (`v1.0.0`) → Release mit GitHub Release
- **Pull Request** → Test Builds
- **Manuell** → Über GitHub Actions UI

## 📁 Projektstruktur

```
E-Rechnungen_Schreiben/
├── rechnungstool_menu.py         # Hauptprogramm (CLI Interface)
├── rechnungstool_backend.py      # PDF/XML-Generierung
├── build_rechnungstool.py        # Intel Build-Script
├── build_apple_silicon.py        # Apple Silicon Build-Script
├── requirements.txt              # Python Dependencies
├── unternehmen.csv              # Firmendaten (Beispiel)
├── kunden.csv                   # Kundendatenbank (Beispiel)
├── rechnungsnummer.json         # Rechnungsnummern-Tracker
└── .github/workflows/           # CI/CD Pipeline
```

## 🔧 Systemanforderungen

- **macOS 10.13** (High Sierra) oder neuer
- **~50 MB** freier Speicherplatz
- **Architektur**: Intel (x86_64) oder Apple Silicon (ARM64)

## 🐛 Problembehebung

### "Unbekannter Entwickler" Warnung
```bash
xattr -cr RechnungsTool
```

### Terminal Start bei GUI-Problemen
```bash
cd /pfad/zum/RechnungsTool
./RechnungsTool
```

### Dependencies prüfen
```bash
python3 -c "import reportlab, pypdf, lxml; print('✅ Alle OK')"
```

## 📞 Support & Community

- **🐛 Bug Reports**: [GitHub Issues](https://github.com/JP-Berges/E-Rechnungen_Schreiben/issues)
- **💡 Feature Requests**: [GitHub Discussions](https://github.com/JP-Berges/E-Rechnungen_Schreiben/discussions)
- **📧 Direct Contact**: jp.berges9@googlemail.com

## 🤝 Beitragen

Contributions sind willkommen! Bitte:

1. **Fork** das Repository
2. **Feature Branch** erstellen (`git checkout -b feature/amazing-feature`)
3. **Commit** deine Änderungen (`git commit -m 'Add amazing feature'`)
4. **Push** zum Branch (`git push origin feature/amazing-feature`)
5. **Pull Request** öffnen

## 📜 Lizenz

Dieses Projekt steht unter der **MIT License** - siehe [LICENSE](LICENSE) für Details.

## 🙏 Credits

- **ReportLab** für PDF-Generierung
- **PyPDF** für PDF-Manipulation  
- **lxml** für XML-Processing
- **PyInstaller** für macOS Builds

---

**© 2025 JP Engineering** | Made with ❤️ in Germany