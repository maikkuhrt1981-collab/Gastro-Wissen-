import pandas as pd
import streamlit as st

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="Gastro-Wissensdatenbank", page_icon="🔧", layout="wide"
)

st.title("🔧 Gastro-Wissensdatenbank")

# Initialisierung von Session State für die Daten, damit alles direkt im Speicher bleibt
if "waffen_db" not in st.session_state:
  st.session_state.waffen_db = pd.DataFrame([
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

# Tabs für die Bedienung
tab_list, tab_add = st.tabs(
    ["📂 Vorhandene Einträge", "➕ Neuen Eintrag hinzufügen"]
)

with tab_list:
  st.subheader("Übersicht der Wissensdatenbank")

  search_term = st.text_input(
      "🔍 Suche nach Gerät oder Fehler:", ""
  )

  df = st.session_state.waffen_db

  if search_term:
    # Filterung über alle Spalten
    mask = (
        df.astype(str)
        .apply(lambda col: col.str.contains(search_term, case=False))
        .any(axis=1)
    )
    filtered_df = df[mask]
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
        # Neuen Eintrag anfügen
        st.session_state.waffen_db = pd.concat(
            [st.session_state.waffen_db, pd.DataFrame([new_entry])],
            ignore_index=True,
        )
        st.success(f"Eintrag für '{geraet}' erfolgreich hinzugefügt!")
        st.rerun()
      else:
        st.error(
            "Bitte fülle mindestens die Felder 'Gerät / Anlage' und 'Lösung /"
            " Notiz' aus."
        )
