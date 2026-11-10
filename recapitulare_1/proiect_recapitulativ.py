import os
import time
from google.genai import types
from pathlib import Path
from dataclasses import dataclass
import streamlit as st
from dotenv import load_dotenv
from google import genai

env_local = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local)
load_dotenv()

api_key=os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("Nu s-a gasit cheia")
    st.stop()

st.set_page_config(page_title="Aplicatia number 1")
st.title("Asistent Gemini")

client=genai.Client(api_key=api_key)

@dataclass
class CityReport:
    oras:str
    vreme:str
    moneda_locala:str="RON"
def afla_vremea(oras:str)->str:
    baza={
        "pascani":"20 grade",
        "iasi":"22 grade",
        "bucuresti":"18 grade"
    }
    curat=oras.lower().strip()
    for v,n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat=curat.replace(v,n)
    return baza.get(curat,f"In orasul {oras} avem aproximativ 19 grade")
def calculeaza_buget_turist(suma:float,moneda_sursa:str)->str:
    schimb={
        "EUR":5.2,
        "USD":4.6
    }
    curat=moneda_sursa.upper().strip()
    curs=schimb.get(curat)
    if curs:
        ron=suma*curs
        return f"{suma}{curat} valoreaza {ron:.2f} RON la cursul {curs}."
    return f"Curs indisponibil"
FUNCTII_MAPATE={
    "afla_vremea":afla_vremea,
    "calculeaza_buget_turist":calculeaza_buget_turist
}

if "messages" not in st.session_state:
    st.session_state.messages=[]
with st.sidebar:
    if st.button("Reseteaza chat"):
        st.session_state.messages=[]
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:= st.chat_input("Scrie..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Procesez cererea..."):
            try:
                response=client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[afla_vremea,calculeaza_buget_turist]
                    ),
                )
                if response.function_calls:
                    for call in response.function_calls:
                        nume=call.name
                        args=call.args

                        if nume in FUNCTII_MAPATE:
                            rez=FUNCTII_MAPATE[nume](**args)

                            r_final=client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"Utilizatorul a intrebat {prompt}.Rezultatul {nume} este: {rez}"
                            )
                            text_raspuns=r_final.text
                        else:
                            text_raspuns=f"Eroare:Functia {nume} nu exista."
                else:
                    text_raspuns=response.text if response.text else "Nu am putut genera raspuns"

                st.markdown(text_raspuns)
                st.session_state.messages.append({"role":"assistant","content":text_raspuns})
            except Exception as e:
                st.error(f"Eroare:{e}")
