import os
from pathlib import Path
from google import genai
from dotenv import load_dotenv
import math
import streamlit as st
from google.genai import types
import json

env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY","").strip()

if not api_key:
    st.error("Nu este cheie")
    st.stop()
client=genai.Client(api_key=api_key)
st.set_page_config(page_title="Ghid IT")
st.title("Assistent IT")

def  incarca_si_imparte(nume_fisier:str,marime:int=160,overlap:int=25)->list[str]:
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

def similaritate_cosinus(v1:list[float],v2:list[float])->float:
    produs_scalar=sum(a*b for a,b in zip(v1,v2))
    norma_v1=math.sqrt(sum(a*a for a in v1))
    norma_v2=math.sqrt(sum(b*b for b in v2))
    if norma_v1==0 or norma_v2==0:
        return 0.0
    return produs_scalar/(norma_v2*norma_v1)
def cauta_solutie_it(interogare:str)->str:
    """Cauta informatii despre ghid_it"""
    fragmente=incarca_si_imparte("ghid_it.txt")
    vec_intrebare=obtine_vector(interogare)
    scoruri=[]
    for frag in fragmente:
        vec_frag=obtine_vector(frag)
        scor=similaritate_cosinus(vec_intrebare,vec_frag)
        scoruri.append((scor,frag))
    scoruri.sort(key=lambda x: x[0],reverse=True)
    top_2=[]
    for scor, frag in scoruri[:2]:
        top_2.append(f"[Relevanta:{scor:.2f}] {frag}")
    if top_2:
        return "\n---\n".join(top_2)
    return "Nu am gasit solutie"
FUNCTII_DISPONIBILE={
    "cauta_solutie_it":cauta_solutie_it,
}
if "messages" not in st.session_state:
    st.session_state.messages=[]
with st.sidebar:
    if st.button("Resetare chat"):
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
            mime="application/json",
        )
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt :=st.chat_input(
    "scrie intrebarea ta..."
):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    istoric_recent=st.session_state.messages[-6:]
    context_text = "\n".join([f"{m['role']}: {m['content']}" for m in istoric_recent])
    with st.chat_message("assistant"):
        with st.spinner("Procesez.."):
            try:
                response=client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=f"Istoric recent:\n{context_text}\n\nRăspunde la ultima cerere",
                    config=types.GenerateContentConfig(
                        tools=[cauta_solutie_it]
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
                                contents=f"Context conversație:\n{context_text}\n\nRezultatul funcției {nume} este: {rez}. Formulează răspunsul final.",

                            )
                            text_raspuns=r_final.text
                        else:
                            text_raspuns=f"Eroare {nume} nu exista"
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