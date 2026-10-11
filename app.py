import streamlit as st
import json
import io
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# --- SEITENKONFIGURATION ---
st.set_page_config(page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="centered")

# --- PASSWORT-AUTHENTIFIZIERUNG ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.subheader("🔒 Bitte anmelden")
        pwd = st.text_input("Passwort", type="password")
        if st.button("Anmelden"):
            if pwd == "gastro2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Falsches Passwort!")
        return False
    return True

if not check_password():
    st.stop()

# --- GOOGLE DRIVE ANBINDUNG ---
@st.cache_resource
def get_drive_service():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("❌ Secret-Fehler: Der Block [gcp_service_account] fehlt in deinen Streamlit-Secrets!")
            return None
            
        secrets_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            secrets_dict, 
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        st.error(f"Fehler bei der Verbindung zu Google Drive: {e}")
        return None

# Ordner-ID abrufen
DRIVE_FOLDER_ID = st.secrets.get("GDRIVE_FOLDER_ID", "")
if not DRIVE_FOLDER_ID and "gcp_service_account" in st.secrets:
    DRIVE_FOLDER_ID = st.secrets["gcp_service_account"].get("GDRIVE_FOLDER_ID", "")

def lade_daten_aus_drive():
    service = get_drive_service()
    if not service or not DRIVE_FOLDER_ID:
        return []
    
    try:
        query = f"'{DRIVE_FOLDER_ID}' in parents and name = 'datenbank.json' and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if not files:
            speichere_daten_in_drive([])
            return []
            
        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return json.loads(fh.read().decode('utf-8'))
    except Exception as e:
        st.error(f"Fehler beim Laden aus Drive: {e}")
        return []

def speichere_daten_in_drive(daten):
    service = get_drive_service()
    if not service or not DRIVE_FOLDER_ID:
        st.error("Google Drive Service oder Ordner-ID nicht bereit. Bitte Secrets prüfen.")
        return False
    
    try:
        json_str = json.dumps(daten, ensure_ascii=False, indent=4)
        media = MediaIoBaseUpload(io.BytesIO(json_str.encode('utf-8')), mimetype='application/json', resumable=True)
        
        query = f"'{DRIVE_FOLDER_ID}' in parents and name = 'datenbank.json' and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if files:
            file_id = files[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            file_metadata = {'name': 'datenbank.json', 'parents': [DRIVE_FOLDER_ID]}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except Exception as e:
        st.error(f"Fehler beim Speichern in Drive: {e}")
        return False

def bild_hochladen_zu_drive(uploaded_file):
    service = get_drive_service()
    if not service or not uploaded_file or not DRIVE_FOLDER_ID:
        return None
    
    try:
        file_metadata = {
            'name': uploaded_file.name,
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(uploaded_file.getvalue()), mimetype=uploaded_file.type, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        try:
            service.permissions().create(
                fileId=file['id'],
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
        except:
            pass
            
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"Fehler beim Bildupload: {e}")
        return None

# --- HAUPTAPP ---
st.title("🔧 Gastro-Wissensdatenbank")

datenbank = lade_daten_aus_drive()

menu = st.sidebar.selectbox("Menü", ["Datenbank durchsuchen", "Neuen Eintrag hinzufügen", "🛠️ Diagnose"])

if menu == "Datenbank durchsuchen":
    st.subheader("Datenbank durchsuchen")
    suchbegriff = st.text_input("Wonach suchen? (z.B. Garland, E1, Combi)").strip().lower()
    
    if suchbegriff:
        treffer = [
            eintrag for eintrag in datenbank 
            if suchbegriff in eintrag.get("geraet", "").lower() 
            or suchbegriff in eintrag.get("fehler", "").lower() 
            or suchbegriff in eintrag.get("anleitung", "").lower()
        ]
        
        if treffer:
            st.success(f"{len(treffer)} Eintrag/Einträge gefunden:")
            for t in treffer:
                with st.expander(f"Gerät: {t.get('geraet')} | Fehler: {t.get('fehler')}"):
                    st.write(f"**Reparaturanleitung:**\n{t.get('anleitung')}")
                    if t.get('bild_link'):
                        st.image(t['bild_link'], caption="Schaltplan / Foto", use_container_width=True)
        else:
            st.warning("Keine passenden Einträge gefunden.")

elif menu == "Neuen Eintrag hinzufügen":
    st.subheader("Neuen Eintrag erfassen")
    
    with st.form("eintrag_form"):
        geraet = st.text_input("Gerät / Hersteller:")
        fehler = st.text_input("Fehler / Fehlercode:")
        anleitung = st.text_area("Reparaturanleitung:")
        uploaded_file = st.file_uploader("Schaltplan / Foto hochladen (optional):", type=["png", "jpg", "jpeg", "pdf"])
        
        submitted = st.form_submit_button("Speichern")
        
        if submitted:
            if not geraet or not fehler:
                st.error("Bitte Gerät und Fehler ausfüllen!")
            else:
                bild_link = None
                if uploaded_file is not None:
                    with st.spinner("Lade Bild hoch..."):
                        bild_link = bild_hochladen_zu_drive(uploaded_file)
                
                neuer_eintrag = {
                    "geraet": geraet,
                    "fehler": fehler,
                    "anleitung": anleitung,
                    "bild_link": bild_link,
                    "datum": str(datetime.date.today())
                }
                
                datenbank.append(neuer_eintrag)
                if speichere_daten_in_drive(datenbank):
                    st.success("Erfolgreich hinzugefügt und in Google Drive gespeichert!")
                else:
                    st.error("Fehler beim Speichern in der Datenbank.")

elif menu == "🛠️ Diagnose":
    st.subheader("Google Drive & Datenbank Status")
    if st.button("Verbindung & Datei prüfen"):
        service = get_drive_service()
        if service:
            try:
                query = f"'{DRIVE_FOLDER_ID}' in parents and name = 'datenbank.json' and trashed = false"
                results = service.files().list(q=query, spaces='drive', fields='files(id, name, size)').execute()
                files = results.get('files', [])
                if files:
                    st.success("Gefunden! datenbank.json existiert im Ordner.")
                    st.write(f"Aktuelle Einträge in der Liste: {len(datenbank)}")
                    st.json(datenbank)
                else:
                    st.warning("Die Datei 'datenbank.json' existiert noch nicht im Ordner.")
            except Exception as e:
                st.error(f"Fehler bei der Diagnose: {e}")
