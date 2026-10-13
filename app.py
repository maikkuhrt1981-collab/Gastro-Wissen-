import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# Passwort-Schutz
if "authenticated" not in st.session_state:
  st.session_state.authenticated = False

if not st.session_state.authenticated:
  st.subheader("🔒 Bitte Passwort eingeben")
  password_input = st.text_input("Passwort:", type="password")
  if st.button("Anmelden"):
    if password_input == "Gastro2026":
      st.session_state.authenticated = True
      st.rerun()
    else:
      st.error("Falsches Passwort!")
  st.stop()


# Verbindung zu Google Sheets via gspread herstellen
@st.cache_resource
py_gc = None


def get_sheet_data():
  # Holt den Spreadsheet-Link aus den Secrets
  sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]

  # Verbindung aufbauen (für öffentliche oder freigegebene Tabellen)
  gc = gspread.oauth_from_dict(...)  # oder direkt über public sheet:
  # Alternativ ganz einfach über pandas lesbar, wenn die Tabelle öffentlich/geteilt ist:
  df = pd.read_csv(
      sheet_url.replace("/edit?usp=drivesdk", "/export?format=csv")
  )
  return df
