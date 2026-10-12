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

# --- DAUERHAFTE SPEICHERUNG AUF DEM SERVER ---
DB_FILE = "gastro_lokal.csv"
UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

# Laden oder Initialisieren der persistenten Datenbank
if "gastro_db" not in st.session_state:
  if os.path.exists(DB_FILE):
    try:
      st.session_state.gastro_db = pd.read_csv(DB_FILE)
    except Exception:
      st.session_state.gastro_db = pd.DataFrame()

  if "gastro_db" not in st.session_state or st.session_state.gastro_db.empty:
    st.session_state.gastro_db = pd.DataFrame([
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
    st.session_state.gastro_db.to_csv(DB_FILE, index=False)

tab_list, tab_add = st.tabs(["📂 Vorhandene Einträge", "➕ Neuen Eintrag"])

with tab_list:
  st.subheader("Wissensdatenbank")

  search_term = st.text_input("🔍 Suche (Gerät oder Fehler):", "")
  df = st.session_state.gastro_db

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
      geraet = str(row.get("Gerät / Anlage", "Unbekanntes Gerät"))
      fehler = str(row.get("Fehlercode / Symptom", "Kein Fehler angegeben"))
      loesung = str(row.get("Lösung / Notiz", "Keine Lösung hinterlegt"))

      with st.expander(f"🛠️ {geraet} — {fehler}"):
        st.write(f"**Lösung:** {loesung}")
        img_path = str(row.get("Bild", ""))
        if img_path and img_path != "nan" and os.path.exists(img_path):
          st.image(img_path, caption="Foto", use_container_width=True)

with tab_add:
  st.subheader("Neuen Eintrag erfassen")
  with st.form("add_form_persist", clear_on_submit=True):
    geraet_input = st.text_input("Gerät / Anlage:")
    fehler_input = st.text_input("Fehlercode / Symptom:")
    loesung_input = st.text_area("Lösung / Notiz:")
    uploaded_file = st.file_uploader(
        "📷 Foto hochladen (optional):", type=["jpg", "jpeg", "png"]
    )
    submitted = st.form_submit_button("Eintrag speichern")

    if submitted:
      if geraet_input and loesung_input:
        image_path = ""
        if uploaded_file is not None:
          image_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
          with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        new_row = {
            "Gerät / Anlage": geraet_input,
            "Fehlercode / Symptom": fehler_input,
            "Lösung / Notiz": loesung_input,
            "Bild": image_path,
        }

        st.session_state.gastro_db = pd.concat(
            [st.session_state.gastro_db, pd.DataFrame([new_row])],
            ignore_index=True,
        )
        st.session_state.gastro_db.to_csv(DB_FILE, index=False)

        st.success("Eintrag erfolgreich dauerhaft gespeichert!")
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
