import json
import io
import datetime
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Gastro-Wissensdatenbank", layout="centered")

# --- GOOGLE DRIVE INITIALISIERUNG ---
@st.cache_resource
def init_gdrive_service():
    try:
        if "GDRIVE_JSON" not in st.secrets or "GDRIVE_FOLDER_ID" not in st.secrets:
            st.error("Google Drive Secrets fehlen in den Streamlit-Einstellungen.")
            return None, None

        gdrive_json_raw = st.secrets["GDRIVE_JSON"]
        
        # Falls es ein String ist, sicherstellen, dass der private Schlüssel korrekt formatiert ist
        if isinstance(gdrive_json_raw, str):
            creds_dict = json.loads(gdrive_json_raw)
        else:
            creds_dict = dict(gdrive_json_raw)

        # WICHTIG: Zeilenumbrüche im privaten Schlüssel korrigieren
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=["https://www.googleapis.com/auth/drive"]
        )

        service = build("drive", "v3", credentials=creds)
        folder_id = st.secrets["GDRIVE_FOLDER_ID"]
        
        return service, folder_id

    except Exception as e:
        st.error(f"Fehler bei der Verbindung zu Google Drive: {e}")
        return None, None

# Service und Ordner-ID abrufen
service, FOLDER_ID = init_gdrive_service()

# --- PASSWORT-AUTHENTIFIZIERUNG ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔒 Gastro-Wissensdatenbank - Anmeldung")
        pwd = st.text_input("Bitte Passwort eingeben:", type="password")
        if st.button("Anmelden"):
            if pwd == "gastro123":  
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Falsches Passwort!")
        return False
    return True

if not check_password():
    st.stop()

# --- HAUPTPROGRAMM ---
st.title("🛠️ Gastro-Wissensdatenbank")
if service and FOLDER_ID:
    st.success("Google Drive Service ist bereit und verbunden.")
else:
    st.error("Google Drive Service oder Ordner-ID nicht bereit.")
