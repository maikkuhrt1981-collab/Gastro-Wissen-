import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

# Modernes Custom CSS für ein schöneres Smartphone-Design
st.markdown(
    """
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
        padding-left: 20px;
        padding-right: 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    div.stButton > button:hover {
        background-color: #e03e3e;
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🔧 Gastro-Wissensdatenbank")
st.markdown("---")

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

# --- DATENBANK & SPEICHERUNG ---
DB_FILE = "gastro_lokal.csv"
UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

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
  st.subheader("💡 Wissensdatenbank durchsuchen")

  search_term = st.text_input(
      "🔍 Suchbegriff eingeben (z. B. Rational, Fehler, etc.):", ""
  )
  df = st.session_state.gastro_db

  if search_term:
    search_lower = search_term.lower()
    mask = df.astype(str).apply(
        lambda x: x.str.lower().str.contains(search_lower).any(), axis=1
    )
    filtered_df = df[mask]
  else:
    filtered_df = df

  st.write("")  - Abstandsleiste

  if filtered_df.empty:
    st.warning("⚠️ Keine passenden Einträge gefunden.")
  else:
    st.caption(f"Anzahl Ergebnisse: {len(filtered_df)}")
    for index, row in filtered_df.iterrows():
      geraet = str(row.get("Gerät / Anlage", "Unbekanntes Gerät"))
      fehler = str(row.get("Fehlercode / Symptom", "Kein Fehler angegeben"))
      loesung = str(row.get("Lösung / Notiz", "Keine Lösung hinterlegt"))

      # Schöne, moderne Box für jeden Eintrag
      with st.container():
        st.markdown(
            f"""
                <div style="background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #ff4b4b; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
                    <h3 style="margin: 0; color: #111; font-size: 18px;">🛠️ {geraet}</h3>
                    <p style="margin: 5px 0 10px 0; color: #d9534f; font-weight: bold; font-size: 15px;">Fehler: {fehler}</p>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
                    <p style="margin: 5px 0 0 0; color: #444; font-size: 14px;"><b>Lösung:</b> {loesung}</p>
                </div>
                """,
            unsafe_allow_html=True,
        )

        # Falls ein Bild existiert, sauber darunter anzeigen
        img_path = str(row.get("Bild", ""))
        if img_path and img_path != "nan" and os.path.exists(img_path):
          st.image(img_path, caption="Foto zum Fehler", use_container_width=True)

with tab_add:
  st.subheader("✍️ Neuen Fehler / Eintrag erfassen")
  st.markdown(
      "Fülle die Felder aus, um das Wissen dauerhaft in der App zu speichern."
  )

  with st.form("add_form_styled", clear_on_submit=True):
    geraet_input = st.text_input("Gerät / Anlage (z.B. Rational Combi):")
    fehler_input = st.text_input("Fehlercode / Symptom (z.B. E12):")
    loesung_input = st.text_area("Lösung / Notiz (Was ist zu tun?):")
    uploaded_file = st.file_uploader(
        "📷 Foto hochladen (optional):", type=["jpg", "jpeg", "png"]
    )

    st.write("")
    submitted = st.form_submit_button("💾 Eintrag dauerhaft speichern")

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

        st.success("🎉 Eintrag erfolgreich gespeichert!")
        st.rerun()
      else:
        st.error(
            "⚠️ Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung"
            " / Notiz' aus."
        )
