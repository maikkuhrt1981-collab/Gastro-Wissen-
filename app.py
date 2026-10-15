import base64
import pandas as pd
import requests
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

# Fester Link zur Tabelle (zum Lesen)
sheet_url = "https://docs.google.com/spreadsheets/d/1L8WF_WNugzy8rTgHjBJ-aS7OG01qnVonDfeDkW5xA8Q/edit?usp=drivesdk"
csv_url = sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")

# Deine Google Apps Script Web-App URL
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxmJAJ11kb7KvESLGesaBSDfjyl2q8vh_WCeoVyvJ5PlSSksrWhuUQE67ogs6s5Radm/exec"

# Tabs für Ansicht und Neuer Eintrag
tab_lesen, tab_neu = st.tabs(["📚 Einträge anzeigen", "➕ Neuer Eintrag"])

# --- TAB 1: ANZEIGEN ---
with tab_lesen:
  st.subheader("Aktuelle Einträge")
  try:
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")

    if not df.empty:
      st.dataframe(df, use_container_width=True)

      st.markdown("---")
      st.subheader("🖼️ Bild / Details anzeigen")
      eintrag_index = st.selectbox(
          "Wähle Zeile aus:",
          options=df.index,
          format_func=lambda x: f"Zeile {x+2}: {df.iloc[x].values[0]}",
      )
      if eintrag_index is not None:
        akt_zeile = df.iloc[eintrag_index]
        letzte_spalte = str(akt_zeile.values[-1])
        if letzte_spalte.startswith("http"):
          st.markdown(f"🔗 [Direkt zum Bild in Google Drive]({letzte_spalte})")
          st.image(letzte_spalte, caption="Hochgeladenes Bild", width=300)
        else:
          st.info("Für diesen Eintrag ist kein Bild hinterlegt.")
    else:
      st.info("Die Tabelle ist noch leer.")
  except Exception as e:
    st.info(f"Tabelle wird geladen... ({e})")

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
          bild_data_b64 = ""
          bild_name = ""
          bild_mime = ""

          if bild_datei is not None:
            bild_name = bild_datei.name
            bild_mime = bild_datei.type
            bild_data_b64 = base64.b64encode(bild_datei.getvalue()).decode(
                "utf-8"
            )

          payload = {
              "anlage": anlage,
              "fehlercode": fehlercode,
              "loesung": loesung,
              "bild_name": bild_name,
              "bild_mime": bild_mime,
              "bild_data": bild_data_b64,
          }
          response = requests.post(WEB_APP_URL, json=payload)

          if response.status_code == 200:
            st.success(
                "Erfolgreich mit Bild in Google Drive & Sheets gespeichert!"
            )
            st.rerun()
          else:
            st.error("Fehler beim Speichern über das Skript.")
        except Exception as e:
          st.error(f"Verbindungsfehler: {e}")
      else:
        st.warning("Bitte mindestens 'Anlage' und 'Lösung' ausfüllen.")
