import streamlit as st
import pandas as pd
import re
from datetime import datetime
from fpdf import FPDF
import base64
import os

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

    codici_trovati = df_codici["Regionale-Basilicata"].astype(str).tolist()
    codici_non_trovati = [c for c in codici if c not in codici_trovati]
    if codici_non_trovati:
        for c in codici_non_trovati:
            righe_dettaglio.append(f"- codice non trovato: {c}")

    dettaglio = "\n".join(righe_dettaglio)

    data_oggi = datetime.today().strftime('%d/%m/%Y')
    intestazione = "Laboratorio di analisi cliniche MONTEMURRO - Matera"
    intestazione += f"\nPreventivo - data di generazione: {data_oggi}"

    contenuto = f"{intestazione}\n\n1) Preventivo: € {round(totale, 2)}\n2) Dettaglio:\n{dettaglio}"
    return contenuto

# Funzione per creare PDF con fpdf2 e font Unicode
class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", size=12)

@st.cache_resource
def carica_font():
    import urllib.request
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/version_2_37/ttf/DejaVuSans.ttf"
        urllib.request.urlretrieve(url, font_path)
    return font_path

def crea_pdf_unicode(contenuto: str) -> bytes:
    pdf = PDF()
    font_path = carica_font()
    pdf.add_page()
    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", size=12)
    pdf.set_auto_page_break(auto=True, margin=15)
    for linea in contenuto.split("\n"):
        pdf.multi_cell(0, 10, linea)
    return pdf.output(dest='S').encode("latin1")

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
        risultato_testo = genera_preventivo_da_dettato(input_codici, carica_tariffario())
        st.text_area("Risultato del Preventivo:", risultato_testo, height=300, key="output_area")

        # Pulsante di copia (versione migliorata con Streamlit native)
        st.download_button(
            label="📋 Copia preventivo (testo)",
            data=risultato_testo,
            file_name="preventivo.txt",
            mime="text/plain"
        )

        # Genera PDF e link per download
        pdf_bytes = crea_pdf_unicode(risultato_testo)
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="preventivo.pdf">⬇️ Esporta come PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

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
