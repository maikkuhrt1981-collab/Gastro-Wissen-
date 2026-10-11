import difflib
import io
import json
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank")


# --- PASSWORTSCHUTZ ---
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
      st.error("Falsches Passwort! Bitte versuche es noch einmal.")
  st.stop()


# --- GOOGLE DRIVE VERBINDUNG & DATEN-SYNC ---
@st.cache_resource
def init_drive_service():
  try:
    if "GDRIVE_JSON" in st.secrets:
      raw_json = st.secrets["GDRIVE_JSON"]
      secret_data = (
          json.loads(raw_json) if isinstance(raw_json, str) else dict(raw_json)
      )
    else:
      secret_data = dict(st.secrets)

    if "private_key" in secret_data:
      secret_data["private_key"] = secret_data["private_key"].replace(
          "\\n", "\n"
      )

    folder_id = st.secrets.get(
        "GDRIVE_FOLDER_ID", "1gvcVXerMdevilo5vDDVVFBK8q-wc_uHW"
    )

    creds = service_account.Credentials.from_service_account_info(
        secret_data, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)
    return service, folder_id
  except Exception as e:
    st.error(f"Verbindungsfehler zu Google Drive: {e}")
    return None, None


service, FOLDER_ID = init_drive_service()
FILENAME = "gastro_wissen_daten.csv"


def load_data_from_drive():
  if not service:
    return pd.DataFrame([
        {
            "Gerät / Anlage": "Convotherm Combi-Dämpfer",
            "Fehlercode / Symptom": "E04 - Wassertank läuft leer",
            "Lösung / Notiz": (
                "Schwimmerschalter entkalken und auf Freigang prüfen."
            ),
        }
    ])

  try:
    query = f"'{FOLDER_ID}' in parents and name = '{FILENAME}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
      file_id = files[0]["id"]
      request = service.files().get_media(fileId=file_id)
      fh = io.BytesIO()
      downloader = MediaIoBaseDownload(fh, request)
      done = False
      while not done:
        _, done = downloader.next_chunk()
      fh.seek(0)
      return pd.read_csv(fh)
    else:
      df_init = pd.DataFrame([
          {
              "Gerät / Anlage": "Convotherm Combi-Dämpfer",
              "Fehlercode / Symptom": "E04 - Wassertank läuft leer",
              "Lösung / Notiz": (
                  "Schwimmerschalter entkalken und auf Freigang prüfen."
              ),
          },
          {
              "Gerät / Anlage": "Garland Clamshell Grill",
              "Fehlercode / Symptom": "Temperaturabweichung Oben/Unten",
              "Lösung / Notiz": (
                  "Fühlerkalibrierung im Service-Menü durchführen."
              ),
          },
      ])
      save_data_to_drive(df_init)
      return df_init
  except Exception as e:
    st.warning(f"Konnte Daten nicht aus Drive laden: {e}")
    return pd.DataFrame()


def save_data_to_drive(df):
  if not service:
    return
  try:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    media_upload = MediaIoBaseUpload(
        io.BytesIO(csv_bytes), mimetype="text/csv", resumable=True
    )

    query = f"'{FOLDER_ID}' in parents and name = '{FILENAME}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if files:
      file_id = files[0]["id"]
      service.files().update(
          fileId=file_id, media_body=media_upload
      ).execute()
    else:
      file_metadata = {"name": FILENAME, "parents": [FOLDER_ID]}
      service.files().create(
          body=file_metadata, media_body=media_upload, fields="id"
      ).execute()
  except Exception as e:
    st.error(f"Fehler beim Speichern in Google Drive: {e}")


if "gastro_db" not in st.session_state:
  st.session_state.gastro_db = load_data_from_drive()

# --- HAUPTOBERFLÄCHE ---
tab_list, tab_add = st.tabs(
    ["📂 Vorhandene Einträge", "➕ Neuen Eintrag hinzufügen"]
)

with tab_list:
  st.subheader("Übersicht der Wissensdatenbank (Google Drive)")

  if st.button("🔄 Daten aus Drive aktualisieren"):
    st.session_state.gastro_db = load_data_from_drive()
    st.rerun()

  search_term = st.text_input(
      "🔍 Suche nach Gerät oder Fehler (mit Rechtschreibtoleranz):", ""
  )
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

  st.dataframe(filtered_df, use_container_width=True)

with tab_add:
  st.subheader("Neuen Eintrag erfassen & in Google Drive speichern")

  with st.form("add_form"):
    geraet = st.text_input("Gerät / Anlage (z.B. Carpigiani, Taylor, Convotherm):")
    fehler = st.text_input("Fehlercode / Symptom:")
    loesung = st.text_area("Lösung / Reparatur-Notiz:")

    submitted = st.form_submit_button("Eintrag speichern & in Drive ablegen")

    if submitted:
      if geraet and loesung:
        new_entry = {
            "Gerät / Anlage": geraet,
            "Fehlercode / Symptom": fehler,
            "Lösung / Notiz": loesung,
        }
        st.session_state.gastro_db = pd.concat(
            [st.session_state.gastro_db, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        save_data_to_drive(st.session_state.gastro_db)
        st.success(
            f"Eintrag für '{geraet}' erfolgreich hinzugefügt und in Google"
            " Drive gespeichert!"
        )
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
