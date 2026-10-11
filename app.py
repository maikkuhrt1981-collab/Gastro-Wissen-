import difflib
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)
st.title("🔧 Gastro-Wissensdatenbank (Stabil)")

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

# --- DATENBANK INITIALISIEREN ---
if "gastro_db" not in st.session_state:
  st.session_state.gastro_db = pd.DataFrame([
      {
          "Gerät / Anlage": "Carpigiani Softeismaschine",
          "Fehlercode / Symptom": "E01 - Überdruck im Zylinder",
          "Lösung / Notiz": (
              "Kondensator auf Verschmutzung prüfen, Kühlung kontrollieren."
          ),
          "Bild": "",
      }
  ])

UPLOAD_DIR = "uploaded_images"
if not os.path.exists(UPLOAD_DIR):
  os.makedirs(UPLOAD_DIR)

tab_list, tab_add = st.tabs(["📂 Vorhandene Einträge", "➕ Neuen Eintrag mit Bild"])

with tab_list:
  st.subheader("Wissensdatenbank & Drive-Backup")

  # --- HIER IST DER EXPORT-BUTTON ---
  if not st.session_state.gastro_db.empty:
    csv_data = st.session_state.gastro_db.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="💾 Alle Einträge als CSV für Google Drive herunterladen",
        data=csv_data,
        file_name="gastro_wissen_backup.csv",
        mime="text/csv",
    )
    st.markdown("---")

  search_term = st.text_input("🔍 Suche:", "")
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
        f"🛠️ {row.get('Gerät / Anlage', '')} —"
        f" {row.get('Fehlercode / Symptom', '')}"
    ):
      st.write(f"**Lösung:** {row.get('Lösung / Notiz', '')}")
      img_path = row.get("Bild", "")
      if img_path and os.path.exists(str(img_path)):
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
    submitted = st.form_submit_button("Speichern")

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
        st.success("Erfolgreich gespeichert!")
        st.rerun()
      else:
        st.error("Bitte mindestens Gerät und Lösung ausfüllen.")
