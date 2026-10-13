import gspread
from google.oauth2.service_account import Credentials
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

sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
csv_url = sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")

# Tabs für Ansicht und Neuer Eintrag
tab_lesen, tab_neu = st.tabs(["📚 Einträge anzeigen", "➕ Neuer Eintrag"])

# --- TAB 1: ANZEIGEN & LÖSCHEN ---
with tab_lesen:
  st.subheader("Aktuelle Einträge")
  try:
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    if not df.empty:
      st.dataframe(df, use_container_width=True)

      # Lösch-Funktion
      st.markdown("---")
      st.subheader("🗑️ Eintrag löschen")
      eintrag_zu_loeschen = st.selectbox(
          "Wähle einen Eintrag zum Löschen:",
          options=df.index,
          format_func=lambda x: (
              f"Zeile {x+2}: {df.iloc[x].values[0]} -"
              f" {df.iloc[x].values[1] if len(df.iloc[x]) > 1 else ''}"
          ),
      )

      if st.button("Ausgewählten Eintrag löschen"):
        try:
          scope = [
              "https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive",
          ]
          creds_dict = dict(st.secrets["connections"]["gsheets"])
          creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
          client = gspread.authorize(creds)
          sheet = client.open_by_url(sheet_url).sheet1
          sheet.delete_rows(int(eintrag_zu_loeschen) + 2)
          st.success("Eintrag erfolgreich gelöscht! Seite wird aktualisiert...")
          st.rerun()
        except Exception as e:
          st.error(
              "Fehler beim Löschen. Bitte prüfe die Service-Account-Berechtigung"
              " in den Secrets."
          )
    else:
      st.info("Die Tabelle ist noch leer.")
  except Exception:
    st.info("Tabelle wird geladen oder ist noch leer.")

# --- TAB 2: NEUER EINTRAG ---
with tab_neu:
  st.subheader("Neuen Fehler / Lösung erfassen")

  with st.form("neuer_eintrag_form", clear_on_submit=True):
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
          scope = [
              "https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive",
          ]
          creds_dict = dict(st.secrets["connections"]["gsheets"])
          creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
          client = gspread.authorize(creds)

          sheet = client.open_by_url(sheet_url).sheet1
          bild_name = bild_datei.name if bild_datei else "Kein Bild"
          sheet.append_row([anlage, fehlercode, loesung, bild_name])

          st.success("Erfolgreich in Google Sheets gespeichert!")
          st.rerun()
        except Exception as e:
          st.error(
              "Fehler beim Speichern. Bitte stelle sicher, dass die"
              " Service-Account-Daten in den Streamlit Secrets hinterlegt sind"
              " und die E-Mail als Bearbeiter in der Tabelle berechtigt ist."
          )
      else:
        st.warning("Bitte mindestens 'Anlage' und 'Lösung' ausfüllen.")
