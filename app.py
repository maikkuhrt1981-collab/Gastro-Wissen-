import difflib
import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank")


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


# --- DATENBANK-INITIALISIERUNG ---
if "gastro_db" not in st.session_state:
  st.session_state.gastro_db = pd.DataFrame([
      {
          "Gerät / Anlage": "Convotherm Combi-Dämpfer",
          "Fehlercode / Symptom": "E04 - Wassertank läuft leer",
          "Lösung / Notiz": (
              "Schwimmerschalter entkalken und auf Freigang prüfen."
          ),
      },
      {
          "Gerät / Anlage": "Garland Clamshell Grill",
          "Fehlercode / Symptom": "Temperaturabweichung Oben/Unten",
          "Lösung / Notiz": (
              "Fühlerkalibrierung im Service-Menü durchführen."
          ),
      },
      {
          "Gerät / Anlage": "Henny Penny Friteuse",
          "Fehlercode / Symptom": "Heizfehler / Oil Temp Low",
          "Lösung / Notiz": (
              "Sicherheitstemperaturbegrenzer (STB) zurücksetzen."
          ),
      },
  ])

# --- HAUPTFUNKTIONEN ---
tab_list, tab_add = st.tabs(
    ["📂 Vorhandene Einträge", "➕ Neuen Eintrag hinzufügen"]
)

with tab_list:
  st.subheader("Übersicht der Wissensdatenbank")

  search_term = st.text_input(
      "🔍 Suche nach Gerät oder Fehler (mit Rechtschreibtoleranz):", ""
  )

  df = st.session_state.gastro_db

  if search_term:
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

  st.dataframe(filtered_df, use_container_width=True)

with tab_add:
  st.subheader("Neuen Eintrag erfassen")

  with st.form("add_form"):
    geraet = st.text_input("Gerät / Anlage (z.B. Carpigiani, Taylor, Convotherm):")
    fehler = st.text_input("Fehlercode / Symptom:")
    loesung = st.text_area("Lösung / Reparatur-Notiz:")

    submitted = st.form_submit_button("Eintrag speichern")

    if submitted:
      if geraet and loesung:
        new_entry = {
            "Gerät / Anlage": geraet,
            "Fehlercode / Symptom": fehler,
            "Lösung / Notiz": loesung,
        }
        st.session_state.gastro_db = pd.concat(
            [st.session_state.gastro_db, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        st.success(f"Eintrag für '{geraet}' erfolgreich hinzugefügt!")
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
