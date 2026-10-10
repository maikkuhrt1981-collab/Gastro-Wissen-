import os
import difflib
import streamlit as st

st.set_page_config(page_title="Gastro Reparatur-Wissensdatenbank", page_icon="🔧", layout="centered")

# --- PASSWORT-SCHUTZ ---
PASSWORT = "gastro2026"  # Hier können Sie das Passwort für Ihr Team anpassen

def passwort_pruefen():
    if "authentifiziert" not in st.session_state:
        st.session_state.authentifiziert = False

    if not st.session_state.authentifiziert:
        st.title("🔒 Gastro-Wissensdatenbank - Login")
        eingabe = st.text_input("Bitte Team-Passwort eingeben:", type="password")
        if st.button("Anmelden"):
            if eingabe == PASSWORT:
                st.session_state.authentifiziert = True
                st.rerun()
            else:
                st.error("Falsches Passwort!")
        return False
    return True

if not passwort_pruefen():
    st.stop()
# -----------------------

st.title("🔧 Gastro Reparatur-Wissensdatenbank")
st.write("Zentrale Wissensdatenbank für Gastro-Geräte und Fehlersuche (Frymaster, Carpigiani, Garland u.a.)")

DATEI_PFAD = "wissensdatenbank.txt"

def datenbank_initialisieren():
    if not os.path.exists(DATEI_PFAD):
        standard_inhalt = """## Gerät: Carpigiani
- Fehler: E01 / Überdruck im Zylinder
- Reparatur: Kondensator auf Verschmutzung prüfen und reinigen.

## Gerät: Carpigiani
- Fehler: E02 / Viskosität zu hoch
- Reparatur: Mix-Zufuhr prüfen und Viskositätseinstellung kalibrieren.

## Gerät: Frymaster / Frittieranlagen & Systeme
- Fehler: Alarm 6 / High Temp / Übertemperatur
- Reparatur: Übertemperatur im Becken überschritten. Fühler kalibrieren, Solid-State-Relais (SSR) auf Kurzschluss/Dauerbetrieb prüfen, High-Limit-Thermostat (Sicherheitstemperaturbegrenzer) prüfen.

## Gerät: Garland Grill / Frymaster
- Fehler: E20 / Heizungsfehler - Heizt nicht
- Reparatur: Keine Temperaturerhöhung um min. 3°C in 425s erkannt. Flachbandkabel vom SIB zum SSRB Board prüfen, Thermoelemente und Anschlüsse der Heizungen kontrollieren.

## Gerät: garland grill
- Fehler: Alarm 6
- Reparatur: sensorstecker sib
"""
        with open(DATEI_PFAD, "w", encoding="utf-8") as f:
            f.write(standard_inhalt)

datenbank_initialisieren()

auswahl = st.sidebar.radio("Navigation", ["🔍 Fehler suchen", "➕ Neuen Eintrag hinzufügen"])

# ----------------- SUCHEN (Tolerant bei Tippfehlern) -----------------
if auswahl == "🔍 Fehler suchen":
    st.header("Datenbank durchsuchen")
    suchbegriff = st.text_input("Wonach suchen? (z.B. alarmo, E20, Carpigiani):").strip()
    
    if suchbegriff:
        try:
            with open(DATEI_PFAD, "r", encoding="utf-8") as f:
                inhalt = f.read()
                
            bloecke = inhalt.split("## Gerät:")
            treffer = 0
            suchbegriff_clean = suchbegriff.lower()
            
            # Wörter für Tippfehler-Toleranz sammeln
            alle_woerter = set()
            for block in bloecke:
                if not block.strip():
                    continue
                for wort in block.lower().split():
                    bereinigtes_wort = wort.strip(".,/:;-_()#")
                    if len(bereinigtes_wort) > 1:
                        alle_woerter.add(bereinigtes_wort)

            ahnliche_woerter = difflib.get_close_matches(suchbegriff_clean, list(alle_woerter), n=3, cutoff=0.5)

            for block in bloecke:
                if not block.strip():
                    continue
                
                block_lower = block.lower()
                direkt_treffer = suchbegriff_clean in block_lower
                tippfehler_treffer = any(w in block_lower for w in ahnliche_woerter)
                
                if direkt_treffer or tippfehler_treffer:
                    st.success("Gefundener Eintrag:")
                    st.markdown(f"```text\n## Gerät:{block.strip()}\n```")
                    treffer += 1
                    
            if treffer == 0:
                st.warning(f"Keine Treffer für '{suchbegriff}' gefunden.")
                if ahnliche_woerter:
                    st.info(f"💡 Meinten Sie vielleicht: {', '.join(ahnliche_woerter)}?")
            else:
                st.info(f"Es wurden {treffer} passende Einträge gefunden.")
        except Exception as e:
            st.error(f"Fehler beim Lesen der Datenbank: {e}")

# ----------------- NEUEN EINTRAG HINZUFÜGEN -----------------
elif auswahl == "➕ Neuen Eintrag hinzufügen":
    st.header("Neuen Reparatur-Eintrag erfassen")
    
    with st.form("neuer_eintrag_form"):
        geraet = st.text_input("Gerät / Marke (z.B. Frymaster, Garland Grill):")
        fehler = st.text_input("Fehler / Fehlercode / Symptom (z.B. Alarm 6, E21):")
        loesung = st.text_area("Reparaturanleitung / Ursache:")
        
        submitted = st.form_submit_button("Eintrag dauerhaft speichern")
        
        if submitted:
            if geraet and fehler and loesung:
                eintrag = f"\n## Gerät: {geraet}\n- Fehler: {fehler}\n- Reparatur: {loesung}\n"
                with open(DATEI_PFAD, "a", encoding="utf-8") as f:
                    f.write(eintrag)
                st.success("✅ Neuer Eintrag wurde erfolgreich gespeichert und steht dem Team zur Verfügung!")
            else:
                st.error("Bitte füllen Sie alle Felder aus.")
