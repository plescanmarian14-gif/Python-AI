from dataclasses import dataclass
import json
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

env_local = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY","").strip()

st.set_page_config(page_title="Magazin & Memorie")
st.title("🛒 Asistent Magazin (Ziua 7)")

if not api_key:
    st.error("Nu s-a găsit cheia în .env")
    st.stop()

client = genai.Client(api_key=api_key)


@dataclass
class Produs:
    nume: str
    pret_ron: float
    stoc: int


def verificare_stoc(produs: str) -> str:
    """Verifică stocul și prețul unui produs din magazin."""
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
        return f"Stoc: {stoc}, preț: {pret}"
    return f"{produs} nu există în magazin!"


def calculeaza_livrare(oras: str, urgenta: bool = False) -> str:
    """Calculează prețul livrării în funcție de oraș și urgență."""
    deplasari = {"iasi": 15, "pascani": 20}
    curat = oras.lower().strip()
    for v, n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat = curat.replace(v, n)
    pret_baza = deplasari.get(curat, 25)
    if urgenta:
        pret_baza += 20
        return f"Livrare urgentă în {oras}: {pret_baza} RON"
    return f"Livrare standard în {oras}: {pret_baza} RON"


FUNCTII_DISPONIBILE = {
    "verificare_stoc": verificare_stoc,
    "calculeaza_livrare": calculeaza_livrare,
}

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("Resetare chat"):
        st.session_state.messages = []
        st.rerun()

    st.metric("Mesaje în sesiune", len(st.session_state.messages))

    if st.session_state.messages:
        # Folosim dumps (cu s) și salvăm în altă variabilă decât numele modulului
        json_data = json.dumps(
            st.session_state.messages, indent=2, ensure_ascii=False
        )
        st.download_button(
            label="📥 Descarcă istoric",
            data=json_data,
            file_name="istoric_asistent.json",
            mime="application/json",
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input(
    "Scrie întrebarea ta (ex: Verifică stoc laptop și livrare la Iași)..."
):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Fereastra glisantă (Sliding Window): ultimele 6 mesaje transformate în context
    istoric_recent = st.session_state.messages[-6:]
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in istoric_recent])

    with st.chat_message("assistant"):
        with st.spinner("Procesez..."):
            try:
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"Istoric recent:\n{context_text}\n\nRăspunde la ultima cerere a utilizatorului.",
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
                                contents=f"Context conversație:\n{context_text}\n\nRezultatul funcției {nume} este: {rez}. Formulează răspunsul final.",
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