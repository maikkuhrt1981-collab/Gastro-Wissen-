import difflib
import os
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)
st.title("🔧 Gastro-Wissensdatenbank (Google Drive Sync)")

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


@st.cache_resource
def init_gspread():
  try:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Hier lesen wir die Secrets absolut sicher und direkt einzeln aus:
    private_key_raw = st.secrets.get("private_key", "")
    if not private_key_raw and "GDRIVE_JSON" in st.secrets:
      import json

      raw = st.secrets["GDRIVE_JSON"]
      creds_dict = json.loads(raw) if isinstance(raw, str) else dict(raw)
    else:
      creds_dict = {
          "type": st.secrets.get("type", "service_account"),
          "project_id": st.secrets.get("project_id", "projektdaten"),
          "private_key_id": st.secrets.get("private_key_id", ""),
          "private_key": private_key_raw,
          "client_email": st.secrets.get("client_email", ""),
          "client_id": st.secrets.get("client_id", ""),
          "auth_uri": "https://accounts.google.com/o/oauth2/auth",
          "token_uri": "https://oauth2.googleapis.com/token",
          "auth_provider_x509_cert_url": (
              "https://www.googleapis.com/oauth2/v1/certs"
          ),
          "client_x509_cert_url": st.secrets.get("client_x509_cert_url", ""),
      }

    if "private_key" in creds_dict:
      creds_dict["private_key"] = creds_dict["private_key"].replace(
          "\\n", "\n"
      )

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)
  except Exception as e:
    # Falls die Secrets nicht als flache Variablen da sind, fangen wir es ab
    st.warning(
        "Hinweis zu den Secrets (läuft im lokalen Fallback-Modus): " + str(e)
    )
    return None


gc = init_gspread()
SPREADSHEET_NAME = "gastro_wissen_daten"


def load_data_from_sheet():
  if not gc:
    return pd.DataFrame(
        columns=["Gerät / Anlage", "Fehlercode / Symptom", "Lösung / Notiz", "Bild"]
    )
  try:
    try:
      sheet = gc.open(SPREADSHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
      spreadsheet = gc.create(SPREADSHEET_NAME)
      sheet = spreadsheet.sheet1
      sheet.append_row([
          "Gerät / Anlage",
          "Fehlercode / Symptom",
          "Lösung / Notiz",
          "Bild",
      ])
    data = sheet.get_all_records()
    if not data:
      return pd.DataFrame(
          columns=["Gerät / Anlage", "Fehlercode / Symptom", "Lösung / Notiz", "Bild"]
      )
    return pd.DataFrame(data)
  except Exception as e:
    return pd.DataFrame(
        columns=["Gerät / Anlage", "Fehlercode / Symptom", "Lösung / Notiz", "Bild"]
    )


def save_row_to_sheet(geraet, fehler, loesung, bild):
  if not gc:
    return
  try:
    sheet = gc.open(SPREADSHEET_NAME).sheet1
    sheet.append_row([geraet, fehler, loesung, bild])
  except Exception as e:
    st.error(f"Fehler beim Speichern in Drive: {e}")


if "gastro_db" not in st.session_state:
  st.session_state.gastro_db = load_data_from_sheet()

UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

tab_list, tab_add = st.tabs(["📂 Vorhandene Einträge", "➕ Neuen Eintrag mit Bild"])

with tab_list:
  st.subheader("Wissensdatenbank (Google Drive)")
  if st.button("🔄 Aktualisieren"):
    st.session_state.gastro_db = load_data_from_sheet()
    st.success("Aktualisiert!")
    st.rerun()

  search_term = st.text_input("🔍 Suche:", "")
  df = st.session_state.gastro_db

  if search_term and not df.empty:
    search_lower = search_term.lower()


    def fuzzy_match(row):
      combined_text = (
          f"{row.get('Gerät / Anlage', '')} {row.get('Fehlercode / Symptom', '')} {row.get('Lösung / Notiz', '')}".lower()
      )
      if search_lower in combined_text:
        return True
      words_in_row = combined_text.split()
      for sw in search_lower.split():
        if difflib.get_close_matches(sw, words_in_row, n=1, cutoff=0.4):
          return True
      return False


    filtered_df = df[df.apply(fuzzy_match, axis=1)]
  else:
    filtered_df = df

  for index, row in filtered_df.iterrows():
    with st.expander(
        f"🛠️ {row.get('Gerät / Anlage', '')} —"
        f" {row.get('Fehlercode / Symptom', '')}"
    ):
      st.write(f"**Lösung:** {row.get('Lösung / Notiz', '')}")
      img_path = row.get("Bild", "")
      if img_path and os.path.exists(str(img_path)):
        st.image(img_path, caption="Foto", use_container_width=True)

with tab_add:
  st.subheader("Neuen Eintrag erfassen")
  with st.form("add_form"):
    geraet = st.text_input("Gerät / Anlage:")
    fehler = st.text_input("Fehlercode / Symptom:")
    loesung = st.text_area("Lösung / Notiz:")
    uploaded_file = st.file_uploader(
        "📷 Foto hochladen:", type=["jpg", "jpeg", "png"]
    )
    submitted = st.form_submit_button("Speichern")

    if submitted:
      if geraet and loesung:
        image_path = ""
        if uploaded_file is not None:
          image_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
          with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        save_row_to_sheet(geraet, fehler, loesung, image_path)

        new_entry = {
            "Gerät / Anlage": geraet,
            "Fehlercode / Symptom": fehler,
            "Lösung / Notiz": loesung,
            "Bild": image_path,
        }
        st.session_state.gastro_db = pd.concat(
            [st.session_state.gastro_db, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        st.success("Erfolgreich gespeichert und in Drive abgelegt!")
        st.rerun()
      else:
        st.error("Bitte mindestens Gerät und Lösung ausfüllen.")
