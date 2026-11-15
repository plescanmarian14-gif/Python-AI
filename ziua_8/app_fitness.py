import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()

api_key=os.getenv("GEMINI_API_KEY","").strip()
if not api_key:
    st.error("Nu s-a gasit .env")
    st.stop()

st.set_page_config(page_title="Endorfine")
st.title("Sala de fitness")

client=genai.Client(api_key=api_key)

@dataclass
class Antrenament:
    tip:str
    durata_min:int
    calorii:int

def calculeaza_calorii(activitate:str,minute:int)->str:
    antrenamente={
        "alergare":10,
        "inot":8,
        "mers":4,
        "ciclism":9
    }
    curat=activitate.lower().strip()
    for v,n in  [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat=curat.replace(v,n)
    total_min=0
    if curat in antrenamente:
        total_min=antrenamente[curat]*minute
    else:
        return f"{curat} nu se gaseste la sala noastra"
    return f"Astazi petreceti la sala {total_min}"

def recomandare_masa(obiectiv:str)->str:
    alimentatie={
        "slabire":"Piept de pui la grătar cu salată verde - 350 kcal",
        "masa musculara":"Orez brun cu somon și avocado - 650 kcal",
        "energie":"Fulgi de ovăz cu banană și unt de arahide - 450 kcal"
    }
    curat=obiectiv.lower().strip()
    for v,n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat=curat.replace(v,n)
    if curat in alimentatie:
        return f"{alimentatie[curat]}"
    else:
        return f"Nu corespunde alegeti dintre slabire/masa musculara/energie"

FUNCTII_DISPONIBILE={
    "calculeaza_calorii":calculeaza_calorii,
    "recomandare_masa":recomandare_masa
}

if "messages" not in st.session_state:
    st.session_state.messages=[]

with st.sidebar:
    if st.button("Resetare chat"):
        st.session_state.messages=[]
        st.rerun()
    st.metric("Mesaje in sesiune",len(st.session_state.messages))
    if st.session_state.messages:
        json_data=json.dumps(
            st.session_state.messages,indent=2,ensure_ascii=False
        )
        st.download_button(
            label="Descarca",
            data=json_data,
            file_name="Istoric.json",
            mime="application/json"
        )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:=st.chat_input("Scrie intrebarea ta..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    istoric=st.session_state.messages[-6:]
    context_text="\n".join([f"{m['role']}: {m['content']}" for m in istoric])
    with st.chat_message("assitant"):
        with st.spinner("Procesez.."):
            try:
                reponse=client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"Istoric recent:\n{context_text}\n\nRăspunde la ultima cerere a utilizatorului.",
                    config=types.GenerateContentConfig(
                        tools=[calculeaza_calorii,recomandare_masa]
                    ),
                )
                text_raspuns=""
                if reponse.function_calls:
                    for call in reponse.function_calls:
                        nume=call.name
                        args=call.args
                        if nume in FUNCTII_DISPONIBILE:
                            rez=FUNCTII_DISPONIBILE[nume](**args)
                            r_final=client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"Context conversație:\n{context_text}\n\nRezultatul funcției {nume} este: {rez}. Formulează răspunsul final.",
                            )
                            text_raspuns=r_final.text
                        else:
                            text_raspuns = f"Eroare: Funcția {nume} nu există."
                else:
                    text_raspuns=(
                        reponse.text
                        if reponse.text
                        else "Nu am putut genera raspuns"
                    )
                st.markdown(text_raspuns)
                st.session_state.messages.append(
                    {"role":"assistant","content":text_raspuns}
                )
            except Exception as e:
                st.error(f"Eroare:{e}")