import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank")


# --- GOOGLE DRIVE VERBINDUNG & AUTHENTIFIZIERUNG ---
@st.cache_resource
def init_drive_service():
  try:
    # Versuche, die Secrets zu laden
    if "gdrive" in st.secrets:
      secret_data = dict(st.secrets["gdrive"])
    elif "GDRIVE_JSON" in st.secrets:
      # Falls es als JSON-String hinterlegt ist
      raw_json = st.secrets["GDRIVE_JSON"]
      if isinstance(raw_json, str):
        secret_data = json.loads(raw_json)
      else:
        secret_data = dict(raw_json)
    else:
      st.error(
          "Keine 'gdrive' oder 'GDRIVE_JSON' Sektion in den Streamlit-Secrets"
          " gefunden!"
      )
      return None, None

    # Privaten Schlüssel bereinigen und Zeilenumbrüche korrigieren
    if "private_key" in secret_data:
      pk = secret_data["private_key"]
      # Ersetzt wörtliche \n-Sequenzen durch echte Zeilenumbrüche
      pk = pk.replace("\\n", "\n")
      secret_data["private_key"] = pk

    # Ordner-ID aus Secrets oder Fallback laden
    folder_id = st.secrets.get("folder_id") or st.secrets.get(
        "GDRIVE_FOLDER_ID", "1gvcVXerMdevilo5vDDVVFBK8q-wc_uHW"
    )

    # Google Credentials erstellen
    creds = service_account.Credentials.from_service_account_info(
        secret_data, scopes=["https://www.googleapis.com/auth/drive"]
    )

    service = build("drive", "v3", credentials=creds)
    return service, folder_id

  except Exception as e:
    st.error(f"Fehler bei der Verbindung zu Google Drive: {e}")
    return None, None


service, FOLDER_ID = init_drive_service()

if not service or not FOLDER_ID:
  st.error("Google Drive Service oder Ordner-ID nicht bereit.")
  st.stop()


# --- HILFSFUNKTIONEN FÜR DRIVE ---
def get_files_in_folder(current_folder_id):
  try:
    query = f"'{current_folder_id}' in parents and trashed = false"
    results = (
        service.files()
        .list(
            q=query,
            pageSize=50,
            fields="files(id, name, mimeType, modifiedTime, size)",
        )
        .execute()
    )
    return results.get("files", [])
  except Exception as e:
    st.error(f"Fehler beim Laden der Dateien: {e}")
    return []


# --- HAUPTOBERFLÄCHE DER APP ---
st.success("Erfolgreich mit Google Drive verbunden!")

# Tabs für Navigation
tab_list, tab_upload = st.tabs(
    ["📂 Vorhandene Dokumente & Geräte", "📤 Neues Dokument hochladen"]
)

with tab_list:
  st.subheader("Einträge im Wissensdatenbank-Ordner")

  if st.button("🔄 Liste aktualisieren"):
    st.rerun()

  files = get_files_in_folder(FOLDER_ID)

  if not files:
    st.info(
        "Der Ordner ist aktuell leer oder es konnten keine Dateien gefunden"
        " werden."
    )
  else:
    for file in files:
      file_name = file.get("name")
      file_id = file.get("id")
      mime_type = file.get("mimeType")

      col1, col2, col3 = st.columns([3, 2, 1])
      with col1:
        st.markdown(f"**{file_name}**")
      with col2:
        st.caption(f"Typ: {mime_type.split('.')[-1]}")
      with col3:
        if st.button("Öffnen / Ansehen", key=file_id):
          st.info(
              f"Datei-ID: {file_id} (Direkter Download/Ansicht kann hier"
              " erweitert werden)"
          )

with tab_upload:
  st.subheader("Neues Dokument oder Handbuch hinzufügen")

  uploaded_file = st.file_uploader(
      "Wähle eine Datei aus (PDF, TXT, Bilder, etc.)",
      type=["pdf", "txt", "png", "jpg", "jpeg", "csv"],
  )

  if uploaded_file is not None:
    if st.button("In Google Drive hochladen"):
      file_metadata = {"name": uploaded_file.name, "parents": [FOLDER_ID]}

      media = MediaIoBaseDownload(
          io.BytesIO(uploaded_file.getvalue()),
          mimetype=uploaded_file.type,
          chunksize=1024 * 1024,
      )
      # Alternativ MediaFileUpload nutzen:
      # Wir speichern die Bytes temporär oder nutzen MediaIoBaseUpload:
      from googleapiclient.http import MediaIoBaseUpload

      media_upload = MediaIoBaseUpload(
          io.BytesIO(uploaded_file.getvalue()),
          mimetype=uploaded_file.type,
          resumable=True,
      )

      try:
        file = (
            service.files()
            .create(body=file_metadata, media_body=media_upload, fields="id")
            .execute()
        )
        st.success(f"Datei '{uploaded_file.name}' erfolgreich hochgeladen!")
        st.rerun()
      except Exception as e:
        st.error(f"Fehler beim Hochladen: {e}")
