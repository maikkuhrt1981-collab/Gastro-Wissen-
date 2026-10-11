import difflib
import os
import pandas as pd
import streamlit as str_lit
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank (Google Drive / Sheets Anbindung)")


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


# --- LOKALER BILDSPEICHER & DATEN-INIT ---
UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

# Fallback-Datenbank, falls Verbindung aufgebaut wird
if "gastro_db" not in st.session_state:
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
          "Gerät / Anlage": "Convotherm Combi-Dämpfer",
          "Fehlercode / Symptom": "E04 - Wassertank läuft leer",
          "Lösung / Notiz": (
              "Schwimmerschalter entkalken und auf Freigang prüfen."
          ),
          "Bild": "",
      },
  ])

# --- HAUPTOBERFLÄCHE ---
tab_list, tab_add = st.tabs(
    ["📂 Vorhandene Einträge", "➕ Neuen Eintrag mit Bild hinzufügen"]
)

with tab_list:
  st.subheader("Übersicht der Wissensdatenbank")

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

  for index, row in filtered_df.iterrows():
    with st.expander(
        f"🛠️ {row['Gerät / Anlage']} — {row['Fehlercode / Symptom']}"
    ):
      st.write(f"**Lösung / Notiz:** {row['Lösung / Notiz']}")
      if (
          pd.notna(row["Bild"])
          and row["Bild"] != ""
          and os.path.exists(str(row["Bild"]))
      ):
        st.image(
            row["Bild"], caption="Zugehöriges Foto", use_container_width=True
        )

with tab_add:
  st.subheader("Neuen Eintrag mit Foto erfassen")

  with st.form("add_form"):
    geraet = st.text_input("Gerät / Anlage (z.B. Carpigiani, Taylor, Convotherm):")
    fehler = st.text_input("Fehlercode / Symptom:")
    loesung = st.text_area("Lösung / Reparatur-Notiz:")
    uploaded_file = st.file_uploader(
        "📷 Foto hochladen (z.B. Display oder Bauteil):",
        type=["jpg", "jpeg", "png"],
    )

    submitted = st.form_submit_button("Eintrag speichern")

    if submitted:
      if geraet and loesung:
        image_path = ""
        if uploaded_file is not None:
          image_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
          with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

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
        st.success(
            f"Eintrag für '{geraet}' erfolgreich hinzugefügt und lokal gespeichert!"
        )
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
