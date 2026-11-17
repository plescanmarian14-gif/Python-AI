import os
import streamlit as st
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv
import math
from pathlib import Path


env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()
api_key=os.getenv("GEMINI_KEY_API","").strip()

if not api_key:
    st.error("Eroare")
    st.stop()
client=genai.Client(api_key=api_key)

st.set_page_config(page_title="HR")
st.title("HR ASSISTENT")

def incarcare_si_impartire(nume_fisier:str,marime:int=160,overlap:int=25)->list[str]:
    cale=Path(__file__).resolve().parent / nume_fisier
    text=cale.read_text(encoding="utf-8")
    bucati=[]
    for i in range(0,len(text),marime-overlap):
        bucati.append(text[i:i+marime])
    return bucati
def obtine_vector(text:str)->list[float]:
    raspuns=client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return raspuns.embeddings[0].values
def similaritate_vectori(v1:list[float],v2:list[float])->float:
    produs_scalar=sum(a*b for a,b in zip(v1,v2))
    norma_v1=math.sqrt(sum(a*a for a in v1))
    norma_v2=math.sqrt(sum(b*b for b in v2))
    if norma_v1==0 or norma_v2==0:
        return 0.0
    return produs_scalar/(norma_v2*norma_v1)

@st.cache_data
def indexeaza_document(nume_fisier:str)->list[tuple[str,list[float]]]:
    fragmente=incarcare_si_impartire(nume_fisier)
    index=[]
    for frag in fragmente:
        vec=obtine_vector(frag)
        index.append((frag,vec))
    return index

def cauta_potici_hr(interogare:str)->str:
    """cauta informatii despre potici hr"""
    baza_indexata=indexeaza_document("politici_hr.txt")
    vec_intrebare=obtine_vector(interogare)
    scoruri=[]
    for frag,vec_frag in baza_indexata:
        scor=similaritate_vectori(vec_intrebare,vec_frag)
        if scor>=0.60:
            scoruri.append((scor,frag))

    scoruri.sort(key=lambda x:x[0],reverse=True)
    top_2=[]
    for scor,frag in scoruri[:2]:
        top_2.append(f"[Relevanta:{scor:.2f}]{frag}")
    if top_2:
        return "\n---\n".join(top_2)
    return "Nu am gasit solutie"
FUNCTII_DISPONIBILE={
    "cauta_potici_hr":cauta_potici_hr
}
if "messages" not in st.session_state:
    st.session_state.messages=[]
with st.sidebars:
    if st.button("Reseteaza"):
        st.session_state.messages=[]
        st.rerun()
    st.metric("Mesaje primite",len(st.session_state.messages))
    if st.session_state.messages:
        json_data=json.dumps(
            st.session_state.messages,indent=2,ensure_ascii=False
        )
        st.download_button(
            data=json_data,
            label="Download",
            file_name="istoric.json",
            mime="application/json"
        )
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
if prompt:=st.chat_input("Scrie..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    istoric_recent=st.session_state.messages[-6:]
    content_text="\n".join([f"{m['role']}:{m['content']}" for m in istoric_recent])
    with st.chat_message("assistant"):
        with st.spinner("Procesez.."):
            try:
                response=client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"istoric recent:\n {content_text}\n\n Raspunse la ultima cerere",
                    config=types.GenerateContentConfig(
                        tools=[cauta_potici_hr]
                    ),
                )
                text_raspuns=""
                if response.function_calls:
                    for call in response.function_calls:
                        nume=call.name
                        args=call.args
                        if nume in FUNCTII_DISPONIBILE:
                            rez=FUNCTII_DISPONIBILE[nume](**args)
                            r_final=client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"Context conversație:\n{content_text}\n\nRezultatul funcției {nume} este: {rez}. Formulează răspunsul final.",
                            )
                            text_raspuns=r_final.text
                        else:
                            text_raspuns=f"Eroare{nume} nu exista"
                else:
                    text_raspuns=(
                        response.text
                        if response.text
                        else "Nu am putut genera raspuns"
                    )
                st.markdown(text_raspuns)
                st.session_state.messages.append(
                    {"role":"assistant","content":text_raspuns}
                )
            except Exception as e:
                st.error(f"Eroare: {e}")