import streamlit as st
import pandas as pd
import re
from datetime import datetime
import urllib.parse

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

    # Identifica i codici non trovati
    codici_trovati = df_codici["Regionale-Basilicata"].astype(str).tolist()
    codici_non_trovati = [c for c in codici if c not in codici_trovati]
    if codici_non_trovati:
        for c in codici_non_trovati:
            righe_dettaglio.append(f"<span style='color:red'>- codice non trovato: {c}</span>")

    dettaglio = "<br>".join(righe_dettaglio)

    data_oggi = datetime.today().strftime('%d/%m/%Y')
    intestazione = f"<h4>Laboratorio di analisi cliniche MONTEMURRO - Matera</h4>"
    intestazione += f"<p>Preventivo - data di generazione: {data_oggi}</p>"

    contenuto = f"1) Preventivo: € {round(totale, 2)}<br>2) Dettaglio:<br>{dettaglio}"
    blocco = f"{intestazione}<br>{contenuto}"
    return blocco

# Layout Streamlit
st.set_page_config(page_title="Preventivo Sanitario Basilicata", layout="centered")
st.title("Preventivo Sanitario - Basilicata")

st.markdown("Inserisci i codici regionali separati da virgola.\n" 
            "Puoi usare anche punti o spazi tra i numeri.\n" 
            "Esempio: 3.0.0.12.31, 3.0.0.13.82")

# Input manuale in Streamlit
input_codici = st.text_input("Scrivi qui i codici regionali:")

# Bottone di elaborazione
if st.button("Genera Preventivo") or input_codici:
    try:
        risultato_html = genera_preventivo_da_dettato(input_codici, carica_tariffario())
        st.markdown(risultato_html, unsafe_allow_html=True)

        # Codifica contenuto preventivo nell'URL per nuova finestra
        contenuto_encoded = urllib.parse.quote(risultato_html)
        html_link = f"""
        <br>
        <a href="javascript:void(0);" onclick="
            var w = window.open('', '', 'width=800,height=600');
            w.document.write(decodeURIComponent('{contenuto_encoded}'));
            w.document.title = 'Preventivo';
            w.document.close();
        ">📄 Apri in finestra per stampa</a>
        """
        st.markdown(html_link, unsafe_allow_html=True)

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
