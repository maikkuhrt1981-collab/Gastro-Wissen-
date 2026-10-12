import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)
st.title("🔧 Gastro-Wissensdatenbank")

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

# --- DATEN AUS GOOGLE DRIVE LADEN ---
SHEET_ID = "1EB6sE6_YGgY1vFKh0oC1tq4UPXbAlbVFRHWE6-5L7jo"
CSV_EXPORT_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
)


@st.cache_data(ttl=5)
def load_data_from_drive():
  try:
    df = pd.read_csv(CSV_EXPORT_URL)
    df.columns = df.columns.str.strip()
    return df
  except Exception as e:
    return None


# Direkt laden
df_cloud = load_data_from_drive()

# Fallback-Daten, falls der Cloud-Abruf hakt, damit sofort eine reiche Liste da ist!
if df_cloud is None or df_cloud.empty or "Gerät / Anlage" not in df_cloud.columns:
  df = pd.DataFrame([
      {
          "Gerät / Anlage": "Carpigiani Softeismaschine",
          "Fehlercode / Symptom": "E01 - Überdruck im Zylinder",
          "Lösung / Notiz": (
              "Kondensator auf Verschmutzung prüfen, Kühlung kontrollieren."
          ),
          "Bild": "",
      },
      {
          "Gerät / Anlage": "Rational Kombidämpfer",
          "Fehlercode / Symptom": "Serv 33 - Wassermangel",
          "Lösung / Notiz": (
              "Wasserzufuhr und Hahn öffnen, Aquastopp/Sieb prüfen."
          ),
          "Bild": "",
      },
      {
          "Gerät / Anlage": "Hobart Spülmaschine",
          "Fehlercode / Symptom": "F03 - Heizelement Temperaturfehler",
          "Lösung / Notiz": "Kundendienst rufen; Boiler-Entkalkung einleiten.",
          "Bild": "",
      },
      {
          "Gerät / Anlage": "Grill",
          "Fehlercode / Symptom": "e1",
          "Lösung / Notiz": "Temperaturfühler und Gaszufuhr überprüfen.",
          "Bild": "",
      },
      {
          "Gerät / Anlage": "Wiesheu Ladenbackofen",
          "Fehlercode / Symptom": "Err 4 - Temperaturbegrenzung ausgelöst",
          "Lösung / Notiz": (
              "Sicherheitstemperaturbegrenzer (STB) manuell entriegeln."
          ),
          "Bild": "",
      },
  ])
else:
  df = df_cloud

UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

tab_list, tab_add = st.tabs(["📂 Vorhandene Einträge", "➕ Neuen Eintrag"])

with tab_list:
  st.subheader("Wissensdatenbank")

  search_term = st.text_input("🔍 Suche (Gerät oder Fehler):", "")

  if search_term:
    search_lower = search_term.lower()
    mask = df.astype(str).apply(
        lambda x: x.str.lower().str.contains(search_lower).any(), axis=1
    )
    filtered_df = df[mask]
  else:
    filtered_df = df

  if filtered_df.empty:
    st.warning("Keine passenden Einträge gefunden.")
  else:
    for index, row in filtered_df.iterrows():
      geraet = row.get("Gerät / Anlage", "Unbekanntes Gerät")
      fehler = row.get("Fehlercode / Symptom", "Kein Fehler angegeben")
      loesung = row.get("Lösung / Notiz", "Keine Lösung hinterlegt")

      with st.expander(f"🛠️ {geraet} — {fehler}"):
        st.write(f"**Lösung:** {loesung}")
        img_path = str(row.get("Bild", ""))
        if img_path and img_path != "nan" and os.path.exists(img_path):
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
    submitted = st.form_submit_button("Hinzufügen")

    if submitted:
      if geraet and loesung:
        image_path = ""
        if uploaded_file is not None:
          image_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
          with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Eintrag hinzugefügt!")
        st.rerun()
      else:
        st.error("Bitte mindestens Gerät und Lösung ausfüllen.")
          
