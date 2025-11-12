import os
import sys
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
try:
    import pypdf
    PDF_LIBRARY_AVAILABLE = True
except ImportError:
    PDF_LIBRARY_AVAILABLE = False

def formatiere_betrag(betrag):
    """Formatiert Beträge mit deutschem Zahlenformat: 1.234,56 €"""
    # Deutsche Formatierung: Punkt als Tausender, Komma als Dezimal
    betrag_str = f"{betrag:,.2f}"
    # Ersetze amerikanische Formatierung durch deutsche
    betrag_deutsch = betrag_str.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return betrag_deutsch + " €"

def formatiere_iban(iban):
    """Formatiert IBAN mit Leerzeichen alle 4 Zeichen"""
    if not iban:
        return ""
    # Entferne alle Leerzeichen und füge sie alle 4 Zeichen ein
    iban_clean = iban.replace(" ", "")
    return " ".join([iban_clean[i:i+4] for i in range(0, len(iban_clean), 4)])

def erstelle_rechnung(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, rechnungen_dir, freitext=None):
    """
    Erstellt eine PDF-Rechnung und separate XRechnung-XML-Datei
    """
    try:
                # Dateiname-sichere Version der Rechnungsnummer (ersetzt : durch -)
        datei_nummer = str(rechnungsnummer).replace(':', '-')
        
        # Pfade für verschiedene Formate
        temp_xml_path = f"temp_invoice_{datei_nummer}.xml"
        xrechnung_xml_path = os.path.join(rechnungen_dir, f"XRechnung_{datei_nummer}.xml")
        pdf_path = os.path.join(rechnungen_dir, f"Rechnung_{datei_nummer}.pdf")
        
        # Betrag berechnen
        betrag = sum(pos["menge"] * pos["einzelpreis"] for pos in positionen)
        
        # Kleinunternehmer prüfen
        ist_kleinunternehmer = unternehmen_data.get('Kleinunternehmer', 'nein').lower() in ['ja', 'yes', 'true', '1']
        
        # Temporäre XML für interne Zwecke erstellen
        erstelle_zugferd_xml(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, temp_xml_path, ist_kleinunternehmer)
        
        # PDF erstellen (ohne XML-Einbettung)
        erstelle_pdf(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, temp_xml_path, pdf_path, ist_kleinunternehmer, freitext)
        
        # Temporäre XML löschen
        if os.path.exists(temp_xml_path):
            os.remove(temp_xml_path)
        
        # XRechnung XML erstellen
        erstelle_xrechnung_xml(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, xrechnung_xml_path, ist_kleinunternehmer)
        
        return True
        
    except Exception as e:
        print(f"Fehler beim Erstellen der Rechnung: {e}")
        return False

def erstelle_pdf(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, xml_path, pdf_path, ist_kleinunternehmer, freitext=None):
    """Erstellt das PDF mit Unternehmen- und Kundendaten"""
    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    
    # Faltmarken nach DIN 5008 - Geschäftsbrief Form A
    # Falzmarke 1: 87mm von der oberen Blattkante
    c.line(5*mm, height-87*mm, 10*mm, height-87*mm)
    # Falzmarke 2: 192mm von der oberen Blattkante  
    c.line(5*mm, height-192*mm, 10*mm, height-192*mm)
    
    # Lochmarke nach DIN 5008 - Geschäftsbrief Form A
    # Lochmarke: 148,5mm von der oberen Blattkante
    c.line(2*mm, height-148.5*mm, 6*mm, height-148.5*mm)
    
    # Logo (falls vorhanden) - oben rechts
    # Pfad zur Executable/zum Skript ermitteln (PyInstaller-kompatibel)
    if getattr(sys, 'frozen', False):
        # Läuft als PyInstaller-Executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Läuft als Python-Skript
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    logo_namen = ["logo.png", "logo.jpg", "logo.jpeg", "logo.gif", "Logo.PNG", "Logo.JPG"]
    logo_pfade = [os.path.join(base_dir, name) for name in logo_namen]
    logo_gefunden = False
    
    for logo_path in logo_pfade:
        if os.path.exists(logo_path):
            try:
                # Bitmap-Logo (PNG, JPG, etc.) - rechts positioniert
                c.drawImage(logo_path, 150*mm, height-25*mm, width=40*mm, height=20*mm, preserveAspectRatio=True, mask='auto')
                print(f"✅ Logo geladen: {logo_path}")
                logo_gefunden = True
                break
                
            except Exception as e:
                print(f"❌ Fehler beim Laden von {logo_path}: {e}")
    
    if not logo_gefunden:
        print("ℹ️ Kein Logo gefunden.")
        print("📁 Unterstützte Formate: logo.png (empfohlen), logo.jpg")
        print("� Speichern Sie Ihr Logo als 'logo.png' im Projektordner")
    
    # Unternehmensdaten (oben rechts) - Absender  
    # Firmenname weggelassen da bereits im Logo sichtbar
    c.setFont("Helvetica", 9)
    y_unternehmen = height-25*mm
    c.drawRightString(190*mm, y_unternehmen, f"{unternehmen_data.get('Straße', '')} {unternehmen_data.get('Hausnummer', '')}")
    y_unternehmen -= 3.5*mm
    c.drawRightString(190*mm, y_unternehmen, f"{unternehmen_data.get('PLZ', '')} {unternehmen_data.get('Ort', '')}")
    y_unternehmen -= 3.5*mm
    
    # USt-IdNr oder Steuernummer bei Unternehmensdaten
    if unternehmen_data.get('USt-IdNr') and not ist_kleinunternehmer:
        c.drawRightString(190*mm, y_unternehmen, f"USt-IdNr: {unternehmen_data.get('USt-IdNr')}")
    else:
        c.drawRightString(190*mm, y_unternehmen, f"St.-Nr.: {unternehmen_data.get('Steuernummer', '')}")
    y_unternehmen -= 3.5*mm
    
    c.drawRightString(190*mm, y_unternehmen, f"Tel: {unternehmen_data.get('Telefon', '')}")
    y_unternehmen -= 3.5*mm
    c.drawRightString(190*mm, y_unternehmen, f"Email: {unternehmen_data.get('Email', '')}")
    y_unternehmen -= 3.5*mm
    
    # Bankverbindung (mit mehr Abstand)
    y_unternehmen -= 2*mm  # Zusätzlicher Abstand vor Bankverbindung
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(190*mm, y_unternehmen, "Bankverbindung:")
    y_unternehmen -= 3.5*mm
    c.setFont("Helvetica", 8)
    c.drawRightString(190*mm, y_unternehmen, f"IBAN: {formatiere_iban(unternehmen_data.get('IBAN', ''))}")
    y_unternehmen -= 3.5*mm
    c.drawRightString(190*mm, y_unternehmen, f"BIC: {unternehmen_data.get('BIC', '')}")
    y_unternehmen -= 3.5*mm
    c.drawRightString(190*mm, y_unternehmen, f"{unternehmen_data.get('Bank', '')}")
    
    # Absenderzeile (klein, für Fensterkuvert) - 17.7mm vom oberen Rand
    c.setFont("Helvetica", 8)
    absender_text = f"{unternehmen_data.get('Firmenname', '')}, {unternehmen_data.get('Straße', '')} {unternehmen_data.get('Hausnummer', '')}, {unternehmen_data.get('PLZ', '')} {unternehmen_data.get('Ort', '')}"
    c.drawString(20*mm, height-17.7*mm, absender_text)
    
    # Linie unter Absenderzeile
    c.line(20*mm, height-20*mm, 110*mm, height-20*mm)
    
    # Kundenadresse (DIN 5008 konform für Fensterkuvert)
    # Beginnt 45mm vom oberen Rand, 20mm vom linken Rand
    c.setFont("Helvetica", 11)
    y_kunde = height-45*mm  # DIN-konforme Position
    
    # Unterscheidung zwischen Firma und Privatperson
    ist_privatperson = not kunde_data.get('Ansprechpartner')
    
    if ist_privatperson:
        # Privatperson: Name direkt ohne "z.Hd."
        c.drawString(20*mm, y_kunde, kunde_data.get('Firmenname', ''))
    else:
        # Firma: Firmenname und dann z.Hd. Ansprechpartner
        c.drawString(20*mm, y_kunde, kunde_data.get('Firmenname', ''))
        y_kunde -= 4*mm
        c.drawString(20*mm, y_kunde, f"z.Hd. {kunde_data.get('Ansprechpartner')}")
    
    y_kunde -= 4*mm
    c.drawString(20*mm, y_kunde, f"{kunde_data.get('Straße', '')} {kunde_data.get('Hausnummer', '')}")
    y_kunde -= 4*mm
    c.drawString(20*mm, y_kunde, f"{kunde_data.get('PLZ', '')} {kunde_data.get('Ort', '')}")
    if kunde_data.get('Land', 'DE') != 'DE':
        y_kunde -= 4*mm
        c.drawString(20*mm, y_kunde, kunde_data.get('Land', ''))
    
    # Rechnungsdaten - kompakter positioniert (nach der Adresse)
    y_daten = height-105*mm  # Direkt nach der Adresse
    
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, y_daten, f"Kundennummer:")
    c.drawString(50*mm, y_daten, kunde_data.get('Kundennummer', ''))
    c.drawString(100*mm, y_daten, f"Rechnungsnummer:")
    c.drawString(140*mm, y_daten, str(rechnungsnummer))
    
    y_daten -= 4*mm
    c.drawString(20*mm, y_daten, f"Rechnungsdatum:")
    c.drawString(50*mm, y_daten, datum)
    c.drawString(100*mm, y_daten, f"Leistungsdatum:")
    c.drawString(140*mm, y_daten, f"{datum} (= Rechnungsdatum)")
    
    # Rechnungsheader
    y_header = y_daten - 6*mm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y_header, f"Rechnung {rechnungsnummer}")
    
    # Freitext / Begrüßung
    y_text = y_header - 8*mm
    c.setFont("Helvetica", 10)
    if freitext:
        # Mehrzeiliger Freitext unterstützen
        import textwrap
        wrapped_lines = textwrap.wrap(freitext, width=80)
        for line in wrapped_lines:
            c.drawString(20*mm, y_text, line)
            y_text -= 4*mm
    else:
        default_text = "Vielen Dank für Ihr Vertrauen. Hiermit stellen wir Ihnen folgende Leistungen in Rechnung:"
        c.drawString(20*mm, y_text, default_text)
        y_text -= 4*mm
    
    # Mehrseitige Tabelle für Positionen
    y_tabelle = y_text - 8*mm
    min_y = 100*mm  # Mindestabstand zum unteren Rand (für Summen und Fußzeile)
    
    def zeichne_tabellenkopf(y_pos):
        """Zeichnet den Tabellenkopf"""
        c.setFont("Helvetica-Bold", 9)
        c.drawString(20*mm, y_pos, "Pos.")
        c.drawString(35*mm, y_pos, "Bezeichnung (Art der Leistung)")
        c.drawString(110*mm, y_pos, "Menge")
        c.drawRightString(140*mm, y_pos, "Einzelpreis")
        c.drawRightString(175*mm, y_pos, "Nettobetrag")
        if not ist_kleinunternehmer:
            c.drawString(185*mm, y_pos, "MwSt")
        
        # Linie unter Kopf
        y_pos -= 2*mm
        c.line(20*mm, y_pos, 190*mm, y_pos)
        return y_pos - 3*mm
    
    # Ersten Tabellenkopf zeichnen
    y_tabelle = zeichne_tabellenkopf(y_tabelle)
    
    # Positionen mit Seitenumbruch-Logik
    c.setFont("Helvetica", 9)
    zeilen_pro_position = 5*mm
    
    for i, pos in enumerate(positionen, 1):
        # Prüfen ob noch Platz für Position + Summen vorhanden
        if y_tabelle < min_y:
            # Neue Seite beginnen
            c.showPage()
            y_tabelle = height - 40*mm  # Start auf neuer Seite
            y_tabelle = zeichne_tabellenkopf(y_tabelle)
        
        netto_pos = pos["menge"] * pos["einzelpreis"]
        c.drawString(20*mm, y_tabelle, str(i))
        
        # Lange Bezeichnungen umbrechen
        import textwrap
        bezeichnung_lines = textwrap.wrap(pos["bezeichnung"], width=40)
        for j, line in enumerate(bezeichnung_lines):
            c.drawString(35*mm, y_tabelle - j*3*mm, line)
        
        c.drawString(110*mm, y_tabelle, f"{pos['menge']}")
        c.drawRightString(140*mm, y_tabelle, formatiere_betrag(pos['einzelpreis']))
        c.drawRightString(175*mm, y_tabelle, formatiere_betrag(netto_pos))
        if not ist_kleinunternehmer:
            c.drawString(185*mm, y_tabelle, "19%")
        
        # Y-Position für nächste Position anpassen
        zeilen_verwendet = max(1, len(bezeichnung_lines))
        y_tabelle -= zeilen_verwendet * zeilen_pro_position
    
    # Summen-Bereich (garantiert auf der letzten Seite)
    y = y_tabelle - 8*mm
    
    # Sicherstellen, dass genug Platz für Summen vorhanden ist
    if y < min_y:
        c.showPage()
        y = height - 120*mm  # Neue Seite für Summen
    
    # Summen (rechtsbündig)
    c.line(140*mm, y, 190*mm, y)  # Linie vor Summen
    y -= 6*mm
    
    c.setFont("Helvetica", 10)
    if ist_kleinunternehmer:
        # Kleinunternehmerregelung - Pflichtangaben gem. §14 UStG
        c.drawString(120*mm, y, f"Summe Nettobetrag:")
        c.drawRightString(190*mm, y, formatiere_betrag(betrag))
        y -= 4*mm
        c.drawString(120*mm, y, f"Steuerbefreiung:")
        c.drawRightString(190*mm, y, "0,00 €")
        y -= 4*mm
        c.line(120*mm, y, 190*mm, y)
        y -= 6*mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120*mm, y, f"Gesamtbetrag:")
        c.drawRightString(190*mm, y, formatiere_betrag(betrag))
        gesamt_betrag = betrag
        steuer_betrag = 0
    else:
        # Normale MwSt-Berechnung - Pflichtangaben gem. §14 UStG
        steuer_betrag = betrag * 0.19
        gesamt_betrag = betrag * 1.19
        
        c.drawString(120*mm, y, f"Summe Nettobetrag:")
        c.drawRightString(190*mm, y, formatiere_betrag(betrag))
        y -= 4*mm
        c.drawString(120*mm, y, f"Steuerbetrag (19%):")
        c.drawRightString(190*mm, y, formatiere_betrag(steuer_betrag))
        y -= 4*mm
        c.line(120*mm, y, 190*mm, y)
        y -= 6*mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(120*mm, y, f"Gesamtbetrag:")
        c.drawRightString(190*mm, y, formatiere_betrag(gesamt_betrag))
    
    # Footer immer am unteren Rand positionieren
    footer_height = 40*mm  # Höhe für rechtliche Hinweise
    y_footer = footer_height
    
    # Rechtliche Hinweise (Footer)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20*mm, y_footer, "Rechtliche Hinweise:")
    y_footer -= 5*mm
    
    # Pflicht-Steuerhinweis gem. §14 UStG
    c.setFont("Helvetica", 8)
    if ist_kleinunternehmer:
        c.drawString(20*mm, y_footer, "Steuerrechtlicher Hinweis (Pflichtangabe gem. §14 UStG):")
        y_footer -= 3*mm
        c.drawString(20*mm, y_footer, "Kleinunternehmerregelung nach §19 UStG - keine Umsatzsteuer ausgewiesen")
        y_footer -= 5*mm
    else:
        c.drawString(20*mm, y_footer, f"Anwendbarer Steuersatz: 19% Umsatzsteuer - Steuerbetrag: {steuer_betrag:.2f} EUR")
        y_footer -= 5*mm
    
    # Zahlungshinweise
    c.drawString(20*mm, y_footer, "Zahlungshinweise:")
    y_footer -= 3*mm
    c.drawString(20*mm, y_footer, f"Bitte überweisen Sie den Rechnungsbetrag innerhalb von 14 Tagen ohne Abzug auf unser Konto.")
    y_footer -= 4*mm
    
    # Verwendungszweck hervorgehoben
    c.setFont("Helvetica-Bold", 9)
    c.drawString(20*mm, y_footer, f"➤ VERWENDUNGSZWECK: Rechnung {rechnungsnummer}")
    c.setFont("Helvetica", 8)
    y_footer -= 6*mm
    
    # Allgemeine Geschäftsbedingungen
    c.drawString(20*mm, y_footer, "Es gelten unsere Allgemeinen Geschäftsbedingungen. Erfüllungsort und Gerichtsstand ist unser Geschäftssitz.")
    y_footer -= 3*mm
    c.drawString(20*mm, y_footer, "Bei Rückfragen stehen wir Ihnen gerne zur Verfügung.")
    
    c.save()
    
    # Einfaches PDF ohne XML-Einbettung
    print(f"✅ PDF-Rechnung erstellt")

def erstelle_zugferd_xml(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, xml_path, ist_kleinunternehmer=False):
    """Erstellt temporäre XML für interne Zwecke (kein echtes ZUGFeRD)"""
    datum_obj = datetime.strptime(datum, "%d.%m.%Y")
    datum_iso = datum_obj.strftime("%Y%m%d")
    faellig_datum = (datum_obj + timedelta(days=14)).strftime("%Y%m%d")
    
    if ist_kleinunternehmer:
        steuer_betrag = 0
        gesamt_betrag = betrag
        steuer_kategorie = "E"
        steuer_prozent = 0
        steuer_grund = "Kleinunternehmerregelung nach §19 UStG"
    else:
        steuer_betrag = betrag * 0.19
        gesamt_betrag = betrag * 1.19
        steuer_kategorie = "S"
        steuer_prozent = 19
        steuer_grund = ""
    
    # XML direkt als String erstellen für bessere Kompatibilität
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice 
    xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100" 
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" 
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  
  <rsm:ExchangedDocumentContext>
    <ram:BusinessProcessSpecifiedDocumentContextParameter>
      <ram:ID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</ram:ID>
    </ram:BusinessProcessSpecifiedDocumentContextParameter>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  
  <rsm:ExchangedDocument>
    <ram:ID>{rechnungsnummer}</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime>
      <udt:DateTimeString format="102">{datum_iso}</udt:DateTimeString>
    </ram:IssueDateTime>
  </rsm:ExchangedDocument>
  
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument>
        <ram:LineID>1</ram:LineID>
      </ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct>
        <ram:Name>Dienstleistung</ram:Name>
      </ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice>
          <ram:ChargeAmount>{betrag:.2f}</ram:ChargeAmount>
        </ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery>
        <ram:BilledQuantity unitCode="H87">1.00</ram:BilledQuantity>
      </ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax>
          <ram:TypeCode>VAT</ram:TypeCode>
          <ram:CategoryCode>{steuer_kategorie}</ram:CategoryCode>
          <ram:RateApplicablePercent>{steuer_prozent}</ram:RateApplicablePercent>
        </ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation>
          <ram:LineTotalAmount>{betrag:.2f}</ram:LineTotalAmount>
        </ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:BuyerReference>RECHNUNG-{rechnungsnummer}</ram:BuyerReference>
      <ram:SellerTradeParty>
        <ram:Name>{unternehmen_data.get('Firmenname', 'Mein Unternehmen')}</ram:Name>
        <ram:PostalTradeAddress>
          <ram:PostcodeCode>{unternehmen_data.get('PLZ', '12345')}</ram:PostcodeCode>
          <ram:LineOne>{unternehmen_data.get('Straße', 'Musterstraße')} {unternehmen_data.get('Hausnummer', '1')}</ram:LineOne>
          <ram:CityName>{unternehmen_data.get('Ort', 'Musterstadt')}</ram:CityName>
          <ram:CountryID>{unternehmen_data.get('Land', 'DE')}</ram:CountryID>
        </ram:PostalTradeAddress>
        <ram:SpecifiedTaxRegistration>
          <ram:ID schemeID="VA">{unternehmen_data.get('USt-IdNr', 'DE999999999')}</ram:ID>
        </ram:SpecifiedTaxRegistration>
        <ram:URIUniversalCommunication>
          <ram:URIID schemeID="EM">{unternehmen_data.get('Email', 'info@unternehmen.de')}</ram:URIID>
        </ram:URIUniversalCommunication>
        <ram:DefinedTradeContact>
          <ram:PersonName>{unternehmen_data.get('Geschäftsführer', 'Ansprechpartner')}</ram:PersonName>
          <ram:TelephoneUniversalCommunication>
            <ram:CompleteNumber>{unternehmen_data.get('Telefon', '+49 123 456789')}</ram:CompleteNumber>
          </ram:TelephoneUniversalCommunication>
          <ram:EmailURIUniversalCommunication>
            <ram:URIID>{unternehmen_data.get('Email', 'info@unternehmen.de')}</ram:URIID>
          </ram:EmailURIUniversalCommunication>
        </ram:DefinedTradeContact>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>{kunde_data.get('Firmenname', 'Kunde') or 'Kunde'}</ram:Name>
        <ram:PostalTradeAddress>
          <ram:PostcodeCode>{kunde_data.get('PLZ', '54321') if kunde_data.get('PLZ', '').strip() else '54321'}</ram:PostcodeCode>
          <ram:LineOne>{(kunde_data.get('Straße', '') + ' ' + kunde_data.get('Hausnummer', '')).strip() if (kunde_data.get('Straße', '') + kunde_data.get('Hausnummer', '')).strip() else 'Kundenstraße 1'}</ram:LineOne>
          <ram:CityName>{kunde_data.get('Ort', 'Kundenstadt') if kunde_data.get('Ort', '').strip() else 'Kundenstadt'}</ram:CityName>
          <ram:CountryID>{kunde_data.get('Land', 'DE')}</ram:CountryID>
        </ram:PostalTradeAddress>
        <ram:URIUniversalCommunication>
          <ram:URIID schemeID="EM">{kunde_data.get('Email', 'kunde@example.com') if kunde_data.get('Email', '').strip() else 'kunde@example.com'}</ram:URIID>
        </ram:URIUniversalCommunication>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    
    <ram:ApplicableHeaderTradeDelivery>
      <ram:ActualDeliverySupplyChainEvent>
        <ram:OccurrenceDateTime>
          <udt:DateTimeString format="102">{datum_iso}</udt:DateTimeString>
        </ram:OccurrenceDateTime>
      </ram:ActualDeliverySupplyChainEvent>
    </ram:ApplicableHeaderTradeDelivery>
    
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementPaymentMeans>
        <ram:TypeCode>58</ram:TypeCode>
        <ram:Information>Überweisung</ram:Information>
        <ram:PayeePartyCreditorFinancialAccount>
          <ram:IBANID>{unternehmen_data.get('IBAN', 'DE89370400440532013000').replace(' ', '')}</ram:IBANID>
          <ram:AccountName>{unternehmen_data.get('Firmenname', 'Mein Unternehmen')}</ram:AccountName>
        </ram:PayeePartyCreditorFinancialAccount>
        <ram:PayeeSpecifiedCreditorFinancialInstitution>
          <ram:BICID>{unternehmen_data.get('BIC', 'COBADEFFXXX')}</ram:BICID>
          <ram:Name>{unternehmen_data.get('Bank', 'Commerzbank')}</ram:Name>
        </ram:PayeeSpecifiedCreditorFinancialInstitution>
      </ram:SpecifiedTradeSettlementPaymentMeans>
      <ram:ApplicableTradeTax>
        <ram:CalculatedAmount>{steuer_betrag:.2f}</ram:CalculatedAmount>
        <ram:TypeCode>VAT</ram:TypeCode>
        <ram:BasisAmount>{betrag:.2f}</ram:BasisAmount>
        <ram:CategoryCode>{steuer_kategorie}</ram:CategoryCode>
        <ram:RateApplicablePercent>{steuer_prozent}</ram:RateApplicablePercent>{f'<ram:ExemptionReason>{steuer_grund}</ram:ExemptionReason>' if ist_kleinunternehmer else ''}
      </ram:ApplicableTradeTax>
      <ram:SpecifiedTradePaymentTerms>
        <ram:Description>Zahlbar innerhalb 14 Tage ohne Abzug.</ram:Description>
        <ram:DueDateDateTime>
          <udt:DateTimeString format="102">{faellig_datum}</udt:DateTimeString>
        </ram:DueDateDateTime>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>{betrag:.2f}</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>{betrag:.2f}</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">{steuer_betrag:.2f}</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>{gesamt_betrag:.2f}</ram:GrandTotalAmount>
        <ram:DuePayableAmount>{gesamt_betrag:.2f}</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
    
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""
    
    # XML speichern
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"✅ Temporäre XML erstellt: {xml_path}")
    return xml_content

def erstelle_xrechnung_xml(rechnungsnummer, kunde_data, unternehmen_data, datum, positionen, betrag, xml_path, ist_kleinunternehmer=False):
    """Erstellt XRechnung-XML mit Unternehmen- und Kundendaten"""
    datum_obj = datetime.strptime(datum, "%d.%m.%Y")
    datum_iso = datum_obj.strftime("%Y-%m-%d")
    due_date = (datum_obj + timedelta(days=14)).strftime("%Y-%m-%d")
    
    if ist_kleinunternehmer:
        steuer_betrag = 0
        gesamt_betrag = betrag
        steuer_kategorie = "E"  # Exempt (befreit)
        steuer_prozent = 0
    else:
        steuer_betrag = betrag * 0.19
        gesamt_betrag = betrag * 1.19
        steuer_kategorie = "S"  # Standard
        steuer_prozent = 19
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<ubl:Invoice xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
    <cbc:CustomizationID>urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0</cbc:CustomizationID>
    <cbc:ProfileID>urn:fdc:peppol.eu:2017:poacc:billing:01:1.0</cbc:ProfileID>
    <cbc:ID>{rechnungsnummer}</cbc:ID>
    <cbc:IssueDate>{datum_iso}</cbc:IssueDate>
    <cbc:DueDate>{due_date}</cbc:DueDate>
    <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
    <cbc:Note>Rechnung</cbc:Note>
    <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
    <cbc:BuyerReference>RECHNUNG-{rechnungsnummer}</cbc:BuyerReference>
    <cac:AccountingSupplierParty>
        <cac:Party>
            {f'<cbc:EndpointID schemeID="EM">{unternehmen_data.get("Email", "info@unternehmen.de")}</cbc:EndpointID>' if unternehmen_data.get("Email", "info@unternehmen.de") else ''}
            <cac:PartyIdentification>
                <cbc:ID>{unternehmen_data.get('USt-IdNr', 'DE123456789')}</cbc:ID>
            </cac:PartyIdentification>
            <cac:PartyName>
                <cbc:Name>{unternehmen_data.get('Firmenname', 'Mein Unternehmen')}</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>{unternehmen_data.get('Straße', 'Musterstraße')} {unternehmen_data.get('Hausnummer', '1')}</cbc:StreetName>
                <cbc:CityName>{unternehmen_data.get('Ort', 'Musterstadt')}</cbc:CityName>
                <cbc:PostalZone>{unternehmen_data.get('PLZ', '12345')}</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>{unternehmen_data.get('Land', 'DE')}</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyTaxScheme>
                <cbc:CompanyID>{unternehmen_data.get('USt-IdNr', 'DE123456789')}</cbc:CompanyID>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:PartyTaxScheme>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{unternehmen_data.get('Firmenname', 'Mein Unternehmen')}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
            <cac:Contact>
                <cbc:Name>{unternehmen_data.get('Geschäftsführer', 'Max Mustermann')}</cbc:Name>
                <cbc:Telephone>{unternehmen_data.get('Telefon', '+49 123 456789')}</cbc:Telephone>
                <cbc:ElectronicMail>{unternehmen_data.get('Email', 'info@unternehmen.de')}</cbc:ElectronicMail>
            </cac:Contact>
        </cac:Party>
    </cac:AccountingSupplierParty>
    <cac:AccountingCustomerParty>
        <cac:Party>
            {f'<cbc:EndpointID schemeID="EM">{kunde_data.get("Email")}</cbc:EndpointID>' if kunde_data.get("Email") and kunde_data.get("Email").strip() else ''}
            <cac:PartyName>
                <cbc:Name>{kunde_data.get('Firmenname', 'Kunde') if kunde_data.get('Firmenname', '').strip() else 'Kunde'}</cbc:Name>
            </cac:PartyName>
            <cac:PostalAddress>
                <cbc:StreetName>{(kunde_data.get('Straße', '') + ' ' + kunde_data.get('Hausnummer', '')).strip() if (kunde_data.get('Straße', '') + kunde_data.get('Hausnummer', '')).strip() else 'Kundenstraße 1'}</cbc:StreetName>
                <cbc:CityName>{kunde_data.get('Ort', 'Kundenstadt') if kunde_data.get('Ort', '').strip() else 'Kundenstadt'}</cbc:CityName>
                <cbc:PostalZone>{kunde_data.get('PLZ', '54321') if kunde_data.get('PLZ', '').strip() else '54321'}</cbc:PostalZone>
                <cac:Country>
                    <cbc:IdentificationCode>{kunde_data.get('Land', 'DE')}</cbc:IdentificationCode>
                </cac:Country>
            </cac:PostalAddress>
            <cac:PartyLegalEntity>
                <cbc:RegistrationName>{kunde_data.get('Firmenname', 'Kunde') if kunde_data.get('Firmenname', '').strip() else 'Kunde'}</cbc:RegistrationName>
            </cac:PartyLegalEntity>
        </cac:Party>
    </cac:AccountingCustomerParty>
    <cac:PaymentMeans>
        <cbc:PaymentMeansCode>58</cbc:PaymentMeansCode>
        <cac:PayeeFinancialAccount>
            <cbc:ID>{unternehmen_data.get('IBAN', 'DE89370400440532013000')}</cbc:ID>
        </cac:PayeeFinancialAccount>
    </cac:PaymentMeans>
    <cac:PaymentTerms>
        <cbc:Note>Zahlbar innerhalb von 14 Tagen ohne Abzug</cbc:Note>
    </cac:PaymentTerms>
    <cac:TaxTotal>
        <cbc:TaxAmount currencyID="EUR">{steuer_betrag:.2f}</cbc:TaxAmount>
        <cac:TaxSubtotal>
            <cbc:TaxableAmount currencyID="EUR">{betrag:.2f}</cbc:TaxableAmount>
            <cbc:TaxAmount currencyID="EUR">{steuer_betrag:.2f}</cbc:TaxAmount>
            <cac:TaxCategory>
                <cbc:ID>{steuer_kategorie}</cbc:ID>
                <cbc:Percent>{steuer_prozent}</cbc:Percent>
                {f'<cbc:TaxExemptionReason>Kleinunternehmerregelung § 19 UStG</cbc:TaxExemptionReason>' if ist_kleinunternehmer else ''}
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:TaxCategory>
        </cac:TaxSubtotal>
    </cac:TaxTotal>
    <cac:LegalMonetaryTotal>
        <cbc:LineExtensionAmount currencyID="EUR">{betrag:.2f}</cbc:LineExtensionAmount>
        <cbc:TaxExclusiveAmount currencyID="EUR">{betrag:.2f}</cbc:TaxExclusiveAmount>
        <cbc:TaxInclusiveAmount currencyID="EUR">{gesamt_betrag:.2f}</cbc:TaxInclusiveAmount>
        <cbc:PayableAmount currencyID="EUR">{gesamt_betrag:.2f}</cbc:PayableAmount>
    </cac:LegalMonetaryTotal>"""

    # Positionen hinzufügen
    for i, pos in enumerate(positionen, 1):
        linien_betrag = pos["menge"] * pos["einzelpreis"]
        xml_content += f"""
    <cac:InvoiceLine>
        <cbc:ID>{i}</cbc:ID>
        <cbc:InvoicedQuantity unitCode="HUR">{pos["menge"]}</cbc:InvoicedQuantity>
        <cbc:LineExtensionAmount currencyID="EUR">{linien_betrag:.2f}</cbc:LineExtensionAmount>
        <cac:Item>
            <cbc:Name>{pos["bezeichnung"]}</cbc:Name>
            <cac:ClassifiedTaxCategory>
                <cbc:ID>{steuer_kategorie}</cbc:ID>
                <cbc:Percent>{steuer_prozent}</cbc:Percent>
                <cac:TaxScheme>
                    <cbc:ID>VAT</cbc:ID>
                </cac:TaxScheme>
            </cac:ClassifiedTaxCategory>
        </cac:Item>
        <cac:Price>
            <cbc:PriceAmount currencyID="EUR">{pos["einzelpreis"]:.2f}</cbc:PriceAmount>
        </cac:Price>
    </cac:InvoiceLine>"""

    xml_content += """
</ubl:Invoice>"""
    
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)