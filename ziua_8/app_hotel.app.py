from pathlib import Path
from google import genai
from dotenv import load_dotenv
import os

def incarcare_date(nume_fisier:str,marime:int=160,overlap:int=25)->list[str]:
    cale=Path(__file__).resolve().parent / nume_fisier
    text=cale.read_text(encoding="utf-8")
    bucati=[]
    for frag in range(0,len(text),marime-overlap):
        bucati.append(text[frag:frag+marime])
    return bucati
def cauta_info_hotel(intrebare:str)->str:
    """Caută informații despre programul hotelului, check-in, mic dejun, parcare, spa sau animale."""
    date=incarcare_date("info_hotel.txt")
    rezultate=[]
    for v, n in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat=intrebare.replace(v,n)
        frag=date.replace(v,n)
    curat=curat.split()
    if any(cuv in frag for cuv in curat):
        rezultate.append(frag)
    if rezultate:
        return "\n---\n".join(rezultate)
    else:
        return f"Nu a fost gasit"
env_local=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_local,override=True)
load_dotenv()
api_key=os.getenv("GEMINI_API_KEY","").split()
client=genai.Client(api_key=api_key)