import pandas as pd
import streamlit as st
from streamlit_gsheets import GsheetsConnection

# Seiten-Konfiguration
st.set_page_config(
    page_title="Gastro-Wissensdatenbank",
    page_icon="🔧",
    layout="centered",
)

st.title("🔧 Gastro-Wissensdatenbank")

# Passwort-Schutz
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

# --- VERBINDUNG ZU GOOGLE SHEETS ---
# Wir verbinden uns mit der Google-Tabelle über die Streamlit Connection
conn = st.connection("gsheets", type=GsheetsConnection)

# Daten aus Google Sheets laden (ttl=0 sorgt dafür, dass immer die aktuellen Daten geholt werden)
try:
  df = conn.read(ttl=0)
  if df is None or df.empty:
    df = pd.DataFrame(
        columns=["Gerät / Anlage", "Fehlercode / Symptom", "Lösung / Notiz", "Bild"]
    )
except Exception:
  df = pd.DataFrame(
      columns=["Gerät / Anlage", "Fehlercode / Symptom", "Lösung / Notiz", "Bild"]
  )

st.session_state.gastro_db = df

tab_list, tab_add = st.tabs(["📂 Vorhandene Einträge", "➕ Neuen Eintrag"])

with tab_list:
  st.subheader("Wissensdatenbank")

  search_term = st.text_input("🔍 Suche (Gerät oder Fehler):", "")
  current_df = st.session_state.gastro_db

  if search_term:
    search_lower = search_term.lower()
    mask = current_df.astype(str).apply(
        lambda x: x.str.lower().str.contains(search_lower).any(), axis=1
    )
    filtered_df = current_df[mask]
  else:
    filtered_df = current_df

  if filtered_df.empty:
    st.info("Noch keine Einträge vorhanden oder keine Treffer gefunden.")
  else:
    for index, row in filtered_df.iterrows():
      geraet = str(row.get("Gerät / Anlage", "Unbekanntes Gerät"))
      fehler = str(row.get("Fehlercode / Symptom", "Kein Fehler angegeben"))
      loesung = str(row.get("Lösung / Notiz", "Keine Lösung hinterlegt"))

      with st.expander(f"🛠️ {geraet} — {fehler}"):
        if st.button("🗑️ Diesen Eintrag löschen", key=f"del_in_{index}"):
          # Zeile aus dem DataFrame entfernen
          updated_df = st.session_state.gastro_db.drop(index).reset_index(drop=True)
          # Sofort in Google Sheets aktualisieren
          conn.update(data=updated_df)
          st.session_state.gastro_db = updated_df
          st.success("Eintrag wurde gelöscht!")
          st.rerun()

        st.markdown("---")
        st.write(f"**Lösung:** {loesung}")

        img_path = str(row.get("Bild", ""))
        if img_path and img_path != "nan" and img_path != "":
          st.image(img_path, caption="Foto-Link / Bild", use_container_width=True)

with tab_add:
  st.subheader("Neuen Eintrag erfassen")
  with st.form("add_form_gsheets", clear_on_submit=True):
    geraet_input = st.text_input("Gerät / Anlage:")
    fehler_input = st.text_input("Fehlercode / Symptom:")
    loesung_input = st.text_area("Lösung / Notiz:")
    image_link_input = st.text_input(
        "📷 Bild-Link (optional, z.B. Web-Adresse):"
    )
    submitted = st.form_submit_button("Eintrag speichern")

    if submitted:
      if geraet_input and loesung_input:
        new_row = pd.DataFrame([{
            "Gerät / Anlage": geraet_input,
            "Fehlercode / Symptom": fehler_input,
            "Lösung / Notiz": loesung_input,
            "Bild": image_link_input,
        }])

        # An bestehende Tabelle anhängen
        updated_df = pd.concat(
            [st.session_state.gastro_db, new_row], ignore_index=True
        )
        # In Google Sheets speichern
        conn.update(data=updated_df)
        st.session_state.gastro_db = updated_df

        st.success("Eintrag erfolgreich in Google Sheets gespeichert!")
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
