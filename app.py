
import json
import io
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="centered")

# --- PASSWORT-SCHUTZ ---
PASSWORT = "gastro2026"

def passwort_pruefen():
    if "authentifiziert" not in st.session_state:
        st.session_state.authentifiziert = False

    if not st.session_state.authentifiziert:
        st.title("🔒 Gastro-Wissensdatenbank - Login")
        eingabe = st.text_input("Bitte Team-Passwort eingeben:", type="password")
        if st.button("Anmelden"):
            if eingabe == PASSWORT:
                st.session_state.authentifiziert = True
                st.rerun()
            else:
                st.error("Falsches Passwort!")
        return False
    return True

if not passwort_pruefen():
    st.stop()

# --- GOOGLE DRIVE VERBINDUNG EINRICHTEN ---
def get_drive_service():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        return None

DRIVE_FOLDER_ID = st.secrets.get("GDRIVE_FOLDER_ID", "1gvcVXerMdevilo5vDDVVFBK8q-wc_uHW")

# --- DATEN LADEN & SPEICHERN ÜBER GOOGLE DRIVE ---
def lade_daten_aus_drive():
    service = get_drive_service()
    if not service:
        return standard_daten()
    
    try:
        query = f"'{DRIVE_FOLDER_ID}' in parents and name = 'datenbank.json' and trashed = false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        files = results.get('files', [])
        
        if not files:
            initial_data = standard_daten()
            speichere_daten_in_drive(initial_data)
            return initial_data
        
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
        return standard_daten()

def speichere_daten_in_drive(daten):
    service = get_drive_service()
    if not service:
        return
    
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
    except Exception as e:
        st.error(f"Fehler beim Speichern in Drive: {e}")

def bild_hochladen_zu_drive(uploaded_file):
    service = get_drive_service()
    if not service or not uploaded_file:
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
        return None

# --- STANDARDDATEN ---
def standard_daten():
    return [
        {
            "geraet": "Frymaster / Frittieranlagen",
            "fehler": "Alarm 6 / High Temp / Übertemperatur",
            "reparatur": "Übertemperatur im Becken überschritten. Thermostat prüfen, Fühler auf Kabelbruch und Widerstand prüfen, Schütz prüfen.",
            "bild_url": ""
        },
        {
            "geraet": "Garland Grill",
            "fehler": "Alarm 6",
            "reparatur": "Sensorstecker sitzt lose oder Kabelbeschädigung am Plattenfühler. Stecker prüfen und ggf. nachdrücken.",
            "bild_url": ""
        },
        {
            "geraet": "Carpigiani Speiseeisbereiter",
            "fehler": "E20 / Rührwerk Überlast",
            "reparatur": "Mixer-Welle blockiert oder Mix-Konsistenz zu fest eingestellt. Chargengröße prüfen, Getriebe und Messer auf Verschleiß kontrollieren.",
            "bild_url": ""
        }
    ]

# Daten laden
datenbank = lade_daten_aus_drive()

# --- SEITENLEISTE (NAVIGATION) ---
st.sidebar.title("Navigation")
auswahl = st.sidebar.radio("Menü", ["🔍 Fehler suchen", "➕ Neuen Eintrag hinzufügen"])

# --- ANSICHT 1: FEHLER SUCHEN ---
if auswahl == "🔍 Fehler suchen":
    st.title("Datenbank durchsuchen")
    suchbegriff = st.text_input("Wonach suchen? (z.B. Alarm 6, E20, Carpigiani):", "")
    
    if suchbegriff:
        ergebnisse = [
            e for e in datenbank 
            if suchbegriff.lower() in e["geraet"].lower() 
            or suchbegriff.lower() in e["fehler"].lower() 
            or suchbegriff.lower() in e["reparatur"].lower()
        ]
        
        if ergebnisse:
            for item in ergebnisse:
                st.success("Gefundener Eintrag:")
                st.markdown(f"## Gerät: {item['geraet']}")
                st.markdown(f"- **Fehler:** {item['fehler']}")
                st.markdown(f"- **Reparatur:** {item['reparatur']}")
                
                if item.get('bild_url'):
                    st.markdown(f"- **Schaltplan / Foto:** [Datei in Google Drive öffnen]({item['bild_url']})")
                st.markdown("---")
        else:
            st.warning("Keine passenden Einträge gefunden.")

# --- ANSICHT 2: NEUEN EINTRAG HINZUFÜGEN ---
elif auswahl == "➕ Neuen Eintrag hinzufügen":
    st.title("Neuen Eintrag hinzufügen")
    
    with st.form("neuer_eintrag_form"):
        neues_geraet = st.text_input("Gerät / Hersteller:")
        neuer_fehler = st.text_input("Fehler / Fehlercode:")
        neue_reparatur = st.text_area("Reparaturanleitung:")
        hochgeladene_datei = st.file_uploader("Schaltplan / Foto hochladen (optional):", type=["png", "jpg", "jpeg", "pdf"])
        
        submit_button = st.form_submit_button(label="Speichern")
        
        if submit_button:
            if neues_geraet and neuer_fehler and neue_reparatur:
                bild_link = ""
                if hochgeladene_datei is not None:
                    with st.spinner("Lade Datei in Google Drive hoch..."):
                        bild_link = bild_hochladen_zu_drive(hochgeladene_datei)
                
                neuer_eintrag = {
                    "geraet": neues_geraet,
                    "fehler": neuer_fehler,
                    "reparatur": neue_reparatur,
                    "bild_url": bild_link if bild_link else ""
                }
                
                datenbank.append(neuer_eintrag)
                speichere_daten_in_drive(datenbank)
                
                st.success("Erfolgreich hinzugefügt!")
            else:
                st.error("Bitte alle Pflichtfelder (Gerät, Fehler, Reparatur) ausfüllen.")
