import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank")


# --- GOOGLE DRIVE VERBINDUNG & AUTHENTIFIZIERUNG ---
@st.cache_resource
def init_drive_service():
  try:
    # Direktes Auslesen der flachen TOML-Secrets
    secret_data = {
        "type": st.secrets["type"],
        "project_id": st.secrets["project_id"],
        "private_key_id": st.secrets["private_key_id"],
        # Hier werden echte Zeilenumbrüche für das PEM-Format wiederhergestellt
        "private_key": st.secrets["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["client_email"],
        "client_id": st.secrets["client_id"],
        "auth_uri": st.secrets["auth_uri"],
        "token_uri": st.secrets["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["client_x509_cert_url"],
        "universe_domain": st.secrets["universe_domain"],
    }

    folder_id = st.secrets["folder_id"]

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
      mime_type = file.get("mimeType", "")

      col1, col2, col3 = st.columns([3, 2, 1])
      with col1:
        st.markdown(f"**{file_name}**")
      with col2:
        st.caption(f"Typ: {mime_type.split('.')[-1]}")
      with col3:
        if st.button("Ansehen", key=file_id):
          st.info(f"Datei ausgewählt.")

with tab_upload:
  st.subheader("Neues Dokument oder Handbuch hinzufügen")

  uploaded_file = st.file_uploader(
      "Wähle eine Datei aus (PDF, TXT, Bilder, etc.)",
      type=["pdf", "txt", "png", "jpg", "jpeg", "csv"],
  )

  if uploaded_file is not None:
    if st.button("In Google Drive hochladen"):
      file_metadata = {"name": uploaded_file.name, "parents": [FOLDER_ID]}

      media_upload = MediaIoBaseUpload(
          io.BytesIO(uploaded_file.getvalue()),
          mimetype=uploaded_file.type,
          resumable=True,
      )

      try:
        service.files().create(
            body=file_metadata, media_body=media_upload, fields="id"
        ).execute()
        st.success(f"Datei '{uploaded_file.name}' erfolgreich hochgeladen!")
        st.rerun()
      except Exception as e:
        st.error(f"Fehler beim Hochladen: {e}")
