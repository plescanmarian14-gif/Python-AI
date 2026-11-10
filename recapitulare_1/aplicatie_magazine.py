import os
from pathlib import Path
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Încărcare mediu & cheie API
env_local = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local)
load_dotenv()

api_key1 = os.getenv("GEMINI_API_KEY")
if not api_key1:
    st.error("Indisponibil: GEMINI_API_KEY nu s-a găsit!")
    st.stop()


@dataclass
class Produs:
    nume: str
    pret_ron: float
    stoc: int


st.set_page_config(page_title="Magazin Online")
st.title("⚡ Magazin Electrocasnice")
client = genai.Client(api_key=api_key1)


# 2. DEFINIRE TOOLS CU DOCSTRINGS
def verificare_stoc(produs: str) -> str:
    """Verifică stocul și prețul pentru un anumit produs.

    Args:
        produs: Numele produsului căutat (ex: laptop, telefon, casti).
    """
    depozit = {
        "laptop": ("3 bucăți", "3500 RON"),
        "telefon": ("0 bucăți", "2200 RON"),
        "casti": ("3 bucăți", "350 RON"),
    }
    curat = produs.lower().strip()
    for v, n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat = curat.replace(v, n)

    if curat in depozit:
        stoc, pret = depozit[curat]
        return f"Produsul {produs} are stoc {stoc} și costă {pret}."
    return f"Nu avem produsul {produs} în stoc."


def calculeaza_livrare(oras: str, urgenta: bool = False) -> str:
    """Calculează costul de livrare în funcție de oraș și opțiunea de urgență.

    Args:
        oras: Orașul de destinație (ex: Iași, Pașcani).
        urgenta: True pentru livrare expres/urgentă, False pentru livrare normală.
    """
    deplasari = {"iasi": 15, "pascani": 20}
    curat = oras.lower().strip()
    for v, n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat = curat.replace(v, n)

    pret_baza = deplasari.get(curat, 25)
    if urgenta:
        pret_total = pret_baza + 20
        return f"Livrare URGENTĂ în {oras}: {pret_total} RON."
    return f"Livrare STANDARD în {oras}: {pret_baza} RON."


FUNCTII_DISPONIBILE = {
    "verificare_stoc": verificare_stoc,
    "calculeaza_livrare": calculeaza_livrare,
}

# 3. INTERFAȚĂ STREAMLIT CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("Resetare chat"):
        st.session_state.messages = []
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Scrie întrebarea ta (ex: Verifică stoc laptop și livrare la Iași)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Procesez cererea..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[verificare_stoc, calculeaza_livrare]
                    ),
                )
                text_raspuns = ""
                if response.function_calls:
                    for call in response.function_calls:
                        nume = call.name
                        args = call.args
                        if nume in FUNCTII_DISPONIBILE:
                            rez = FUNCTII_DISPONIBILE[nume](**args)
                            r_final = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"Utilizatorul a întrebat: '{prompt}'. Rezultatul executării funcției {nume} este: {rez}. Răspunde-i scurt și amabil.",
                            )
                            text_raspuns = r_final.text
                        else:
                            text_raspuns = f"Eroare: Funcția {nume} nu există."
                else:
                    text_raspuns = (
                        response.text
                        if response.text
                        else "Nu am putut genera un răspuns."
                    )

                st.markdown(text_raspuns)
                st.session_state.messages.append(
                    {"role": "assistant", "content": text_raspuns}
                )

            except Exception as e:
                st.error(f"Eroare: {e}")