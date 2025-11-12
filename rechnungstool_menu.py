import csv
import os
import sys
import json
import hashlib
import random
import subprocess
import glob
import shutil
import time
from datetime import datetime
from rechnungstool_backend import erstelle_rechnung

class RechnungsManager:
    def __init__(self):
        # Pfad zur Executable/zum Skript ermitteln (PyInstaller-kompatibel)
        if getattr(sys, 'frozen', False):
            # Läuft als PyInstaller-Executable
            self.base_dir = os.path.dirname(sys.executable)
        else:
            # Läuft als Python-Skript
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.unternehmen_file = os.path.join(self.base_dir, "unternehmen.csv")
        self.kunden_file = os.path.join(self.base_dir, "kunden.csv")
        self.rechnungsnummer_file = os.path.join(self.base_dir, "rechnungsnummer.json")
        self.rechnungen_dir = os.path.join(self.base_dir, "Rechnungen")
        
        self.unternehmen_daten = self.lade_unternehmen_daten()
        self.kunden = self.lade_kunden()
        
        if not os.path.exists(self.rechnungen_dir):
            os.makedirs(self.rechnungen_dir)
    
    def lade_unternehmen_daten(self):
        try:
            with open(self.unternehmen_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return next(reader)
        except:
            return {}
    
    def lade_kunden(self):
        kunden = {}
        try:
            with open(self.kunden_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    kunden[row['Kundennummer']] = row
        except:
            pass
        return kunden
    
    def generiere_kundennummer(self, kunde_data):
        """Generiert eine undurchsichtige Kundennummer basierend auf Kundendaten und Zufallszahl"""
        # Eindeutiger String aus Kundendaten
        unique_string = f"{kunde_data['Firmenname']}{kunde_data['Straße']}{kunde_data['PLZ']}{kunde_data['Ort']}"
        
        # Aktueller Timestamp für zusätzliche Eindeutigkeit
        timestamp = str(datetime.now().timestamp())
        
        # Zufallszahl für mehr Unvorhersagbarkeit
        random_part = str(random.randint(1000, 9999))
        
        # Hash erstellen
        hash_input = f"{unique_string}{timestamp}{random_part}"
        hash_object = hashlib.sha256(hash_input.encode())
        hash_hex = hash_object.hexdigest()
        
        # Nur die ersten 8 Zeichen verwenden und mit K präfixieren
        neue_nummer = f"K{hash_hex[:8].upper()}"
        
        # Sicherstellen, dass die Nummer einzigartig ist
        while neue_nummer in self.kunden:
            random_part = str(random.randint(1000, 9999))
            hash_input = f"{unique_string}{timestamp}{random_part}"
            hash_object = hashlib.sha256(hash_input.encode())
            hash_hex = hash_object.hexdigest()
            neue_nummer = f"K{hash_hex[:8].upper()}"
        
        return neue_nummer

    def speichere_kunde(self, kunde_data):
        # Undurchsichtige Kundennummer generieren
        neue_nummer = self.generiere_kundennummer(kunde_data)
        
        kunde_data['Kundennummer'] = neue_nummer
        self.kunden[neue_nummer] = kunde_data
        
        # CSV aktualisieren
        fieldnames = ['Kundennummer', 'Firmenname', 'Ansprechpartner', 'Straße', 'Hausnummer', 'PLZ', 'Ort', 'Land', 'Telefon', 'Email', 'Bemerkungen']
        with open(self.kunden_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for kunde in self.kunden.values():
                writer.writerow(kunde)
        
        return neue_nummer
    
    def lade_letzte_nummern(self):
        """Lädt die gespeicherten Rechnungsnummern pro Tag"""
        try:
            with open(self.rechnungsnummer_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def speichere_letzte_nummern(self, nummern_dict):
        """Speichert die Rechnungsnummern pro Tag"""
        with open(self.rechnungsnummer_file, "w") as f:
            json.dump(nummern_dict, f, indent=2)
    
    def generiere_rechnungsnummer(self, datum):
        """Generiert eine datumsbasierte Rechnungsnummer im Format YYYY-MM-DD-##"""
        # Datum in YYYY-MM-DD Format umwandeln
        datum_obj = datetime.strptime(datum, "%d.%m.%Y")
        datum_key = datum_obj.strftime("%Y-%m-%d")
        
        # Bisherige Nummern laden
        nummern_dict = self.lade_letzte_nummern()
        
        # Tägliche Nummer ermitteln
        if datum_key in nummern_dict:
            naechste_nummer = nummern_dict[datum_key] + 1
        else:
            naechste_nummer = 1
        
        # Neue Nummer speichern
        nummern_dict[datum_key] = naechste_nummer
        self.speichere_letzte_nummern(nummern_dict)
        
        # Rechnungsnummer im Format YYYY-MM-DD-## zurückgeben
        return f"{datum_key}-{naechste_nummer:02d}"

def system_reset_menu():
    """System-Reset mit Benutzerbestätigung"""
    print("\n🧹 SYSTEM-RESET")
    print("=" * 50)
    print("⚠️  ACHTUNG: Dies wird folgende Aktionen durchführen:")
    print("   🔪 Alle Python-Prozesse beenden")
    print("   🗑️ Python-Cache löschen (__pycache__, *.pyc)")
    print("   📁 Temporäre ZUGFeRD-Dateien entfernen")
    print("   🔄 Import-Cache zurücksetzen")
    print()
    print("✅ Ihre Daten bleiben erhalten:")
    print("   📄 Alle erstellten Rechnungen")
    print("   👥 Kundendaten")
    print("   🏢 Unternehmensdaten")
    print()
    
    bestaetigung = input("🤔 System-Reset durchführen? (j/N): ").lower()
    
    if bestaetigung in ['j', 'ja', 'y', 'yes']:
        print("\n🧹 Führe System-Reset durch...")
        
        try:
            # 1. Prozesse beenden (außer dem aktuellen)
            print("🔪 Beende andere Python-Prozesse...")
            subprocess.run(["pkill", "-f", "rechnungstool"], capture_output=True)
            time.sleep(0.5)
            
            # 2. Cache löschen
            print("🗑️ Lösche Python-Cache...")
            cache_count = 0
            
            # __pycache__ Ordner löschen
            for pycache_dir in glob.glob("**/__pycache__", recursive=True):
                try:
                    shutil.rmtree(pycache_dir)
                    cache_count += 1
                except:
                    pass
            
            # .pyc Dateien löschen
            for pyc_file in glob.glob("**/*.pyc", recursive=True):
                try:
                    os.remove(pyc_file)
                    cache_count += 1
                except:
                    pass
            
            # 3. Temporäre Dateien löschen
            print("� Lösche temporäre Dateien...")
            temp_count = 0
            temp_patterns = ["temp_invoice_*.xml", "test_*.xml", "*.tmp"]
            
            for pattern in temp_patterns:
                for temp_file in glob.glob(pattern):
                    try:
                        os.remove(temp_file)
                        temp_count += 1
                    except:
                        pass
            
            # 4. Import-Cache zurücksetzen
            print("🔄 Setze Import-Cache zurück...")
            import sys
            modules_to_remove = [m for m in sys.modules.keys() 
                               if any(keyword in m.lower() for keyword in 
                                     ['rechnungstool', 'zugferd', 'facturx'])]
            
            for module in modules_to_remove:
                try:
                    del sys.modules[module]
                except:
                    pass
            
            print(f"✅ Reset abgeschlossen!")
            print(f"   🗑️ {cache_count} Cache-Dateien gelöscht")
            print(f"   📁 {temp_count} temporäre Dateien entfernt")
            print(f"   🔄 {len(modules_to_remove)} Module aus Cache entfernt")
            print()
            print("🚀 System bereit für den Betrieb!")
            
            input("📱 Drücken Sie Enter um fortzufahren...")
            
        except Exception as e:
            print(f"❌ Fehler beim Reset: {e}")
            print("⚠️ System läuft weiter...")
            input("📱 Drücken Sie Enter um fortzufahren...")
    else:
        print("❌ Reset abgebrochen")
        input("📱 Drücken Sie Enter um fortzufahren...")

def zeige_kunden(manager):
    """Zeigt alle Kunden an"""
    print("\n�📋 ALLE KUNDEN:")
    print("-" * 60)
    if not manager.kunden:
        print("Noch keine Kunden vorhanden.")
        return
    
    for kunde in manager.kunden.values():
        # Unterscheidung zwischen Firma und Privatperson
        typ_icon = "🏢" if kunde.get('Ansprechpartner') else "👤"
        typ_text = "Firma" if kunde.get('Ansprechpartner') else "Privatperson"
        
        print(f"{kunde['Kundennummer']}: {typ_icon} {kunde['Firmenname']} ({kunde['Ort']}) - {typ_text}")
        if kunde.get('Ansprechpartner'):
            print(f"         Ansprechpartner: {kunde['Ansprechpartner']}")
        print(f"         {kunde.get('Straße', '')} {kunde.get('Hausnummer', '')}, {kunde.get('PLZ', '')} {kunde.get('Ort', '')}")
        print(f"         Email: {kunde.get('Email', '')}")
        print()

def neuer_kunde(manager):
    print("\n➕ NEUER KUNDE:")
    print("-" * 40)
    
    kunde_data = {}
    kunde_data['Firmenname'] = input("Firmenname (leer lassen für Privatperson): ")
    
    # Wenn kein Firmenname, dann Name der Person erfragen
    if not kunde_data['Firmenname']:
        name_person = input("Name der Person: ")
        if not name_person:
            print("❌ Name ist erforderlich!")
            return
        kunde_data['Firmenname'] = name_person  # Name als "Firmenname" speichern
        kunde_data['Ansprechpartner'] = ""  # Leer lassen für Privatpersonen
        print(f"📝 Kunde als Privatperson angelegt: {name_person}")
    else:
        kunde_data['Ansprechpartner'] = input("Ansprechpartner (optional): ")
    kunde_data['Straße'] = input("Straße: ")
    kunde_data['Hausnummer'] = input("Hausnummer: ")
    kunde_data['PLZ'] = input("PLZ: ")
    kunde_data['Ort'] = input("Ort: ")
    kunde_data['Land'] = input("Land [DE]: ") or "DE"
    kunde_data['Telefon'] = input("Telefon (optional): ")
    kunde_data['Email'] = input("Email: ")
    kunde_data['Bemerkungen'] = input("Bemerkungen (optional): ")
    
    neue_nummer = manager.speichere_kunde(kunde_data)
    print(f"✅ Kunde gespeichert mit Nummer: {neue_nummer}")

def rechnung_erstellen_dialog(manager):
    print("\n💼 RECHNUNG ERSTELLEN:")
    print("-" * 50)
    
    # Kunde auswählen - Benutzerfreundliche numerische Auswahl
    if not manager.kunden:
        print("❌ Noch keine Kunden vorhanden! Bitte erst einen Kunden anlegen.")
        return
    
    print("Verfügbare Kunden:")
    print("-" * 50)
    kunden_liste = list(manager.kunden.items())
    for i, (nr, kunde) in enumerate(kunden_liste, 1):
        # Firmenname oder Privatperson erkennen
        if kunde.get('Ansprechpartner'):
            kunde_typ = "🏢"
            zusatz = f" (Ansprechpartner: {kunde['Ansprechpartner']})"
        else:
            kunde_typ = "👤"
            zusatz = " (Privatperson)"
        print(f"{i:2d}. {kunde_typ} {kunde['Firmenname']}{zusatz}")
        print(f"    📍 {kunde.get('Ort', 'Unbekannt')}")
    
    print("-" * 50)
    
    # Numerische Auswahl
    while True:
        try:
            auswahl = input(f"Kunde auswählen (1-{len(kunden_liste)}): ").strip()
            if not auswahl:
                print("❌ Bitte eine Nummer eingeben!")
                continue
                
            auswahl_nr = int(auswahl)
            if 1 <= auswahl_nr <= len(kunden_liste):
                kunde_nr, kunde_data = kunden_liste[auswahl_nr - 1]
                print(f"✅ Kunde gewählt: {kunde_data['Firmenname']}")
                break
            else:
                print(f"❌ Bitte eine Nummer zwischen 1 und {len(kunden_liste)} eingeben!")
        except ValueError:
            print("❌ Bitte eine gültige Nummer eingeben!")
    
    
    # Datum
    datum = input(f"Rechnungsdatum [{datetime.today().strftime('%d.%m.%Y')}]: ") or datetime.today().strftime('%d.%m.%Y')
    
    # Freitext
    print("\nFrei wählbarer Begrüßungstext:")
    print("(Leer lassen für Standard: 'Vielen Dank für Ihr Vertrauen...')")
    freitext = input("Ihr Text: ") or None
    
    # Positionen
    positionen = []
    print("\nRechnungspositionen eingeben (leere Bezeichnung beendet):")

    while True:
        print(f"\nPosition {len(positionen) + 1}:")
        bezeichnung = input("Bezeichnung: ")
        if not bezeichnung:
            break
        
        try:
            menge = float(input("Menge: "))
            einzelpreis = float(input("Einzelpreis: "))
            
            positionen.append({
                'bezeichnung': bezeichnung,
                'menge': menge,
                'einzelpreis': einzelpreis
            })
            
            gesamt = menge * einzelpreis
            print(f"➡ Position hinzugefügt: {menge} x {einzelpreis:.2f}€ = {gesamt:.2f}€")
            
        except ValueError:
            print("❌ Ungültige Eingabe für Menge oder Preis!")
    
    if not positionen:
        print("❌ Keine Positionen eingegeben!")
        return
    
    # Datumsbasierte Rechnungsnummer generieren
    rechnungsnummer = manager.generiere_rechnungsnummer(datum)
    
    print(f"\n🔄 Erstelle Rechnung {rechnungsnummer}...")
    
    erfolg = erstelle_rechnung(
        rechnungsnummer=rechnungsnummer,
        kunde_data=kunde_data,
        unternehmen_data=manager.unternehmen_daten,
        datum=datum,
        positionen=positionen,
        rechnungen_dir=manager.rechnungen_dir,
        freitext=freitext
    )
    
    if erfolg:
        betrag = sum(pos["menge"] * pos["einzelpreis"] for pos in positionen)
        
        # Kleinunternehmer prüfen
        ist_kleinunternehmer = manager.unternehmen_daten.get('Kleinunternehmer', 'nein').lower() in ['ja', 'yes', 'true', '1']
        
        if ist_kleinunternehmer:
            gesamt_betrag = betrag
            steuer_hinweis = "(keine MwSt - Kleinunternehmerregelung § 19 UStG)"
        else:
            gesamt_betrag = betrag * 1.19
            steuer_hinweis = "(inkl. 19% MwSt.)"
        
        print(f"\n✅ Rechnung {rechnungsnummer} erfolgreich erstellt!")
        print(f"📄 PDF-Rechnung: Rechnungen/Rechnung_{rechnungsnummer.replace(':', '-')}.pdf")
        print(f"📋 XRechnung-XML: Rechnungen/XRechnung_{rechnungsnummer.replace(':', '-')}.xml")
        print(f"💰 Gesamtbetrag: {gesamt_betrag:.2f}€ {steuer_hinweis}")
        print(f"🔢 Format: YYYY-MM-DD-## (Jahr-Monat-Tag-Tagesnummer)")
    else:
        print("❌ Fehler beim Erstellen der Rechnung!")

def zeige_rechnungsnummern_demo(manager):
    """Zeigt eine Demo des neuen Rechnungsnummernsystems mit aktuellen Informationen"""
    print("\n📋 RECHNUNGSNUMMERN-SYSTEM (Datumsbasiert):")
    print("-" * 60)
    print("Format: YYYY-MM-DD-## (Jahr-Monat-Tag-Tagesnummer)")
    
    # Aktuelle Rechnungsnummern-Daten laden
    nummern_dict = manager.lade_letzte_nummern()
    heute = datetime.today().strftime("%Y-%m-%d")
    
    print("\n📊 AKTUELLER STATUS:")
    print("-" * 30)
    
    if nummern_dict:
        # Letzte verwendete Rechnungsnummer finden
        letzte_datum = max(nummern_dict.keys())
        letzte_nummer_im_datum = nummern_dict[letzte_datum]
        letzte_vollnummer = f"{letzte_datum}-{letzte_nummer_im_datum:02d}"
        print(f"📋 Letzte Rechnungsnummer: {letzte_vollnummer}")
        
        # Nächste Rechnungsnummer für heute
        if heute in nummern_dict:
            naechste_nummer_heute = nummern_dict[heute] + 1
        else:
            naechste_nummer_heute = 1
        naechste_vollnummer = f"{heute}-{naechste_nummer_heute:02d}"
        print(f"🔢 Nächste Nummer (heute): {naechste_vollnummer}")
        
        # Anzahl Rechnungen heute
        rechnungen_heute = nummern_dict.get(heute, 0)
        print(f"📈 Rechnungen heute: {rechnungen_heute}")
        
    else:
        print("📋 Noch keine Rechnungen erstellt")
        print(f"🔢 Erste Nummer wird: {heute}-01")
    
    print("\n💡 BEISPIELE:")
    print("-" * 15)
    # Demo für verschiedene Tage (ohne die Nummern tatsächlich zu ändern)
    beispiel_dates = ["26.09.2025", "27.09.2025"]
    for datum in beispiel_dates:
        datum_obj = datetime.strptime(datum, "%d.%m.%Y")
        datum_key = datum_obj.strftime("%Y-%m-%d")
        if datum_key in nummern_dict:
            naechste = nummern_dict[datum_key] + 1
        else:
            naechste = 1
        print(f"  Datum {datum} → nächste Nummer: {datum_key}-{naechste:02d}")
    
    print("\n✅ VORTEILE:")
    print("• Keine Rückschlüsse auf Gesamtzahl der Rechnungen möglich")
    print("• Chronologische Sortierung automatisch")
    print("• Mehrere Rechnungen pro Tag möglich (01, 02, 03...)")
    print("• Rechtlich einwandfrei (eindeutig und fortlaufend)")

def hauptmenue():
    manager = RechnungsManager()
    
    while True:
        print("\n" + "="*60)
        print("🧾  RECHNUNGS-TOOL - PDF & XRechnung  🧾")
        print("="*60)
        print("1. 💼 Rechnung erstellen")
        print("2. ➕ Neuen Kunden anlegen")
        print("3. 📋 Kunden anzeigen")
        print("4. 🏢 Unternehmensdaten anzeigen")
        print("5. 🔢 Rechnungsnummern-System anzeigen")
        print("6. 🧹 System-Reset")
        print("7. ❌ Beenden")
        print("-" * 60)
        
        auswahl = input("Ihre Auswahl (1-7): ")
        
        if auswahl == "1":
            rechnung_erstellen_dialog(manager)
        elif auswahl == "2":
            neuer_kunde(manager)
        elif auswahl == "3":
            zeige_kunden(manager)
        elif auswahl == "4":
            print("\n🏢 UNTERNEHMENSDATEN:")
            print("-" * 40)
            for key, value in manager.unternehmen_daten.items():
                if key == "Kleinunternehmer":
                    status = "✅ JA (keine MwSt)" if value.lower() in ['ja', 'yes', 'true', '1'] else "❌ NEIN (mit MwSt)"
                    print(f"{key}: {status}")
                else:
                    print(f"{key}: {value}")
        elif auswahl == "5":
            zeige_rechnungsnummern_demo(manager)
        elif auswahl == "6":
            system_reset_menu()
        elif auswahl == "7":
            print("👋 Auf Wiedersehen!")
            break
        else:
            print("❌ Ungültige Auswahl! Bitte 1-7 wählen.")

if __name__ == "__main__":
    hauptmenue()