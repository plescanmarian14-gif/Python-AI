import json
import os
import math
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from google import genai
from google.genai import types

env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY","").strip()

if not api_key:
    st.error("Not found")
    st.stop()
client=genai.Client(api_key=api_key)
st.set_page_config(page_title="matematica")
st.title("Assistant AI")

def incarca_si_imparte(text:str,marime:int=180,overleap:int=30)->list[str]:
    bucati=[]
    for i in range(0,len(text),marime-overleap):
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

@st.cache_data
def indexeaza_fisier(texte_fisier:list[tuple[str,str]])->list[tuple[str,str,list[float]]]:
    index=[]
    for nume_fisier,text in texte_fisier:
        fragmente=incarca_si_imparte(text)
        for frag in fragmente:
            vec=obtine_vector(frag)
            index.append((nume_fisier,frag,vec))
    return index
if "messages" not in st.session_state:
    st.session_state.messages=[]
with st.sidebar:
    st.header("Document")
    fisiere_incarcate=st.file_uploader(
        "Incarca fisier",
        accept_multiple_files=True,
        type=["txt","md"]
    )
    if not fisiere_incarcate:
        st.info("Incarcati fisiere")
        st.stop()
    date_fisiere=[]
    for f in fisiere_incarcate:
        continut=f.getvalue().decode("utf-8")
        date_fisiere.append((f.name,continut))
    baza_indexata=indexeaza_fisier(date_fisiere)
    st.success(f"{len(date_fisiere)} fisiere ({len(baza_indexata)} fragmente)")
    st.divider()
    if st.button("Reseteaza chat"):
        st.session_state.messages=[]
        st.rerun()
    st.metric("Mesaje in sesiune",len(st.session.messages))
    if st.session_state.messages:
        json_data=json.dumps(st.session_state.messages,indent=2,ensure_ascii=False)
        st.download_button(
            label="Descarca",
            data=json_data,
            file_name="istoric.json",
            mime="application/json"
        )

def inregistreaza_tichet(nume_client:str,subiect:str,detalii:str)->str:
    cale_json=Path(__file__).resolve().parent / "tichete.json"
    if cale_json.exists():
        tichete=json.loads(cale_json.read_text(encoding="utf-8"))
    else:
        tichete=[]
    tichete.append(
        {
            "client":nume_client,
            "subiect":subiect,
            "detalii":detalii,
            "status":"Deschis"
        }
    )
    cale_json.write_text(json.dumps(tichete,indent=2,ensure_ascii=False),encoding="utf-8")
    return f"Tichet înregistrat cu succes pentru {nume_client} pe subiectul '{subiect}'."

def cauta_in_documente(question:str)->str:
    """search information in download document"""
    vec_intrebare=obtine_vector(question)
    scoruri=[]
    for nume_fisier,frag,vec_frag in baza_indexata:
        scor=similaritate_cosinus(vec_intrebare,vec_frag)
        if scor>=0.60:
            scoruri.append((scor,nume_fisier,frag))
    scoruri.sort(key=lambda x:x[0],reverse=True)
    top_3=[]
    for scor,nume_fisier,frag in scoruri[:3]:
        top_3.append(f"[Sursa:{nume_fisier}| Relevanta:{scor:.2f}]\n{frag}")
    if top_3:
        return "\n--\n".join(top_3)
    return "Not found"
FUNCTII_DISPONIBILE={
    "cauta_in_documente":cauta_in_documente,
    "inregistreaza_tichet": inregistreaza_tichet,
}
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt:=st.chat_input("O intrebare.."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        istoric_recent=st.session_state.messages[-6:]
        context_text="\n".join([f"{m['role']}:{m['content']}" for m in istoric_recent])
        with st.chat_message("assistant"):
            with st.spinner("caut.."):
                try:
                    response=client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=f"Istoric recent:\n{context_text}\n\nRăspunde la ultima cerere folosind documentele.",
                        config=types.GenerateContentConfig(
                            tools=[cauta_in_documente,inregistreaza_tichet]
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
                                    contents=(
                                        f"Context conversație:\n{context_text}\n\n"
                                        f"Rezultatul căutării:\n{rez}\n\n"
                                        "Formulează un răspuns clar și menționează întotdeauna numele fișierului sursă."
                                    ),
                                )
                                text_raspuns=r_final.text
                            else:
                                text_raspuns=f"Eroare {nume} nu exista"
                    else:
                        text_raspuns=response.text if response.text else "Nu am putut genera"
                    st.markdown(text_raspuns)
                    st.session_state.messages.append({"role":"assistant","content":text_raspuns})
                except Exception as e:
                    st.error(f"Eroare:{e}")
