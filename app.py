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
st.success("Erfolgreich angemeldet!")

# Google Sheets Daten laden
sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
csv_url = sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")

try:
  df = pd.read_csv(csv_url)
  st.write("### Aktuelle Einträge:")
  st.dataframe(df)
except Exception as e:
  st.info(
      "Deine Tabelle ist noch leer oder wird geladen. Füge hier bald deine"
      " Einträge ein!"
  )
