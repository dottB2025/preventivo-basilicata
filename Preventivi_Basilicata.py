import streamlit as st
import pandas as pd
import re

# Caricamento del file Excel con caching
@st.cache_data
def carica_tariffario(percorso="TariffarioRegioneBasilicata.xlsx"):
    return pd.read_excel(percorso)

# Funzione per generare il preventivo

def genera_preventivo_da_dettato(testo: str, df: pd.DataFrame) -> str:
    testo = testo.upper().replace("PAI", "")
    testo = testo.replace(".", "").replace(" ", "")
    codici = re.findall(r"\b\d{5,7}\b", testo)

    df_codici = df[df["Regionale-Basilicata"].astype(str).isin(codici)]
    totale = df_codici["Tariffa-Basilicata"].sum()

    righe_dettaglio = [
        f"- {row['Descrizione'].capitalize()} € {row['Tariffa-Basilicata']}"
        for _, row in df_codici.iterrows()
    ]
    dettaglio = "\n".join(righe_dettaglio)

    return f"1) Preventivo: € {round(totale, 2)}\n2) Dettaglio:\n{dettaglio}"

# Layout Streamlit
st.set_page_config(page_title="Preventivo Sanitario Basilicata", layout="centered")
st.title("Preventivo Sanitario - Basilicata")

st.markdown("Inserisci o detta i codici regionali separati da virgola.\n" 
            "Puoi usare anche punti o spazi tra i numeri.\n" 
            "Esempio: 3.0.0.12.31, 3.0.0.13.82")

# Area per testo e riconoscimento vocale
st.markdown("""
<script>
function startRecognition() {
  const recognition = new webkitSpeechRecognition();
  recognition.lang = 'it-IT';
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onresult = function(event) {
    const result = event.results[0][0].transcript;
    document.getElementById('speech_input').value = result;
    const inputEvent = new Event('input', { bubbles: true });
    document.getElementById('speech_input').dispatchEvent(inputEvent);
  };
  recognition.start();
}
</script>
<button onclick="startRecognition()">🎙️ Dettatura vocale</button>
<input id="speech_input" style="width:100%; padding:10px; margin-top:10px" />
""", unsafe_allow_html=True)

# Input testo collegato al campo JavaScript
input_codici = st.text_input("Scrivi o detta qui i codici regionali:", key="speech_input")

# Bottone di elaborazione
if st.button("Genera Preventivo") or input_codici:
    try:
        risultato = genera_preventivo_da_dettato(input_codici, carica_tariffario())
        st.text_area("Risultato del Preventivo:", risultato, height=200)
    except Exception as e:
        st.error(f"Errore durante la generazione del preventivo: {e}")

# Caricamento opzionale di un file Excel aggiornato
st.write("\nSe vuoi aggiornare il tariffario, carica un nuovo file Excel:")
file_excel = st.file_uploader("Carica nuovo tariffario", type=["xlsx"])
if file_excel:
    try:
        df = pd.read_excel(file_excel)
        st.success("Tariffario aggiornato correttamente! Rilancia il preventivo con i nuovi dati.")
    except Exception as e:
        st.error(f"Errore nel caricamento del file: {e}")