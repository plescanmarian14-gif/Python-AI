import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


def incarca_imparte(nume_fisier:str,marime:int=180,overlap:int=30)->list[str]:
    cale=Path(__file__).resolve().parent / "regulament.txt"
    text=cale.read_text(encoding="utf-8")
    bucati=[]
    for i in range(0,len(text),marime-overlap):
        bucati.append(text[i : i +marime])
    return bucati

def cauta_in_regulament(interogare:str)->str:
    fragmente=incarca_imparte("regulament.txt")
    rezultate=[]
    for v,n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat=interogare.replace(v,n)
        frag_curat=fragmente.replace(v,n)
    cuvinte=curat.split()
    if any(cuv in frag_curat for cuv in cuvinte):
        rezultate.append(fragmente)
    if rezultate:
        return "\n---\n".join(rezultate)
    else:
        return "Nu am gasit info"

env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY","").strip()
client=genai.Client(api_key=api_key)


