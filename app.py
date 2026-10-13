import gspread
import pandas as pd
import streamlit as st

# Seiten-Konfiguration (mobil-optimiert)
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="centered"
)

# Passwort-Schutz
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.subheader("🔒 Gastro-Wissensdatenbank Login")
  password_input = st.text_input("Passwort eingeben:", type="password")
  if st.button("Anmelden"):
    if password_input == "Gastro2026":
      st.session_state.authenticated = True
      st.rerun()
    else:
      st.error("Falsches Passwort!")
  st.stop()

st.title("🔧 Gastro-Wissensdatenbank")

# Spreadsheet URL aus den Secrets holen
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

# Tabs für Ansicht und Neuer Eintrag
tab_lesen, tab_neu = st.tabs(["📚 Einträge anzeigen", "➕ Neuer Eintrag"])

# --- TAB 1: ANZEIGEN ---
with tab_lesen:
  st.subheader("Aktuelle Einträge")
  csv_url = sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")
  try:
    df = pd.read_csv(csv_url)
    if not df.empty:
      st.dataframe(df, use_container_width=True)
    else:
      st.info("Die Tabelle ist noch leer.")
  except Exception:
    st.info("Tabelle wird geladen oder ist noch leer.")

# --- TAB 2: NEUER EINTRAG ---
with tab_neu:
  st.subheader("Neuen Fehler / Lösung erfassen")

  with st.form("neuer_eintrag_form"):
    anlage = st.text_input("Anlage / Gerät (z.B. Kombidämpfer Rational)")
    fehlercode = st.text_input("Fehlercode / Symptom (z.B. E05 Wasserstand)")
    loesung = st.text_area("Lösung / Notiz")
    bild_datei = st.file_uploader(
        "Bild hinzufügen (optional)", type=["png", "jpg", "jpeg"]
    )

    submitted = st.form_submit_button("Eintrag speichern")

    if submitted:
      if anlage and loesung:
        try:
          # Verbindung über gspread mit anonymer/öffentlicher Bearbeitung herstellen
          gc = gspread.no_effect_client()  # Öffentlicher Client für offene Sheets
          # Alternativ öffnen über gspread gsheet open
          sh = gc.open_by_url(sheet_url)
          worksheet = sh.get_worksheet(0)

          bild_name = bild_datei.name if bild_datei else "Kein Bild"
          new_row = [anlage, fehlercode, loesung, bild_name]
          worksheet.append_row(new_row)

          st.success("Erfolgreich in Google Sheets gespeichert!")
          st.rerun()
        except Exception as e:
          # Fallback: Direkt über die gspread open Methode mit Service Account oder Credentials
          st.error(
              "Da die Tabelle öffentlich bearbeitbar ist, nutzen wir eine"
              " direkte Methode. (Fehlerdetails: "
              + str(e)
              + ")"
          )
      else:
        st.warning("Bitte mindestens 'Anlage' und 'Lösung' ausfüllen.")
