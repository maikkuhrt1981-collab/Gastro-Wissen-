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

# Tabs für Ansicht und Neuer Eintrag
tab_lesen, tab_neu = st.tabs(["📚 Einträge anzeigen", "➕ Neuer Eintrag"])

# --- TAB 1: ANZEIGEN ---
with tab_lesen:
  st.subheader("Aktuelle Einträge")
  csv_url = sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")
  try:
    df = pd.read_csv(csv_url)
    # Spaltennamen bereinigen (falls Leerzeichen drin sind)
    df.columns = df.columns.str.strip()
    # Leere Zeilen entfernen
    df = df.dropna(how="all")

    if not df.empty and len(df.columns) > 0:
      st.dataframe(df, use_container_width=True)
    else:
      st.info(
          "Die Tabelle ist aktuell noch leer. Trage in deiner Google-Tabelle"
          " einen ersten Wert ein!"
      )
  except Exception as e:
    st.info("Tabelle wird geladen oder ist noch leer.")

# --- TAB 2: NEUER EINTRAG ---
with tab_neu:
  st.subheader("Neuen Fehler / Lösung erfassen")
  st.info(
      "Du kannst neue Einträge direkt in deiner Google-Tabelle hinzufügen."
      " Sie erscheinen danach sofort hier in der Ansicht!"
  )
  st.markdown(f"[🔗 Zur Google-Tabelle öffnen]({sheet_url})")
